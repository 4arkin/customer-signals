# Setup interview

Goal: a `data/config.json` the person recognises as their own. Do the homework first, then ask only what you cannot find. Five minutes of the person's time is the budget.

## 1. Learn the project

Read what is in front of you: the README, the website, a positioning or ICP doc, a backlog, past call notes. Find out:
- what the project sells, and to whom;
- who is on the team and talks to customers (names, email domains);
- what the person wants from their calls: a backlog, messaging, an offer, a sales script, retention.

Write `project.description` in two sentences: what is sold to whom, and what the calls should teach.

## 2. Propose pools

A pool is what a signal is about and whom it serves. Propose 3 to 6, from what the project needs. Common ones:

| Pool | About | Serves |
|---|---|---|
| `product` | bugs, missing features, friction, requests | the backlog |
| `marketing` | pains, gains, the words customers use | messaging, positioning, offers |
| `sales` | objections, buying process, budget, competitors | the sales script |
| `customer-success` | onboarding, churn risk, workarounds | retention |
| `strategy` | who to serve, what to build next, pricing model | the founder's decisions |

Rename or drop any of them. Add a pool when the project has a specific need (`pricing`, `partnerships`, `hiring`). Each pool gets one `about` line: the extraction and matching steps read it to decide what goes where.

## 3. Segments, only when they exist

Segments say who the customer is (for example agencies, in-house teams, freelancers). Propose them only when the project already defines them, you can read a source that does, or the person shares them. Otherwise leave `segments` empty: a founder with ten calls does not need them.

## 4. Our side

List the team's email domains in `our_domains` and the names of the people who run calls in `our_names`. The engine uses the domains to find the customer in the participant emails. The notes use the names to tell our side from the customer.

## 5. Where signals live

Ask: "Where do you want to see the signals: in a tool you already use, or only here?" If they name a store and you have a connector for it (Notion, Airtable, Google Sheets, a database), set `mirror.store` and describe in `mirror.notes` how you write to it. Otherwise `"none"`: the ranked list lives in `data/signals/INDEX.md`, and the person asks you.

`mirror.min_customers` (default 2) keeps the store clean: a signal goes there once two customers back it. Every signal stays in the local log, from the first call.

## 6. Confirm

Show the config as a short summary: project, pools with their `about` lines, segments, our side, the store. Let the person edit it. Then write the file and run `bin/cs doctor`.
