"""Notes → signals. The engine does all bookkeeping; the agent makes one judgment.

`plan` packs the new notes and the existing signals into one file. The agent reads it
and decides which notes back which signals (`appends`) and which patterns are new
(`new`). `apply` verifies every quote against its call, writes the records, and
recomputes every count from the record's Log, so a count can never drift.

A signal's rank is the number of distinct customers behind it. Calls are shown
beside it: one talkative customer on five calls is one customer.
"""

from __future__ import annotations

import json
import re
from collections import Counter

from . import checks, core, intake

PERSONAL = {"gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "yahoo.com",
            "icloud.com", "me.com", "proton.me", "protonmail.com", "aol.com", "gmx.com", "gmx.de",
            "mail.ru", "yandex.ru", "hey.com", "fastmail.com"}
INFRA = {"fireflies.ai", "otter.ai", "fathom.video", "tldv.io", "read.ai", "gong.io", "chorus.ai",
         "zoom.us", "calendly.com", "granola.so", "grain.com", "airgram.io", "krisp.ai",
         "google.com", "microsoft.com", "teams.microsoft.com", "resource.calendar.google.com"}
STOP = {"inc", "ltd", "llc", "gmbh", "sa", "bv", "ag", "plc", "co", "corp", "the", "limited", "company"}
SECOND_LEVEL = {"co", "com", "ac", "org", "gov", "net", "edu"}
LOG = re.compile(r"^- (\d{4}-\d{2}-\d{2}) — (.*?) — call `([^`]+)`(?:: (.*))?$")
EVIDENCE_MAX = 5
TOP = 3


# ── who is the customer ──────────────────────────────────────────────


def registrable(domain: str) -> str:
    parts = domain.lower().strip(".").split(".")
    if len(parts) >= 3 and parts[-2] in SECOND_LEVEL and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def norm_name(s: str) -> str:
    s = re.sub(r"\(.*?\)", " ", s.lower())
    return " ".join(w for w in re.findall(r"[^\W_]+", s) if w not in STOP)


def _ours(cfg) -> set:
    return {d.lower().lstrip("@") for d in (cfg.get("project") or {}).get("our_domains") or []}


def email_key(meta: dict, cfg) -> str:
    """A company domain, else a personal address (a person is the customer). '' if none."""
    ours, doms, people = _ours(cfg), Counter(), []
    for e in meta.get("participants") or []:
        e = str(e).strip().lower()
        if "@" not in e:
            continue
        d = e.split("@", 1)[1]
        if any(d == o or d.endswith("." + o) for o in ours) or d in INFRA or registrable(d) in INFRA:
            continue
        if d in PERSONAL:
            people.append(e)
        else:
            doms[registrable(d)] += 1
    if doms:
        return "domain:" + doms.most_common(1)[0][0]
    return "email:" + people[0] if people else ""


def alias_map(cfg) -> dict:
    """Customer name → email key, learned from calls that carry both."""
    out = {}
    for cid in intake.all_calls():
        meta = core.read_doc(core.call_path(cid))[0]
        k, n = email_key(meta, cfg), norm_name(str(meta.get("customer", "")))
        if k and n:
            out.setdefault(n, k)
    return out


def customer_key(meta: dict, cfg, aliases: dict) -> str:
    """The identity a call counts under. '' = unresolved: shown, never counted."""
    k = email_key(meta, cfg)
    if k:
        return k
    n = norm_name(str(meta.get("customer", "")))
    return aliases.get(n) or ("name:" + n if n else "")


# ── records ──────────────────────────────────────────────────────────


def sig_path(sid):
    return core.ws.signals / f"{sid}.md"


def load_signals() -> dict:
    if not core.ws.signals.exists():
        return {}
    return {p.stem: core.read_doc(p) for p in sorted(core.ws.signals.glob("*.md")) if p.stem != "INDEX"}


def log_rows(body: str) -> list:
    return [m.groups() for m in map(LOG.match, core.sections(body).get("log", "").splitlines()) if m]


def note_quotes(call_id: str) -> list:
    """The note's Quote bank, in file order, as (quote, speaker)."""
    p = core.note_path(call_id)
    if not p.exists():
        return []
    return checks.quote_bank(core.sections(core.read_doc(p)[1]).get("quote bank", ""))


