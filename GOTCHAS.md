# Gotchas

## Calls in

- **A transcript with no speaker labels.** It is stored as paragraphs. Quotes are still checked; the speaker check is skipped. Export with speaker names when the recorder allows it.
- **Generic labels ("Speaker 1", "Speaker 2").** The recorder could not name the speakers. Quotes are credited to those labels. Rename them before `bin/cs add` if you know who is who, with a find-and-replace on the file.
- **A group call** (a workshop, a webinar, a panel) counts as one customer, the one in `--customer`. For a count per person, add each person's part as its own call, or give each person their own call with their own `--customer`.
- **The same customer under two names.** "Northwind" and "Northwind Ltd" match, because the engine drops company suffixes. "Northwind" and "NW Labs" do not. Pass `--participants` emails: a company domain wins over the name.
- **Personal email addresses** (gmail and others) identify a person, not a company. For a founder who talks to individuals, that is the right count.
- **A long call** (two hours or more) still goes to one subagent. Check its quality rating: a long, noisy group call often rates `partial`.

## Notes

- **`quote recased` / `reworded`.** The model fixed the words. The rule is the exact span. Re-extract in a fresh subagent with the error text.
- **`quote wrong-call:<id>`.** The note saw two calls. One call per subagent, always.
- **A quote with `…`.** Allowed when every piece is exact, from one speaker, in order.
- **Quotation marks in prose sections.** Only the Quote bank and Their words are checked. Elsewhere, write without quotation marks, so a paraphrase never looks like a quote.

## Signals

- **A count looks low.** Calls without a customer name or a customer email are `unresolved`: they show on the signal, but never count. Run `bin/cs signals --json` and look at `unresolved`.
- **Two signals for one pattern.** Matching prefers appending, but it can split. Merge them: move the Log lines of one record into the other, delete the empty record, and run `bin/cs plan`. The counts recompute from the Log.
- **A count changed with no new calls.** Counts are recomputed on every run from the Log and the call files. A fixed customer name or new participant emails change them. That is the intent.
