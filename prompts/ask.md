# Answering questions from the signals

The person asks things like "what comes up most across all calls?", "what do agencies say about pricing?", "which tools do they compare us to?", "what should go in the backlog?", "show me the quotes for onboarding".

1. **Start from the ranked list.** `bin/cs signals --json`, filtered with `--pool`, `--segment` or `--min`. It is ranked by distinct customers, then calls.
2. **Read the records** (`data/signals/<id>.md`) for the signals you will mention: the description, the evidence quotes, the log of calls.
3. **Answer with the numbers the engine wrote.** "4 customers, 6 calls". Never count again yourself, never round up, never merge two signals into one number.
4. **Quote only from the records and the notes.** Each quote carries the speaker, the customer and the date. Never paraphrase inside quotation marks.
5. **Say how thin it is.** A signal backed by one customer is a lead, not a pattern. Say so.
6. **Go deeper on request.** A note (`data/notes/<call_id>.notes.md`) holds the full context of one call. The call file holds the full transcript.

For a backlog, a messaging doc or an offer: group the signals of that pool, keep the counts beside each line, and link each line to its record.
