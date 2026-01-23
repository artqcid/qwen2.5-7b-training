#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Cleanup script - stops all servers when VSCode workspace is closed
    
.DESCRIPTION
    This script is called when VSCode is closing to ensure all servers are properly stopped.
    It can be triggered via tasks or other methods.
#>

Write-Host "`n========== CLEANUP: STOPPING ALL SERVERS ==========" -ForegroundColor Yellow

$projectRoot = "C:\Users\marku\Documents\GitHub\artqcid\ai-projects\qwen2.5-7b-training"
$manageScript = Join-Path $projectRoot "scripts\manage_servers.ps1"

if (Test-Path $manageScript) {
    & $manageScript -Action "stop-all" | Out-Null
    Start-Sleep -Milliseconds 500
    Write-Host "✓ All servers stopped" -ForegroundColor Green
} else {
    Write-Host "ERROR: manage_servers.ps1 not found" -ForegroundColor Red
}

Write-Host "===================================================`n" -ForegroundColor Yellow
