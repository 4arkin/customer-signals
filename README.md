# customer-signals

**Rank what your customers say by how many of them say it. Check every quote word for word against its call.**

An AI debrief of one call forgets the call when you close the chat. It counts nothing across calls.

customer-signals gives your AI agent a memory of all your customer calls. Your agent reads each call alone, in its own subagent. It writes down pains, gains, the words customers use, workflows, tools, alternatives and quotes. The engine checks every quote word for word against its call, and it flags a quote that came from a different call. Each signal gets a rank by the number of distinct customers who raised it, with the number of calls beside it. One talkative customer on five calls counts as one customer.

Ask your agent *"what are the top pains in the product pool?"* and you get a ranked list with counts and quotes. A pool tells what a signal is about and whom it serves, such as marketing, sales, product or customer service. Setup reads your project and proposes the pools, and one signal can sit in several pools. You can also open your store and work with the signals as a database. The example in this repo uses invented calls for a made-up product. Its 8 calls from 7 customers give 9 signals.

It is for founders who talk to customers and ask AI to debrief each transcript. It is for marketers who do not talk to customers and use AI research to make hypotheses, messaging, offers and positioning. It is for product managers who talk to customers but have no time to analyse each call and fill the hypotheses backlog.

You need an AI agent that works in a folder: Claude Code, Codex, Gemini CLI or similar. You send one message, and the agent installs it. You do not need code or API keys. It works with any call recorder: at setup, your agent finds how to get the transcripts, through the recorder's connector, its export, or a paste. Your local files are the source of truth, and your agent copies the signals to the store you choose: Notion, Airtable, a sheet, or none. It costs nothing except the usage of your own agent.

> **AI agents:** read [`AGENTS.md`](AGENTS.md). It is the complete protocol.

---

## Start with one message

Open your project in your AI agent and send:

```
Install https://github.com/4arkin/customer-signals, read its AGENTS.md,
and set up customer signals for this project.
```

Your agent then:

```
reads your project ──→ proposes pools (and segments, if you have them) ──→ you confirm
        │
        ▼
finds your calls: recorder connector, export or paste ──→ adds the last 10–30 calls
        │
        ▼
one subagent per call writes a note ──→ the engine checks every quote
        │
        ▼
matches notes to signals ──→ the engine counts customers and calls ──→ ranked list
        │
        ▼
copies the signals to your store ──→ schedules the next run
```

## What you get

| Where | What |
|---|---|
| `data/signals/INDEX.md` | Every signal, ranked by distinct customers, with calls, pools and the last date seen |
| `data/signals/<signal>.md` | One signal: a description, up to five checked quotes with speaker, customer and date, and a log of every call behind it |
| `data/notes/<call>.notes.md` | One call: customer context, pains, gains, their words, workflow, tools, decision, requests, quote bank, open questions |
| Your store | The signals with two or more customers, one row each, updated on every run |

See [`examples/ledgerly/`](examples/ledgerly/) for all of it on invented calls.

## Works with

- **Agents:** Claude Code, Codex, Gemini CLI, or any agent that can run commands in a folder.
- **Recorders:** any that gives a transcript. The engine reads `Name: text`, `**Name:** text`, timestamped lines, speaker-header blocks, WebVTT, SRT and plain text.
- **Stores:** any your agent has a connector for, such as Notion, Airtable or Google Sheets. Or none.
- **Python 3.9+**, standard library only. Nothing to install.

## How it works

The agent makes two judgments: the note for each call, and which signals a note backs. The engine (`bin/cs`) does the rest:

1. `add` stores each transcript once, in one format, and never edits it again.
2. `check` tests every quote against its call: the exact words, from one speaker, in that call. A quote with changed words, or from another call, fails.
3. `plan` packs the new notes with the known signals for the agent to match.
4. `apply` checks the quotes again, writes the signals, and counts customers and calls from each signal's log. Counts are rebuilt on every run, so they cannot drift.

A customer is the company domain in the participant emails, then the customer name. A call with neither shows on the signal but does not count.

## Inside

| Path | What |
|---|---|
| [`AGENTS.md`](AGENTS.md) | The protocol your agent follows: setup, every run, answering questions |
| [`prompts/`](prompts/) | The setup interview, the note rules, the matching rules, how to answer |
| [`schedule/`](schedule/) | Agent-session, launchd and cron recipes |
| [`GOTCHAS.md`](GOTCHAS.md) | Known traps, and the fix for each |
| `bin/cs`, `cs/` | The engine |
| [`examples/ledgerly/`](examples/ledgerly/) | A full run on invented calls |
| `tests/` | `python3 -m unittest discover -s tests`, offline |

## License

MIT. See [`LICENSE`](LICENSE).
