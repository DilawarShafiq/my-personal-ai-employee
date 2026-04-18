# Pre-record bootstrap -- runs everything you need to hit F9 in OBS.
#
#   powershell -ExecutionPolicy Bypass -File scripts\record_bootstrap.ps1

$ErrorActionPreference = 'Stop'

Write-Host "`n[1/5] Checking Docker + Odoo..." -ForegroundColor Cyan
try {
  docker compose ps --format json | Out-Null
  $status = docker compose ps --services --filter "status=running"
  if ($status -notmatch 'odoo') {
    Write-Host "   Odoo not running -- starting now..."
    docker compose up -d
    Write-Host "   (waiting 60 s for Odoo to boot)"
    Start-Sleep -Seconds 60
  } else {
    Write-Host "   ok  Odoo already up"
  }
} catch {
  Write-Host "   warn  Docker not reachable -- CEO briefing demo will use fallback data"
}

Write-Host "`n[2/5] Re-seeding the vault to a pristine starting state..." -ForegroundColor Cyan
uv run python scripts\seed_vault.py

Write-Host "`n[3/5] Rendering intro + outro SVG cards to PNG..." -ForegroundColor Cyan
& "$PSScriptRoot\render_cards.ps1"

Write-Host "`n[4/5] Verifying every module imports..." -ForegroundColor Cyan
uv run python -c "from watchers.filesystem_watcher import FileSystemWatcher; from watchers.gmail_watcher import GmailWatcher; from mcp_servers.odoo_mcp.server import _safe_snapshot; s = _safe_snapshot(); print('   gmail import ok, odoo live:', s['live'])"

Write-Host "`n[5/5] Starting the orchestrator in a background window..." -ForegroundColor Cyan
$repo = (Resolve-Path "$PSScriptRoot\..").Path
$orch = Start-Process -FilePath "uv" -ArgumentList 'run', 'autosapien-orchestrator' -WorkingDirectory $repo -PassThru -WindowStyle Normal
Write-Host "   orchestrator pid: $($orch.Id)"

Write-Host "`nReady. Arrange windows:" -ForegroundColor Green
Write-Host "  left:   terminal (this one)" -ForegroundColor Green
Write-Host "  right:  Obsidian pointed at AI_Employee_Vault/" -ForegroundColor Green
Write-Host "  behind: Claude Code in the repo root" -ForegroundColor Green
Write-Host "  hidden: OBS Studio preview" -ForegroundColor Green
Write-Host "`nNow hit F9 in OBS." -ForegroundColor Green
