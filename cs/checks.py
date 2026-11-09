"""Checks on the agent's notes. Read-only: they report, they never repair.

1. Quote fidelity: every quote is an exact piece of ONE speaker's turn in ITS call.
2. Wrong call: a quote that is missing from its call but present in another call.
3. Speaker: the name on a quote is the speaker who said it (labelled calls only).
4. Shape: the note has its frontmatter and every heading, once, in order.
"""

from __future__ import annotations

import re

from . import core, intake

HEADINGS = ["customer context", "pains", "gains", "their words", "workflow",
            "tools and alternatives", "decision", "requests", "quote bank", "open questions"]
REQUIRED = ["call_id", "customer", "pools", "extracted_at", "quality"]
QUALITY = {"clean", "partial", "poor"}
GAP = re.compile(r"\s*(?:\[(?:…|\.\.\.)\]|…|\.\.\.)\s*")
WRAP = {'"': '"', "“": "”", "'": "'", "‘": "’", "«": "»"}
INLINE = re.compile(r"[\"“]([^\"”]{12,}?)[\"”]")
NOBODY = {"", "unattributed", "unknown", "speaker"}


def strip_wrapper(q: str) -> str:
    q = core.squash(q)
    if len(q) > 1 and q[0] in WRAP and q[-1] == WRAP[q[0]]:
        q = q[1:-1].strip()
    return q


def find(quote: str, turns) -> int:
    """Index of the one turn that holds every piece of the quote, in order. -1 if none."""
    parts = [p for p in GAP.split(strip_wrapper(quote)) if p]
    if not parts:
        return -1
    for i, (_, text) in enumerate(turns):
        pos = 0
        for p in parts:
            j = text.find(p, pos)
            if j == -1:
                break
            pos = j + len(p)
        else:
            return i
    return -1


def classify(quote: str, turns, call_id: str, corpus) -> str:
    """Why a quote failed: recased | wrong-call:<id> | reworded | not-found."""
    q = strip_wrapper(quote)
    low = q.lower()
    if any(low in t.lower() for _, t in turns):
        return "recased"
    for other in corpus():
        if other != call_id and find(q, intake.load_turns(other)[1]) >= 0:
            return f"wrong-call:{other}"
    words = set(re.findall(r"\w+", low))
    best = max((len(words & set(re.findall(r"\w+", t.lower()))) for _, t in turns), default=0)
    return "reworded" if words and best >= 0.6 * len(words) else "not-found"


def quote_bank(text: str) -> list:
    """`> quote` blocks with their `— Speaker, on topic` line. → [(quote, speaker)]."""
    out, buf, spk = [], [], None
    for line in text.splitlines() + [""]:
        s = line.strip()
        if s.startswith(">"):
            if buf and spk is not None:
                out.append((" ".join(buf), spk))
                buf, spk = [], None
            buf.append(s.lstrip("> ").strip())
        elif s and (s[0] in "—–" or s.startswith("-- ")):
            if buf:
                spk = s.lstrip("—–- ").strip()
        else:
            if buf:
                out.append((" ".join(buf), spk or ""))
            buf, spk = [], None
    return [(q, re.split(r",| on | at |\(", s or "", maxsplit=1)[0].strip()) for q, s in out if q]


def _norm_name(n: str) -> list:
    return re.sub(r"[^\w ]", " ", n.lower()).split()


def name_matches(a: str, b: str) -> bool:
    x, y = _norm_name(a), _norm_name(b)
    if not x or not y:
        return False
    if x == y:
        return True
    short, long_ = (x, y) if len(x) <= len(y) else (y, x)
    if long_[:len(short)] == short:                    # "Ana" vs "Ana Ruiz"
        return True
    return x[-1] == y[-1] and x[0][0] == y[0][0]       # "A. Ruiz" vs "Ana Ruiz"


def check_note(path, cfg, corpus) -> dict:
    meta, body = core.read_doc(path)
    res = {"note": core.ws.rel(path), "call_id": meta.get("call_id", ""), "errors": [], "info": [],
           "quotes": 0, "verified": 0}
    err, info = res["errors"].append, res["info"].append
    for k in REQUIRED:
        if k not in meta:
            err(f"shape: missing frontmatter key '{k}'")
    if meta.get("quality") and meta["quality"] not in QUALITY:
        err(f"shape: quality must be one of {sorted(QUALITY)}")
    unknown = [p for p in meta.get("pools") or [] if p not in core.pool_ids(cfg)]
    if unknown:
        err(f"shape: unknown pools {unknown}; use only {core.pool_ids(cfg)}")
    heads = [l[3:].strip().lower() for l in body.splitlines() if l.startswith("## ")]
    if heads != HEADINGS:
        missing = [h for h in HEADINGS if h not in heads]
        err("shape: headings must be, in order: " + " · ".join(HEADINGS)
            + (f" (missing: {', '.join(missing)})" if missing else ""))
    cid = meta.get("call_id", "")
    if not core.call_path(cid).exists():
        err(f"shape: call '{cid}' not found in calls/")
        return res
    cmeta, turns = intake.load_turns(cid)
    sec = core.sections(body)
    bank = quote_bank(sec.get("quote bank", ""))
    if not bank and not sec.get("quote bank", "").startswith("_("):
        err("shape: Quote bank has no quotes")
    spans = [(q, None) for q in INLINE.findall(sec.get("their words", ""))]
    for q, spk in bank + spans:
        res["quotes"] += 1
        i = find(q, turns)
        if i < 0:
            err(f"quote {classify(q, turns, cid, corpus)}: \"{core.squash(q)[:90]}\"")
            continue
        res["verified"] += 1
        said_by = turns[i][0]
        if spk is None or not cmeta.get("labelled"):
            continue
        if spk.lower() in NOBODY:
            info(f"speaker: unattributed \"{core.squash(q)[:50]}\" (said by {said_by})")
        elif not name_matches(spk, said_by or ""):
            err(f"speaker: \"{core.squash(q)[:60]}\" is credited to {spk}, but {said_by} said it")
    return res


def check_all(cfg, since: str = "", only=None) -> list:
    if not core.ws.notes.exists():
        return []
    calls = intake.all_calls
    out = []
    for p in sorted(core.ws.notes.glob("*.notes.md")):
        meta, _ = core.read_doc(p)
        if only and meta.get("call_id") not in only:
            continue
        if since and str(meta.get("extracted_at", "")) < since:
            continue
        out.append(check_note(p, cfg, calls))
    return out