def verified(call_id: str, quote: str) -> tuple:
    """→ (quote, speaker) if the quote is an exact piece of the call, else ('', '').
    No fallback to another quote: a quote about a different topic is worse evidence than none."""
    if not quote:
        return "", ""
    _, turns = intake.load_turns(call_id)
    i = checks.find(quote, turns)
    if i < 0:
        return "", ""
    q = checks.strip_wrapper(quote)
    spk = next((s for b, s in note_quotes(call_id) if checks.strip_wrapper(b) == q), "") or turns[i][0] or ""
    return q, spk


def recompute(meta: dict, body: str, cfg, aliases) -> dict:
    """Counts come from the Log, every time. Nothing is incremented."""
    rows = log_rows(body)
    keys, segs, dates = set(), set(meta.get("segments") or []), []
    unresolved = 0
    for date, _, cid, _ in rows:
        dates.append(date)
        cm = core.read_doc(core.call_path(cid))[0] if core.call_path(cid).exists() else {}
        k = customer_key(cm, cfg, aliases)
        if k:
            keys.add(k)
        else:
            unresolved += 1
        if cm.get("segment"):
            segs.add(cm["segment"])
    meta.update({"customers": len(keys), "calls": len({r[2] for r in rows}), "unresolved": unresolved,
                 "segments": sorted(segs), "first_seen": min(dates) if dates else "",
                 "last_seen": max(dates) if dates else ""})
    meta.setdefault("status", "open")
    return meta


def _label(cm: dict) -> str:
    if cm.get("customer"):
        return str(cm["customer"])
    ek = email_key(cm, {"project": {}})
    return ek.split(":", 1)[1] if ek else "unknown customer"


def _log_line(cid: str, quote: str) -> str:
    cm = core.read_doc(core.call_path(cid))[0]
    q = f': "{quote}"' if quote else ""
    return f"- {cm.get('date', '')} — {_label(cm)} — call `{cid}`{q}"


def _evidence_line(cid: str, quote: str, spk: str) -> str:
    cm = core.read_doc(core.call_path(cid))[0]
    who = " · ".join(x for x in (spk, _label(cm), str(cm.get("date", ""))) if x)
    return f'- "{quote}" — {who} · call `{cid}`'


def render(meta: dict, title: str, description: str, evidence: list, log: list) -> str:
    return (f"# {title}\n\n> {description}\n\n## Evidence\n\n" + ("\n".join(evidence) or "_(none yet)_")
            + "\n\n## Log\n\n" + "\n".join(log) + "\n")


def _parts(body: str) -> tuple:
    sec = core.sections(body)
    m = re.search(r"^> (.*)$", body, re.M)
    ev = [l for l in sec.get("evidence", "").splitlines() if l.startswith("- ")]
    log = [l for l in sec.get("log", "").splitlines() if l.startswith("- ")]
    return (m.group(1) if m else ""), ev, log


# ── plan ─────────────────────────────────────────────────────────────


def plan(cfg) -> dict:
    """The match pack: new notes + the signal index. Writes cache/match-pack.json."""
    done = set(core.load_state().get("matched", []))
    new, held = [], []
    for res in checks.check_all(cfg):
        cid = res["call_id"]
        if not cid or cid in done:
            continue
        if any(e.startswith("shape:") for e in res["errors"]):
            held.append(cid)                           # fix the note first; apply would misread it
            continue
        meta, body = core.read_doc(core.note_path(cid))
        cm = core.read_doc(core.call_path(cid))[0]
        sec = core.sections(body)
        tops = []
        for q, s in note_quotes(cid):
            if checks.find(q, intake.load_turns(cid)[1]) >= 0:
                tops.append({"quote": checks.strip_wrapper(q), "speaker": s})
            if len(tops) == TOP:
                break
        new.append({"call_id": cid, "date": cm.get("date", ""), "customer": _label(cm),
                    "segment": cm.get("segment", ""), "pools": meta.get("pools") or [],
                    "pains": core.squash(sec.get("pains", ""))[:700],
                    "gains": core.squash(sec.get("gains", ""))[:400],
                    "requests": core.squash(sec.get("requests", ""))[:300], "top_quotes": tops})
    index = []
    for sid, (meta, body) in load_signals().items():
        desc, _, _ = _parts(body)
        index.append({"id": sid, "title": meta.get("title", ""), "pools": meta.get("pools") or [],
                      "customers": meta.get("customers", 0), "calls": meta.get("calls", 0),
                      "description": desc[:200]})
    prompt = core.REPO / "prompts" / "match.md"
    pack = {"instructions": prompt.read_text(encoding="utf-8") if prompt.exists() else "",
            "pools": cfg.get("pools") or [], "segments": cfg.get("segments") or [],
            "decision_schema": {
                "appends": [{"signal_id": "existing signal id", "call_id": "call id from new_notes",
                             "quote": "one exact quote from that call's top_quotes"}],
                "new": [{"id": "kebab-case-id", "title": "short name of the pattern",
                         "pools": ["pool ids"], "description": "1-2 sentences: the pattern and why it matters",
                         "members": ["call ids"], "evidence": [{"call_id": "id", "quote": "exact quote"}]}]},
            "signals": index, "new_notes": new, "held_notes": held}
    core.atomic_write(core.ws.pack, json.dumps(pack, indent=1, ensure_ascii=False))
    return pack


