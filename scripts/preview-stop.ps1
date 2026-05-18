#!/usr/bin/env pwsh
# Stop the CustomerFlow AI preview services started by scripts\preview.ps1.

$ErrorActionPreference = "SilentlyContinue"
$Root  = Resolve-Path "$PSScriptRoot\.."
$Pids  = Join-Path $Root ".preview-pids.json"

if (-not (Test-Path $Pids)) {
    Write-Host "No preview is currently running (no .preview-pids.json found)." -ForegroundColor Yellow
    return
}

$data = Get-Content $Pids | ConvertFrom-Json
foreach ($name in "api","web") {
    $procId = $data.$name
    if ($procId) {
        Write-Host ("Stopping {0,-3} pid={1}" -f $name, $procId)
        Stop-Process -Id $procId -Force 2>$null
    }
}
Remove-Item $Pids -Force
Write-Host "Preview stopped." -ForegroundColor Green
