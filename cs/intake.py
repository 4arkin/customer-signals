"""Intake: any text transcript → one normalised call file in data/calls/.

Recorders export in many shapes. This module reads the common ones (`Name: text`,
`**Name:** text`, timestamped lines, speaker-header blocks, WebVTT, SRT, plain text)
and writes one form: a speaker turn per paragraph, `Name: text`. Every quote check
runs against that body, so it is written once and never edited.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from . import core

TS = r"(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?"
LEAD_TS = re.compile(rf"^\s*(?:[\[(]\s*{TS}(?:\s*(?:-|–|—|-->)\s*{TS})?\s*[\])]|{TS})\s*[-–—]?\s*")
NAME = r"[^\W\d_][\w.'’ -]{0,38}?(?: \d{1,2})?"
BOLD = re.compile(rf"^\*\*({NAME})(?::\*\*|\*\*:)\s*(.*)$")
COLON = re.compile(rf"^({NAME}):\s+(.*)$")
HEADER = re.compile(rf"^({NAME})\s*(?:[-–—|]\s*)?[\[(]?\s*{TS}\s*[\])]?\s*$")
VTT_VOICE = re.compile(r"<v(?:\.[^ >]*)?\s+([^>]+)>(.*?)(?:</v>|$)", re.S)
TAG = re.compile(r"<[^>]+>")
NOT_NAMES = {"note", "notes", "summary", "agenda", "action items", "http", "https", "title",
             "date", "transcript", "participants", "attendees", "duration", "source", "meeting"}
DATE_IN = re.compile(r"(20\d\d)[-_.](\d\d)[-_.](\d\d)")


def _is_name(s: str, seen=None) -> bool:
    s = s.strip()
    if not s or len(s.split()) > 5 or s.lower() in NOT_NAMES:
        return False
    # a one-off label with a lowercase word is prose ("The thing is: …"), not a speaker
    if seen is not None and seen.get(s, 0) < 2 and len(s.split()) >= 2 and any(w[:1].islower() for w in s.split()):
        return False
    return True


def _label_counts(text: str) -> dict:
    counts = {}
    for line in text.split("\n"):
        s = LEAD_TS.sub("", line.strip())
        m = BOLD.match(s) or COLON.match(s)
        if m:
            counts[m.group(1).strip()] = counts.get(m.group(1).strip(), 0) + 1
    return counts


def parse(text: str) -> tuple:
    """→ (turns, labelled). A turn is (speaker or None, text)."""
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    head = text.lstrip()
    if head.startswith("WEBVTT"):
        raw = _cues(text, vtt=True)
    elif re.search(r"^\d+\n\d\d:\d\d:\d\d,\d{3}\s*-->", head, re.M):
        raw = _cues(text, vtt=False)
    else:
        raw = _lines(text)
    turns = []
    for spk, t in raw:
        t = core.squash(t)
        if not t:
            continue
        if turns and turns[-1][0] == spk and spk is not None:
            turns[-1] = (spk, turns[-1][1] + " " + t)
        else:
            turns.append((spk, t))
    named = [t for t in turns if t[0]]
    words = sum(len(t[1].split()) for t in turns) or 1
    labelled = len(named) >= 2 and sum(len(t[1].split()) for t in named) / words >= 0.5
    if not labelled:                                   # plain text: keep its paragraphs
        paras = [core.squash(p) for p in re.split(r"\n\s*\n", "\n".join(
            (f"{s}: {t}" if s else t) for s, t in raw))]
        turns = [(None, p) for p in paras if p]
    return turns, labelled


def _cues(text: str, vtt: bool) -> list:
    out = []
    for block in re.split(r"\n\s*\n", text):
        lines = [l for l in block.split("\n") if l.strip()]
        if not lines or lines[0].startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        lines = [l for l in lines if "-->" not in l and not re.fullmatch(r"\s*\d+\s*", l)]
        body = " ".join(lines)
        if vtt and VTT_VOICE.search(body):
            for name, t in VTT_VOICE.findall(body):
                out.append((name.strip(), TAG.sub("", t)))
            continue
        body = TAG.sub("", body)
        m = COLON.match(body.strip())
        out.append((m.group(1).strip(), m.group(2)) if m and _is_name(m.group(1)) else (None, body))
    return out


def _lines(text: str) -> list:
    out, cur, seen = [], None, _label_counts(text)
    for line in text.split("\n"):
        if not line.strip():
            out.append((cur, "\n\n") if cur is None else (cur, ""))
            continue
        s = LEAD_TS.sub("", line.strip())
        m = BOLD.match(s)
        if m and _is_name(m.group(1), seen):
            cur = m.group(1).strip()
            out.append((cur, m.group(2)))
            continue
        h = HEADER.match(line.strip())
        if h and _is_name(h.group(1)):
            cur = h.group(1).strip()
            continue
        m = COLON.match(s)
        if m and _is_name(m.group(1), seen):
            cur = m.group(1).strip()
            out.append((cur, m.group(2)))
            continue
        out.append((cur, s))
    return out


def render(turns, labelled: bool) -> str:
    return "\n\n".join(f"{s}: {t}" if labelled and s else t for s, t in turns) + "\n"


def load_turns(call_id: str) -> tuple:
    """→ (meta, turns) for a stored call."""
    meta, body = core.read_doc(core.call_path(call_id))
    turns = []
    for para in re.split(r"\n\s*\n", body.strip()):
        para = para.strip()
        if not para:
            continue
        if meta.get("labelled") and ": " in para:
            s, t = para.split(": ", 1)
            turns.append((s, t))
        else:
            turns.append((None, para))
    return meta, turns


def all_calls() -> list:
    return sorted(p.stem for p in core.ws.calls.glob("*.md")) if core.ws.calls.exists() else []


def add(path: str, customer="", date="", title="", segment="", participants=None, source="") -> tuple:
    """Store one transcript. → (status, call_id, info). status: ADDED | SAME."""
    raw = Path(path).read_bytes().decode("utf-8", errors="replace")
    given = {}
    if raw.startswith("---\n"):                        # an agent may hand over frontmatter
        tmp = core.ws.cache / "intake.tmp"
        core.atomic_write(tmp, raw)
        given, raw = core.read_doc(tmp)
        tmp.unlink()
    turns, labelled = parse(raw)
    if not turns:
        raise ValueError(f"{path}: no text found")
    body = render(turns, labelled)
    sha = hashlib.sha256(body.encode()).hexdigest()[:16]
    for cid in all_calls():
        if core.read_doc(core.call_path(cid))[0].get("sha") == sha:
            return "SAME", cid, "already stored"
    name = Path(path).name
    title = title or given.get("title") or Path(path).stem
    m = DATE_IN.search(date or str(given.get("date", "")) or name) or DATE_IN.search(raw[:3000])
    date = "-".join(m.groups()) if m else core.today()
    customer = customer or given.get("customer", "")
    parts = participants if participants is not None else given.get("participants") or []
    if isinstance(parts, str):
        parts = [p.strip() for p in parts.split(",") if p.strip()]
    base = f"{date}_{core.slugify(customer or title, 40)}"
    call_id, n = base, 2
    while core.call_path(call_id).exists():
        call_id, n = f"{base}-{n}", n + 1
    speakers = sorted({s for s, _ in turns if s})
    meta = {"call_id": call_id, "date": date, "title": title, "customer": customer,
            "segment": segment or given.get("segment", ""), "participants": parts,
            "speakers": speakers, "labelled": labelled, "source": source or given.get("source") or name,
            "sha": sha}
    core.write_doc(core.call_path(call_id), meta, body)
    info = f"{len(turns)} turns, " + (f"speakers: {', '.join(speakers)}" if labelled else "no speaker labels")
    return "ADDED", call_id, info
