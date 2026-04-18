# Odoo setup — healthcare accounting ledger for the demo

This is the fastest path: **one PowerShell command** that boots Odoo,
creates the `autosapien` database, and seeds it with healthcare
customers, products, and invoices matching
`AI_Employee_Vault/Accounting/Current_Month.md`.

## 0. Prerequisites

- **Docker Desktop** installed and running. Verify:
  ```powershell
  docker --version
  docker compose version
  ```
- **~2 GB free RAM** for Odoo + Postgres + Chromium (for other demos).
- **Port 8069** free on localhost. If something else is using it,
  `docker compose up` will fail — find the process with
  `netstat -ano | findstr :8069` and stop it.

## 1. One-command bootstrap (3 min)

From the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\bootstrap_odoo.ps1
```

This does four things, in order, with progress output:

1. `docker compose up -d` — boots Postgres 16 + Odoo 19.
2. Waits up to 3 min for `http://localhost:8069` to respond.
3. `scripts\create_odoo_db.py` — creates the `autosapien` database
   with master password `admin`, admin user `admin` / `admin`, no
   Odoo demo data (we're seeding our own).
4. `scripts\seed_odoo.py` — authenticates, creates:
   - 6 healthcare customers (Meridian Primary Care, Harbor Psychiatry
     Group, Cedar Health Billing, Northside Ortho, Lakeshore Family
     Practice, Valley Billing LLC).
   - 4 products: `xEHR.io Annual`, `rcmemployee.com Monthly`,
     `xEHR.io Onboarding`, `rcmemployee.com Pilot`.
   - 7 invoices: 4 paid, 2 overdue, 1 upcoming — exactly matching the
     numbers narrated in the CEO Briefing section of the demo.

At the end it prints the financial snapshot the CEO Briefing will
read from the Odoo MCP. If you see `"live": true`, everything worked.

## 2. Manual path (if the one-command fails)

Only needed if `bootstrap_odoo.ps1` fails mid-stream.

```powershell
docker compose up -d

# wait ~90 seconds, then open http://localhost:8069 in a browser
# fill the "Create Database" form:
#   Master Password: admin
#   DB Name:         autosapien
#   Email:           admin
#   Password:        admin
#   Country:         United States
#   UNCHECK Demo data

# once the dashboard loads, back in the terminal:
uv run python scripts\seed_odoo.py
```

## 3. Verify on camera (30 s)

Open http://localhost:8069 → **Invoicing** (or **Accounting**). You
should see:

- 6 partners under **Customers** with emails like
  `billing@meridianprimary.example`.
- 4 products under **Products** with healthcare-flavored names.
- 7 invoices under **Invoices**, with 4 in Paid status, 2 overdue,
  1 draft.

This is what the judges will see when the CEO Briefing runs — every
number in the briefing traces back to one of these rows.

## 4. Shutting down

```powershell
docker compose down        # stops containers; keeps data
docker compose down -v     # stops AND deletes all Odoo data (re-seed required)
```

## 5. Troubleshooting

**`create_odoo_db.py` prints 500 error.**
The master password in `odoo/config/odoo.conf` (`admin_passwd = admin`)
must match `ODOO_MASTER_PASSWORD` in `.env`. Both default to `admin`;
if you changed one, change the other.

**`seed_odoo.py` prints "Odoo login failed".**
Either the DB wasn't created, or `.env` has the wrong password. Verify:
```powershell
curl http://localhost:8069/jsonrpc -Method POST -Body '{"jsonrpc":"2.0","method":"call","params":{"service":"db","method":"list","args":[]}}' -ContentType 'application/json'
```
should return `{"result": ["autosapien"]}`.

**"Payment registration failed" warnings during seed.**
Odoo needs a journal and receivable account for payments. If you
didn't uncheck "Demo data" during creation, some required accounts
may be missing. Either re-create without demo data or let the
warnings slide — the unpaid invoices still flow into the CEO Briefing.

**`.conf` not picked up.**
The docker-compose mount is read-only. After editing
`odoo/config/odoo.conf`, you must:
```powershell
docker compose restart odoo
```

## 6. Why Odoo at all?

The hackathon spec's Gold tier explicitly requires:

> *Create an accounting system for your business in Odoo Community
> (self-hosted, local) and integrate it via an MCP server using Odoo's
> JSON-RPC APIs (Odoo 19+).*

We chose Community (not Odoo.sh) so the entire stack stays local-first,
which matches the hackathon's "local-first, privacy-centric" theme.
The seed is healthcare-RCM-flavored because that's the real autosapien
business — xEHR.io and rcmemployee.com sell to exactly the customers
in `CUSTOMERS` in `seed_odoo.py`.
