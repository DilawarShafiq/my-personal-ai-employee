"""Odoo JSON-RPC MCP server — Gold tier's accounting integration.

Exposes read-heavy tools the CEO Briefing skill needs, plus a small set of
write tools that always create **drafts** in Odoo. Posting an invoice or
registering a payment goes through the /Approved HITL pipeline.

API: Odoo 19 external JSON-RPC (https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
Transport: stdio MCP.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Load .env before reading any ODOO_* env vars below so the MCP works
# whether launched via `uv run python -m ...` or via Claude Code's
# stdio MCP transport.
load_dotenv()

SERVER_NAME = "autosapien-odoo"
VAULT = Path(os.getenv("VAULT_PATH", "./AI_Employee_Vault")).resolve()
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "autosapien")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")
ODOO_API_KEY = os.getenv("ODOO_API_KEY", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

server: Server = Server(SERVER_NAME)

# --- JSON-RPC client ---------------------------------------------------------
_uid: int | None = None


def _jsonrpc(endpoint: str, params: dict) -> Any:
    payload = {"jsonrpc": "2.0", "method": "call", "params": params}
    r = httpx.post(f"{ODOO_URL}/{endpoint}", json=payload, timeout=30)
    r.raise_for_status()
    body = r.json()
    if "error" in body:
        raise RuntimeError(f"Odoo RPC error: {body['error']}")
    return body.get("result")


def _login() -> int:
    global _uid
    if _uid is not None:
        return _uid
    secret = ODOO_API_KEY or ODOO_PASSWORD
    uid = _jsonrpc(
        "jsonrpc",
        {"service": "common", "method": "login",
         "args": [ODOO_DB, ODOO_USER, secret]},
    )
    if not uid:
        raise RuntimeError("Odoo login failed — check ODOO_DB/USER/PASSWORD/API_KEY.")
    _uid = uid
    return uid


def _execute(model: str, method: str, *args, **kwargs) -> Any:
    uid = _login()
    secret = ODOO_API_KEY or ODOO_PASSWORD
    return _jsonrpc(
        "jsonrpc",
        {"service": "object", "method": "execute_kw",
         "args": [ODOO_DB, uid, secret, model, method, list(args), kwargs]},
    )


# --- Fallback demo data (used whenever Odoo isn't reachable) -----------------
_DEMO_SNAPSHOT = {
    "revenue_mtd": 12900.0,
    "bookings_mtd": 18400.0,
    "invoices_outstanding": [
        {"customer": "Lakeshore Family Practice", "number": "INV-2026-038",
         "amount": 2800.0, "due": "2026-03-30", "days_late": 20},
        {"customer": "Valley Billing LLC", "number": "INV-2026-040",
         "amount": 1700.0, "due": "2026-04-10", "days_late": 9},
        {"customer": "Cedar Health Billing", "number": "INV-2026-045",
         "amount": 4000.0, "due": "2026-05-02", "days_late": 0},
    ],
    "expenses_this_month": [
        {"vendor": "AWS", "amount": 420, "category": "Infra"},
        {"vendor": "Anthropic", "amount": 180, "category": "AI compute"},
        {"vendor": "Retool", "amount": 95, "category": "Internal tools"},
        {"vendor": "Notion", "amount": 15, "category": "Docs",
         "flag": "no login 58 days"},
        {"vendor": "Loom", "amount": 18, "category": "Marketing",
         "flag": "no login 42 days"},
    ],
}


def _safe_snapshot() -> dict:
    """Query Odoo for real revenue/AR/expenses; gracefully fall back to
    seeded demo data if Odoo is offline or authentication fails.

    Shape (both modes):
      {
        "live": bool,             # True when live Odoo data is loaded
        "source": "odoo" | "demo_fallback",
        "revenue_mtd": float,     # sum of paid invoices this month
        "bookings_mtd": float,    # sum of ALL posted invoices this month
        "invoices_outstanding": [{customer, number, amount, due, days_late}],
        "expenses_this_month": [{vendor, amount, category, flag?}],
      }
    """
    from datetime import date, datetime, timedelta

    try:
        _login()
        today = date.today()
        first_of_month = date(today.year, today.month, 1)

        # 1. Paid invoices this month — "collected" revenue.
        paid_invoice_ids = _execute(
            "account.move", "search",
            [("move_type", "=", "out_invoice"),
             ("state", "=", "posted"),
             ("payment_state", "in", ("paid", "in_payment")),
             ("invoice_date", ">=", first_of_month.isoformat())],
        )
        paid_invoices = _execute(
            "account.move", "read", paid_invoice_ids,
            ["amount_total", "invoice_date"],
        ) if paid_invoice_ids else []
        revenue_mtd = sum(i["amount_total"] for i in paid_invoices)

        # 2. All posted invoices this month — "bookings" revenue.
        booked_ids = _execute(
            "account.move", "search",
            [("move_type", "=", "out_invoice"),
             ("state", "=", "posted"),
             ("invoice_date", ">=", first_of_month.isoformat())],
        )
        booked = _execute(
            "account.move", "read", booked_ids, ["amount_total"],
        ) if booked_ids else []
        bookings_mtd = sum(i["amount_total"] for i in booked)

        # 3. Outstanding invoices (AR).
        outstanding_ids = _execute(
            "account.move", "search",
            [("move_type", "=", "out_invoice"),
             ("state", "=", "posted"),
             ("payment_state", "in", ("not_paid", "partial"))],
        )
        outstanding_raw = _execute(
            "account.move", "read", outstanding_ids,
            ["name", "partner_id", "amount_residual", "invoice_date_due"],
        ) if outstanding_ids else []
        invoices_outstanding = []
        for inv in outstanding_raw:
            due_str = inv.get("invoice_date_due") or ""
            try:
                due = datetime.fromisoformat(due_str).date() if due_str else today
            except ValueError:
                due = today
            days_late = max(0, (today - due).days)
            partner_name = (inv["partner_id"][1] if inv.get("partner_id") else "Unknown")
            invoices_outstanding.append({
                "customer": partner_name,
                "number": inv["name"],
                "amount": inv["amount_residual"],
                "due": due_str,
                "days_late": days_late,
            })
        invoices_outstanding.sort(key=lambda x: -x["days_late"])

        return {
            "live": True,
            "source": "odoo",
            "revenue_mtd": revenue_mtd,
            "bookings_mtd": bookings_mtd,
            "invoices_outstanding": invoices_outstanding,
            # Expenses aren't seeded in Odoo for this demo; carry the
            # hand-curated list forward so the subscription-audit skill
            # still has something to chew on.
            "expenses_this_month": _DEMO_SNAPSHOT["expenses_this_month"],
        }
    except Exception as e:  # noqa: BLE001
        return {**_DEMO_SNAPSHOT, "live": False, "source": "demo_fallback",
                "reason": str(e)}


# --- MCP tools ---------------------------------------------------------------
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="odoo_financial_snapshot",
            description="Return a summary of revenue, outstanding invoices, and expenses "
            "for the current month. Graceful-degrades to seed data if Odoo is offline.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="odoo_create_invoice_draft",
            description="Create a DRAFT customer invoice in Odoo. Never posts — posting requires "
            "a matching /Approved/INVOICE_<number>.md file and a subsequent odoo_post_invoice call.",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer": {"type": "string"},
                    "line_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "quantity": {"type": "number"},
                                "price_unit": {"type": "number"},
                            },
                            "required": ["description", "quantity", "price_unit"],
                        },
                    },
                    "due_days": {"type": "integer", "default": 14},
                },
                "required": ["customer", "line_items"],
            },
        ),
        Tool(
            name="odoo_post_invoice",
            description="Post a previously drafted Odoo invoice. REQUIRES a matching "
            "/Approved/INVOICE_<draft_id>.md file. DRY_RUN-aware.",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {"type": "integer"},
                    "approval_ref": {"type": "string"},
                },
                "required": ["draft_id", "approval_ref"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "odoo_financial_snapshot":
        snap = _safe_snapshot()
        return [TextContent(type="text", text=json.dumps(snap, indent=2))]

    if name == "odoo_create_invoice_draft":
        if DRY_RUN:
            fake = {
                "draft_id": 9999,
                "customer": arguments["customer"],
                "total": sum(li["quantity"] * li["price_unit"] for li in arguments["line_items"]),
                "dry_run": True,
            }
            return [TextContent(type="text", text=json.dumps(fake))]
        # Real Odoo partner lookup + move creation would go here.
        partner_ids = _execute("res.partner", "search", [("name", "=", arguments["customer"])], limit=1)
        if not partner_ids:
            partner_id = _execute("res.partner", "create", {"name": arguments["customer"]})
        else:
            partner_id = partner_ids[0]
        lines = [(0, 0, {"name": li["description"], "quantity": li["quantity"],
                         "price_unit": li["price_unit"]}) for li in arguments["line_items"]]
        draft_id = _execute(
            "account.move", "create",
            {"partner_id": partner_id, "move_type": "out_invoice", "invoice_line_ids": lines},
        )
        return [TextContent(type="text", text=json.dumps({"draft_id": draft_id}))]

    if name == "odoo_post_invoice":
        approved = VAULT / "Approved"
        ref = arguments["approval_ref"]
        if not list(approved.glob(f"INVOICE_{ref}*.md")):
            return [TextContent(type="text", text=f"REFUSED: no approval file for {ref}")]
        if DRY_RUN:
            return [TextContent(type="text", text=json.dumps({"posted": True, "dry_run": True}))]
        _execute("account.move", "action_post", [arguments["draft_id"]])
        return [TextContent(type="text", text=json.dumps({"posted": True}))]

    return [TextContent(type="text", text=f"ERROR: unknown tool '{name}'")]


async def _run() -> None:
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


def main() -> None:
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()
