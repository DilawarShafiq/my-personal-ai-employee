"""Master orchestrator — starts every watcher in its own thread.

Bronze tier starts only the filesystem watcher. Silver adds Gmail. Gold
adds Odoo-sync + social trackers. The orchestrator owns process
lifetime so a single entry-point (`uv run autosapien-orchestrator`)
brings the whole AI Employee online.
"""
from __future__ import annotations

import logging
import os
import signal
import sys
import threading
from pathlib import Path

import structlog
from dotenv import load_dotenv

from orchestrator.approval_watcher import main as run_approval_watcher
from watchers.filesystem_watcher import FileSystemWatcher

load_dotenv()

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


def _start_watchers() -> list[threading.Thread]:
    vault = _vault()
    threads: list[threading.Thread] = []

    # Bronze: filesystem watcher is always on.
    fs = FileSystemWatcher(vault)
    t = threading.Thread(target=fs.run, name="fs-watcher", daemon=True)
    t.start()
    threads.append(t)
    log.info("orchestrator.watcher.started", name="filesystem")

    # Silver: Gmail watcher (opt-in via env).
    if os.getenv("ENABLE_GMAIL_WATCHER", "false").lower() == "true":
        try:
            from watchers.gmail_watcher import GmailWatcher  # lazy import

            gm = GmailWatcher(vault)
            t = threading.Thread(target=gm.run, name="gmail-watcher", daemon=True)
            t.start()
            threads.append(t)
            log.info("orchestrator.watcher.started", name="gmail")
        except Exception as e:  # noqa: BLE001
            log.error("orchestrator.gmail_failed", error=str(e))

    # Silver: WhatsApp watcher — second opt-in watcher.
    if os.getenv("ENABLE_WHATSAPP_WATCHER", "false").lower() == "true":
        try:
            from watchers.whatsapp_watcher import WhatsAppWatcher  # lazy import

            wa = WhatsAppWatcher(vault)
            t = threading.Thread(target=wa.run, name="whatsapp-watcher", daemon=True)
            t.start()
            threads.append(t)
            log.info("orchestrator.watcher.started", name="whatsapp")
        except Exception as e:  # noqa: BLE001
            log.error("orchestrator.whatsapp_failed", error=str(e))

    # Silver: approval executor — the HITL bridge. Always on.
    t = threading.Thread(target=run_approval_watcher, name="approval-watcher", daemon=True)
    t.start()
    threads.append(t)
    log.info("orchestrator.watcher.started", name="approval")

    return threads


def main() -> int:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    log.info("orchestrator.boot", vault=str(_vault()), dry_run=os.getenv("DRY_RUN", "true"))
    threads = _start_watchers()

    stop_event = threading.Event()

    def _stop(*_):  # type: ignore[no-untyped-def]
        log.info("orchestrator.shutdown_requested")
        stop_event.set()

    signal.signal(signal.SIGINT, _stop)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _stop)  # type: ignore[attr-defined]

    # Heartbeat file for the watchdog.
    heartbeat = _vault() / ".heartbeat"
    try:
        while not stop_event.is_set():
            heartbeat.touch()
            stop_event.wait(timeout=5)
    finally:
        log.info("orchestrator.exit", thread_count=len(threads))
    return 0


if __name__ == "__main__":
    sys.exit(main())
