"""Filesystem drop watcher — Bronze tier's "one working watcher".

Watches `AI_Employee_Vault/Drops/`. Any file dropped there (PDF, CSV, image,
text) gets copied into `Inbox/` with a metadata `.md` sidecar in
`Needs_Action/` that tells Claude what was dropped and suggests actions.

Why filesystem for Bronze? It needs zero external credentials, runs in
60 seconds, and gives a compelling demo: drop a fake denial-letter PDF
onto your desktop → AI Employee files it + suggests next steps.
"""
from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any, Iterable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from watchers.base_watcher import BaseWatcher, log


class _DropHandler(FileSystemEventHandler):
    def __init__(self, parent: "FileSystemWatcher") -> None:
        self.parent = parent

    def on_created(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.is_directory:
            return
        src = Path(event.src_path)
        if src.name.startswith(".") or src.suffix == ".tmp":
            return
        # Debounce — file may still be being written.
        time.sleep(0.5)
        self.parent._enqueue(src)


class FileSystemWatcher(BaseWatcher):
    """Moves files from `/Drops/` into `/Inbox/` and drafts a Needs_Action note."""

    name = "filesystem"

    def __init__(self, vault_path: str | Path, check_interval: int = 3) -> None:
        super().__init__(vault_path, check_interval=check_interval)
        self.drops_dir = self.vault_path / "Drops"
        self.drops_dir.mkdir(parents=True, exist_ok=True)
        self._queue: list[Path] = []
        self._observer: Observer | None = None

    # ------------------------------------------------------------ internals
    def _enqueue(self, src: Path) -> None:
        self._queue.append(src)

    # ------------------------------------------------------------ BaseWatcher
    def check_for_updates(self) -> Iterable[dict[str, Any]]:
        if self._observer is None:
            handler = _DropHandler(self)
            self._observer = Observer()
            self._observer.schedule(handler, str(self.drops_dir), recursive=False)
            self._observer.start()
            # Also sweep any files that were already in Drops at startup.
            for existing in self.drops_dir.iterdir():
                if existing.is_file() and not existing.name.startswith("."):
                    self._queue.append(existing)

        pending, self._queue = self._queue, []
        for p in pending:
            if not p.exists():
                continue
            if str(p) in self.processed_ids:
                continue
            yield {"path": p}

    def create_action_file(self, item: dict[str, Any]) -> Path:
        src: Path = item["path"]
        dest_inbox = self.inbox / src.name
        try:
            shutil.move(str(src), dest_inbox)
        except Exception as e:  # file may be locked by another process
            log.warning("fs.move_failed", src=str(src), error=str(e))
            return self.needs_action / "unreadable.md"

        # Classify by extension for the suggested actions list.
        suffix = dest_inbox.suffix.lower()
        hint = {
            ".pdf": "Likely a denial letter / EOB / signed contract — extract key fields, redact PHI, file in /Accounting or /Contracts.",
            ".csv": "Looks like a bank or claims export — parse rows, update /Accounting/Current_Month.md.",
            ".png": "Screenshot — OCR if useful, otherwise attach to the relevant project note.",
            ".jpg": "Screenshot — OCR if useful, otherwise attach to the relevant project note.",
            ".txt": "Raw notes — summarize and route to the correct project.",
            ".md": "Pre-formatted note — move to the appropriate folder.",
        }.get(suffix, "Unknown type — open, read, and decide where it belongs.")

        size_kb = dest_inbox.stat().st_size / 1024
        body = f"""---
type: file_drop
source: filesystem_watcher
original_name: {src.name}
vault_path: Inbox/{dest_inbox.name}
size_kb: {size_kb:.1f}
received: {self._stamp()}
priority: normal
status: pending
phi_check: caller_must_redact_before_reading
---

## New file received

A new file was dropped into `/Drops/` and moved to `Inbox/{dest_inbox.name}`.

### Classification hint
{hint}

### Suggested actions for Claude
- [ ] Open and read the file (use the Read tool — never paste PHI into this note).
- [ ] Classify: is this billing, legal, marketing, or personal?
- [ ] If it contains PHI, redact all identifiers before summarizing here.
- [ ] Route: move the source file to the correct vault folder
      (`/Accounting`, `/Contracts`, `/Marketing`, etc.).
- [ ] Update `Dashboard.md` with a one-line entry under *Recent activity*.
- [ ] Move this Needs_Action note to `/Done/` when complete.
"""
        note_path = self._write_md(
            "Needs_Action",
            f"FILE_{dest_inbox.stem}_{int(time.time())}.md",
            body,
        )
        self.processed_ids.add(str(src))
        return note_path


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    vault = os.getenv("VAULT_PATH", "./AI_Employee_Vault")
    FileSystemWatcher(vault).run()
