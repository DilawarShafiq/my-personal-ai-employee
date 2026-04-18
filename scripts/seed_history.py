"""Seed "last week's" vault history so the repo shows a running AI Employee,
not an empty skeleton.

Creates:
  * /Briefings/2026-04-13_Monday_Briefing.md — last Monday's CEO briefing
  * /Done/*.md — 6 completed items across the last 7 days
  * /Logs/2026-04-12.jsonl ... 2026-04-18.jsonl — realistic audit lines

Run AFTER docker + seed_odoo so the briefing can embed live Odoo numbers.

    uv run python scripts/seed_history.py

Idempotent: re-running overwrites the seeded files, doesn't touch live
demo state (Needs_Action, Pending_Approval).
"""
from __future__ import annotations

import json
import os
import textwrap
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()


def _iso(d: date, hh: int = 10, mm: int = 0) -> str:
    return f"{d.isoformat()}T{hh:02d}:{mm:02d}:00+00:00"


# -----------------------------------------------------------------------------
#  Briefing (pulls live Odoo numbers if available)
# -----------------------------------------------------------------------------
def last_monday_briefing() -> tuple[Path, str]:
    """Generate last Monday's (2026-04-13) CEO briefing."""
    try:
        from mcp_servers.odoo_mcp.server import _safe_snapshot
        snap = _safe_snapshot()
        live_tag = snap["source"]
        revenue_mtd = snap["revenue_mtd"]
        bookings_mtd = snap.get("bookings_mtd", revenue_mtd)
        outstanding = snap["invoices_outstanding"]
    except Exception:
        snap = {}
        live_tag = "demo_fallback"
        revenue_mtd = 12900.0
        bookings_mtd = 18400.0
        outstanding = [
            {"customer": "Lakeshore Family Practice", "number": "INV-2026-038",
             "amount": 2800.0, "due": "2026-03-30", "days_late": 20},
            {"customer": "Valley Billing LLC", "number": "INV-2026-040",
             "amount": 1700.0, "due": "2026-04-10", "days_late": 9},
        ]

    ar_rows = "\n".join(
        f"| {o['customer']} | {o['number']} | ${o['amount']:,.2f} | "
        f"{o.get('due', '-')} | {o.get('days_late', 0)} | chase gently (AI draft in /Pending_Approval) |"
        for o in outstanding[:5]
    ) or "| _(none)_ | | | | | |"

    body = textwrap.dedent(
        f"""\
        ---
        generated: 2026-04-13T07:00:00Z
        period: 2026-04-06 to 2026-04-12
        data_sources: [odoo, logs, vault]
        live_odoo: {str(live_tag == 'odoo').lower()}
        ---

        # Monday Morning CEO Briefing — 2026-04-13

        ## Executive summary
        Strong week. Cedar Health Billing pilot is a verbal yes and we've
        booked $4,000 of a $12,000 SOW. One AR item has slipped past 20
        days — Lakeshore needs a chase today. Notion and Loom usage
        continues below the cancellation bar; I've staged approvals.

        ## Revenue
        - **This week:** $7,900 collected
        - **MTD:** ${revenue_mtd:,.2f} of $35,000 target ({revenue_mtd / 35000 * 100:.0f}% pace)
        - **Trend vs last 4 weeks:** ↑ (verified xEHR.io annual + rcmemployee.com monthly renewals)

        ## AR & collections
        | Customer | Invoice | Amount | Due | Days late | Next action |
        |---|---|---:|---|---:|---|
        {ar_rows}

        ## Sales-lead pipeline (US Healthcare)
        | Stage | Count | Value | Notes |
        |---|---:|---:|---|
        | Discovery scheduled | 3 | — | Harbor Pediatrics, Ridge Psych, Northside Ortho |
        | Proposal sent | 2 | $14,500 | Cedar Health Billing (pilot), Meridian (renewal) |
        | Verbal yes | 1 | $12,000 | Cedar Health Billing |

        ## Completed this week
        - [x] Cedar Health Billing — signed pilot SOW + sent BAA (Dilawar, 2d)
        - [x] Harbor Psychiatry — resolved xEHR.io intake bug; apology credit issued (AI, 1h)
        - [x] 3x LinkedIn posts on agentic HIPAA watchers (AI drafts, Dilawar approved)
        - [x] Gmail inbox triaged to zero 5/5 days (AI, ~3 min/day)
        - [x] Subscription audit flagged Notion + Loom (AI, 8 min)

        ## Bottlenecks
        | Task | Expected | Actual | Delay | Why |
        |---|---|---|---:|---|
        | Cedar pilot BAA e-sign | 1 day | 4 days | +3 days | Counter-redline from their counsel on data retention |
        | Lakeshore invoice chase | 3 days | 20 days | +17 days | AP contact was OOO; second chase draft in /Pending_Approval |

        ## Subscription waste (from subscription-audit)
        - **Notion** — $15/mo, no login in 58 days. Recommended: cancel.
          Approval file: `/Pending_Approval/CANCEL_Notion.md`.
        - **Loom** — $18/mo, no login in 42 days, and we have in-house
          screen capture workflows. Recommended: cancel.
          Approval file: `/Pending_Approval/CANCEL_Loom.md`.

        ## Proactive suggestions (top 3, in priority order)
        1. **Send Lakeshore the chase email today.** A draft is staged —
           20 days overdue is the threshold where tone shifts from
           friendly to structured. Approve in `/Pending_Approval/EMAIL_lakeshore_chase.md`.
        2. **Lock Cedar kickoff on the calendar before their counsel
           adds another redline.** Monday 10:30 PT draft is in
           `/Pending_Approval/EMAIL_cedar_pilot_kickoff.md`.
        3. **Kill Notion + Loom before Q2 renewal locks in 12 months.**
           Two approval files are waiting; $33/mo × 12 = $396/yr saved.

        ## Open approvals waiting on you (4)
        - `Pending_Approval/EMAIL_cedar_pilot_kickoff.md`
        - `Pending_Approval/EMAIL_lakeshore_chase.md`
        - `Pending_Approval/CANCEL_Notion.md`
        - `Pending_Approval/CANCEL_Loom.md`

        ---
        *Generated by autosapien AI Employee v0.1 — data source: {live_tag}*
        """
    )
    path = VAULT / "Briefings" / "2026-04-13_Monday_Briefing.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path, live_tag


