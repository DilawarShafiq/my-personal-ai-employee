# Render docs/intro_card.svg and docs/outro_card.svg to 1920x1080 PNG
# via Chrome headless. Requires Chrome installed.
#
#   powershell -ExecutionPolicy Bypass -File scripts\render_cards.ps1

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path "$PSScriptRoot\..").Path
$out  = Join-Path $repo 'docs\rendered'
New-Item -ItemType Directory -Force -Path $out | Out-Null

# Find Chrome (Stable) — fall back to Edge if Chrome isn't installed.
$browsers = @(
  "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
  "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe"
)
$browser = $browsers | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $browser) {
  Write-Error "Chrome or Edge not found. Install either and retry."
  exit 1
}
Write-Host "Using: $browser"

foreach ($name in 'intro_card', 'outro_card') {
  $svg = Join-Path $repo "docs\$name.svg"
  $png = Join-Path $out "$name.png"
  $url = "file:///" + $svg.Replace('\', '/')

  Write-Host "Rendering $name -> $png"
  & $browser `
      --headless=new `
      --disable-gpu `
      --hide-scrollbars `
      --force-device-scale-factor=1 `
      --window-size=1920,1080 `
      --screenshot="$png" `
      "$url"

  if (Test-Path $png) {
    $size = (Get-Item $png).Length
    Write-Host "  ok  $($size / 1KB) KB"
  } else {
    Write-Warning "  failed to render $name"
  }
}

Write-Host "`nDone. Add the PNGs as OBS 'Image' sources for the Intro/Outro scenes." -ForegroundColor Green
