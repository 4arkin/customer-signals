"""Shared plumbing: the data folder, config, frontmatter files, state, small helpers."""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import date as _date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
REPO_URL = "https://github.com/4arkin/customer-signals"
TODAY = None  # set by `--date` (tests, backdated runs); otherwise the real date


# ── the data folder ──────────────────────────────────────────────────


class Workspace:
    """Every path the tool writes. All user data lives under one folder (default
    `<repo>/data`, gitignored), so updating the tool never touches your signals."""

    def __init__(self, root):
        self.root = Path(root)
        self.config = self.root / "config.json"
        self.env = self.root / ".env"
        self.pause = self.root / ".paused"
        self.calls = self.root / "calls"
        self.notes = self.root / "notes"
        self.signals = self.root / "signals"
        self.mirror = self.root / "mirror"
        self.reports = self.root / "reports"
        self.cache = self.root / "cache"
        self.state = self.cache / "state.json"
        self.pack = self.cache / "match-pack.json"
        self.decisions = self.cache / "decisions.json"

    def dirs(self):
        return [self.calls, self.notes, self.signals, self.mirror, self.reports, self.cache]

    def rel(self, p) -> str:
        try:
            return str(Path(p).relative_to(self.root))
        except ValueError:
            return str(p)


ws = Workspace(os.environ.get("CS_DATA") or REPO / "data")


def use(root) -> Workspace:
    """Point every module at another data folder (tests, or one install serving several projects)."""
    global ws
    ws = Workspace(root)
    return ws


def load_env() -> None:
    """Read KEY=VALUE lines from data/.env. Real environment variables win."""
    if not ws.env.exists():
        return
    for line in ws.env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v and not os.environ.get(k):
            os.environ[k] = v


def today() -> str:
    return TODAY or _date.today().isoformat()


# ── config ───────────────────────────────────────────────────────────

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_config() -> dict:
    return json.loads(ws.config.read_text(encoding="utf-8"))


def config_problems(cfg: dict) -> list:
    """Everything wrong with a config, as readable lines. Empty list = valid."""
    out = []
    if not (cfg.get("project") or {}).get("name"):
        out.append("project.name is empty")
    for key, required in (("pools", True), ("segments", False)):
        items = cfg.get(key) or []
        if required and not items:
            out.append(f"{key}: add at least one")
        seen = set()
        for it in items:
            pid = (it or {}).get("id", "")
            if not SLUG.match(pid):
                out.append(f"{key}: id {pid!r} must be lowercase-kebab")
            if not (it or {}).get("about"):
                out.append(f"{key}: {pid!r} needs an 'about' line")
            if pid in seen:
                out.append(f"{key}: {pid!r} is listed twice")
            seen.add(pid)
    m = cfg.get("mirror") or {}
    if not isinstance(m.get("min_customers", 2), int) or m.get("min_customers", 2) < 1:
        out.append("mirror.min_customers must be a whole number, 1 or more")
    return out


def pool_ids(cfg) -> list:
    return [p["id"] for p in cfg.get("pools") or []]


def segment_ids(cfg) -> list:
    return [s["id"] for s in cfg.get("segments") or []]


# ── frontmatter files ────────────────────────────────────────────────
# Values are written as JSON (valid YAML too), so lists and odd characters round-trip.


def read_doc(path) -> tuple:
    """→ (frontmatter dict, body str). A file without frontmatter gives ({}, text)."""
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    meta = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith((" ", "#")):
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = _value(v.strip())
    return meta, text[end + 5:]


def _value(v: str):
    if v == "":
        return ""
    try:
        return json.loads(v)
    except ValueError:
        pass
    if v.startswith("[") and v.endswith("]"):          # hand-written YAML list: [a, b]
        return [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
    return v.strip("'\"") if len(v) > 1 and v[0] == v[-1] and v[0] in "'\"" else v


def write_doc(path, meta: dict, body: str) -> None:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str) and re.match(r"^[\w .@/+-]*$", v) and v.strip() == v and v not in ("", "true", "false", "null"):
            lines.append(f"{k}: {v}")
        else:
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    lines.append("---")
    atomic_write(path, "\n".join(lines) + "\n" + body.lstrip("\n"))


def atomic_write(path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def sections(body: str) -> dict:
    """`## Heading` → its text (heading names lowercased)."""
    out, cur, buf = {}, None, []
    for line in body.splitlines():
        if line.startswith("## "):
            if cur is not None:
                out[cur] = "\n".join(buf).strip()
            cur, buf = line[3:].strip().lower(), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf).strip()
    return out


# ── state ────────────────────────────────────────────────────────────


def load_state() -> dict:
    try:
        return json.loads(ws.state.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"matched": []}


def save_state(st: dict) -> None:
    atomic_write(ws.state, json.dumps(st, indent=1, ensure_ascii=False))


# ── text helpers ─────────────────────────────────────────────────────


def slugify(s: str, n: int = 50) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:n].rstrip("-") or "call"


def squash(s: str) -> str:
    """Collapse every run of whitespace to one space."""
    return re.sub(r"\s+", " ", s).strip()


def call_path(call_id: str) -> Path:
    return ws.calls / f"{call_id}.md"


def note_path(call_id: str) -> Path:
    return ws.notes / f"{call_id}.notes.md"
