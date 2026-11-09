---
call_id: 2026-10-01_leo-marchetti
customer: "Leo Marchetti"
pools: [product, marketing]
extracted_at: 2026-11-09
extracted_by: claude-sonnet
quality: partial
---
# 2026-10-01_leo-marchetti

## Customer context
Leo Marchetti is a freelancer who bills clients himself. He signed up three weeks before the call. He kept all his clients in a Google Sheet and bills about ten of them most often. He also tracks unpaid invoices in the same sheet.

## Pains
**Said:**
- The client import wanted a different column order than his sheet, so he gave up and added only the ten clients he bills most.
- The rest of the clients are still in the sheet, so he now has two places to look, which he says is worse than before.

**Shown:**
- He marks who owes him with a red cell in the sheet and checks it by hand.

## Gains
He wants one place for all clients. He wants the app to know who is late and to nudge them, so he can stop using the sheet.

## Their words
- "two places to look"
- "worse than before"
- "who owes me"
- "close the sheet for good"

## Workflow
He keeps every client in a Google Sheet. He marks late payers with a red cell in the same sheet. After signup he moved the ten clients he bills most into the app by hand.

## Tools and alternatives
Google Sheet, still in use for the remaining clients and for payment tracking. He gave up on the app's import after the column order did not match.

## Decision
_(none observed)_

## Requests
- On import, expected to map his own columns, got a fixed column order. He asks to see his sheet and be asked which column is the email.
- Automatic detection of late invoices and a reminder sent to the late client. Reason: he would stop using the sheet.

## Quote bank
> I had all my clients in a Google Sheet and the import wanted a different column order.
— Leo Marchetti, on client import

> So now I have two places to look, which is worse than before.
— Leo Marchetti, on running the app and the sheet side by side

> If the app knew who was late and nudged them, I would close the sheet for good.
— Leo Marchetti, on late payments

> Let me match the columns myself. Show me my sheet and ask which column is the email.
— Leo Marchetti, on the fix for import

> I track who owes me in the same sheet, with a red cell.
— Leo Marchetti, on tracking who is late

## Open questions
- How many clients does he have in total beyond the ten he added?
- Do other freelancers keep clients in a sheet and hit the same import problem?
