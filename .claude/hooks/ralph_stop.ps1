# Ralph Wiggum Stop hook — PowerShell variant (Windows default shell).
#
# Same semantics as ralph_stop.sh. Use this one on Windows if your hook
# runs under pwsh.
$ErrorActionPreference = 'Stop'

$vault = if ($env:VAULT_PATH) { $env:VAULT_PATH } else { './AI_Employee_Vault' }
$maxIter = if ($env:RALPH_MAX_ITERATIONS) { [int]$env:RALPH_MAX_ITERATIONS } else { 8 }
$stateDir = Join-Path $vault '.ralph_state'
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
$iterFile = Join-Path $stateDir 'iter.count'

$input = [Console]::In.ReadToEnd()

if ($input -match '<promise>[A-Z_]+_COMPLETE</promise>') {
    Remove-Item -Force -ErrorAction SilentlyContinue $iterFile
    '{"decision": "approve", "reason": "ralph.promise_seen"}'
    exit 0
}

$needsActionCount = (Get-ChildItem -Path (Join-Path $vault 'Needs_Action') -Filter '*.md' -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne '.gitkeep' }).Count

if ($needsActionCount -eq 0) {
    Remove-Item -Force -ErrorAction SilentlyContinue $iterFile
    '{"decision": "approve", "reason": "ralph.queue_empty"}'
    exit 0
}

$iter = 0
if (Test-Path $iterFile) { $iter = [int](Get-Content $iterFile) }
$iter += 1
Set-Content -Path $iterFile -Value $iter -Encoding utf8

if ($iter -ge $maxIter) {
    Remove-Item -Force -ErrorAction SilentlyContinue $iterFile
    '{"decision": "approve", "reason": "ralph.max_iterations_hit"}'
    exit 0
}

$msg = "You still have $needsActionCount file(s) in /Needs_Action. " +
       "Ralph iteration $iter/$maxIter. Continue the triage-inbox skill " +
       "on the remaining items. End with <promise>TRIAGE_COMPLETE</promise> when done."

$payload = @{
    decision       = 'block'
    reason         = 'ralph.still_working'
    systemMessage  = $msg
} | ConvertTo-Json -Compress

$payload
