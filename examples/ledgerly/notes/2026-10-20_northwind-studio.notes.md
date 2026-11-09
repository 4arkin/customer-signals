---
call_id: 2026-10-20_northwind-studio
customer: "Northwind Studio"
pools: [product, sales]
extracted_at: 2026-11-09
extracted_by: claude-sonnet
quality: partial
---
# 2026-10-20_northwind-studio

## Customer context
- Northwind Studio is a design studio and a current paying Ledgerly customer. This is a follow-up call after an earlier call about reminders.
- Dana Holt handles invoicing and payment chasing herself.
- The studio just hired two juniors. They only need to see invoice status.
- Their biggest client pays in Swiss francs.

## Pains
**Said**
- Invoices in Swiss francs cannot be sent from Ledgerly because the VAT line is wrong when the currency is not euros. Dana Holt calls it a blocker.
- Paying full seats for two juniors who only need to view invoice status.

**Shown**
- Dana Holt keeps a spreadsheet for the franc invoices and runs it next to Ledgerly, which means paying for two tools.

## Gains
- Send every invoice, including the biggest client's franc invoices, from Ledgerly alone and drop the spreadsheet.
- Give junior staff a way to see invoice status without a full paid seat.

## Their words
- "VAT line is still wrong"
- "pay full seats"
- "why am I paying for both"

## Workflow
- Payment reminders now use two templates: one for regulars and one for slow payers.
- The Friday reminder session went from three hours to one hour after the templates.
- Franc invoices are made by hand in a spreadsheet, outside Ledgerly.

## Tools and alternatives
- Ledgerly for most invoices and reminders; its new templates helped.
- A spreadsheet for Swiss franc invoices. Dana Holt will keep it unless Ledgerly handles the currency.

## Decision
- Dana Holt speaks as the budget holder on seats and on whether to keep paying for Ledgerly next to the spreadsheet.
- Criterion: Ledgerly must replace the spreadsheet, or the double cost is not worth it.
- Seat pricing for view-only users is a second cost objection.
- Budget figures and timing were not stated.

## Requests
- Correct VAT line on invoices in non-euro currencies, Swiss francs first. Reason: the biggest client pays in francs and the invoice cannot be sent from Ledgerly today. Bug report: on a franc invoice, expected a correct VAT line, got a wrong one.
- A cheaper or free view-only seat for people who only see invoice status. Reason: two new juniors.

## Quote bank
> Our biggest client pays in francs. If I can not send that invoice from Ledgerly, I keep the spreadsheet, and then why am I paying for both?
— Dana Holt, on Swiss franc invoices and the cost of running a spreadsheet alongside Ledgerly

> We hired two juniors who only need to see the invoice status. I do not want to pay full seats for them.
— Dana Holt, on seat pricing for view-only users

> The VAT line is still wrong when the currency is not euros.
— Dana Holt, on the VAT bug on non-euro invoices

> Fridays went from three hours to one.
— Dana Holt, on the effect of the new reminder templates

> I can now write one template for regulars and one for slow payers.
— Dana Holt, on reminder templates

## Open questions
- Which other currencies besides Swiss francs do they invoice in?
- Would a view-only seat at a lower price satisfy the junior-seat objection, and what price would they accept?
- Does Dana Holt alone decide on keeping Ledgerly, or does someone else sign off?
