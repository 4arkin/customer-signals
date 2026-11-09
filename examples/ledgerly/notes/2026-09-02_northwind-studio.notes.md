---
call_id: 2026-09-02_northwind-studio
customer: "Northwind Studio"
pools: [product, marketing]
extracted_at: 2026-11-09
extracted_by: claude-sonnet
quality: clean
---
# 2026-09-02_northwind-studio

## Customer context
- Dana Holt speaks for Northwind Studio, a design studio, and handles the invoicing and the chasing herself.
- The studio sends about thirty invoices in a normal month.
- It bills two clients in dollars and one in Swiss francs.
- The studio switched to Ledgerly recently; sending invoices works for them now.

## Pains
**Said**
- Getting paid is the problem. Dana spends every Friday morning chasing late invoices by email.
- About eight of thirty invoices are late in a normal month, and each one is an awkward money conversation with a client the studio wants to keep.
- The reminder feature sends the same cold text to everyone. A client of five years got the same message as a one-off job.
- The VAT line comes out wrong on invoices in foreign currency.

**Shown**
- Dana turned the reminder feature off and chases by hand instead.
- Dana still makes the dollar and Swiss franc invoices in a spreadsheet.

## Gains
- Late payers get chased without a weekly manual chore.
- Each client gets a tone that fits the relationship: friendly for regulars, firm for chronic late payers.
- Foreign currency invoices with a correct VAT line, made inside the app instead of a spreadsheet.

## Their words
- "Getting paid is the problem"
- "chasing late invoices"
- "an awkward money conversation"
- "the same cold text to everyone"
- "in my voice"

## Workflow
- Dana sends invoices from Ledgerly.
- Every Friday morning she emails clients with late invoices by hand.
- About eight of thirty invoices a month need chasing.
- Invoices for the two dollar clients and the Swiss franc client are made in a spreadsheet.

## Tools and alternatives
- Ledgerly for sending invoices.
- Ledgerly's reminder feature: tried and turned off, because the text is the same for every client.
- A spreadsheet for foreign currency invoices, because the VAT line is wrong in the app.

## Decision
_(none observed)_

## Requests
- Reminders written per client, in Dana's voice, so tone can differ between regulars and chronic late payers.
- Correct VAT line on invoices in dollars and Swiss francs. Bug report: on a foreign currency invoice, expected a correct VAT line, got a wrong one.

## Quote bank
> Sending them is fine now. Getting paid is the problem. I spend every Friday morning chasing late invoices by email.
— Dana Holt, on the weekly chase

> Out of thirty, maybe eight. And each one is an awkward money conversation with a client we want to keep.
— Dana Holt, on late invoices per month

> I turned it off. It sends the same cold text to everyone. A client of five years got the same message as a one-off job.
— Dana Holt, on the reminder feature

> Reminders I can write per client, in my voice. Friendly for the regulars, firm for the ones who always pay sixty days late.
— Dana Holt, on the reminders she wants

> We bill two clients in dollars and one in Swiss francs. I still do those invoices in a spreadsheet because the VAT line comes out wrong.
— Dana Holt, on foreign currency invoices

## Open questions
- Which VAT rule does the invoice get wrong for dollars, and which for Swiss francs? Dana did not say.
- Do other studios turn the reminder feature off for the same reason?
