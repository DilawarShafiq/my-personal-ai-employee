"""Approval executor — the bridge between HITL and the action layer.

This watcher tails `AI_Employee_Vault/Approved/`. When a file lands here
(because the human moved it from `/Pending_Approval/`), the executor:

  1. Parses the YAML frontmatter to find `action`, `target`, `parameters`.
  2. Dispatches to the correct MCP client (email, linkedin, odoo, ...).
  3. On success, moves the file into `/Done/` and writes an audit entry.
  4. On failure, leaves the file in `/Approved/` and appends an error note.

This is the one piece of glue that turns a markdown vault into a real
autonomous system. The human acts by **moving a file**, not by typing.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import structlog
import yaml

log = structlog.get_logger()

VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()
APPROVED = VAULT / "Approved"
DONE = VAULT / "Done"
LOGS = VAULT / "Logs"
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


def _parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    try:
        return yaml.safe_load(block) or {}
    except yaml.YAMLError:
        # Best-effort fallback: line-by-line "key: value" split so a single
        # unquoted "Re: subject" line doesn't kill the whole approval.
        parsed: dict = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            parsed[k.strip()] = v.strip().strip('"').strip("'")
        return parsed


def _audit(event: dict) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    event.setdefault("timestamp", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    event.setdefault("actor", "approval_watcher")
    log_file = LOGS / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _dispatch(path: Path, meta: dict) -> bool:
    """Return True on success → caller moves file to /Done."""
    action = (meta.get("action") or "").lower()

    if action == "send_email":
        # Delegate to Gmail via the email MCP. Because this lives in the
        # same process as the orchestrator we can call the helpers directly
        # rather than spinning up an MCP client — faster and simpler.
        from mcp_servers.email_mcp.server import _gmail_service, _rate_limit_ok

        if DRY_RUN:
            _audit({"action_type": "email_send", "result": "dry_run",
                    "target": meta.get("to"), "parameters": {"subject": meta.get("subject")},
                    "approval_status": "approved", "approved_by": "human"})
            log.info("approval.email_dry_run", to=meta.get("to"))
            return True

        if not _rate_limit_ok():
            _audit({"action_type": "email_send", "result": "rate_limited"})
            log.warning("approval.rate_limited")
            return False

        svc = _gmail_service()
        if svc is None:
            _audit({"action_type": "email_send", "result": "no_credentials"})
            return False

        from email.mime.text import MIMEText
        import base64 as b64
        body_text = meta.get("body") or path.read_text(encoding="utf-8").split("---", 2)[-1].strip()
        mime = MIMEText(body_text)
        mime["to"] = meta["to"]
        mime["subject"] = meta.get("subject", "(no subject)")
        raw = b64.urlsafe_b64encode(mime.as_bytes()).decode()
        result = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
        _audit({"action_type": "email_send", "result": "success",
                "target": meta["to"], "parameters": {"subject": meta.get("subject"),
                "sent_message_id": result.get("id")},
                "approval_status": "approved", "approved_by": "human"})
        return True

    if action == "linkedin_post":
        from mcp_servers.linkedin_poster import post as linkedin_post  # lazy
        ok = linkedin_post(meta.get("content", ""), dry_run=DRY_RUN)
        _audit({"action_type": "linkedin_post",
                "result": "dry_run" if DRY_RUN else ("success" if ok else "failure"),
                "parameters": {"chars": len(meta.get("content", ""))},
                "approval_status": "approved", "approved_by": "human"})
        return ok

    if action in ("x_post", "facebook_post", "instagram_post"):
        # Gold tier handlers — stubbed until Gold MCPs are live.
        _audit({"action_type": action, "result": "not_implemented_yet"})
        log.warning("approval.action_not_implemented", action=action)
        return False

    if action == "cancel_subscription":
        # High-risk; always dry-run for demo purposes.
        _audit({"action_type": "cancel_subscription", "result": "dry_run",
                "target": meta.get("vendor"),
                "approval_status": "approved", "approved_by": "human"})
        return True

    log.warning("approval.unknown_action", action=action, file=str(path))
    _audit({"action_type": "unknown", "result": "ignored",
            "parameters": {"raw_action": action, "file": path.name}})
    return False


def _run_once() -> None:
    if not APPROVED.exists():
        return
    for path in sorted(APPROVED.iterdir()):
        if path.suffix != ".md" or path.name.startswith("."):
            continue
        meta = _parse_frontmatter(path)
        if not meta:
            log.warning("approval.no_frontmatter", file=path.name)
            continue
        log.info("approval.dispatch", file=path.name, action=meta.get("action"))
        try:
            ok = _dispatch(path, meta)
        except Exception as e:  # noqa: BLE001
            log.error("approval.dispatch_error", file=path.name, error=str(e))
            _audit({"action_type": meta.get("action"), "result": "error", "error": str(e)})
            continue
        if ok:
            DONE.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), DONE / path.name)


def main() -> None:
    log.info("approval_watcher.start", vault=str(VAULT), dry_run=DRY_RUN)
    while True:
        try:
            _run_once()
        except KeyboardInterrupt:
            return
        except Exception as e:  # noqa: BLE001
            log.error("approval_watcher.loop_error", error=str(e))
        time.sleep(5)


if __name__ == "__main__":
    main()