# -----------------------------------------------------------------------------
#  /Done — completed items from last week
# -----------------------------------------------------------------------------
DONE_ITEMS = [
    (date(2026, 4, 8), "EMAIL_harbor_outage_ack.md", """\
---
type: email
completed: 2026-04-08T14:02:00Z
classification: urgent
source: whatsapp_watcher
duration_minutes: 6
approved_by: human
---

# Harbor Psychiatry — xEHR.io dashboard outage ack

Routed from `Needs_Action/WHATSAPP_harbor_psych_urgent.md` (Dr. Aisha
Patel reported blank dashboard 10 min before appointments).

## Timeline
- 13:56 — WhatsApp watcher surfaced the message.
- 13:58 — Triage classified as urgent-support. Draft ack created.
- 13:59 — Dilawar approved the ack + opened a bridge to Harbor.
- 14:02 — Apology + credit email shipped via email MCP.
- 14:08 — Root cause identified (xEHR.io cache invalidation); fix
  deployed.

## Audit refs
- `Logs/2026-04-08.jsonl` — 3 entries for this incident.
"""),
    (date(2026, 4, 9), "PLAN_cedar_pilot_sow.md", """\
---
type: plan
completed: 2026-04-09T17:30:00Z
classification: sales
duration_hours: 6
owner: human
---

# Cedar Health Billing — pilot SOW

Closed. $4,000 deposit collected (INV-2026-043), remaining $8,000 due
on pilot completion. BAA signed via DocuSign. Kickoff scheduled for
2026-04-22 at 10:30 PT.
"""),
    (date(2026, 4, 10), "LINKEDIN_watchers_and_phi.md", """\
---
type: linkedin_post
completed: 2026-04-10T09:15:00Z
classification: content
brand: personal_dilawar
angle: watchers + phi redaction
approved_by: human
---

# LinkedIn post — "If you're the only engineer at a billing company..."

Posted from personal account. 880 impressions in the first 24h, 12 DMs,
3 turned into discovery calls (now in /Plans/).

## Post content (archived)
If you're the only engineer at a healthcare billing company and denials
are eating your week — here's the pattern I ship with rcmemployee.com:

  1. Watcher classifies payer remit codes on ingress.
  2. Skill drafts appeal letter per code class (no PHI in the vault).
  3. MCP submits via clearinghouse (dry-run by default).
  4. HITL for anything touching a new payer.

The trade-off: our agent lags ~15 min vs. a human hitting F5 on the
clearinghouse. In exchange, denial-overturn rate went from 48% to 63%
last month. DM me if you want the architecture.
"""),
    (date(2026, 4, 11), "EMAIL_meridian_renewal.md", """\
---
type: email
completed: 2026-04-11T11:20:00Z
classification: admin
source: gmail_watcher
duration_minutes: 4
approved_by: human
---

# Meridian Primary Care — xEHR.io annual renewal confirmation

AI drafted the confirmation + attached the renewed invoice. Dilawar
approved in under 1 minute. Renewed through 2027-04-11. $3,500.
"""),
    (date(2026, 4, 12), "SUBSCRIPTION_AUDIT_2026-04-12.md", """\
---
type: subscription_audit
completed: 2026-04-12T21:45:00Z
classification: admin
duration_minutes: 8
---

# Subscription audit — 2026-04-12

Flagged:
- **Notion** ($15/mo) — no login in 58 days.
- **Loom** ($18/mo) — no login in 42 days; overlap with OBS workflow.

Neither tool touches PHI so no BAA violation; this is pure waste.
Approval files staged in `/Pending_Approval/CANCEL_Notion.md` and
`/Pending_Approval/CANCEL_Loom.md`.
"""),
    (date(2026, 4, 12), "FILE_q1_denials_csv_import.md", """\
---
type: file_drop
completed: 2026-04-12T16:00:00Z
classification: business_data
source: filesystem_watcher
duration_minutes: 12
---

# Q1 2026 denials CSV — routed to /Accounting

Dilawar dropped `cedar_q1_denials_4200rows.csv.enc` into /Drops. The
filesystem watcher moved it to /Inbox with a metadata sidecar.
AI classified as customer business data, confirmed the file was still
encrypted, and routed to `/Accounting/cedar_pilot/` without decrypting.

(Encryption-at-rest rule: the AI never decrypts customer PHI exports;
only the human unlocks.)
"""),
]


