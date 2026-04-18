# =============================================================================
# One-command Odoo bootstrap for the autosapien.com AI Employee.
#
#   powershell -ExecutionPolicy Bypass -File scripts\bootstrap_odoo.ps1
#
# Runs: docker compose up -d  →  wait  →  create DB  →  seed healthcare data.
# End state: http://localhost:8069 has a live `autosapien` DB with 6 customers,
# 4 products, and 7 invoices matching Accounting/Current_Month.md.
# =============================================================================

$ErrorActionPreference = 'Stop'

Write-Host "`n[1/4] Booting Odoo + Postgres via Docker Compose..." -ForegroundColor Cyan
docker compose up -d

Write-Host "`n[2/4] Waiting up to 3 min for Odoo to become reachable..." -ForegroundColor Cyan
$deadline = (Get-Date).AddMinutes(3)
do {
    Start-Sleep -Seconds 5
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8069/web/database/selector" -TimeoutSec 5 -UseBasicParsing
        if ($r.StatusCode -lt 500) { break }
    } catch {
        Write-Host "   still booting..."
    }
} while ((Get-Date) -lt $deadline)

Write-Host "`n[3/4] Creating 'autosapien' database (admin / admin)..." -ForegroundColor Cyan
uv run python scripts\create_odoo_db.py

Write-Host "`n[4/4] Seeding healthcare customers, products, and invoices..." -ForegroundColor Cyan
uv run python scripts\seed_odoo.py

Write-Host "`nDone. Open http://localhost:8069 (admin / admin)." -ForegroundColor Green
Write-Host "Financial snapshot from the MCP:" -ForegroundColor Green
uv run python -c "from mcp_servers.odoo_mcp.server import _safe_snapshot; import json; print(json.dumps(_safe_snapshot(), indent=2)[:800])"
