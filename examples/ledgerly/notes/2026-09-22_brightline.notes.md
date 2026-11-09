---
call_id: 2026-09-22_brightline
customer: "Brightline"
pools: [product, marketing, sales]
extracted_at: 2026-11-09
extracted_by: claude-sonnet
quality: partial
---
# 2026-09-22_brightline

## Customer context
Brightline is a design studio and a Ledgerly customer for one year. Jonas Weber speaks for it and handles money and invoicing. The studio has eleven salaries. Its accountant works in Xero. The studio logs hours in Harvest.

## Pains
**Said**
- Every month somebody retypes Harvest hours into the invoices, and it takes a full afternoon.
- A single late phase sign-off forces Jonas to move money around for a week, because he cannot see incoming cash before the bank shows it.

**Shown**
- Jonas answers the "what would you add first" question with cash visibility, not an invoicing feature. Cash timing worries him more than invoice creation.

## Gains
- See next month's incoming money, by client, ahead of the bank.
- Hours flow from Harvest into invoices without retyping.

## Their words
- "retypes them into the invoices"
- "a full afternoon"
- "before the bank tells me"
- "move money around for a week"

## Workflow
Brightline bills by phase. An invoice goes out when the client signs off a phase, not on a fixed date. Hours come from Harvest. Each month one person retypes them into the invoices by hand. The accountant works in Xero.

## Tools and alternatives
- Harvest: source of hours.
- Xero: the accountant's system. Sync with Xero is a hard requirement.
- No competitor is named in this call.

## Decision
Jonas appears to decide for the studio. The accountant influences the choice through Xero. Xero sync was the deciding criterion for the switch to Ledgerly: without it the answer is a no. Budget and timing are not discussed.

## Requests
- A cash forecast view for next month: what comes in, by client, ahead of the bank. Reason: eleven salaries and phase-based billing make timing risky.
- Harvest hours imported into invoices (implied by the monthly retyping pain, not asked for outright).

## Quote bank
> Anything we pick has to sync with Xero, or it is a no.
— Jonas Weber, on the switch decision

> Every month somebody retypes them into the invoices. It takes a full afternoon.
— Jonas Weber, on Harvest hours

> We have eleven salaries. One late phase sign-off and I move money around for a week.
— Jonas Weber, on why cash visibility matters

> A view of next month. I want to see what comes in, by client, before the bank tells me.
— Jonas Weber, on the first feature he would add

> By phase. The invoice goes out when the client signs off a phase, not on a date.
— Jonas Weber, on how Brightline bills

## Open questions
- Does Jonas want a Harvest integration, or only less retyping? He never asked for it by name.
- Does "view of next month" need only phase sign-off dates, or also expected payment dates?
