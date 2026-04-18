"""Watchdog — keeps every watcher alive with backoff + restart.

The orchestrator starts watchers in threads; watchdog.py is a separate
process that monitors them and restarts the orchestrator if the whole
process dies. On Windows this plays nicely with the Task Scheduler
startup entry we register in `scripts/install_windows_tasks.ps1`.

Design:
  * Poll every `WATCHDOG_INTERVAL` seconds (default 30).
  * Track last-seen liveness via an on-disk heartbeat file written by the
    orchestrator (`AI_Employee_Vault/.heartbeat`).
  * If heartbeat is older than `WATCHDOG_STALENESS` seconds, restart.
  * Exponential backoff between restarts (2, 4, 8, 16, 32 — cap 60).
  * After `WATCHDOG_MAX_RESTARTS` failures, stop and write an
    `/Needs_Action/INCIDENT_orchestrator_down.md` so the CEO sees it.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import structlog

log = structlog.get_logger()
VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()
HEARTBEAT = VAULT / ".heartbeat"
INTERVAL = int(os.getenv("WATCHDOG_INTERVAL", "30"))
STALE = int(os.getenv("WATCHDOG_STALENESS", "180"))
MAX_RESTARTS = int(os.getenv("WATCHDOG_MAX_RESTARTS", "6"))


def _heartbeat_age() -> float:
    if not HEARTBEAT.exists():
        return 10**9
    return time.time() - HEARTBEAT.stat().st_mtime


def _start_orchestrator() -> subprocess.Popen:
    log.info("watchdog.starting_orchestrator")
    return subprocess.Popen(
        [sys.executable, "-m", "orchestrator.orchestrator"],
        cwd=str(VAULT.parent),
    )


def _write_incident(restart_count: int, reason: str) -> None:
    VAULT.joinpath("Needs_Action").mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    body = f"""---
type: incident
source: watchdog
priority: urgent
created: {stamp}
status: pending
---

# Orchestrator down — watchdog gave up after {restart_count} restarts

**Reason:** {reason}

Check:
- Is `uv` reachable? (`uv --version`)
- Is the `.venv` intact? (`uv sync`)
- Any Python exceptions in the last run? Look in the most recent
  `orchestrator.*` log under `AI_Employee_Vault/Logs/`.

Until this is resolved, **no watchers are running** — your AI Employee
is offline.
"""
    (VAULT / "Needs_Action" / "INCIDENT_orchestrator_down.md").write_text(body, encoding="utf-8")


def main() -> None:
    restarts = 0
    backoff = 2
    proc = _start_orchestrator()

    try:
        while True:
            time.sleep(INTERVAL)

            if proc.poll() is not None:
                log.warning("watchdog.orchestrator_exited", code=proc.returncode)
                restarts += 1
                if restarts > MAX_RESTARTS:
                    _write_incident(restarts, f"orchestrator exited with code {proc.returncode}")
                    return
                time.sleep(backoff)
                backoff = min(60, backoff * 2)
                proc = _start_orchestrator()
                continue

            age = _heartbeat_age()
            if age > STALE:
                log.warning("watchdog.heartbeat_stale", age=age)
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                restarts += 1
                if restarts > MAX_RESTARTS:
                    _write_incident(restarts, f"heartbeat stale for {age:.0f}s")
                    return
                time.sleep(backoff)
                backoff = min(60, backoff * 2)
                proc = _start_orchestrator()
            else:
                # Healthy tick — decay backoff.
                backoff = max(2, backoff // 2)
    except KeyboardInterrupt:
        log.info("watchdog.exit")
        proc.terminate()


if __name__ == "__main__":
    main()
