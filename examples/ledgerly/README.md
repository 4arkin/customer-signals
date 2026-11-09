# Example: Ledgerly (invented calls)

Every call in this folder is invented. Ledgerly is a made-up invoicing app for design studios and freelance designers. The customers, people and email domains (`.example`) do not exist.

The run itself is real. The transcripts went in through `bin/cs add`. One subagent per call wrote each note with `prompts/extract.md`, and the engine checked every quote against its call. A separate agent matched the notes with `prompts/match.md`, seeing only the match pack and the notes, and `bin/cs apply` wrote the signals and counted them.

| Path | What |
|---|---|
| [`transcripts/`](transcripts/) | The 8 calls as a recorder would export them: VTT, SRT, Markdown, timestamped lines, speaker headers, and typed notes with no speaker labels |
| [`config.json`](config.json) | The project, 3 pools and 2 segments the setup interview would propose |
| [`calls/`](calls/) | The same calls after `bin/cs add`, in one format |
| [`notes/`](notes/) | One note per call |
| [`signals/INDEX.md`](signals/INDEX.md) | The signals, ranked by distinct customers |
| [`signals/`](signals/) | One record per signal: description, checked quotes, the log of calls |
| [`mirror/rows.json`](mirror/rows.json) | The rows a store would get: signals with 2 or more customers |
| [`reports/`](reports/) | What the run did |

Things to look at:
- **Many kinds of signal, not only problems.** The top of the list holds a way of working (invoices go out when a phase is approved), a goal (see next month's cash), an objection (years of invoice history hold them in the old tool), a buying criterion (it must sync to the accountant's software) and a problem (chasing late payers).
- **Customers, not calls.** Northwind Studio had two calls. On "Wants to see next month's incoming cash ahead of time" it counts as 1 of 3 customers, on 4 calls.
- **Same customer, no emails.** Northwind's second call has no participant emails. The engine still counts it as Northwind, from the name on the first call.
- **A call with no quote.** Quiet Fox Design's call is typed notes, not a recording, so nobody's exact words were written down. It backs three signals with no quote, and "Retypes each approved estimate into a new invoice" has no quote at all.

Try it:

```bash
bin/cs --data examples/ledgerly signals
bin/cs --data examples/ledgerly signals --pool sales
bin/cs --data examples/ledgerly signals --min 3
bin/cs --data examples/ledgerly check
```