# ── apply ────────────────────────────────────────────────────────────


def decision_problems(d) -> list:
    if not isinstance(d, dict):
        return ["decisions must be a JSON object with 'appends' and 'new'"]
    out = []
    for key, need in (("appends", ("signal_id", "call_id")), ("new", ("id", "title", "members"))):
        if not isinstance(d.get(key, []), list):
            out.append(f"'{key}' must be a list")
            continue
        for i, row in enumerate(d.get(key, [])):
            miss = [k for k in need if not (isinstance(row, dict) and row.get(k))]
            if miss:
                out.append(f"{key}[{i}]: missing {', '.join(miss)}")
    return out


def apply(cfg, d: dict) -> dict:
    pack = json.loads(core.ws.pack.read_text(encoding="utf-8")) if core.ws.pack.exists() else {"new_notes": []}
    judged = [n["call_id"] for n in pack.get("new_notes", [])]
    known_pools = set(core.pool_ids(cfg))
    sigs = load_signals()
    aliases = alias_map(cfg)
    rep = {"appended": [], "created": [], "skipped": [], "quote_fallbacks": [], "rejected": []}
    touched = {}

    def ok_call(cid):
        return core.call_path(cid).exists() and core.note_path(cid).exists()

    def add_to(sid, cid, quote):
        meta, body = touched.get(sid) or sigs[sid]
        desc, ev, log = _parts(body)
        if any(f"call `{cid}`" in l for l in log):
            rep["skipped"].append(f"{sid} ← {cid} (already in its log)")
            return
        q, spk = verified(cid, quote)
        if quote and checks.strip_wrapper(quote) != q:
            rep["quote_fallbacks"].append(f"{sid} ← {cid}: quote not found in the call; logged without a quote")
        log.append(_log_line(cid, q))
        if q and len(ev) < EVIDENCE_MAX and not any(q in l for l in ev):
            ev.append(_evidence_line(cid, q, spk))
        touched[sid] = (meta, render(meta, meta.get("title", sid), desc, ev, log))
        rep["appended"].append(f"{sid} ← {cid}")

    for row in d.get("new", []):
        sid = core.slugify(str(row["id"]), 60)
        members = [c for c in dict.fromkeys(list(row.get("members") or [])
                   + [e.get("call_id") for e in row.get("evidence") or [] if isinstance(e, dict)]) if c]
        bad = [c for c in members if not ok_call(c)]
        members = [c for c in members if ok_call(c)]
        if bad:
            rep["rejected"].append(f"{sid}: unknown calls {bad}")
        if not members:
            rep["rejected"].append(f"{sid}: no valid calls; not created")
            continue
        quotes = {e["call_id"]: e.get("quote", "") for e in row.get("evidence") or []
                  if isinstance(e, dict) and e.get("call_id")}
        if sid not in sigs and sid not in touched:
            pools = [p for p in row.get("pools") or [] if p in known_pools]
            dropped = [p for p in row.get("pools") or [] if p not in known_pools]
            if dropped:
                rep["rejected"].append(f"{sid}: unknown pools {dropped} dropped")
            meta = {"id": sid, "title": core.squash(str(row["title"])), "pools": pools,
                    "segments": [s for s in row.get("segments") or [] if s in core.segment_ids(cfg)],
                    "status": "open"}
            touched[sid] = (meta, render(meta, meta["title"], core.squash(str(row.get("description", ""))), [], []))
            rep["created"].append(sid)
        for c in members:
            add_to(sid, c, quotes.get(c, ""))

    for row in d.get("appends", []):
        sid, cid = str(row["signal_id"]), str(row["call_id"])
        if sid not in sigs and sid not in touched:
            rep["rejected"].append(f"append to unknown signal '{sid}'")
            continue
        if not ok_call(cid):
            rep["rejected"].append(f"{sid}: unknown call '{cid}'")
            continue
        add_to(sid, cid, str(row.get("quote", "")))

    for sid, (meta, body) in touched.items():
        meta = recompute(meta, body, cfg, aliases)
        desc, ev, log = _parts(body)
        core.write_doc(sig_path(sid), meta, render(meta, meta.get("title", sid), desc, ev, log))
    st = core.load_state()
    st["matched"] = sorted(set(st.get("matched", [])) | set(judged))
    core.save_state(st)
    rep["judged"] = judged
    rebuild(cfg)
    _report(rep)
    return rep


