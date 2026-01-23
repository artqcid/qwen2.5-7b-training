#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Stop MCP Server

.DESCRIPTION
    Stops the MCP server process
#>

function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "Info"
    )
    
    $colors = @{
        "Success" = "Green"
        "Error"   = "Red"
        "Warning" = "Yellow"
        "Info"    = "Cyan"
    }
    
    $color = $colors[$Status]
    if (-not $color) { $color = "White" }
    Write-Host $Message -ForegroundColor $color
}

Write-Status "`n========== STOP MCP SERVER ==========" "Cyan"

# Find MCP server process
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $PSCommandPath }

$mcpProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -and $_.Path -like "*mcp-server-misc*"
}

if ($mcpProcesses) {
    foreach ($proc in $mcpProcesses) {
        try {
            Write-Status "[STOP] Stopping MCP Server (PID: $($proc.Id))..." "Info"
            Stop-Process -Id $proc.Id -Force
            Write-Status "[OK] MCP Server stopped" "Success"
        }
        catch {
            Write-Status "[ERROR] Failed to stop process: $_" "Error"
        }
    }
}
else {
    Write-Status "[INFO] No MCP Server process found" "Warning"
}

Write-Status "====================================`n" "Cyan"
