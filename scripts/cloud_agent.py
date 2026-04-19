"""Cloud-side orchestrator — Platinum tier role separation.

Domain ownership (per hackathon spec § Platinum):
  Cloud OWNS: email triage + draft replies + social post drafts
              + Odoo draft-only accounting
  Cloud FORBIDDEN: WhatsApp sessions, banking/payment creds, final send/post

Enforcement:
  1. Refuses to start if any forbidden env var is set (fail-closed).
  2. Refuses to boot the WhatsApp watcher or any payment MCP.
  3. All send-class actions are rewritten to draft-only: the MCP writes
     a /Pending_Approval file instead of actually dispatching.
  4. Dashboard.md is read-only here; Cloud writes to /Updates/ instead.
  5. Every action writes a JSONL audit line with actor='cloud-agent'.

Claim-by-move (the Platinum anti-race pattern):
  On each tick, Cloud moves freshly-written /Needs_Action/*.md files
  into /In_Progress/cloud-agent/ before processing. If a file is
  already inside /In_Progress/local-agent/, Cloud ignores it forever.
"""
from __future__ import annotations

import logging
import os
import shutil
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import structlog
from dotenv import load_dotenv

load_dotenv()

FORBIDDEN_ENV_VARS = [
    "WHATSAPP_SESSION_PATH_REAL",       # the Cloud env MUST NOT have a captured session
    "BANK_API_TOKEN",                   # no banking
    "STRIPE_SECRET_KEY",                # no payments
    "PLAID_ACCESS_TOKEN",
    "DWOLLA_ACCESS_TOKEN",
]


def _enforce_role_separation() -> None:
    """Fail-closed if anything smells like a local-only secret in our env."""
    bad = [k for k in FORBIDDEN_ENV_VARS if os.getenv(k)]
    if bad:
        print(f"[FATAL] Cloud agent refuses to start. Forbidden vars present in env: {bad}")
        print("  Cloud may never hold WhatsApp sessions, banking, or payment creds.")
        print("  See hackathon spec § Platinum > Security rule.")
        sys.exit(2)

    if os.getenv("ENABLE_WHATSAPP_WATCHER", "false").lower() == "true":
        print("[FATAL] Cloud agent refuses to boot the WhatsApp watcher.")
        print("  WhatsApp sessions stay on Local per work-zone ownership.")
        sys.exit(2)

    if os.getenv("AUTOSAPIEN_ROLE") != "cloud":
        print("[WARN] AUTOSAPIEN_ROLE != 'cloud'. Set it to 'cloud' in .env.cloud so the")
        print("       audit lines are correctly tagged. Continuing anyway.")


structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()


def _vault() -> Path:
    return Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _claim_by_move(vault: Path) -> list[Path]:
    """Move any unclaimed Needs_Action/*.md into /In_Progress/cloud-agent/.

    Returns the list of paths Cloud now owns this tick.
    """
    na = vault / "Needs_Action"
    target = vault / "In_Progress" / "cloud-agent"
    target.mkdir(parents=True, exist_ok=True)

    claimed: list[Path] = []
    for p in sorted(na.iterdir()):
        if p.suffix != ".md" or p.name.startswith("."):
            continue
        dest = target / p.name
        try:
            shutil.move(str(p), dest)
            claimed.append(dest)
            log.info("cloud.claim", file=p.name)
        except Exception as e:  # noqa: BLE001
            log.warning("cloud.claim_failed", file=p.name, error=str(e))
    return claimed


def _write_update(vault: Path, message: str) -> None:
    """Post a Dashboard-destined note to /Updates/ (Cloud never writes Dashboard.md)."""
    updates = vault / "Updates"
    updates.mkdir(parents=True, exist_ok=True)
    slug = _now_iso().replace(":", "-")
    (updates / f"{slug}_cloud.md").write_text(
        f"---\norigin: cloud-agent\nts: {_now_iso()}\n---\n\n{message}\n",
        encoding="utf-8",
    )


def _start_cloud_watchers() -> list[threading.Thread]:
    """Only the watchers Cloud is allowed to run: filesystem + Gmail."""
    from watchers.filesystem_watcher import FileSystemWatcher

    vault = _vault()
    threads: list[threading.Thread] = []

    fs = FileSystemWatcher(vault)
    t = threading.Thread(target=fs.run, name="cloud-fs-watcher", daemon=True)
    t.start()
    threads.append(t)
    log.info("cloud.watcher.started", name="filesystem")

    if os.getenv("ENABLE_GMAIL_WATCHER", "true").lower() == "true":
        try:
            from watchers.gmail_watcher import GmailWatcher

            gm = GmailWatcher(vault)
            t = threading.Thread(target=gm.run, name="cloud-gmail-watcher", daemon=True)
            t.start()
            threads.append(t)
            log.info("cloud.watcher.started", name="gmail")
        except Exception as e:  # noqa: BLE001
            log.error("cloud.gmail_failed", error=str(e))

    return threads


def main() -> int:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    _enforce_role_separation()

    vault = _vault()
    log.info("cloud_agent.boot",
             vault=str(vault),
             role=os.getenv("AUTOSAPIEN_ROLE", "cloud"),
             dry_run=os.getenv("DRY_RUN", "true"))

    threads = _start_cloud_watchers()
    stop_event = threading.Event()

    def _stop(*_):  # type: ignore[no-untyped-def]
        log.info("cloud_agent.shutdown_requested")
        stop_event.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    heartbeat = vault / ".heartbeat.cloud"
    tick = 0

    while not stop_event.is_set():
        try:
            # 1. Claim new Needs_Action items via move-to-In_Progress.
            claimed = _claim_by_move(vault)

            # 2. For each claimed item, the expectation is that Claude
            #    Code (running via `claude -p` or a schedule) picks them
            #    up and drafts into /Plans/<domain>/ and stages into
            #    /Pending_Approval/<domain>/. This orchestrator doesn't
            #    call Claude directly — it creates the surface area and
            #    lets the reasoning loop do its thing.
            if claimed:
                _write_update(
                    vault,
                    f"Cloud claimed {len(claimed)} new item(s) into /In_Progress/cloud-agent/. "
                    f"Waiting for the reasoning loop to draft into /Plans/<domain>/.",
                )

            # 3. Heartbeat for watchdog.
            heartbeat.touch()

            tick += 1
        except Exception as e:  # noqa: BLE001
            log.error("cloud_agent.tick_error", error=str(e))

        stop_event.wait(timeout=5)

    log.info("cloud_agent.exit", ticks=tick, thread_count=len(threads))
    return 0


if __name__ == "__main__":
    sys.exit(main())
