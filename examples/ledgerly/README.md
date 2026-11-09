# Example: Ledgerly (invented calls)

Every call in this folder is invented. Ledgerly is a made-up invoicing app for design studios and freelance designers. The customers, people and email domains (`.example`) do not exist.

The run itself is real. The transcripts went in through `bin/cs add`. One subagent per call wrote each note with `prompts/extract.md`. The engine checked all 59 quotes against their calls, the agent matched the notes with `prompts/match.md`, and `bin/cs apply` wrote the signals and counted them.

| Path | What |
|---|---|
| [`transcripts/`](transcripts/) | The 8 calls as a recorder would export them: VTT, SRT, Markdown, timestamped lines, speaker headers, and typed notes with no speaker labels |
| [`config.json`](config.json) | The project, 3 pools and 2 segments the setup interview would propose |
| [`calls/`](calls/) | The same calls after `bin/cs add`, in one format |
| [`notes/`](notes/) | One note per call |
| [`signals/INDEX.md`](signals/INDEX.md) | 9 signals, ranked by distinct customers |
| [`signals/`](signals/) | One record per signal: description, checked quotes, the log of calls |
| [`mirror/rows.json`](mirror/rows.json) | The rows a store would get: signals with 2 or more customers |
| [`reports/`](reports/) | What the run did |

Things to look at:
- **Customers, not calls.** Northwind Studio had two calls. On "VAT line is wrong on invoices in a non-euro currency" it counts as 1 customer and 2 calls.
- **Same customer, no emails.** Northwind's second call has no participant emails. The engine still counts it as Northwind, from the name on the first call.
- **A call with no quote.** Quiet Fox Design's call is typed notes, not a recording. It backs "Wants an automatic late fee" with no quote, because nobody's exact words were written down.

Try it:

```bash
bin/cs --data examples/ledgerly signals
bin/cs --data examples/ledgerly signals --pool sales
bin/cs --data examples/ledgerly check
```
