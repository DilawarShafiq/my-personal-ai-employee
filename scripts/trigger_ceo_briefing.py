"""Cron-friendly entry point: drop a 'generate CEO briefing' task into the
vault for the reasoning loop to pick up.

The Task Scheduler fires this weekly. It does NOT call Claude directly —
it leaves a Needs_Action file so the next orchestrator cycle (or a manual
Ralph run) triggers the `ceo-briefing` skill.
"""
from __future__ import annotations

import os
import textwrap
from datetime import datetime, timezone, timedelta
from pathlib import Path

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()


def main() -> None:
    today = datetime.now(timezone.utc).date()
    week_start = today - timedelta(days=7)
    needs = VAULT / "Needs_Action"
    needs.mkdir(parents=True, exist_ok=True)

    body = textwrap.dedent(
        f"""\
        ---
        type: scheduled_task
        task: ceo_briefing
        period_start: {week_start.isoformat()}
        period_end: {today.isoformat()}
        created: {datetime.now(timezone.utc).isoformat(timespec='seconds')}
        priority: high
        status: pending
        ---

        # Monday Morning CEO Briefing — {today.isoformat()}

        Invoke the `ceo-briefing` Agent Skill. Target output:
        `Briefings/{today.isoformat()}_Monday_Briefing.md`.

        Pull inputs from:
        - `Accounting/Current_Month.md`
        - Odoo JSON-RPC (if running)
        - `Done/` folder for completed tasks this week
        - `Business_Goals.md` for KPI targets
        - `Logs/*.jsonl` for AI actions taken this week
        """
    )
    target = needs / f"BRIEFING_TRIGGER_{today.isoformat()}.md"
    target.write_text(body, encoding="utf-8")
    print(f"Dropped briefing trigger: {target}")


if __name__ == "__main__":
    main()
