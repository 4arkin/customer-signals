# AGENTS.md: operating protocol

You are setting up and running customer signals for the person you work with. They record calls with customers. You turn each call into a note: what the customer said about their problems and goals, how they work, the tools they use and compare, how they buy, what they ask for, and their exact words. Then you match the notes to signals, the patterns that repeat across calls. The engine checks every quote against its call and counts how many distinct customers back each signal. The person asks you "what are the top pains in the product pool?" and you answer from the ranked log.

You make two judgments: the note for each call, and which signals a note backs. The engine does everything else: storing calls, checking quotes, counting, ranking. Everything runs through `bin/cs` (Python 3.9+, standard library only, nothing to install). Run it from the repository folder.

## Rules

- **One call per subagent.** Write each note in its own subagent, or its own fresh context, with only that call in it. Never two calls in one context. This is how a quote never ends up credited to the wrong meeting.
- **Quotes are exact.** Every quote is copied character for character from its call. `bin/cs check` verifies it. Never fix a quote by changing a call file. Fix the note.
- **The engine counts. You never do.** Never write a count into a note, a title or a description. Never edit `data/signals/`, `data/mirror/` or `data/cache/` by hand. `bin/cs apply` writes them. The person may change a signal's `status:` line (`open`, `done`, `dropped`).
- **`data/` is the person's private data.** It is gitignored. Never commit it, never send calls anywhere except the store they chose.
- **Report what happened, including failures.** A failed check, a skipped call, a quote that fell back: say so.

## 1. Install

If the person gave you a link to this repository, clone it next to their project, or inside it with the folder added to their `.gitignore`. Then:

```bash
bin/cs init      # creates data/ with an example config
bin/cs doctor
```

## 2. Setup interview → `data/config.json`

Follow [`prompts/setup-interview.md`](prompts/setup-interview.md). In short:
1. Read the person's project: what it sells, to whom, who is on the team. Ask only what you cannot find.
2. Propose the **pools**: what a signal can be about and whom it serves (for example product, marketing, sales, customer-success, strategy). Each pool gets one `about` line. A signal can sit in several pools.
3. Propose **segments** only if the project defines customer types, you can read a source that does, or the person shares them. Otherwise leave `segments` empty.
4. Write down **our side**: the team's email domains and names, so the engine and the notes can tell our side from the customer.
5. Ask where the signals should live: a store they already use (Notion, Airtable, a Google Sheet) through a connector you have, or no store. Set `mirror.store`, and `mirror.min_customers` (default 2: a signal goes to the store once two customers back it).
6. Show the config as a short summary. Let the person confirm or edit it. Write `data/config.json` (schema: [`templates/config.example.json`](templates/config.example.json)). Run `bin/cs doctor` until it ends in `DOCTOR: PASS`.

## 3. Wire the intake

The engine reads transcript files. Find the shortest way to get the person's calls into it, in this order:
1. **A recorder connector you already have** (an MCP server for Fireflies, Gong, Zoom, Granola, Otter, tl;dv and others). Fetch each call's transcript, save it to a file, and add it.
2. **The recorder's export**: the person exports transcripts as text, VTT or SRT into one folder.
3. **Pasting**: the person pastes a transcript; you save it to a file.

Add each file with what you know about it:

```bash
bin/cs add <file> --customer "Northwind" --when 2026-11-03 --participants "ana@northwind.io,sam@ourco.com"
```

- `--customer` is the customer's organisation, or the person when there is no organisation. Signals rank by distinct customers, so name each customer the same way every time.
- `--participants` emails make the count exact: a company domain identifies the customer even when names vary.
- The engine reads `Name: text`, `**Name:** text`, timestamped lines, speaker-header blocks, VTT and SRT. A transcript with no speaker labels works too; only the speaker check is skipped.
- Adding the same transcript twice does nothing.

## 4. First run

Add the last 10 to 30 customer calls, then run § Each run. This is the person's first ranked view. Show them the top of `bin/cs signals`.

## 5. Mirror and schedule

