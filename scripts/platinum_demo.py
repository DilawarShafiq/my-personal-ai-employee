"""Platinum-lite delegation demo.

Simulates the Cloud-drafts / Local-approves flow end-to-end WITHOUT
needing a real cloud VM. Two Python functions play the two roles
against the same vault. Perfect for the demo video — shows judges the
claim-by-move rule, the /Updates/ merge pattern, and the single-writer
Dashboard rule, all in 90 seconds.

Usage:
    uv run python scripts/platinum_demo.py

Flow:
    1. Simulate a new inbound email arriving while "local is offline".
    2. `cloud_agent_turn()` — claims the item, drafts a reply, stages
       approval, posts an /Updates/ note.
    3. `local_agent_turn()` — reviews the approval, moves to /Approved/,
       merges /Updates/ into Dashboard.md. Approval watcher ships it.
"""
from __future__ import annotations

import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()
os.environ.setdefault("VAULT_PATH", str(VAULT))
os.environ.setdefault("DRY_RUN", "true")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _banner(title: str) -> None:
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}")


def simulate_inbound_email() -> Path:
    """Gmail watcher ran on Cloud → dropped this into /Needs_Action."""
    path = VAULT / "Needs_Action" / "EMAIL_platinum_demo_001.md"
    path.write_text(
        f"""---
type: email
source: cloud_gmail_watcher
gmail_message_id: platinum_demo_001
from: Morgan Wallis <mw@harborfamilyclinic.example>
subject: HIPAA question before demo
received: {_now()}
priority: high
classification_hint: sales
status: pending
---

## Snippet
Your last LinkedIn post mentioned you run HIPAA-compliant agents on
local-first infra. Our clinic has 8 providers and we are evaluating
rcmemployee.com. Can we get a 20-min call next Tue or Thu?
""",
        encoding="utf-8",
    )
    print(f"  [Gmail watcher] New item: {path.name}")
    return path


def cloud_agent_turn(item: Path) -> None:
    _banner("CLOUD agent turn — claim, draft, stage approval, post update")

    # 1. Claim-by-move
    in_progress = VAULT / "In_Progress" / "cloud-agent"
    in_progress.mkdir(parents=True, exist_ok=True)
    claimed = in_progress / item.name
    shutil.move(str(item), claimed)
    print(f"  [cloud] claimed {claimed.relative_to(VAULT)}")

    # 2. Draft a reply → Plans/email/
    plans = VAULT / "Plans" / "email"
    plans.mkdir(parents=True, exist_ok=True)
    plan_path = plans / "PLAN_platinum_demo_001.md"
    plan_path.write_text(
        f"""---
type: plan
slug: platinum_demo_001
objective: Respond to Morgan's demo request and propose Tue/Thu slot.
owner: ai_employee
created: {_now()}
status: in_progress
linked_source: In_Progress/cloud-agent/{item.name}
approval_gates: [send_email]
---

## Draft reply
Hi Morgan,

Thanks for the note. 8 providers is exactly our sweet spot for the
rcmemployee.com denials workflow. Happy to walk you through how we
keep the loop HIPAA-safe (local-first vault, PHI redaction on ingress,
HITL on every send-class action).

Proposing Tuesday 11:00 PT or Thursday 14:00 PT — whichever works, I'll
send the BAA and an agenda.

— Dilawar
""",
        encoding="utf-8",
    )
    print(f"  [cloud] drafted {plan_path.relative_to(VAULT)}")

    # 3. Stage approval → Pending_Approval/email/
    pend = VAULT / "Pending_Approval" / "email"
    pend.mkdir(parents=True, exist_ok=True)
    pend_path = pend / "EMAIL_platinum_demo_001.md"
    pend_path.write_text(
        f"""---
type: approval_request
action: send_email
to: mw@harborfamilyclinic.example
subject: "Re: HIPAA question before demo"
gmail_message_id: platinum_demo_001
created: {_now()}
status: pending
origin: cloud-agent
---

(draft body inlined from Plans/email/PLAN_platinum_demo_001.md)

## To approve
Move this file to /Approved/
""",
        encoding="utf-8",
    )
    print(f"  [cloud] staged approval {pend_path.relative_to(VAULT)}")

    # 4. Post an /Updates/ note — cloud cannot touch Dashboard.md directly
    updates = VAULT / "Updates"
    updates.mkdir(parents=True, exist_ok=True)
    update_path = updates / f"{_now().replace(':', '-')}_cloud.md"
    update_path.write_text(
        f"""---
origin: cloud-agent
ts: {_now()}
category: draft_ready
---

1 email drafted and staged for approval: `Pending_Approval/email/EMAIL_platinum_demo_001.md`
— from Harbor Family Clinic (HIPAA / demo request).
""",
        encoding="utf-8",
    )
    print(f"  [cloud] wrote update {update_path.relative_to(VAULT)}")


def local_agent_turn() -> None:
    _banner("LOCAL agent turn — pull, approve, merge, ship")

    # 1. Dilawar (human) moves the approval file
    pend = VAULT / "Pending_Approval" / "email" / "EMAIL_platinum_demo_001.md"
    approved_dir = VAULT / "Approved"
    approved_dir.mkdir(parents=True, exist_ok=True)
    approved_path = approved_dir / pend.name
    shutil.move(str(pend), approved_path)
    print(f"  [human]  moved {pend.name} -> /Approved/")

    # 2. Merge /Updates/ into Dashboard.md (single-writer rule)
    dashboard = VAULT / "Dashboard.md"
    dash_text = dashboard.read_text(encoding="utf-8")
    merged_entry = f"- [{_now()}] Cloud drafted reply to Harbor Family Clinic; moved to /Approved."
    dash_text = dash_text.replace(
        "## Recent activity\n<!-- The local agent appends entries here. Keep most-recent first. -->",
        f"## Recent activity\n<!-- The local agent appends entries here. Keep most-recent first. -->\n{merged_entry}",
        1,
    )
    dashboard.write_text(dash_text, encoding="utf-8")
    print(f"  [local]  merged Cloud update into Dashboard.md")

    # 3. Approval watcher dispatches the send (dry-run)
    from orchestrator.approval_watcher import _run_once
    _run_once()
    done = VAULT / "Done" / "EMAIL_platinum_demo_001.md"
    print(f"  [local]  approval watcher fired; Done/ has: {done.exists()}")


def main() -> None:
    item = simulate_inbound_email()
    time.sleep(1)
    cloud_agent_turn(item)
    time.sleep(1)
    local_agent_turn()
    _banner("Done — inspect /Logs/*.jsonl for the audit trail.")


if __name__ == "__main__":
    main()
