"""`bin/cs` commands.

Exit codes: 0 done · 1 failed · 2 bad config or input · 3 waiting for the agent (a `NEXT:` line says what to do).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

from . import checks, core, intake, signals

WAIT = 3


def n(k: int, word: str) -> str:
    return f"{k} {word}" + ("" if k == 1 else "s")


def need_config():
    if not core.ws.config.exists():
        print(f"no config at {core.ws.config}. Run `bin/cs init`, then the setup interview (AGENTS.md § 2).")
        return None
    cfg = core.load_config()
    probs = core.config_problems(cfg)
    if probs:
        print("config problems:\n" + "\n".join(f"  - {p}" for p in probs))
        return None
    return cfg


# ── setup ────────────────────────────────────────────────────────────


def cmd_init(a):
    for d in core.ws.dirs():
        d.mkdir(parents=True, exist_ok=True)
    if not core.ws.config.exists():
        shutil.copy(core.REPO / "templates" / "config.example.json", core.ws.config)
        print(f"wrote {core.ws.config} from the template")
    print(f"data folder ready: {core.ws.root}")
    print("NEXT: run the setup interview (AGENTS.md § 2) and replace the example config.")
    return 0


def cmd_doctor(a):
    ok = True

    def line(good, text):
        nonlocal ok
        ok = ok and good is not False
        print(("PASS " if good else "WARN " if good is None else "FAIL ") + text)

    line(sys.version_info >= (3, 9), f"python {sys.version.split()[0]} (needs 3.9+)")
    line(core.ws.root.exists(), f"data folder {core.ws.root}")
    if core.ws.config.exists():
        cfg = core.load_config()
        probs = core.config_problems(cfg)
        line(not probs, "config valid" if not probs else "config: " + "; ".join(probs))
        example = (cfg.get("project") or {}).get("name") == "Example Co"
        line(None if example else True, "config is the template example, run the setup interview" if example
             else f"project {cfg['project']['name']}: {len(cfg.get('pools') or [])} pools, "
                  f"{len(cfg.get('segments') or [])} segments, mirror → {(cfg.get('mirror') or {}).get('store', 'none')}")
    else:
        line(False, "no config, run `bin/cs init`")
    for name in ("extract.md", "match.md"):
        line((core.REPO / "prompts" / name).exists(), f"prompts/{name}")
    cmd = os.environ.get("CS_AGENT_CMD", "")
    if cmd:
        line(bool(shutil.which(shlex.split(cmd)[0])), f"CS_AGENT_CMD → {shlex.split(cmd)[0]}")
    else:
        line(None, "CS_AGENT_CMD not set (needed only for unattended runs, see schedule/README.md)")
    calls, pend = intake.all_calls(), _pending()
    print(f"     {len(calls)} calls, {len(calls) - len(pend)} with notes, {len(signals.load_signals())} signals")
    print("DOCTOR: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def cmd_status(a):
    calls, pend = intake.all_calls(), _pending()
    rows = _index()
    print(f"{len(calls)} calls · {len(pend)} waiting for notes · {len(rows)} signals"
          + (" · PAUSED" if core.ws.pause.exists() else ""))
    for r in rows[:5]:
        print(f"  {r['rank']:>2}. {r['title']} — {n(r['customers'], 'customer')}, {n(r['calls'], 'call')}")
    return 0


# ── calls in ─────────────────────────────────────────────────────────


def cmd_add(a):
    core.ws.calls.mkdir(parents=True, exist_ok=True)
    core.ws.cache.mkdir(parents=True, exist_ok=True)
    parts = [p.strip() for p in a.participants.split(",") if p.strip()] if a.participants else None
    rc = 0
    for path in a.files:
        try:
            status, cid, info = intake.add(path, a.customer, a.date_of_call, a.title, a.segment, parts)
            print(f"{status} {cid} ({info})")
        except (OSError, ValueError) as e:
            print(f"FAIL {path}: {e}")
            rc = 1
    return rc


def _pending() -> list:
    out = []
    for cid in intake.all_calls():
        if core.note_path(cid).exists():
            continue
        if core.read_doc(core.call_path(cid))[0].get("skip"):
            continue
        out.append(cid)
    return out


def cmd_pending(a):
    todo = _pending()
    for cid in todo:
        print(f"EXTRACT {core.call_path(cid)} → {core.note_path(cid)}")
    if not todo:
        print("no calls waiting for notes")
        return 0
    print(f"NEXT: one subagent per call (never two calls in one), each following prompts/extract.md. "
          f"Then `bin/cs check`.")
    return WAIT


def cmd_skip(a):
    p = core.call_path(a.call_id)
    if not p.exists():
        print(f"no call {a.call_id}")
        return 2
    meta, body = core.read_doc(p)
    meta["skip"] = a.reason
    core.write_doc(p, meta, body)
    print(f"SKIPPED {a.call_id}: {a.reason}")
    return 0


# ── checks and signals ───────────────────────────────────────────────


def cmd_check(a):
    cfg = need_config()
    if cfg is None:
        return 2
    res = checks.check_all(cfg, a.since or "", a.call or None)
    core.atomic_write(core.ws.cache / "check.json", json.dumps(res, indent=1, ensure_ascii=False))
    bad = [r for r in res if r["errors"]]
    for r in bad:
        print(f"{r['note']}:")
        for e in r["errors"]:
            print(f"  ERROR {e}")
    q, v = sum(r["quotes"] for r in res), sum(r["verified"] for r in res)
    print(f"CHECK: {len(res)} notes · {v}/{q} quotes verified · {sum(len(r['errors']) for r in res)} errors")
    if bad:
        print("NEXT: re-extract each note with errors (delete it, then extract again), or fix the quote "
              "to the exact words in the call. Never change a call file.")
        return 1
    return 0


def cmd_plan(a):
    cfg = need_config()
    if cfg is None:
        return 2
    if core.ws.pause.exists():
        print("PAUSED (bin/cs resume to continue)")
        return 0
    pack = signals.plan(cfg)
    for cid in pack["held_notes"]:
        print(f"HELD {cid}: the note has shape errors, see `bin/cs check`")
    if not pack["new_notes"]:
        signals.rebuild(cfg)
        print("nothing new to match")
        return 0
    print(f"PACK {core.ws.rel(core.ws.pack)}: {len(pack['new_notes'])} new notes, {len(pack['signals'])} signals")
    print(f"NEXT: read {core.ws.pack}, follow its `instructions`, write {core.ws.decisions}, then `bin/cs apply`.")
    return WAIT


def cmd_apply(a):
    cfg = need_config()
    if cfg is None:
        return 2
    path = a.decisions or core.ws.decisions
    try:
        d = json.loads(open(path, encoding="utf-8").read())
    except (OSError, ValueError) as e:
        print(f"cannot read decisions {path}: {e}")
        return 2
    probs = signals.decision_problems(d)
    if probs:
        print("decisions rejected:\n" + "\n".join(f"  - {p}" for p in probs))
        return 2
    rep = signals.apply(cfg, d)
    if os.path.abspath(path) == os.path.abspath(core.ws.decisions):
        os.replace(path, core.ws.cache / f"decisions-{core.today()}.json")
    for key in ("rejected", "quote_fallbacks"):
        for x in rep[key]:
            print(f"{key.upper().rstrip('S')}: {x}")
    print(f"APPLIED: {len(rep['judged'])} notes judged · {len(rep['created'])} signals created · "
          f"{len(rep['appended'])} calls added · report {core.ws.rel(core.ws.reports / (core.today() + '.md'))}")
    return 0


def _index() -> list:
    p = core.ws.signals / "index.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def cmd_signals(a):
    rows = _index()
    if a.pool:
        rows = [r for r in rows if a.pool in r["pools"]]
    if a.segment:
        rows = [r for r in rows if a.segment in r["segments"]]
    if not a.all:
        rows = [r for r in rows if r["status"] == "open"]
    rows = [r for r in rows if r["customers"] >= a.min][:a.limit]
    if a.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return 0
    if not rows:
        print("no signals match")
    for r in rows:
        print(f"{r['rank']:>3}. {r['title']} — {n(r['customers'], 'customer')}, {n(r['calls'], 'call')} "
              f"[{', '.join(r['pools'])}] ({r['file']})")
    return 0


def cmd_mirror(a):
    cfg = need_config()
    if cfg is None:
        return 2
    signals.rebuild(cfg)
    data = json.loads((core.ws.mirror / "rows.json").read_text(encoding="utf-8"))
    if data["store"] in ("", "none"):
        print("no store configured (mirror.store is 'none'): the signals live in data/signals/ only")
        return 0
    print(f"ROWS {core.ws.rel(core.ws.mirror / 'rows.json')}: {len(data['rows'])} signals with "
          f"{data['min_customers']}+ customers → {data['store']}")
    print("NEXT: upsert every row into the store, matched on 'Signal ID'. Create missing rows, update the "
          "others. Never delete a row the owner edited.")
    return WAIT if data["rows"] else 0


def cmd_pause(a):
    core.ws.root.mkdir(parents=True, exist_ok=True)
    core.ws.pause.write_text("paused\n")
    print("PAUSED: `plan` and `run` do nothing until `bin/cs resume`")
    return 0


def cmd_resume(a):
    core.ws.pause.unlink(missing_ok=True)
    print("RESUMED")
    return 0


# ── unattended run ───────────────────────────────────────────────────


def extract_json(text: str):
    """The first JSON object in an agent's reply (fenced or bare)."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    for c in ([m.group(1)] if m else []) + ([text[text.find("{"):text.rfind("}") + 1]] if "{" in text else []):
        try:
            return json.loads(c)
        except ValueError:
            continue
    return None


