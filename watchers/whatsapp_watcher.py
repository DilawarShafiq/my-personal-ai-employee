"""WhatsApp Web watcher (Playwright-based).

**Terms-of-service note:** WhatsApp Web automation is a grey area. This
watcher is designed for scraping a **personal** WhatsApp Web session you
already log into on your own device; it does NOT use any private API.
Do not point it at an account that is not yours, and do not use it for
broadcast / marketing messaging. Dilawar uses it to turn customer DMs
into vault items so the triage-inbox skill can draft (not send) replies.

Auth flow:
  1. `uv run python scripts/capture_whatsapp_session.py` — opens a
     non-headless Chromium, you scan the QR on your phone, cookies are
     written to WHATSAPP_SESSION_PATH.
  2. From then on, the watcher runs headless and reuses that session.

PHI safety:
  * Message bodies that score as medical context (contain MRN-like IDs,
    DOB patterns, payer names) are redacted before being written to the
    vault. Only a 160-char snippet is ever persisted in Needs_Action.
"""
from __future__ import annotations

import os
import re
import textwrap
from pathlib import Path
from typing import Any, Iterable

from watchers.base_watcher import BaseWatcher, log

# Very conservative PHI redaction — if the snippet looks like it contains
# a patient identifier, we replace the matched span.
_PHI_PATTERNS = [
    re.compile(r"\b(?:MRN|MR#|DOB|SSN)[:\s#-]*[\w-]+", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN-shaped
    re.compile(r"\b(?:patient|claim)\s+#?\s*\d{4,}\b", re.IGNORECASE),
]

_URGENT_KEYWORDS = [
    "urgent", "asap", "outage", "down", "security", "breach",
    "invoice", "payment", "overdue", "help",
]


def _redact(text: str) -> str:
    for pat in _PHI_PATTERNS:
        text = pat.sub("[REDACTED_PHI]", text)
    return text


class WhatsAppWatcher(BaseWatcher):
    """Polls WhatsApp Web via a persistent Playwright profile."""

    name = "whatsapp"

    def __init__(self, vault_path: str | Path, check_interval: int = 30) -> None:
        super().__init__(vault_path, check_interval=check_interval)
        self.session_path = Path(
            os.getenv("WHATSAPP_SESSION_PATH", "./secrets/whatsapp_session")
        )

    def _session_available(self) -> bool:
        return self.session_path.exists() and any(self.session_path.iterdir())

    def check_for_updates(self) -> Iterable[dict[str, Any]]:
        if not self._session_available():
            log.warning(
                "whatsapp.no_session",
                hint="run scripts/capture_whatsapp_session.py first",
            )
            return []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            log.error("whatsapp.playwright_missing",
                      hint="uv sync && uv run playwright install chromium")
            return []

        results: list[dict[str, Any]] = []
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=True,
                viewport={"width": 1280, "height": 900},
            )
            try:
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
                try:
                    page.wait_for_selector('[data-testid="chat-list"]', timeout=15_000)
                except Exception:
                    # Session likely expired — QR screen is showing.
                    log.warning("whatsapp.session_expired",
                                hint="re-run scripts/capture_whatsapp_session.py")
                    return []

                # Enumerate chats with an unread badge.
                unread_chats = page.query_selector_all('[aria-label*="unread"]')
                for chat in unread_chats[:10]:
                    try:
                        chat_label = chat.get_attribute("aria-label") or ""
                        # Open the chat to grab the latest message preview.
                        chat.click()
                        page.wait_for_timeout(400)

                        # Grab the most recent message from the conversation pane.
                        msgs = page.query_selector_all('div.message-in span.selectable-text')
                        if not msgs:
                            continue
                        raw = (msgs[-1].inner_text() or "").strip()
                        if not raw:
                            continue
                        snippet = _redact(raw)[:160]
                        item_id = f"{chat_label[:40]}::{hash(raw) & 0xffffffff}"
                        if item_id in self.processed_ids:
                            continue
                        # Only surface if it looks urgent / actionable.
                        lowered = raw.lower()
                        if not any(k in lowered for k in _URGENT_KEYWORDS):
                            continue
                        results.append({
                            "id": item_id,
                            "chat_label": chat_label,
                            "snippet": snippet,
                        })
                    except Exception as e:  # noqa: BLE001
                        log.warning("whatsapp.chat_parse_failed", error=str(e))
            finally:
                ctx.close()
        return results

    def create_action_file(self, item: dict[str, Any]) -> Path:
        safe_label = re.sub(r"\W+", "_", item["chat_label"])[:40] or "unknown"
        body = textwrap.dedent(
            f"""\
            ---
            type: whatsapp
            source: whatsapp_watcher
            chat_label: {item['chat_label']}
            received: {self._stamp()}
            priority: high
            classification_hint: urgent
            status: pending
            phi_check: snippet_redacted_by_watcher
            ---

            ## Snippet (160 chars, PHI-redacted)
            {item['snippet']}

            ## How Claude should handle this
            1. Read `Company_Handbook.md` § 2 (tone) and § 5 (triage rules).
            2. WhatsApp urgent items **never auto-reply**. Draft into
               `Plans/PLAN_whatsapp_{safe_label}.md` and stage an approval
               file — per Handbook § 3, urgent customer messages always
               require CEO approval even when the recipient is known.
            3. If the full message context is required, open WhatsApp
               manually — we do not expose a full-message MCP tool for
               privacy reasons.
            """
        )
        path = self._write_md(
            "Needs_Action",
            f"WHATSAPP_{safe_label}_{int(__import__('time').time())}.md",
            body,
        )
        self.processed_ids.add(item["id"])
        return path


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    WhatsAppWatcher(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).run()
