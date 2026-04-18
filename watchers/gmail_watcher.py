"""Gmail watcher — Silver tier's second watcher.

Converts new high-priority Gmail threads into `Needs_Action/*.md` notes.
Runs in DRY_RUN-friendly mode: if credentials aren't present, it logs
and sleeps instead of crashing — so the orchestrator stays green even
before you wire up OAuth.

Auth: standard Google OAuth installed-app flow. On first run, a browser
window opens once; the resulting token is stored in GMAIL_TOKEN_PATH
and reused forever.

PHI policy: email bodies are *not* copied into the vault. Only headers
(From, Subject, Date) + the 150-char Gmail snippet. The full body stays
in Gmail; the vault gets a pointer (`gmail_message_id`) and Claude reads
the body on-demand via the Gmail MCP when it needs context.
"""
from __future__ import annotations

import base64
import os
import textwrap
from pathlib import Path
from typing import Any, Iterable

from watchers.base_watcher import BaseWatcher, log

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailWatcher(BaseWatcher):
    """Polls Gmail for unread, non-promo messages and drops notes into Needs_Action."""

    name = "gmail"

    def __init__(self, vault_path: str | Path, check_interval: int = 120) -> None:
        super().__init__(vault_path, check_interval=check_interval)
        self.credentials_path = Path(
            os.getenv("GMAIL_CREDENTIALS_PATH", "./secrets/gmail_credentials.json")
        )
        self.token_path = Path(os.getenv("GMAIL_TOKEN_PATH", "./secrets/gmail_token.json"))
        self.query = os.getenv("GMAIL_QUERY", "is:unread -category:promotions newer_than:7d")
        self._service = None  # lazily built

    # ----------------------------------------------------------- auth/setup
    def _ensure_service(self):
        if self._service is not None:
            return self._service
        if not self.credentials_path.exists():
            log.warning(
                "gmail.no_credentials",
                hint="place OAuth client JSON at {}".format(self.credentials_path),
            )
            return None

        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds: Credentials | None = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), GMAIL_SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(creds.to_json(), encoding="utf-8")

        self._service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        return self._service

    # ---------------------------------------------------------------- logic
    def check_for_updates(self) -> Iterable[dict[str, Any]]:
        svc = self._ensure_service()
        if svc is None:
            return []
        resp = svc.users().messages().list(userId="me", q=self.query, maxResults=15).execute()
        for m in resp.get("messages", []):
            if m["id"] in self.processed_ids:
                continue
            yield {"id": m["id"], "thread_id": m.get("threadId")}

    def create_action_file(self, item: dict[str, Any]) -> Path:
        svc = self._ensure_service()
        assert svc is not None
        msg = (
            svc.users()
            .messages()
            .get(userId="me", id=item["id"], format="metadata",
                 metadataHeaders=["From", "To", "Subject", "Date"])
            .execute()
        )
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        snippet = msg.get("snippet", "")

        classification_hint = self._guess_classification(headers.get("Subject", ""), snippet)

        body = textwrap.dedent(
            f"""\
            ---
            type: email
            source: gmail_watcher
            gmail_message_id: {item["id"]}
            gmail_thread_id: {item.get("thread_id", "")}
            from: {headers.get("From", "Unknown")}
            to: {headers.get("To", "")}
            subject: {headers.get("Subject", "(no subject)")}
            date: {headers.get("Date", "")}
            received: {self._stamp()}
            priority: {classification_hint["priority"]}
            classification_hint: {classification_hint["label"]}
            status: pending
            phi_check: body_stays_in_gmail_only
            ---

            ## Snippet (first 150 chars, no PHI — full body stays in Gmail)
            {snippet}

            ## How Claude should handle this
            1. Read `Company_Handbook.md` for the tone + approval rules.
            2. If you need the full body, use the Gmail MCP `get_message` tool
               with `gmail_message_id={item["id"]}` — never paste the body here.
            3. Draft a reply in `Plans/PLAN_{item["id"]}.md`.
            4. If the reply is send-class, create `Pending_Approval/EMAIL_{item["id"]}.md`.
            """
        )
        path = self._write_md("Needs_Action", f"EMAIL_{item['id']}.md", body)
        self.processed_ids.add(item["id"])
        return path

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _guess_classification(subject: str, snippet: str) -> dict[str, str]:
        s = f"{subject} {snippet}".lower()
        if any(k in s for k in ("urgent", "asap", "down", "outage", "security", "breach")):
            return {"label": "urgent", "priority": "urgent"}
        if any(k in s for k in ("invoice", "payment", "past due", "overdue", "ap ")):
            return {"label": "admin", "priority": "medium"}
        if any(k in s for k in ("demo", "pricing", "quote", "proposal", "rfp", "pilot")):
            return {"label": "sales", "priority": "high"}
        if any(k in s for k in ("bug", "issue", "error", "ticket", "help")):
            return {"label": "support", "priority": "high"}
        if any(k in s for k in ("unsubscribe", "newsletter", "weekly digest")):
            return {"label": "noise", "priority": "low"}
        return {"label": "unclassified", "priority": "normal"}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    GmailWatcher(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).run()