def ask(cmd: str, prompt: str, timeout: int) -> tuple:
    """→ (reply, error)."""
    try:
        p = subprocess.run(shlex.split(cmd) + [prompt], capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return "", f"agent command not found: {shlex.split(cmd)[0]}"
    except subprocess.TimeoutExpired:
        return "", f"agent command timed out after {timeout}s"
    if p.returncode != 0:
        return "", f"agent command exited {p.returncode}: {p.stderr.strip()[:200]}"
    return p.stdout, ""


def _note_from(reply: str) -> str:
    m = re.search(r"```(?:markdown|md)?\s*\n(---\n.*?)```", reply, re.S)
    text = m.group(1) if m else reply[reply.find("---\n"):] if "---\n" in reply else ""
    return text.strip() + "\n" if text.startswith("---\n") else ""


def cmd_run(a):
    cfg = need_config()
    if cfg is None:
        return 2
    if core.ws.pause.exists():
        print("PAUSED")
        return 0
    cmd = a.cmd or os.environ.get("CS_AGENT_CMD", "")
    if not cmd:
        print("set CS_AGENT_CMD (see schedule/README.md) or pass --cmd")
        return 2
    rules = (core.REPO / "prompts" / "extract.md").read_text(encoding="utf-8")
    failed = []
    for cid in _pending():
        call = core.call_path(cid).read_text(encoding="utf-8")
        prompt = (f"{rules}\n\n---\n\nPools for this project: {json.dumps(cfg.get('pools'), ensure_ascii=False)}\n"
                  f"Today: {core.today()}. Write the note for call `{cid}`. Reply with ONLY the note "
                  f"(frontmatter first), no other text.\n\nCALL FILE:\n\n{call}")
        for attempt in range(2):
            reply, err = ask(cmd, prompt, a.timeout)
            note = _note_from(reply)
            if err or not note:
                err = err or "the reply held no note"
                continue
            core.atomic_write(core.note_path(cid), note)
            res = checks.check_note(core.note_path(cid), cfg, intake.all_calls)
            if not res["errors"]:
                break
            err = "; ".join(res["errors"])[:300]
            prompt += f"\n\nYOUR LAST NOTE FAILED THESE CHECKS, fix them:\n{err}\n\nYOUR LAST NOTE:\n{note}"
        if err:
            failed.append(f"{cid}: {err}")
        print(f"{'NOTE' if not err else 'FAIL'} {cid}" + (f": {err}" if err else ""))
    pack = signals.plan(cfg)
    if pack["new_notes"]:
        prompt = ("Match this customer-signals pack. Follow its `instructions` exactly. Reply with ONLY the "
                  "JSON object it asks for.\n\n" + json.dumps(pack, ensure_ascii=False))
        d = None
        for attempt in range(2):
            reply, err = ask(cmd, prompt, a.timeout)
            d = extract_json(reply) if not err else None
            if d is not None and not signals.decision_problems(d):
                break
            d = None
        if d is None:
            failed.append("match: no valid decisions from the agent")
        else:
            rep = signals.apply(cfg, d)
            print(f"APPLIED: {len(rep['created'])} created · {len(rep['appended'])} calls added")
    else:
        signals.rebuild(cfg)
    for f in failed:
        print(f"FAIL {f}")
    print(f"RUN {core.today()}: {'ok' if not failed else f'{len(failed)} failures'}")
    return 1 if failed else 0


# ── entry ────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cs", description="customer-signals: calls → ranked signals")
    ap.add_argument("--data", help="data folder (default: $CS_DATA or <repo>/data)")
    ap.add_argument("--date", help="treat today as YYYY-MM-DD")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("doctor")
    sub.add_parser("status")
    p = sub.add_parser("add", help="store transcript files as calls")
    p.add_argument("files", nargs="+")
    p.add_argument("--customer", default="")
    p.add_argument("--when", dest="date_of_call", default="", help="date of the call, YYYY-MM-DD")
    p.add_argument("--title", default="")
    p.add_argument("--segment", default="")
    p.add_argument("--participants", default="", help="comma-separated emails")
    sub.add_parser("pending")
    p = sub.add_parser("skip")
    p.add_argument("call_id")
    p.add_argument("--reason", required=True)
    p = sub.add_parser("check")
    p.add_argument("--since", default="")
    p.add_argument("--call", action="append")
    sub.add_parser("plan")
    p = sub.add_parser("apply")
    p.add_argument("--decisions")
    p = sub.add_parser("signals")
    p.add_argument("--pool")
    p.add_argument("--segment")
    p.add_argument("--min", type=int, default=1)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--all", action="store_true", help="include signals not 'open'")
    p.add_argument("--json", action="store_true")
    sub.add_parser("mirror")
    p = sub.add_parser("run", help="unattended: notes, match and apply through CS_AGENT_CMD")
    p.add_argument("--cmd")
    p.add_argument("--timeout", type=int, default=600)
    sub.add_parser("pause")
    sub.add_parser("resume")
    a = ap.parse_args(argv)
    if a.data:
        core.use(a.data)
    core.TODAY = a.date
    core.load_env()
    return globals()["cmd_" + a.command](a)
