"""Seed the vault with realistic healthcare-RCM sample inputs for demos.

Run once after cloning so the first `triage-inbox` invocation has
something to work on:

    uv run python scripts/seed_vault.py

Idempotent: re-running overwrites the seed files without touching any
real work that has accumulated in other folders.
"""
from __future__ import annotations

import os
import textwrap
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


SEEDS: list[tuple[str, str, str]] = [
    (
        "Needs_Action/EMAIL_cedar_health_pilot_kickoff.md",
        "Sales — clinic pilot kickoff request",
        textwrap.dedent(
            f"""\
            ---
            type: email
            source: gmail_watcher
            from: Jennifer Ruiz <jruiz@cedarhealthbilling.com>
            to: dilawar@autosapien.com
            subject: Re: RCM pilot — can we start next Monday?
            received: {_now()}
            priority: high
            status: pending
            phi_risk: none
            classification_hint: sales
            ---

            ## Email body (redacted, no PHI)
            Hi Dilawar,

            The leadership team signed off. We want to kick off the
            rcmemployee.com denials pilot next Monday. Can you send us:
            1. The BAA for e-signature,
            2. The kickoff agenda (30 min), and
            3. The list of clearinghouse credentials you'll need.

            We have about **4,200 denied claims** from Q1 to feed the pilot.

            — Jen

            ## Suggested actions
            - [ ] Reply today (within 4h SLA per handbook § 2)
            - [ ] Attach BAA template
            - [ ] Propose Monday 10:30 PT (respecting no-meeting-before-10 rule)
            - [ ] Create `Plans/PLAN_cedar_pilot_kickoff.md`
            """
        ),
    ),
    (
        "Needs_Action/EMAIL_valley_billing_invoice_followup.md",
        "Admin — overdue invoice follow-up",
        textwrap.dedent(
            f"""\
            ---
            type: email
            source: gmail_watcher
            from: Accounts Payable <ap@valleybilling.example>
            to: billing@autosapien.com
            subject: INV-2026-040 — status?
            received: {_now()}
            priority: medium
            status: pending
            classification_hint: admin
            ---

            ## Email body
            Our records show INV-2026-040 ($1,700) is outstanding but we paid
            it on 4/11 via ACH. Can you confirm receipt? Reference
            trace number 8829-4410.

            ## Suggested actions
            - [ ] Check `Accounting/Current_Month.md` — invoice still marked
                  outstanding. Reconcile vs Odoo when available.
            - [ ] If payment landed, update AR and draft thank-you reply.
            - [ ] If payment NOT landed, escalate to Dilawar — never imply
                  non-receipt to a customer without confirmation.
            """
        ),
    ),
    (
        "Needs_Action/WHATSAPP_harbor_psych_urgent.md",
        "Support — urgent xEHR.io outage report",
        textwrap.dedent(
            f"""\
            ---
            type: whatsapp
            source: whatsapp_watcher
            from: Dr. Aisha Patel — Harbor Psychiatry
            received: {_now()}
            priority: urgent
            status: pending
            classification_hint: support
            keywords_matched: urgent, down
            ---

            ## Message (redacted — no patient info)
            Hey Dilawar, our xEHR.io dashboard has been loading blank
            for the last 20 minutes. Two of my clinicians have appointments
            starting in 10 min. Please help.

            ## Suggested actions
            - [ ] This is urgent per handbook — **do not draft-and-wait**,
                  create an urgent plan and ping Dilawar.
            - [ ] Check status.xEHR.io (placeholder).
            - [ ] Draft a short acknowledgement ("on it, ETA 5 min")
                  and place in `Pending_Approval/` — customer-facing urgent
                  replies still require CEO eyeballs per § 2.
            """
        ),
    ),
    (
        "Needs_Action/CALENDAR_speaking_invite_himss.md",
        "Admin — speaking invite (HIMSS regional)",
        textwrap.dedent(
            f"""\
            ---
            type: calendar_invite
            source: gmail_watcher
            from: HIMSS Regional Coordinator
            received: {_now()}
            priority: low
            status: pending
            classification_hint: admin
            ---

            ## Invite
            Keynote slot at HIMSS Pacific Northwest 2026 on building
            HIPAA-compliant AI agents. 45 min + 15 min Q&A.

            ## Suggested actions
            - [ ] Handbook § 7 says press/speaking invites must escalate
                  to Dilawar. Create an approval file, DO NOT auto-accept.
            """
        ),
    ),
    (
        "Needs_Action/NOISE_newsletter.md",
        "Noise — marketing newsletter",
        textwrap.dedent(
            f"""\
            ---
            type: email
            source: gmail_watcher
            from: DevOps Weekly <news@devopsweekly.example>
            subject: Issue #687 — eBPF, Kubernetes 1.32, ...
            received: {_now()}
            priority: low
            classification_hint: noise
            ---

            ## Body preview
            (newsletter content, no action required)

            ## Suggested actions
            - [ ] Classify as noise, move directly to /Done/ with audit entry.
            """
        ),
    ),
]


def main() -> None:
    for rel, title, body in SEEDS:
        target = VAULT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        print(f"  seeded  {rel}  ({title})")
    print(f"\nDone. {len(SEEDS)} sample items in {VAULT}/Needs_Action")


if __name__ == "__main__":
    main()