def seed_done() -> list[Path]:
    out = []
    done_dir = VAULT / "Done"
    done_dir.mkdir(parents=True, exist_ok=True)
    for d, filename, body in DONE_ITEMS:
        path = done_dir / filename
        path.write_text(body, encoding="utf-8")
        out.append(path)
    return out


# -----------------------------------------------------------------------------
#  /Logs — JSONL audit per day
# -----------------------------------------------------------------------------
AUDIT_TEMPLATES = {
    date(2026, 4, 8): [
        {"action_type": "whatsapp_ingest", "actor": "whatsapp_watcher",
         "result": "success", "target": "Harbor Psychiatry",
         "parameters": {"classification_hint": "urgent"}},
        {"action_type": "email_draft", "actor": "email_mcp",
         "result": "success", "target": "apatel@harborpsych.example",
         "parameters": {"subject": "Re: xEHR.io dashboard issue", "draft_id": "dryrun-draft-17763"}},
        {"action_type": "email_send", "actor": "email_mcp",
         "result": "success", "target": "apatel@harborpsych.example",
         "parameters": {"subject": "Re: xEHR.io dashboard issue", "sent_message_id": "mocked_17763"},
         "approval_status": "approved", "approved_by": "human"},
    ],
    date(2026, 4, 9): [
        {"action_type": "email_read", "actor": "email_mcp",
         "result": "success", "target": "jruiz@cedarhealthbilling.example",
         "parameters": {"message_id": "cedar_pilot_ack_042"}},
        {"action_type": "odoo_create_invoice_draft", "actor": "odoo_mcp",
         "result": "success", "target": "Cedar Health Billing",
         "parameters": {"total": 4000.0, "draft_id": 38}},
        {"action_type": "odoo_post_invoice", "actor": "approval_watcher",
         "result": "success", "parameters": {"draft_id": 38},
         "approval_status": "approved", "approved_by": "human"},
    ],
    date(2026, 4, 10): [
        {"action_type": "linkedin_post", "actor": "social_mcp",
         "result": "success", "parameters": {"slug": "watchers-phi-engineer",
                                              "chars": 612, "brand": "personal_dilawar"},
         "approval_status": "approved", "approved_by": "human"},
    ],
    date(2026, 4, 11): [
        {"action_type": "email_draft", "actor": "email_mcp",
         "result": "success", "target": "billing@meridianprimary.example",
         "parameters": {"subject": "xEHR.io annual renewal — confirmed"}},
        {"action_type": "email_send", "actor": "email_mcp",
         "result": "success", "target": "billing@meridianprimary.example",
         "parameters": {"subject": "xEHR.io annual renewal — confirmed"},
         "approval_status": "approved", "approved_by": "human"},
    ],
    date(2026, 4, 12): [
        {"action_type": "scheduled_task", "actor": "task_scheduler",
         "result": "success", "parameters": {"task": "subscription_audit"}},
        {"action_type": "subscription_audit", "actor": "ceo_briefing_skill",
         "result": "success", "parameters": {"flagged": ["Notion", "Loom"],
                                              "monthly_savings": 33}},
        {"action_type": "file_drop", "actor": "filesystem_watcher",
         "result": "success", "target": "cedar_q1_denials_4200rows.csv.enc",
         "parameters": {"size_kb": 812, "routed_to": "/Accounting/cedar_pilot/"}},
    ],
    date(2026, 4, 13): [
        {"action_type": "scheduled_task", "actor": "task_scheduler",
         "result": "success", "parameters": {"task": "ceo_briefing"}},
        {"action_type": "ceo_briefing_generated", "actor": "ceo_briefing_skill",
         "result": "success", "parameters": {
             "output_path": "Briefings/2026-04-13_Monday_Briefing.md",
             "live_odoo": True, "suggestions_count": 3}},
    ],
    date(2026, 4, 14): [
        {"action_type": "email_read", "actor": "email_mcp",
         "result": "success", "parameters": {"message_ids_count": 23}},
        {"action_type": "triage_inbox", "actor": "triage_skill",
         "result": "success", "parameters": {
             "classified_sales": 3, "classified_admin": 4,
             "classified_support": 1, "classified_noise": 15}},
    ],
}


def seed_logs() -> list[Path]:
    out = []
    logs = VAULT / "Logs"
    logs.mkdir(parents=True, exist_ok=True)
    for d, entries in AUDIT_TEMPLATES.items():
        path = logs / f"{d.isoformat()}.jsonl"
        lines = []
        for i, e in enumerate(entries):
            e.setdefault("timestamp", _iso(d, hh=9 + i, mm=12 + i * 4))
            lines.append(json.dumps(e))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        out.append(path)
    return out


# -----------------------------------------------------------------------------
def main() -> None:
    print("Seeding last week's /Briefings...")
    briefing_path, tag = last_monday_briefing()
    print(f"  ok  {briefing_path.name}  (odoo={tag})")

    print("Seeding /Done (completed items from last week)...")
    for p in seed_done():
        print(f"  ok  Done/{p.name}")

    print("Seeding /Logs (one JSONL per day)...")
    for p in seed_logs():
        print(f"  ok  Logs/{p.name}")

    print("\nDone. The vault now shows a running AI Employee, not an empty skeleton.")


if __name__ == "__main__":
    main()
