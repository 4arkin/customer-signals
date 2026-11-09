"""Stands in for `claude -p` in tests. The prompt is the last argument.

Extraction: quotes the first three customer turns of the call, exactly.
Matching: puts every new note into one signal.
"""

import json
import re
import sys

prompt = sys.argv[-1]

if "CALL FILE:" in prompt:
    call = prompt.split("CALL FILE:", 1)[1]
    cid = re.search(r"^call_id: (.+)$", call, re.M).group(1).strip()
    customer = (re.search(r"^customer: (.*)$", call, re.M).group(1) or "").strip('" ')
    turns = [t for t in re.findall(r"^([^:\n]+): (.+)$", call.strip().split("\n---\n", 1)[1], re.M) if t[0] != "Sam Lee"]
    bank = "\n\n".join(f"> {t[:80]}\n— {s}, on the call" for s, t in turns[:3])
    heads = ["Customer context", "Pains", "Gains", "Their words", "Workflow", "Tools and alternatives",
             "Decision", "Requests", "Quote bank", "Open questions"]
    body = "\n\n".join(f"## {h}\n\n" + (bank if h == "Quote bank" else "Something.") for h in heads)
    print(f"```markdown\n---\ncall_id: {cid}\ncustomer: \"{customer}\"\npools: [\"product\"]\n"
          f"extracted_at: 2026-11-09\nextracted_by: fake\nquality: partial\n---\n\n# {cid}\n\n{body}\n```")
else:
    pack = json.loads(prompt[prompt.index("{"):])
    notes = pack["new_notes"]
    print(json.dumps({"appends": [], "new": [{
        "id": "everything", "title": "Everything", "pools": ["product"], "description": "All calls.",
        "members": [n["call_id"] for n in notes],
        "evidence": [{"call_id": n["call_id"], "quote": n["top_quotes"][0]["quote"]} for n in notes if n["top_quotes"]]}]}))
