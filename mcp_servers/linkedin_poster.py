"""LinkedIn sales-post executor (Playwright session reuse).

We deliberately skip LinkedIn's OAuth review gauntlet and use a reusable
Playwright browser profile. The profile is captured once via
`scripts/capture_linkedin_session.py`; after that, posting is headless.

Invoked from the approval watcher when a `linkedin_post` approval file
lands in `/Approved/`. Returns True on success, False otherwise.
"""
from __future__ import annotations

import os
import time
from pathlib import Path


def post(content: str, *, dry_run: bool = True) -> bool:
    """Post to LinkedIn using the persisted Playwright session."""
    if dry_run:
        print(f"[DRY RUN] Would post to LinkedIn ({len(content)} chars):\n---\n{content[:240]}\n---")
        return True

    session_path = Path(os.getenv("LINKEDIN_SESSION_PATH", "./secrets/linkedin_session"))
    if not session_path.exists():
        print("LinkedIn session not captured. Run scripts/capture_linkedin_session.py first.")
        return False

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed — run `uv sync` and `uv run playwright install chromium`.")
        return False

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=True,
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        # Click "Start a post"
        try:
            page.click("button:has-text('Start a post')", timeout=8000)
        except Exception:
            ctx.close()
            return False

        page.wait_for_selector("div[role='textbox']", timeout=8000)
        page.fill("div[role='textbox']", content)
        page.wait_for_timeout(1500)

        # Click "Post"
        try:
            page.click("button:has-text('Post')", timeout=8000)
        except Exception:
            ctx.close()
            return False

        page.wait_for_timeout(3000)
        ctx.close()
        return True
