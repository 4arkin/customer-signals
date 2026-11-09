"""Offline tests. Run: python3 -m unittest discover -s tests"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cs import checks, core, intake, signals  # noqa: E402
from cs.cli import main  # noqa: E402

CONFIG = {
    "project": {"name": "Test Co", "description": "x", "our_domains": ["testco.com"], "our_names": ["Sam Lee"]},
    "pools": [{"id": "product", "about": "backlog"}, {"id": "sales", "about": "deals"}],
    "segments": [{"id": "agencies", "about": "agencies"}],
    "mirror": {"store": "Notion", "min_customers": 2},
}

NORTHWIND = """Sam Lee: Thanks for joining. How is onboarding going?
Ana Ruiz: Honestly it takes us two weeks to onboard a new client, every single time.
Sam Lee: Where does the time go?
Ana Ruiz: We copy the brief by hand into three tools, and nobody owns the checklist.
"""
NORTHWIND_2 = """**Sam Lee:** Back again. Anything new?
**Ana Ruiz:** Onboarding still eats two weeks per client and the team hates it.
"""
BLUEFIN_VTT = """WEBVTT

1
00:00:01.000 --> 00:00:04.000
<v Sam Lee>What slows your team down?</v>

2
00:00:04.000 --> 00:00:09.000
<v Tom Berg>Every new client means two weeks of setup</v>

3
00:00:09.000 --> 00:00:12.000
<v Tom Berg>before we bill a single hour.</v>
"""
SOLO_TXT = """Notes from a call with a freelancer.

She said onboarding a client takes her about a week of admin.

