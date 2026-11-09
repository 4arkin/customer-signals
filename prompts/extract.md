# Extract one call into a note

You read ONE call file from `data/calls/` and write ONE note to `data/notes/<call_id>.notes.md`.

Read the whole call before you write. A long call does not fit in one read: page through the file until its last line.

Work on one call only. If you run as a subagent, your context holds this call and no other. Never read a second call while you write this note. The isolation is the point: a quote cannot come from another meeting if you never saw the other meeting.

## Who is who

The call has two sides: our side (the project team) and the customer's side. `data/config.json` names our side in `project.our_names` and `project.our_domains`. Everyone else is the customer: whoever the project learns from, as `project.description` says (a prospect, a client, a user, a partner who sells for us). Their pains count even when they are about buying, selling or terms rather than the product.

Mine the customer's side. What our side says is noise, unless the customer reacts to it. Then capture the reaction.

When the labels are generic ("Speaker 1", "Speaker 2"), decide who is on our side from what the call shows: who hosts, who introduces themselves by a name in `our_names`, who presents the product. Use that only to sort the sides. Quotes keep the label as written.

**Group calls** (a workshop, a panel, a community session) hold several customers in one call. Write one note. In Customer context, describe each speaker you mine in one line. Name the speaker in brackets after each point: `(Speaker 4)`. When a host is also a peer with the same pain, leave it out: signals are about customers.

**Relayed speech** ("my clients keep telling me…") is the speaker's own words and can be quoted. Say that it is relayed in the topic after the dash.

## The note

Write this frontmatter first, keys in this order:

```
---
call_id: <copy from the call file>
customer: "<the customer organisation, or the person if there is no organisation>"
pools: [<pool ids from data/config.json that this call serves>]
extracted_at: <today, YYYY-MM-DD>
extracted_by: <your model name>
quality: clean | partial | poor
---
```

Then `# <the call title>` and these ten headings, all of them, in this order:

1. `## Customer context`: facts about the customer. Size, role of the speaker, what the organisation does, the tools and team you can see. Their version, not ours.
2. `## Pains`: what hurts. Split into **Said** (they named the pain) and **Shown** (a workaround, a topic they return to, a sigh, three questions on one thing). Mark which is which.
3. `## Gains`: what they want to get, in their terms. The outcome, not our feature.
4. `## Their words`: the exact phrases they use for the problem and the outcome. Put each phrase in double quotes. Every quoted phrase is checked against the call with the Quote fidelity rules below: a phrase may start mid-sentence, but its characters, capital letters included, stay as spoken.
5. `## Workflow`: how they do the job today. Steps, roles, hand-offs, volume, cadence. What they do, not what they wish they did.
6. `## Tools and alternatives`: what they use now, what they tried and dropped (and why), what they compare us to.
7. `## Decision`: who decides, who influences, the criteria, budget and timing, what could kill it.
8. `## Requests`: what they asked for that does not exist yet, with the reason. Bug reports here too: "on X, expected Y, got Z".
9. `## Quote bank`: 5 to 15 quotes, **strongest first** (see below). A short call or typed notes may hold fewer: write the ones there are, never pad, and let the quality rating show it.
10. `## Open questions`: follow-ups promised, things to test with other customers, and contradictions in the call.

When a section has nothing, write `_(none observed)_`. Never leave a heading out. Never rename one.

## Quote bank

Format, one quote per block:

```
> the exact words
— Speaker Name, on <topic>
```

Order is strength, not time. The matching step reads only the first three quotes. Put first the quotes that are specific (a number, a tool, a role, a consequence), in the customer's own words, about a pain, a gain, a decision or a workflow. Never pleasantries. When the call has several patterns, make the first three cover three different ones.

**Quote fidelity.** Every quote is an exact piece of the call file. You choose where the quote starts and ends. You do not change one character inside it:
- do not fix grammar, spelling or filler words;
- do not re-capitalise the first word because the quote now starts there;
- do not join two speakers' words into one quote.

Spoken text stutters: "you know, you know, the problem is…". Start the quote after the stutter ("the problem is…"), exactly as it continues. Never clean the stutter out of the middle; use a shorter span or `…` instead.

To skip words in the middle, use `…`. Each piece around it must still be exact, from the same speaker, in the order spoken. Put context after the dash, never inside the quote.

**Speaker fidelity.** The name after the dash is the speaker label on that turn in this call file. If the call has no speaker labels, write `— unattributed, on <topic>`. Never take a name from anywhere else.

**Typed notes are not speech.** When the call file is someone's notes about a call (third person: "they said…", "she asked…"), the notes are the writer's words, not the customer's. Quote only text the notes themselves put inside quotation marks. When the notes hold no such text, the Quote bank is `_(none observed)_` and Their words holds no quoted phrases.

The engine checks every quote against the call, and every name against the speaker who said it. A quote that fails is dropped from the signals. Before you finish, run `bin/cs check --call <call_id>` and fix every error by choosing the exact span from the call.

Outside the Quote bank and Their words, write in your own words, without quotation marks. Refer to people by their speaker label. Write the note in the language the person works in (the language of `project.description` in `data/config.json`), whatever language the call is in. Quotes stay in the language spoken: never translate inside quotation marks.

## Quality

A section has real content when it holds at least one concrete item about this customer: a number, a named tool, a named role, a specific event. Generic or implied content does not count. Count the sections with real content:
- `clean`: 9 or 10, at least 3 real quotes;
- `partial`: 5 to 8;
- `poor`: 4 or fewer, or the call was too garbled to follow.

Be honest. A thin note marked `clean` misleads every count downstream.

If the call is garbled, in a language you cannot read, or not a customer call at all (a personal chat, an internal team meeting, a talk), do not write a note. Run `bin/cs skip <call_id> --reason "<why>"` so the call leaves the queue, and report it. A call you skip by mistake comes back when the person deletes the `skip:` line in its call file.
