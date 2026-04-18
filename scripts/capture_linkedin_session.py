"""One-time LinkedIn session capture.

Run this ONCE. A non-headless Chromium opens, you log in manually
(including any 2FA), and the session cookies are saved to
LINKEDIN_SESSION_PATH. After that, headless posts work indefinitely
until LinkedIn invalidates the session (usually months).

    uv run python scripts/capture_linkedin_session.py
"""
from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    session_path = Path(os.getenv("LINKEDIN_SESSION_PATH", "./secrets/linkedin_session"))
    session_path.mkdir(parents=True, exist_ok=True)
    print(f"Opening LinkedIn. Log in and complete any 2FA — the session will save to:\n  {session_path}\n")
    print("Close the browser window when done.")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.linkedin.com/login")
        print("\nWaiting for you to finish logging in (up to 5 minutes)...")
        try:
            page.wait_for_url("**/feed/**", timeout=300_000)
            print("[OK] Session captured. You can close the browser.")
        except Exception:
            print("[WARN] Did not reach the feed in time. If you logged in, the session is still saved to disk.")
        # Leave the browser open so the user can verify & close.


if __name__ == "__main__":
    main()
