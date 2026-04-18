"""One-time WhatsApp Web session capture.

Run ONCE, non-headless. A Chromium opens → you scan the QR from
WhatsApp on your phone → cookies persist to WHATSAPP_SESSION_PATH.
After that, `watchers/whatsapp_watcher.py` runs headless forever
until the session expires (usually 2-3 weeks).

    uv run python scripts/capture_whatsapp_session.py
"""
from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    session = Path(os.getenv("WHATSAPP_SESSION_PATH", "./secrets/whatsapp_session"))
    session.mkdir(parents=True, exist_ok=True)
    print("Opening WhatsApp Web. Scan the QR on your phone to link the session.")
    print(f"Session data will persist to: {session}\n")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(session),
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://web.whatsapp.com")
        print("Waiting up to 5 min for the chat list to appear...")
        try:
            page.wait_for_selector('[data-testid="chat-list"]', timeout=300_000)
            print("[OK] Session captured. You can close the browser window.")
        except Exception:
            print("[WARN] Chat list did not appear in 5 min.")
            print("If you completed the QR scan, the session is probably saved anyway.")


if __name__ == "__main__":
    main()
