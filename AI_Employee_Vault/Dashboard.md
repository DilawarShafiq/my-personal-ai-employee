---
owner: Dilawar Shafiq — CEO, autosapien
updated: 2026-04-19T08:00:00Z
writer: local-agent  # single-writer rule per Platinum spec
---

# autosapien — AI Employee Dashboard

> **Single source of truth for the Digital FTE.** Every watcher writes to `/Inbox` or `/Needs_Action`; the local Claude agent owns this file.

## Status at a glance
| Surface | State | Last update |
|---|---|---|
| Filesystem watcher | 🟢 running | 2026-04-19T07:58:00Z |
| Gmail watcher | 🟢 running | 2026-04-19T07:56:12Z — pulled 2 new |
| WhatsApp watcher | ⚪ opt-in (ENABLE_WHATSAPP_WATCHER=true) | — |
| Odoo connector | 🟢 live | revenue_mtd $14,835 |
| LinkedIn poster | 🟢 session captured | last post 2026-04-10 |
| Ralph loop | 🟢 armed | max-iter 8 |
| Approval watcher | 🟢 polling /Approved every 5s | — |

## This week's focus (Q2 2026)
- Close **Cedar Health Billing** RCM pilot (denials workflow, 4-week SOW) — kickoff Mon 10:30 PT
- Ship **xEHR.io** SOC 2 Type II evidence collection automation
- Hire 2nd full-stack engineer for **rcmemployee.com**
- Cold outreach: 3 clinics/week, theme = agentic AI workflow automation

## Revenue (MTD April 2026, from Odoo)
- Bookings: **$17,595**
- Collected: **$14,835**
- Outstanding invoices: 2 — Lakeshore ($4,025, 6 days late), Valley Billing ($2,760, 0 days late)

## Recent activity
<!-- Most-recent first. local-agent appends; cloud-agent writes to /Updates/ instead. -->
- [2026-04-19T07:58:00Z] Fresh daily run — 5 new items in /Needs_Action, Ralph armed.
- [2026-04-13T07:00:00Z] CEO Briefing generated: `Briefings/2026-04-13_Monday_Briefing.md` — 3 proactive suggestions, 4 approvals pending.
- [2026-04-12T21:45:00Z] Subscription audit: Notion + Loom flagged, approval files staged.
- [2026-04-11T11:20:00Z] Meridian xEHR.io annual renewal sent + logged.
- [2026-04-10T09:15:00Z] LinkedIn post "watchers + PHI" shipped (live, personal_dilawar brand) — 3 discovery calls generated.
- [2026-04-09T17:30:00Z] Cedar Health Billing pilot SOW closed: $4,000 deposit collected (INV-2026-043).
- [2026-04-08T14:02:00Z] Harbor Psychiatry outage ack + credit shipped in 6 minutes from watcher ingress.

## Open approvals (6)
<!-- Mirrors `/Pending_Approval/` — human moves files to `/Approved` or `/Rejected`. -->
- `CANCEL_Notion.md` — $15/mo saved, 58 days no login
- `CANCEL_Loom.md` — $18/mo saved, 42 days no login, duplicate functionality
- `EMAIL_lakeshore_chase.md` — 20 days overdue, escalation level 2
- `EMAIL_cedar_pilot_kickoff.md` — Monday kickoff confirm + BAA intro
- `LINKEDIN_agentic_hipaa_watchers.md` — CTO-persona post, ready to ship
- `OUTREACH_ridge_psychiatric.md` — new-recipient cold email, behavioral health

## Guardrails cheat-sheet
- No PHI in this vault. Ever. See `Company_Handbook.md § 1 PHI policy`.
- Payments > $500 always require human approval.
- Outbound email to new recipients always requires human approval.
- Phase 1 social: personal_dilawar brand only (MCP enforces at server layer).
- DRY_RUN=true globally unless `LIVE_CHANNELS` explicitly lists a channel.
