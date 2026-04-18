# =============================================================================
# Windows Task Scheduler install script for the autosapien AI Employee.
#
# Non-elevated path (no admin needed):
#   powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_tasks.ps1
#
# Installs three things:
#   1. Startup shortcut at shell:startup -> autosapien-Orchestrator (runs at logon).
#   2. schtasks.exe -> autosapien-MondayBriefing (weekly Monday 07:00).
#   3. schtasks.exe -> autosapien-SubscriptionAudit (weekly Sunday 21:00).
#
# Why two mechanisms? Register-ScheduledTask requires admin. schtasks.exe with
# user-scope task names does not. Startup folder shortcut also does not.
# =============================================================================

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path "$PSScriptRoot\..").Path
$uv   = (Get-Command uv).Source

Write-Host "`nInstalling autosapien AI Employee scheduled tasks..." -ForegroundColor Cyan

# ---- 1. Orchestrator: Startup folder shortcut -------------------------------
$startup = [Environment]::GetFolderPath('Startup')
$shortcut = Join-Path $startup 'autosapien-Orchestrator.lnk'
$WshShell = New-Object -ComObject WScript.Shell
$lnk = $WshShell.CreateShortcut($shortcut)
$lnk.TargetPath = $uv
$lnk.Arguments = 'run autosapien-orchestrator'
$lnk.WorkingDirectory = $repo
$lnk.WindowStyle = 7   # minimized, not hidden (so Dilawar can see it)
$lnk.Description = 'autosapien AI Employee orchestrator -- auto-launch at logon'
$lnk.Save()
Write-Host "  [ok] startup shortcut: $shortcut"

# ---- 2. Monday briefing via schtasks ----------------------------------------
$mondayXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-04-20T07:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByWeek>
        <DaysOfWeek><Monday/></DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <Enabled>true</Enabled>
    <AllowStartOnDemand>true</AllowStartOnDemand>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$uv</Command>
      <Arguments>run python -m scripts.trigger_ceo_briefing</Arguments>
      <WorkingDirectory>$repo</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
$mondayXmlPath = Join-Path $env:TEMP 'autosapien_monday.xml'
$mondayXml | Out-File -FilePath $mondayXmlPath -Encoding Unicode
schtasks /Create /XML $mondayXmlPath /TN 'autosapien-MondayBriefing' /F | Out-Null
Remove-Item $mondayXmlPath
Write-Host "  [ok] registered autosapien-MondayBriefing (weekly Mon 07:00)"

# ---- 3. Sunday subscription audit via schtasks ------------------------------
$sundayXml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-04-19T21:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByWeek>
        <DaysOfWeek><Sunday/></DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <Enabled>true</Enabled>
    <AllowStartOnDemand>true</AllowStartOnDemand>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>$uv</Command>
      <Arguments>run python -m scripts.trigger_subscription_audit</Arguments>
      <WorkingDirectory>$repo</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
$sundayXmlPath = Join-Path $env:TEMP 'autosapien_sunday.xml'
$sundayXml | Out-File -FilePath $sundayXmlPath -Encoding Unicode
schtasks /Create /XML $sundayXmlPath /TN 'autosapien-SubscriptionAudit' /F | Out-Null
Remove-Item $sundayXmlPath
Write-Host "  [ok] registered autosapien-SubscriptionAudit (weekly Sun 21:00)"

Write-Host "`nDone. Verify with:  schtasks /Query /TN autosapien-MondayBriefing" -ForegroundColor Green
Write-Host "Or view Startup folder: shell:startup" -ForegroundColor Green
