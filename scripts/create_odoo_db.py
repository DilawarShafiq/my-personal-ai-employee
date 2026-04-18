"""Headless Odoo database creation — no browser clicks.

Hits /web/database/create with the master password set in
odoo/config/odoo.conf (default 'admin'). Creates the `autosapien`
database with admin/admin credentials.

    uv run python scripts/create_odoo_db.py

Safe to re-run: if the DB already exists, it logs and exits cleanly.
"""
from __future__ import annotations

import os
import sys
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "autosapien")
ODOO_MASTER = os.getenv("ODOO_MASTER_PASSWORD", "admin")
ADMIN_LOGIN = os.getenv("ODOO_USER", "admin")
ADMIN_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")


def _wait_for_odoo(url: str, seconds: int = 180) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            r = httpx.get(f"{url}/web/database/selector", timeout=5)
            if r.status_code < 500:
                return
        except Exception:
            pass
        print("  waiting for Odoo to be reachable...")
        time.sleep(5)
    print(f"ERROR: Odoo at {url} did not become reachable within {seconds}s.")
    sys.exit(1)


def _db_exists(url: str, db: str) -> bool:
    r = httpx.post(
        f"{url}/jsonrpc",
        json={"jsonrpc": "2.0", "method": "call",
              "params": {"service": "db", "method": "list", "args": []}},
        timeout=15,
    )
    try:
        return db in (r.json().get("result") or [])
    except Exception:
        return False


def main() -> None:
    print(f"Waiting for Odoo at {ODOO_URL}...")
    _wait_for_odoo(ODOO_URL)

    if _db_exists(ODOO_URL, ODOO_DB):
        print(f"Database '{ODOO_DB}' already exists. Skipping create.")
        return

    print(f"Creating database '{ODOO_DB}'...")
    # Odoo's /web/database/create endpoint takes multipart form data.
    data = {
        "master_pwd": ODOO_MASTER,
        "name": ODOO_DB,
        "login": ADMIN_LOGIN,
        "password": ADMIN_PASSWORD,
        "phone": "",
        "lang": "en_US",
        "country_code": "us",
        "demo": "False",
    }
    with httpx.Client(timeout=180, follow_redirects=True) as client:
        r = client.post(f"{ODOO_URL}/web/database/create", data=data)
    if r.status_code >= 400:
        print(f"ERROR: create_database returned {r.status_code}")
        print(r.text[:500])
        sys.exit(1)

    # Verify.
    time.sleep(3)
    if not _db_exists(ODOO_URL, ODOO_DB):
        print("ERROR: DB creation call returned OK but the DB is not listed.")
        print("Try creating it manually at http://localhost:8069 (master pwd = 'admin').")
        sys.exit(1)

    print(f"\nDone. Login at http://localhost:8069 with "
          f"{ADMIN_LOGIN}/{ADMIN_PASSWORD}.")


if __name__ == "__main__":
    main()
