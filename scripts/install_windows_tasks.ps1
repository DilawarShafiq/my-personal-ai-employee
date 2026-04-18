# =============================================================================
# Windows Task Scheduler install script for the autosapien.com AI Employee.
#
# Run once in an elevated PowerShell:
#     powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_tasks.ps1
#
# It registers three recurring tasks:
#   1. autosapien-Orchestrator  — boots the watchers at user logon.
#   2. autosapien-MondayBriefing — runs the CEO Briefing every Monday 07:00.
#   3. autosapien-SubscriptionAudit — runs the subscription audit every Sunday 21:00.
#
# All tasks run with DRY_RUN=true by default. Flip via the env file.
# =============================================================================

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path "$PSScriptRoot\..").Path
$uv   = (Get-Command uv).Source

function Register-AutosapienTask {
    param(
        [string]$Name,
        [string]$Trigger,   # logon | daily | weekly
        [string]$Args,      # args passed to uv run
        [string]$DayOfWeek = $null,
        [string]$Time = $null
    )

    $action = New-ScheduledTaskAction `
        -Execute $uv `
        -Argument $Args `
        -WorkingDirectory $repo

    switch ($Trigger) {
        'logon'  { $trig = New-ScheduledTaskTrigger -AtLogOn }
        'daily'  { $trig = New-ScheduledTaskTrigger -Daily -At $Time }
        'weekly' { $trig = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DayOfWeek -At $Time }
    }

    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 2)

    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trig `
        -Settings $settings -Description "autosapien.com AI Employee — $Name" -Force | Out-Null
    Write-Host "  ✓ registered $Name"
}

Write-Host "`nInstalling autosapien.com AI Employee scheduled tasks..." -ForegroundColor Cyan
Register-AutosapienTask -Name 'autosapien-Orchestrator' `
    -Trigger 'logon' -Args 'run autosapien-orchestrator'

Register-AutosapienTask -Name 'autosapien-MondayBriefing' `
    -Trigger 'weekly' -DayOfWeek 'Monday' -Time '07:00' `
    -Args 'run python -m scripts.trigger_ceo_briefing'

Register-AutosapienTask -Name 'autosapien-SubscriptionAudit' `
    -Trigger 'weekly' -DayOfWeek 'Sunday' -Time '21:00' `
    -Args 'run python -m scripts.trigger_subscription_audit'

Write-Host "`nDone. View with:  Get-ScheduledTask -TaskName 'autosapien-*'" -ForegroundColor Green
