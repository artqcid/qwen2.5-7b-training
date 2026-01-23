#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start JUCE MCP Server

.DESCRIPTION
    Launches the MCP server for JUCE development with IDE-agnostic SSE endpoint.
    Server listens on http://127.0.0.1:3001/sse

.NOTES
    Called by JUCE Server Autostart Extension
#>

param(
    [int]$Port = 3001
)

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
    Write-Host $Message -ForegroundColor $color
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommandPath
$ConfigFile = Join-Path $ScriptDir "mcp_config.json"

# Verify config exists
if (-not (Test-Path $ConfigFile)) {
    Write-Status "ERROR: mcp_config.json not found at $ConfigFile" "Error"
    exit 1
}

# Check if already running
$running = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -match "mcp_server"
}

if ($running) {
    Write-Status "[OK] MCP Server already running (PID: $($running.Id))" "Success"
    exit 0
}

Write-Status "`n========== JUCE MCP SERVER ==========" "Cyan"
Write-Status "[START] Starting on port $Port..." "Info"
Write-Status "Config: $(Split-Path -Leaf $ConfigFile)" "Info"
Write-Status "=====================================`n" "Cyan"

# Set environment
$env:MCP_CONFIG_FILE = $ConfigFile
$env:MCP_SSE_PORT = $Port
$env:PYTHONUNBUFFERED = "1"

try {
    Push-Location $ScriptDir
    
    # Start MCP server with visible output
    Write-Status "[CMD] python -m mcp_server --config `"$ConfigFile`" --sse-port $Port" "Info"
    & python -m mcp_server --config $ConfigFile --sse-port $Port
    
    Pop-Location
}
catch {
    Write-Status "ERROR: Failed to start MCP server: $_" "Error"
    Pop-Location
    exit 1
}