# ── outputs ──────────────────────────────────────────────────────────


def rebuild(cfg) -> list:
    """Recompute every record, then write the ranked index and the mirror rows."""
    aliases = alias_map(cfg)
    rows = []
    for sid, (meta, body) in load_signals().items():
        old = dict(meta)
        meta = recompute(meta, body, cfg, aliases)
        if meta != old:
            core.write_doc(sig_path(sid), meta, body)
        desc, ev, _ = _parts(body)
        rows.append({"id": sid, "title": meta.get("title", ""), "status": meta.get("status", "open"),
                     "customers": meta["customers"], "calls": meta["calls"], "unresolved": meta["unresolved"],
                     "pools": meta.get("pools") or [], "segments": meta.get("segments") or [],
                     "first_seen": meta["first_seen"], "last_seen": meta["last_seen"], "description": desc,
                     "quotes": [re.sub(r"^- ", "", l) for l in ev[:TOP]], "file": core.ws.rel(sig_path(sid))})
    rows.sort(key=lambda r: (-r["customers"], -r["calls"], -int(r["last_seen"].replace("-", "") or 0), r["id"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    core.atomic_write(core.ws.signals / "index.json", json.dumps(rows, indent=1, ensure_ascii=False))
    lines = ["# Signals", "", f"Ranked by distinct customers. Updated {core.today()}.", "",
             "| # | Signal | Customers | Calls | Pools | Last seen |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['rank']} | [{r['title']}]({r['id']}.md) | {r['customers']} | {r['calls']} | "
                     f"{', '.join(r['pools'])} | {r['last_seen']} |")
    core.atomic_write(core.ws.signals / "INDEX.md", "\n".join(lines) + "\n")
    m = cfg.get("mirror") or {}
    floor = m.get("min_customers", 2)
    mirror = [{"Signal ID": r["id"], "Title": r["title"], "Rank": r["rank"], "Customers": r["customers"],
               "Calls": r["calls"], "Pools": r["pools"], "Segments": r["segments"], "Status": r["status"],
               "First seen": r["first_seen"], "Last seen": r["last_seen"], "Description": r["description"],
               "Quotes": r["quotes"]} for r in rows if r["customers"] >= floor]
    core.atomic_write(core.ws.mirror / "rows.json", json.dumps(
        {"store": m.get("store", "none"), "min_customers": floor, "generated": core.today(),
         "upsert_key": "Signal ID", "rows": mirror}, indent=1, ensure_ascii=False))
    return rows


def _report(rep: dict) -> None:
    out = [f"# Run {core.today()}", "",
           f"- Notes judged: {len(rep['judged'])}",
           f"- Signals created: {len(rep['created'])}",
           f"- Calls added to signals: {len(rep['appended'])}", ""]
    for key, title in (("created", "Created"), ("appended", "Added"), ("quote_fallbacks", "Quote fallbacks"),
                       ("rejected", "Rejected"), ("skipped", "Skipped")):
        if rep[key]:
            out += [f"## {title}", ""] + [f"- {x}" for x in rep[key]] + [""]
    path = core.ws.reports / f"{core.today()}.md"
    prev = path.read_text(encoding="utf-8") + "\n---\n\n" if path.exists() else ""
    core.atomic_write(path, prev + "\n".join(out))
