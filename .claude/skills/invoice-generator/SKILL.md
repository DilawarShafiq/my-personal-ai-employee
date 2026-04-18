---
name: invoice-generator
description: Draft a customer invoice in Odoo (as a DRAFT only), stage it for CEO approval, and prepare the corresponding send-email approval. Use when the user says "invoice X for $Y", "bill client", or when a completed milestone in /Done/ flags itself as billable.
---

# invoice-generator

## When to use
- User says *"send invoice to X"*, *"bill X for $Y"*.
- A milestone file in `Done/` includes frontmatter `billable: true` and
  hasn't been invoiced yet (cross-check with `Accounting/Current_Month.md`).

## Process
1. Collect line items. Source of truth for rate: `Accounting/Rates.md`
   (or the SOW file in `Done/`).
2. Call the Odoo MCP `odoo_create_invoice_draft` tool with:
   - `customer` (Odoo partner name)
   - `line_items[]` — description, quantity, price_unit
   - `due_days` — default 14, override per contract
3. You will get back `draft_id`. Record it.
4. Write `Pending_Approval/INVOICE_<draft_id>.md`:

```markdown
---
type: approval_request
action: odoo_post_invoice
draft_id: <n>
customer: <name>
total: <n>
due: <iso>
created: <iso>
status: pending
---

## Draft invoice
- Customer: ...
- Line items:
  - ...
- Total: $<n>
- Due: <date>

## On approve
Move to /Approved. Approval watcher will call `odoo_post_invoice` and
then stage an `Pending_Approval/EMAIL_invoice_<id>.md` so you can review
the outgoing email separately.
```

5. Update `Dashboard.md`: "Draft invoice <n> for <customer> — $<total> staged".

## Safety
- Never call `odoo_post_invoice` directly from this skill. Always HITL.
- If Odoo is offline (dry_run or connection error), stage the approval
  anyway with `draft_id: pending` and a note that the post will happen
  once Odoo is reachable.

## Output contract
- One Odoo draft (or pending record).
- One `Pending_Approval/INVOICE_*.md`.
- `<promise>INVOICE_DRAFT_READY</promise>`.
