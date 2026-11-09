# Match new notes to signals

You get a pack: `signals` (the patterns already known) and `new_notes` (calls not yet matched). For each new note, decide which signals it backs, and which of its patterns are new. Reply with one JSON object in the `decision_schema` shape: `{"appends": [...], "new": [...]}`.

A signal is one recurring pattern: a pain, a gain, an objection, a request, a way of working. "Onboarding takes two weeks" is a signal. "Onboarding" is not; it is a topic.

## Rules

1. **Match on content, not on labels.** A note backs a signal when the customer said the same thing in other words. Shared pools or shared keywords are not enough.
2. **Prefer appending.** Before you create a signal, read every title and description in `signals`. If one fits, append to it.
3. **One pattern per signal.** Do not make a signal that holds two pains. Do not make two signals for one pain.
4. **Create from one call.** A pattern seen in one call is still a signal. Create it. It waits in the log until other customers repeat it. Most signals start with one customer.
5. **Quotes are exact and on topic.** For every append and every evidence row, copy the quote that shows THIS pattern, character for character: from that call's `top_quotes`, or from the Quote bank in its note (`data/notes/<call_id>.notes.md`). The engine checks it against the call. A quote that fails is dropped, and the call is logged without one. Leave `quote` empty when the call has no quote for this pattern.
6. **Pools come from the pack.** Use only the pool ids listed in `pools`. A signal can sit in several pools: "setup takes two weeks" can serve product, sales and customer-success.
7. **Do not count.** The engine counts customers and calls from the log. Never put a number in a title or a description.
8. **Ids** are short lowercase-kebab descriptions of the pattern: `onboarding-takes-two-weeks`, `pays-for-two-overlapping-tools`. Never a date, never a customer name.

## Shape

```json
{
  "appends": [
    {"signal_id": "onboarding-takes-two-weeks", "call_id": "2026-11-03_northwind", "quote": "exact words from top_quotes"}
  ],
  "new": [
    {"id": "pays-for-two-overlapping-tools", "title": "Pays for two tools that overlap",
     "pools": ["product", "sales"], "description": "They keep two tools because neither covers the whole job. A consolidation pitch lands here.",
     "members": ["2026-11-03_northwind"], "evidence": [{"call_id": "2026-11-03_northwind", "quote": "exact words"}]}
  ]
}
```

A note with nothing worth a signal gets no rows. That is a valid answer.
