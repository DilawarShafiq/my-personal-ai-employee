"""Email MCP server — Silver tier's one working external action.

Exposes three tools over the Model Context Protocol:
  * `gmail_get_message`    — fetch a full message body on demand
  * `gmail_create_draft`   — create a draft (safe, reversible)
  * `gmail_send_draft`     — send a previously created draft
                             (REQUIRES an approved Pending_Approval file)

Safety layers (defense in depth):
  1. DRY_RUN=true short-circuits every send and returns a canned success.
  2. `gmail_send_draft` refuses to send unless there is a matching
     `/Approved/EMAIL_<msg_id>.md` file — proof of human approval.
  3. Rate limit: max `MAX_EMAILS_PER_HOUR` sends per rolling hour,
     enforced by an on-disk counter under `AI_Employee_Vault/.limits/`.
  4. Every call writes a structured audit line to `Logs/YYYY-MM-DD.jsonl`.

Transport: stdio. Registered in `.claude/settings.json` → `mcpServers`.
"""
from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from orchestrator.retry import with_retry

SERVER_NAME = "autosapien-email"
VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()
APPROVED = VAULT / "Approved"
LOGS = VAULT / "Logs"
LIMITS = VAULT / ".limits"
LIMITS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
MAX_PER_HOUR = int(os.getenv("MAX_EMAILS_PER_HOUR", "10"))


# --------------------------------------------------------------------- utils
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _audit(event: dict[str, Any]) -> None:
    event.setdefault("timestamp", _now_iso())
    event.setdefault("actor", "email_mcp")
    log_file = LOGS / f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _rate_limit_ok() -> bool:
    counter = LIMITS / "email_send_hour.json"
    now = datetime.now(timezone.utc)
    window = now.strftime("%Y-%m-%dT%H")
    data = {"window": window, "count": 0}
    if counter.exists():
        data = json.loads(counter.read_text())
        if data.get("window") != window:
            data = {"window": window, "count": 0}
    if data["count"] >= MAX_PER_HOUR:
        return False
    data["count"] += 1
    counter.write_text(json.dumps(data))
    return True


def _approval_file_for(msg_id: str) -> Path | None:
    """Return the approval file for a message id, or None if not approved."""
    candidates = list(APPROVED.glob(f"EMAIL_{msg_id}*.md"))
    return candidates[0] if candidates else None


@with_retry(max_attempts=3, base_delay=1.0, max_delay=10.0)
def _gmail_service():
    """Lazy-build a Gmail API client; returns None when credentials missing.

    Wrapped in with_retry so a transient OAuth refresh hiccup or a flaky
    googleapi discovery call doesn't take down a whole send.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    token_path = Path(os.getenv("GMAIL_TOKEN_PATH", "./secrets/gmail_token.json"))
    if not token_path.exists():
        return None
    creds = Credentials.from_authorized_user_file(
        str(token_path),
        ["https://www.googleapis.com/auth/gmail.send",
         "https://www.googleapis.com/auth/gmail.readonly",
         "https://www.googleapis.com/auth/gmail.modify"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


# --------------------------------------------------------------------- server
server: Server = Server(SERVER_NAME)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="gmail_get_message",
            description="Fetch the full body of a Gmail message by ID. Read-only. "
            "PHI-sensitive output — do NOT paste the result into the vault verbatim.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Gmail message ID"},
                },
                "required": ["message_id"],
            },
        ),
        Tool(
            name="gmail_create_draft",
            description="Create a Gmail draft. Always safe — does not send. Returns draft ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                    "thread_id": {"type": "string", "description": "Optional — reply within a thread."},
                },
                "required": ["to", "subject", "body"],
            },
        ),
        Tool(
            name="gmail_send_draft",
            description="Send a Gmail draft. REQUIRES an approved /Approved/EMAIL_<id>.md file. "
            "Rate-limited. DRY_RUN aware.",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {"type": "string"},
                    "approval_ref": {
                        "type": "string",
                        "description": "The source message_id whose approval file authorizes this send.",
                    },
                },
                "required": ["draft_id", "approval_ref"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "gmail_get_message":
        msg_id = arguments["message_id"]
        svc = _gmail_service()
        if svc is None:
            _audit({"action_type": "email_read", "result": "no_credentials", "target": msg_id})
            return [TextContent(type="text", text="ERROR: Gmail credentials not configured.")]
        msg = svc.users().messages().get(userId="me", id=msg_id, format="full").execute()
        _audit({"action_type": "email_read", "result": "success", "target": msg_id})
        return [TextContent(type="text", text=json.dumps(msg)[:50_000])]

    if name == "gmail_create_draft":
        to = arguments["to"]
        subject = arguments["subject"]
        body = arguments["body"]
        thread_id = arguments.get("thread_id")

        if DRY_RUN:
            fake_id = f"dryrun-draft-{int(datetime.now(timezone.utc).timestamp())}"
            _audit({
                "action_type": "email_draft",
                "result": "dry_run",
                "target": to,
                "parameters": {"subject": subject, "draft_id": fake_id},
            })
            return [TextContent(type="text", text=json.dumps({"draft_id": fake_id, "dry_run": True}))]

        svc = _gmail_service()
        if svc is None:
            return [TextContent(type="text", text="ERROR: Gmail credentials not configured.")]
        mime = MIMEText(body)
        mime["to"] = to
        mime["subject"] = subject
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
        draft_body: dict[str, Any] = {"message": {"raw": raw}}
        if thread_id:
            draft_body["message"]["threadId"] = thread_id
        draft = svc.users().drafts().create(userId="me", body=draft_body).execute()
        _audit({"action_type": "email_draft", "result": "success", "target": to,
                "parameters": {"subject": subject, "draft_id": draft["id"]}})
        return [TextContent(type="text", text=json.dumps({"draft_id": draft["id"]}))]

    if name == "gmail_send_draft":
        draft_id = arguments["draft_id"]
        approval_ref = arguments["approval_ref"]

        approval = _approval_file_for(approval_ref)
        if approval is None:
            _audit({"action_type": "email_send", "result": "denied_no_approval",
                    "target": approval_ref, "parameters": {"draft_id": draft_id}})
            return [TextContent(
                type="text",
                text=f"REFUSED: no approval file /Approved/EMAIL_{approval_ref}*.md found.",
            )]

        if not _rate_limit_ok():
            _audit({"action_type": "email_send", "result": "rate_limited",
                    "parameters": {"draft_id": draft_id}})
            return [TextContent(type="text", text="REFUSED: rate limit exceeded (emails/hour).")]

        if DRY_RUN:
            _audit({"action_type": "email_send", "result": "dry_run",
                    "parameters": {"draft_id": draft_id, "approval_ref": approval_ref},
                    "approval_status": "approved", "approved_by": "human"})
            return [TextContent(type="text", text=json.dumps({"sent": True, "dry_run": True}))]

        svc = _gmail_service()
        if svc is None:
            return [TextContent(type="text", text="ERROR: Gmail credentials not configured.")]
        result = svc.users().drafts().send(userId="me", body={"id": draft_id}).execute()
        _audit({"action_type": "email_send", "result": "success",
                "parameters": {"draft_id": draft_id, "sent_message_id": result.get("id")},
                "approval_status": "approved", "approved_by": "human"})
        return [TextContent(type="text", text=json.dumps(result))]

    return [TextContent(type="text", text=f"ERROR: unknown tool '{name}'")]


async def _run() -> None:
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


def main() -> None:
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()
