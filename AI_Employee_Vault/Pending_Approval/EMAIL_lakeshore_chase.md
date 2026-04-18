---
type: approval_request
action: send_email
to: admin@lakeshorefp.example
subject: "Checking in on INV-2026-038 — anything I can help unblock?"
thread_id: ""
gmail_message_id: lakeshore_chase_20d
created: 2026-04-13T07:00:00Z
expires: 2026-04-14T07:00:00Z
status: pending
escalation_level: 2
generated_by: draft-reply skill
---

## Draft

Hi Erin,

Following up on invoice INV-2026-038 ($2,800) — it's been 20 days past
due and I haven't heard back on my 2026-04-06 check-in. I want to
make sure this isn't stuck on something on your end.

If there's a missing PO number, a new vendor-onboarding step, or
anything else I can unblock for your AP team, let me know and I'll
get it over today.

If there's a reason to hold payment, please flag it and we'll pause
the clock on the March xEHR.io subscription renewal while we sort it.

— Dilawar Shafiq, CEO, autosapien
https://www.linkedin.com/in/dilawar-shafiq-b8923062/

---

## Why this tone
- Handbook § 3 — 20+ days overdue means escalation_level 2, which is
  "structured, no longer breezy". Still not legal.
- Handbook § 2 — we never imply the customer is stalling without
  confirming. Phrasing is "I want to make sure this isn't stuck on
  something on your end", not "please pay immediately".
- If Erin doesn't respond by 2026-04-17, the AI will stage escalation
  level 3 (offer a call, mention a pause on their service).

## On approve
Move to `/Approved/`. Email MCP ships it via the same auth as the
Gmail watcher. Audit line written to `Logs/<today>.jsonl`.
