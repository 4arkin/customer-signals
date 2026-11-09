---
call_id: 2026-09-09_pixel-pine
customer: "Pixel & Pine"
pools: [product, marketing, sales]
extracted_at: 2026-11-09
extracted_by: claude-sonnet
quality: partial
---

# 2026-09-09_pixel-and-pine

## Customer context
- Ravi Shah speaks for Pixel & Pine, a studio of six people. Only two of them send invoices.
- They hold about four hundred clients in a spreadsheet.
- They have an office manager who did the manual data entry.
- They moved to Ledgerly from an older invoicing tool.

## Pains
**Said**
- The old tool charged per seat, so they paid for six seats when two people invoiced.
- The client import rejected about half of the four hundred rows because of the address format.
- Late payers: Ravi Shah has to remember which clients to chase and does not like that this is his own job.

**Shown**
- The office manager typed the rejected clients in by hand, which took three days.
- A sticky note on the screen holds the names of clients to chase. This is a workaround for a missing reminder process.

## Gains
_(none observed)_

## Their words
- "charged per seat"
- "The import was painful"
- "That should not be my system"

## Workflow
- Client list lived in a spreadsheet of four hundred rows.
- Import into Ledgerly: the importer rejected half; the office manager keyed the rest by hand over three days.
- Two of six people send invoices.
- Chasing late payers: Ravi Shah keeps a sticky note with client names and chases them himself.

## Tools and alternatives
- Old invoicing tool with per-seat pricing, dropped because six seats were paid for and two were used.
- A spreadsheet as the client source for the import.
- A sticky note as the late-payer tracker.

## Decision
_(none observed)_

## Requests
- Importer: on the client import with a spreadsheet of four hundred rows, expected all rows to load, got about half rejected because of the address format.
- Late payer chasing: a way to track and chase overdue clients inside the tool, so the sticky note is not needed.

## Quote bank
> Our old tool charged per seat. We are six people, and only two of us ever send an invoice, but we paid for six.
— Ravi Shah, on per-seat pricing in the old tool

> The import was painful. We had four hundred clients in a spreadsheet and the importer rejected half of them because of the address format.
— Ravi Shah, on the client import

> Typed them in by hand. It took our office manager three days.
— Ravi Shah, on the rejected imports

> I have a sticky note on my screen with the names of clients to chase. That should not be my system.
— Ravi Shah, on late payers

## Open questions
- Does a per-seat price complaint recur with other studios where few people invoice?
- Is the importer address-format rejection common, or specific to this spreadsheet?
- What does Ravi Shah expect from a late-payer feature (reminders, status, or automation)?
