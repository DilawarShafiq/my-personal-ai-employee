"""Weekly subscription-audit trigger. Drops a task file for the reasoning loop."""
from __future__ import annotations

import os
import textwrap
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()


def main() -> None:
    ts = datetime.now(timezone.utc).date().isoformat()
    needs = VAULT / "Needs_Action"
    needs.mkdir(parents=True, exist_ok=True)

    body = textwrap.dedent(
        f"""\
        ---
        type: scheduled_task
        task: subscription_audit
        created: {datetime.now(timezone.utc).isoformat(timespec='seconds')}
        priority: medium
        status: pending
        ---

        # Subscription audit — week of {ts}

        Invoke the `subscription-audit` Agent Skill.

        Rules are in `Business_Goals.md § Subscription audit rules`.
        For each tool flagged: create a `Pending_Approval/CANCEL_<vendor>.md`
        with the cancellation recommendation and evidence.
        """
    )
    (needs / f"SUBSCRIPTION_AUDIT_{ts}.md").write_text(body, encoding="utf-8")
    print("Dropped subscription-audit trigger.")


if __name__ == "__main__":
    main()
