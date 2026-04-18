---
name: draft-reply
description: Draft a reply to an inbound email, chat, or DM and stage it for human approval before sending. Use whenever the user says "draft a reply", "respond to X", or when triage-inbox classified an item as needing a send-class response.
---

# draft-reply — turn a Needs_Action item into an approvable draft

## When to use
Triggered whenever an item is classified `sales | support | admin` (from
`Company_Handbook.md § 5`) and the decision is *reply by email/DM*.
Never fires on `noise` or `urgent` (urgent items escalate to the human).

## Inputs
- A source file in `Needs_Action/` (email, WhatsApp, LinkedIn DM, etc.).
- `Company_Handbook.md` — tone, signature, approval thresholds.
- `Business_Goals.md` — metrics you may cite (only if tagged `verified:`).

## Process
1. Read the source file's YAML frontmatter for `from`, `subject`, `gmail_message_id`.
2. For emails, call the `gmail_get_message` MCP tool with `gmail_message_id` to
   read the full body. **Never paste the body back into the vault.** Reason
   about it in your working memory only.
3. Draft a reply that:
   - Opens with the sender's first name.
   - Mirrors their tone (terse → terse; warm → warm).
   - Uses concrete numbers only from `Business_Goals.md` rows marked `verified: ✅`.
   - For healthcare prospects, defaults to BAA-friendly phrasing.
   - Ends with the signature block from `Company_Handbook.md § 2`.
4. Write the draft into `Plans/PLAN_<source_id>.md` (a durable record).
5. If the action is send-class, also create a `Pending_Approval` file:

```markdown
---
type: approval_request
action: send_email
to: <recipient>
subject: "<subject — always quoted, YAML chokes on colons like 'Re:'>"
thread_id: <gmail_thread_id or empty>
gmail_message_id: <source msg id — used as approval_ref>
created: <iso timestamp>
expires: <iso +24h>
status: pending
---

## Draft
<full draft body here>

## Why this requires approval
- Per Company_Handbook.md § 3 — [cite the row that matched].

## To approve
Move this file to `/Approved/`. The approval watcher will execute the send.

## To reject
Move to `/Rejected/` or simply delete.
```

Save it as `Pending_Approval/EMAIL_<gmail_message_id>.md` — the filename
must match the ID the email MCP will look up in `gmail_send_draft`.

## Output contract
- One `Plans/PLAN_*.md` file per handled item.
- One `Pending_Approval/EMAIL_*.md` file per send-class item.
- Source file in `Needs_Action/` moved to `Done/` **only after** the
  approval file is written.
- Audit lines in `Logs/<today>.jsonl` using the standard schema.
- End your turn with `<promise>DRAFT_REPLY_COMPLETE</promise>` so the
  Ralph loop can exit cleanly.
