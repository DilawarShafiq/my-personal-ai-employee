"""Base class for every perception-layer watcher.

A watcher converts an external signal (email, file drop, social mention,
bank transaction) into a Markdown file inside the vault that the Claude
reasoning loop will later pick up. Watchers are **dumb** on purpose —
they do not reason, they do not call Claude, they only translate.

Design rules:
  * Never write PHI or secrets into the vault. Redact on the way in.
  * Idempotent: running the same watcher twice on the same input must
    produce at most one vault file (uses processed-id set + stable
    filenames).
  * Crash-resilient: exceptions are logged and the loop continues so a
    single bad upstream message cannot take down the AI employee.
  * Respects DRY_RUN=true for any side effect beyond writing to the vault.
"""
from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import structlog

log = structlog.get_logger()


class BaseWatcher(ABC):
    """Template for every autosapien.com watcher.

    Subclasses implement `check_for_updates` (pull from the outside world)
    and `create_action_file` (write one vault file per item).
    """

    #: Human-readable name. Used in filenames and log events.
    name: str = "base"

    def __init__(self, vault_path: str | Path, check_interval: int = 60) -> None:
        self.vault_path = Path(vault_path).resolve()
        self.inbox = self.vault_path / "Inbox"
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs = self.vault_path / "Logs"
        self.check_interval = check_interval
        self.processed_ids: set[str] = set()
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

        # Ensure target folders exist. Never silently fail.
        for p in (self.inbox, self.needs_action, self.logs):
            p.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"watcher.{self.name}")

    # ------------------------------------------------------------------ API
    @abstractmethod
    def check_for_updates(self) -> Iterable[dict[str, Any]]:
        """Return an iterable of new items (already filtered by processed_ids)."""

    @abstractmethod
    def create_action_file(self, item: dict[str, Any]) -> Path:
        """Persist a single item into the vault. Return the written path."""

    # ------------------------------------------------------ shared helpers
    def _stamp(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _write_md(self, relative_folder: str, filename: str, body: str) -> Path:
        folder = self.vault_path / relative_folder
        folder.mkdir(parents=True, exist_ok=True)
        # Sanitize filename for Windows
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        path = folder / safe
        path.write_text(body, encoding="utf-8")
        log.info("watcher.write", watcher=self.name, path=str(path))
        return path

    # -------------------------------------------------------------- main
    def run(self) -> None:
        log.info("watcher.start", watcher=self.name, dry_run=self.dry_run)
        while True:
            try:
                items = list(self.check_for_updates())
                for item in items:
                    self.create_action_file(item)
                    # `create_action_file` is responsible for recording
                    # the id in processed_ids so we don't double-write.
            except KeyboardInterrupt:
                log.info("watcher.stop", watcher=self.name)
                return
            except Exception as e:  # noqa: BLE001 — watchers must never die
                log.error("watcher.error", watcher=self.name, error=str(e))
            time.sleep(self.check_interval)
