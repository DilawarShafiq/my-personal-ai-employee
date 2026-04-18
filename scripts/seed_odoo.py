"""Seed Odoo 19 with healthcare-RCM demo data so the CEO Briefing pulls
live numbers during the demo.

Prerequisites (all one-time):
  1. `docker compose up -d` and wait ~90 s for the db healthcheck.
  2. Create the database. Two paths, pick one:
       (a) Browser — visit http://localhost:8069 → Create Database →
           Master Password: admin, DB name: autosapien, admin / admin,
           country: United States, UNCHECK 'Demo data'.
       (b) Automated — run `uv run python scripts/create_odoo_db.py`
           which talks to /web/database/create for you.
  3. Run THIS script: `uv run python scripts/seed_odoo.py`.

Idempotent: re-running finds-or-creates every record.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import date, timedelta
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "autosapien")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")


def _jsonrpc(endpoint: str, params: dict) -> Any:
    r = httpx.post(
        f"{ODOO_URL}/{endpoint}",
        json={"jsonrpc": "2.0", "method": "call", "params": params},
        timeout=60,
    )
    r.raise_for_status()
    body = r.json()
    if "error" in body:
        raise RuntimeError(f"Odoo RPC error: {body['error']}")
    return body.get("result")


def login() -> int:
    uid = _jsonrpc(
        "jsonrpc",
        {"service": "common", "method": "login",
         "args": [ODOO_DB, ODOO_USER, ODOO_PASSWORD]},
    )
    if not uid:
        print(f"ERROR: Odoo login failed. Is the '{ODOO_DB}' DB created "
              f"with user '{ODOO_USER}' / password '{ODOO_PASSWORD}'?")
        sys.exit(1)
    return uid


def execute(uid: int, model: str, method: str, *args, **kwargs) -> Any:
    return _jsonrpc(
        "jsonrpc",
        {"service": "object", "method": "execute_kw",
         "args": [ODOO_DB, uid, ODOO_PASSWORD, model, method, list(args), kwargs]},
    )


def _ensure(uid: int, model: str, domain: list, values: dict) -> int:
    """find-or-create."""
    ids = execute(uid, model, "search", domain, limit=1)
    if ids:
        return ids[0]
    return execute(uid, model, "create", values)


# -----------------------------------------------------------------------------
#  Seed data — matches AI_Employee_Vault/Accounting/Current_Month.md so the
#  narration lines up with what the CEO Briefing displays.
# -----------------------------------------------------------------------------
CUSTOMERS = [
    {"name": "Meridian Primary Care",
     "street": "145 Chestnut Ave, Portland, OR 97202",
     "email": "billing@meridianprimary.example",
     "is_company": True,
     "industry": "healthcare / primary care"},
    {"name": "Harbor Psychiatry Group",
     "street": "22 Bay St, Seattle, WA 98121",
     "email": "ap@harborpsych.example",
     "is_company": True,
     "industry": "healthcare / behavioral health"},
    {"name": "Cedar Health Billing",
     "street": "500 Oakwood Dr, Austin, TX 78701",
     "email": "jruiz@cedarhealthbilling.example",
     "is_company": True,
     "industry": "healthcare / RCM billing co"},
    {"name": "Northside Ortho",
     "street": "3100 Maple Pkwy, Minneapolis, MN 55401",
     "email": "ops@northsideortho.example",
     "is_company": True,
     "industry": "healthcare / orthopedics"},
    {"name": "Lakeshore Family Practice",
     "street": "88 Shoreline Rd, Chicago, IL 60611",
     "email": "admin@lakeshorefp.example",
     "is_company": True,
     "industry": "healthcare / primary care"},
    {"name": "Valley Billing LLC",
     "street": "411 Valley View, Phoenix, AZ 85001",
     "email": "ap@valleybilling.example",
     "is_company": True,
     "industry": "healthcare / RCM billing co"},
]

PRODUCTS = [
    {"name": "xEHR.io — Annual license (small clinic)",
     "list_price": 3500.00, "type": "service"},
    {"name": "rcmemployee.com — Monthly AI RCM",
     "list_price": 2400.00, "type": "service"},
    {"name": "xEHR.io — Onboarding & implementation",
     "list_price": 3000.00, "type": "service"},
    {"name": "rcmemployee.com — Pilot engagement",
     "list_price": 4000.00, "type": "service"},
]

# Invoice layout matches `Accounting/Current_Month.md`:
# 4 paid, 3 outstanding (2 overdue, 1 on-time).
INVOICES = [
    # customer_idx, product_idx, invoice_date, state ('posted'|'draft'), paid?
    (0, 0, date(2026, 4, 2), True, True),   # Meridian — xEHR.io annual
    (1, 1, date(2026, 4, 5), True, True),   # Harbor — rcmemployee monthly
    (2, 3, date(2026, 4, 9), True, True),   # Cedar — pilot deposit
    (3, 2, date(2026, 4, 14), True, True),  # Northside — onboarding
    (4, 0, date(2026, 3, 30), True, False), # Lakeshore — 20 days late
    (5, 1, date(2026, 4, 10), True, False), # Valley Billing — 9 days late
    (2, 3, date(2026, 5, 2), False, False), # Cedar — not-yet-due draft
]


def seed(uid: int) -> None:
    print("Seeding customers...")
    customer_ids = []
    for c in CUSTOMERS:
        cid = _ensure(uid, "res.partner", [("name", "=", c["name"])],
                      {k: v for k, v in c.items() if k != "industry"})
        customer_ids.append(cid)
        print(f"  ok  {c['name']}  (id={cid})")

    print("Seeding products...")
    product_ids = []
    for p in PRODUCTS:
        pid = _ensure(uid, "product.product", [("name", "=", p["name"])], p)
        product_ids.append(pid)
        print(f"  ok  {p['name'][:50]:<50}  (id={pid})")

    print("Seeding invoices...")
    for i, (ci, pi, inv_date, posted, paid) in enumerate(INVOICES, start=38):
        product = execute(uid, "product.product", "read", [product_ids[pi]], ["list_price", "name"])[0]
        move_id = execute(
            uid, "account.move", "create",
            {
                "partner_id": customer_ids[ci],
                "move_type": "out_invoice",
                "invoice_date": inv_date.isoformat(),
                "invoice_date_due": (inv_date + timedelta(days=14)).isoformat(),
                "ref": f"INV-2026-{i:03d}",
                "invoice_line_ids": [(0, 0, {
                    "product_id": product_ids[pi],
                    "name": product["name"],
                    "quantity": 1,
                    "price_unit": product["list_price"],
                })],
            },
        )
        if posted:
            try:
                execute(uid, "account.move", "action_post", [move_id])
            except Exception as e:
                # Odoo sometimes needs an account to be configured first;
                # leave as draft if post fails — CEO Briefing still reads it.
                print(f"  warn  INV-2026-{i:03d}: posting failed ({e}); left as draft")

        if paid:
            try:
                # Register payment for the whole invoice
                payment_wiz = execute(
                    uid, "account.payment.register", "create",
                    {}, context={"active_model": "account.move", "active_ids": [move_id]},
                )
                execute(uid, "account.payment.register", "action_create_payments", [payment_wiz])
                print(f"  paid  INV-2026-{i:03d}")
            except Exception as e:
                print(f"  warn  INV-2026-{i:03d}: payment registration failed ({e}); marked as posted only")
        else:
            print(f"  due   INV-2026-{i:03d}")

    print("\nDone. Open http://localhost:8069 → Invoicing to see the seeded data.")


def main() -> None:
    print(f"Connecting to Odoo at {ODOO_URL} (db={ODOO_DB})...")
    uid = login()
    print(f"  logged in as uid={uid}\n")
    seed(uid)


if __name__ == "__main__":
    main()