- **Mirror.** If `mirror.store` is set, run `bin/cs mirror`. Upsert every row of `data/mirror/rows.json` into the store, matched on `Signal ID`: create the missing rows, update the others. On the first run, create the database or sheet with these columns: Signal ID, Title, Rank, Customers, Calls, Pools, Segments, Status, First seen, Last seen, Description, Quotes. Write the store's name and how you reach it into `mirror.notes`.
- **Schedule.** Ask how often new calls come in. Weekly is typical. Set it up with [`schedule/README.md`](schedule/README.md). If you can fetch calls from a connector, the scheduled run fetches them too. Run one cycle by hand and show the result.

## 6. Hand-off

Tell the person, in at most ten lines: the pools, how calls get in, where the signals live, when the next run is, and that they can ask you "what comes up most in the sales pool?", "what do agencies say about pricing?", "which tools do they compare us to?" or "show me the quotes for X" at any time.

## Each run

```bash
bin/cs pending     # exit 3: calls waiting for notes
```

1. **Notes.** For each `EXTRACT` line, start one subagent with [`prompts/extract.md`](prompts/extract.md), the config's pools and that one call. It writes the note to the path given.
2. **Check.** `bin/cs check`. On an error, delete that note and extract it again in a fresh subagent, with the error text. A call that is garbled, in a language you cannot read, or not a customer call: `bin/cs skip <call_id> --reason "<why>"`, and tell the person.
3. **Match.** `bin/cs plan` exits 3 and writes `data/cache/match-pack.json`. Follow its `instructions` (they are [`prompts/match.md`](prompts/match.md)) and write `data/cache/decisions.json`.
4. **Apply.** `bin/cs apply`. It verifies every quote, writes the records, recomputes every count and rebuilds the ranked index.
5. **Mirror**, if a store is set (§ 5).
6. Tell the person what is new: signals created, and signals that gained a customer.

With `CS_AGENT_CMD` set, `bin/cs run` does steps 1 to 4 unattended.

## Answering questions

Follow [`prompts/ask.md`](prompts/ask.md). Start from `bin/cs signals --json` (filters: `--pool`, `--segment`, `--min`), then read the signal records for evidence. Give counts as the engine wrote them. Quote only from the records and notes.

## Commands

| Command | What it does |
|---|---|
| `bin/cs init` | Create `data/` and an example config |
| `bin/cs doctor` | Check Python, config, prompts, agent command |
| `bin/cs status` | Calls, notes waiting, top 5 signals |
| `bin/cs add <files…>` | Store transcripts as calls (`--customer --when --title --segment --participants`) |
| `bin/cs pending` | Calls without a note |
| `bin/cs skip <call_id> --reason` | Leave a call out for good |
| `bin/cs check` | Verify quotes, speakers and note shape (`--since`, `--call`) |
| `bin/cs plan` | Write the match pack for new notes |
| `bin/cs apply` | Apply `data/cache/decisions.json` |
| `bin/cs signals` | The ranked list (`--pool --segment --min --limit --all --json`) |
| `bin/cs mirror` | Rebuild the rows for the store |
| `bin/cs run` | Unattended: notes, check, match, apply through `CS_AGENT_CMD` |
| `bin/cs pause` / `resume` | Stop and restart scheduled runs |

Global flags: `--data <folder>` (or `CS_DATA`) for a second project, `--date YYYY-MM-DD`.

Exit codes: `0` done · `1` failed · `2` bad config or input · `3` waiting for you (a `NEXT:` line says what to do).

## When something looks wrong

- **A quote fails `recased` or `reworded`.** The note changed the words. Re-extract; the quote must be the exact span.
- **A quote fails `wrong-call:<id>`.** The words were said in another call. The note was written with two calls in context. Re-extract in a fresh subagent.
- **A `speaker` error.** The quote is credited to someone who did not say it. Use the speaker label from the call.
- **A customer counts twice** (for example "Northwind" and "Northwind Ltd" on calls without emails). The engine drops company suffixes. For other spellings, add `--participants` emails or name the customer the same way.
- **`unresolved` calls on a signal.** Those calls have no customer name and no customer email. They show, but never count. Fix the call: delete `data/calls/<call_id>.md` and add the file again with `--customer`. The note stays valid only if the transcript is the same.
- See [`GOTCHAS.md`](GOTCHAS.md).