She pays for two tools that overlap.
"""


def note(cid, customer, quotes, pools=("product",), drop=None):
    heads = ["Customer context", "Pains", "Gains", "Their words", "Workflow", "Tools and alternatives",
             "Decision", "Requests", "Quote bank", "Open questions"]
    bank = "\n\n".join(f"> {q}\n— {s}, on onboarding" for q, s in quotes)
    body = "\n\n".join(f"## {h}\n\n" + (bank if h == "Quote bank" else "_(none observed)_")
                       for h in heads if h != drop)
    path = core.note_path(cid)
    core.write_doc(path, {"call_id": cid, "customer": customer, "pools": list(pools),
                          "extracted_at": "2026-11-09", "extracted_by": "test", "quality": "partial"},
                   f"# {cid}\n\n{body}\n")
    return path


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="cs-test-"))
        self.src = self.tmp / "src"
        self.src.mkdir()
        self.data = self.tmp / "data"
        self.cs("init")
        core.atomic_write(core.ws.config, json.dumps(CONFIG))

    def tearDown(self):
        shutil.rmtree(self.tmp)
        core.use(core.REPO / "data")
        core.TODAY = None

    def cs(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = main(["--data", str(self.data), "--date", "2026-11-09", *args])
        return rc, out.getvalue()

    def add(self, name, text, *extra):
        p = self.src / name
        p.write_text(text)
        rc, out = self.cs("add", str(p), *extra)
        self.assertEqual(rc, 0, out)
        return out.split()[1]


class Intake(Base):
    def test_formats(self):
        cases = {
            "colon": ("Ana: one thing\nTom: another", [("Ana", "one thing"), ("Tom", "another")]),
            "bold": ("**Ana:** first\n**Tom:** second\nmore", [("Ana", "first"), ("Tom", "second more")]),
            "timestamps": ("[00:01] Ana: one\n00:05 Tom: two\n(0:09) Ana: three",
                           [("Ana", "one"), ("Tom", "two"), ("Ana", "three")]),
            "ranges": ("[00:05 - 00:08] Ana: one\n[00:08 - 00:11] Ana: more\n[01:02:03 - 01:02:05] Tom: two",
                       [("Ana", "one more"), ("Tom", "two")]),
            "headers": ("Ana Ruiz  0:03\nWe pay for two tools.\n\nTom  0:09\nWhich ones?",
                        [("Ana Ruiz", "We pay for two tools."), ("Tom", "Which ones?")]),
            "srt": ("1\n00:00:01,000 --> 00:00:02,000\nAna: Hello there\n\n2\n00:00:02,000 --> 00:00:03,000\nTom: Hi",
                    [("Ana", "Hello there"), ("Tom", "Hi")]),
        }
        for name, (text, want) in cases.items():
            self.assertEqual(intake.parse(text), (want, True), name)
        turns, labelled = intake.parse(BLUEFIN_VTT)
        self.assertTrue(labelled)
        self.assertEqual(turns[1], ("Tom Berg", "Every new client means two weeks of setup before we bill a single hour."))

    def test_prose_colon_is_not_a_speaker(self):
        turns, _ = intake.parse("Ana: first\nTom: second\nAna: The thing is clear\nthe thing is: it breaks")
        self.assertNotIn("the thing is", [s for s, _ in turns])

    def test_plain_text_keeps_paragraphs(self):
        turns, labelled = intake.parse(SOLO_TXT)
        self.assertFalse(labelled)
        self.assertEqual(len(turns), 3)

    def test_add_is_idempotent_and_ids_are_unique(self):
        a = self.add("2026-11-03 northwind.txt", NORTHWIND, "--customer", "Northwind")
        self.assertEqual(a, "2026-11-03_northwind")
        rc, out = self.cs("add", str(self.src / "2026-11-03 northwind.txt"))
        self.assertTrue(out.startswith("SAME"))
        b = self.add("other.txt", NORTHWIND_2, "--customer", "Northwind", "--when", "2026-11-03")
        self.assertEqual(b, "2026-11-03_northwind-2")
        self.assertEqual(core.read_doc(core.call_path(a))[0]["speakers"], ["Ana Ruiz", "Sam Lee"])


class Checks(Base):
    def setUp(self):
        super().setUp()
        self.nw = self.add("2026-11-03.txt", NORTHWIND, "--customer", "Northwind")
        self.bf = self.add("2026-11-04.vtt", BLUEFIN_VTT, "--customer", "Bluefin")

    def errors(self, cid):
        return checks.check_note(core.note_path(cid), CONFIG, intake.all_calls)["errors"]

    def test_clean_note_passes(self):
        note(self.nw, "Northwind", [("it takes us two weeks to onboard a new client", "Ana Ruiz"),
                                    ("We copy the brief by hand … nobody owns the checklist", "Ana")])
        self.assertEqual(self.errors(self.nw), [])

    def test_quote_failures_are_classified(self):
        note(self.nw, "Northwind", [("It takes us two weeks to onboard a new client", "Ana Ruiz"),
                                    ("two weeks of setup before we bill", "Ana Ruiz"),
                                    ("it takes two weeks to onboard every client", "Ana Ruiz")])
        errs = " | ".join(self.errors(self.nw))
        self.assertIn("quote recased", errs)
        self.assertIn(f"quote wrong-call:{self.bf}", errs)
        self.assertIn("quote reworded", errs)

    def test_quote_across_two_speakers_fails(self):
        note(self.nw, "Northwind", [("How is onboarding going? Honestly it takes", "Ana Ruiz")])
        self.assertTrue(any(e.startswith("quote") for e in self.errors(self.nw)))

    def test_speaker_mismatch(self):
        note(self.nw, "Northwind", [("it takes us two weeks to onboard a new client", "Sam Lee")])
        self.assertTrue(any(e.startswith("speaker") for e in self.errors(self.nw)))

    def test_unlabelled_call_skips_speaker_check(self):
        solo = self.add("solo.txt", SOLO_TXT, "--customer", "Jo Freelance")
        note(solo, "Jo Freelance", [("takes her about a week of admin", "Whoever")])
        self.assertEqual(self.errors(solo), [])

    def test_shape(self):
        note(self.nw, "Northwind", [("it takes us two weeks to onboard a new client", "Ana Ruiz")], drop="Gains")
        self.assertTrue(any("missing: gains" in e for e in self.errors(self.nw)))
        note(self.nw, "Northwind", [("it takes us two weeks", "Ana Ruiz")], pools=("nope",))
        self.assertTrue(any("unknown pools" in e for e in self.errors(self.nw)))
        rc, out = self.cs("check")
        self.assertEqual(rc, 1)


class Signals(Base):
    def setUp(self):
        super().setUp()
        self.nw = self.add("a.txt", NORTHWIND, "--customer", "Northwind", "--when", "2026-11-03",
                           "--participants", "sam@testco.com,ana@northwind.io")
        self.nw2 = self.add("b.md", NORTHWIND_2, "--customer", "Northwind Ltd", "--when", "2026-11-05")
        self.bf = self.add("c.vtt", BLUEFIN_VTT, "--customer", "Bluefin", "--when", "2026-11-04",
                           "--segment", "agencies")
        self.solo = self.add("d.txt", SOLO_TXT, "--when", "2026-11-06")
        note(self.nw, "Northwind", [("it takes us two weeks to onboard a new client", "Ana Ruiz")])
        note(self.nw2, "Northwind", [("Onboarding still eats two weeks per client", "Ana Ruiz")])
        note(self.bf, "Bluefin", [("Every new client means two weeks of setup", "Tom Berg")], pools=("product", "sales"))
        note(self.solo, "", [("takes her about a week of admin", "unattributed")])

    def decide(self, d):
        core.atomic_write(core.ws.decisions, json.dumps(d))
        return self.cs("apply")

    def test_plan_then_apply_counts_customers_not_calls(self):
        rc, out = self.cs("plan")
        self.assertEqual(rc, 3, out)
        pack = json.loads(core.ws.pack.read_text())
        self.assertEqual(len(pack["new_notes"]), 4)
        self.assertEqual(pack["new_notes"][0]["top_quotes"][0]["speaker"], "Ana Ruiz")
        rc, out = self.decide({"appends": [], "new": [{
            "id": "onboarding-takes-two-weeks", "title": "Onboarding takes two weeks", "pools": ["product", "made-up"],
            "description": "Setup per client takes two weeks.", "members": [self.nw, self.nw2, self.bf, self.solo],
            "evidence": [{"call_id": self.nw, "quote": "it takes us two weeks to onboard a new client"},
                         {"call_id": self.bf, "quote": "a paraphrase that is not in the call"}]}]})
        self.assertEqual(rc, 0, out)
        meta, body = core.read_doc(signals.sig_path("onboarding-takes-two-weeks"))
        # Northwind twice (domain via alias on the second call) + Bluefin; the unnamed solo call is unresolved
        self.assertEqual((meta["customers"], meta["calls"], meta["unresolved"]), (2, 4, 1))
        self.assertEqual(meta["pools"], ["product"])
        self.assertEqual(meta["segments"], ["agencies"])
        self.assertEqual((meta["first_seen"], meta["last_seen"]), ("2026-11-03", "2026-11-06"))
        self.assertNotIn("Tom Berg", body)            # a failed quote is never replaced by another one
        self.assertIn("QUOTE_FALLBACK", out)
        self.assertIn("unknown pools ['made-up']", (core.ws.reports / "2026-11-09.md").read_text())
        rows = json.loads((core.ws.mirror / "rows.json").read_text())["rows"]
        self.assertEqual([r["Signal ID"] for r in rows], ["onboarding-takes-two-weeks"])

    def test_apply_twice_adds_nothing_and_counts_recompute(self):
        self.cs("plan")
        d = {"appends": [], "new": [{"id": "x", "title": "X", "pools": ["product"], "description": "d",
                                      "members": [self.nw, self.bf]}]}
        self.decide(d)
        self.decide({"appends": [{"signal_id": "x", "call_id": self.nw, "quote": ""}], "new": []})
        meta, body = core.read_doc(signals.sig_path("x"))
        self.assertEqual((meta["customers"], meta["calls"]), (2, 2))
        # remove a log line by hand: the next rebuild recomputes, nothing is stuck
        core.write_doc(signals.sig_path("x"), meta, "\n".join(l for l in body.splitlines() if self.bf not in l))
        rc, _ = self.cs("plan")
        self.assertEqual(rc, 0)                         # all notes judged already
        self.assertEqual(core.read_doc(signals.sig_path("x"))[0]["customers"], 1)

    def test_ranking_and_filters(self):
        self.cs("plan")
        self.decide({"appends": [], "new": [
            {"id": "small", "title": "Small", "pools": ["sales"], "description": "d", "members": [self.bf]},
            {"id": "big", "title": "Big", "pools": ["product"], "description": "d", "members": [self.nw, self.bf]}]})
        rc, out = self.cs("signals", "--json")
        self.assertEqual([r["id"] for r in json.loads(out)], ["big", "small"])
        rc, out = self.cs("signals", "--pool", "sales", "--json")
        self.assertEqual([r["id"] for r in json.loads(out)], ["small"])
        rc, out = self.cs("signals", "--min", "2", "--json")
        self.assertEqual([r["id"] for r in json.loads(out)], ["big"])

    def test_bad_decisions_are_refused(self):
        self.cs("plan")
        rc, out = self.decide({"appends": [{"call_id": self.nw}], "new": []})
        self.assertEqual(rc, 2)
        rc, out = self.decide({"appends": [{"signal_id": "ghost", "call_id": self.nw}], "new": []})
        self.assertIn("unknown signal", (core.ws.reports / "2026-11-09.md").read_text())

    def test_held_note_with_shape_errors(self):
        note(self.nw, "Northwind", [("it takes us two weeks", "Ana Ruiz")], drop="Pains")
        rc, out = self.cs("plan")
        self.assertIn(f"HELD {self.nw}", out)


class Customers(unittest.TestCase):
    def test_keys(self):
        cfg = {"project": {"our_domains": ["testco.com"]}}
        k = signals.email_key
        self.assertEqual(k({"participants": ["a@testco.com", "b@mail.bluefin.co.uk", "c@zoom.us"]}, cfg), "domain:bluefin.co.uk")
        self.assertEqual(k({"participants": ["a@testco.com", "jo@gmail.com"]}, cfg), "email:jo@gmail.com")
        self.assertEqual(signals.norm_name("Northwind Ltd (UK)"), "northwind")
        self.assertEqual(signals.customer_key({"customer": "The Northwind Inc"}, cfg, {}), "name:northwind")
        self.assertEqual(signals.customer_key({}, cfg, {}), "")


class Unattended(Base):
    def test_run_with_fake_agent(self):
        self.add("a.txt", NORTHWIND, "--customer", "Northwind")
        self.add("c.vtt", BLUEFIN_VTT, "--customer", "Bluefin")
        rc, out = self.cs("pending")
        self.assertEqual(rc, 3)
        rc, out = self.cs("run", "--cmd", f"{sys.executable} {Path(__file__).parent / 'fake_agent.py'}")
        self.assertEqual(rc, 0, out)
        meta = core.read_doc(signals.sig_path("everything"))[0]
        self.assertEqual((meta["customers"], meta["calls"]), (2, 2))
        rc, out = self.cs("pending")
        self.assertEqual(rc, 0)

    def test_doctor_and_pause(self):
        rc, out = self.cs("doctor")
        self.assertIn("DOCTOR: PASS", out)
        self.cs("pause")
        rc, out = self.cs("plan")
        self.assertIn("PAUSED", out)
        self.cs("resume")
        self.assertFalse(core.ws.pause.exists())


class Example(unittest.TestCase):
    """The committed example stays consistent: every quote verifies, the counts recompute the same."""

    def test_example_is_consistent(self):
        tmp = Path(tempfile.mkdtemp(prefix="cs-example-"))
        try:
            data = tmp / "ledgerly"
            shutil.copytree(core.REPO / "examples" / "ledgerly", data)
            before = (data / "signals" / "INDEX.md").read_text()
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["--data", str(data), "--date", "2026-11-09", "check"]), 0, out.getvalue())
                main(["--data", str(data), "--date", "2026-11-09", "mirror"])
            self.assertEqual((data / "signals" / "INDEX.md").read_text(), before)
        finally:
            shutil.rmtree(tmp)
            core.use(core.REPO / "data")
            core.TODAY = None


if __name__ == "__main__":
    unittest.main()
