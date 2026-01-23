#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start standalone MCP Server (independent from VS Code/Continue)

.DESCRIPTION
    Launches the MCP server as a background service. Can be used with:
    - Continue IDE
    - Cline
    - Windsurf
    - Custom IDE Extensions
    - Direct HTTP/SSE clients

.PARAMETER Port
    Port for SSE endpoint (default: 3001)

.PARAMETER ConfigFile
    Path to mcp_config.json (default: ./mcp_config.json)

.EXAMPLE
    .\start_mcp_server.ps1
    # Starts standalone MCP server with default settings

.EXAMPLE
    .\start_mcp_server.ps1 -Port 3001
    # Starts on custom SSE port
#>

param(
    [int]$Port = 3001,
    [string]$ConfigFile = $null
)

# Define Write-Status function for consistent output
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
        "Yellow"  = "Yellow"
        "Cyan"    = "Cyan"
        "Green"   = "Green"
    }
    
    $color = $colors[$Status]
    Write-Host $Message -ForegroundColor $color
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommandPath
$ProjectRoot = Split-Path -Parent $ScriptDir
$MCPDir = Join-Path $ProjectRoot "mcp-server-misc"

# Resolve config file - try mcp-server-misc first, then fallback to local
if ([string]::IsNullOrEmpty($ConfigFile)) {
    if (Test-Path $MCPDir) {
        $ConfigFile = Join-Path $MCPDir "mcp_config.json"
    } else {
        # Fallback to project-local config
        $ConfigFile = Join-Path $ScriptDir "mcp_config.json"
        $MCPDir = $ProjectRoot
    }
}

if (-not (Test-Path $ConfigFile)) {
    Write-Status "ERROR: Config file not found: $ConfigFile" "Error"
    exit 1
}

# Check if already running
$running = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -match "mcp_server"
}

if ($running) {
    Write-Status "`n[MCP SERVER] Starting..." "Info"
    Write-Status "[OK] MCP Server already running (PID: $($running.Id))" "Success"
    exit 0
}

Write-Status "`n========== STARTING MCP SERVER ==========" "Cyan"
Write-Status "[MCP SERVER] Starting on port $Port..." "Info"
Write-Status "Config:     $(Split-Path -Leaf $ConfigFile)" "Info"
Write-Status "Mode:       Standalone (IDE-agnostic)" "Info"
Write-Status "==========================================`n" "Cyan"

# Set environment for MCP
$env:MCP_CONFIG_FILE = $ConfigFile
$env:MCP_SSE_PORT = $Port
$env:PYTHONUNBUFFERED = "1"

try {
    Push-Location $MCPDir
    
    # Start MCP server as background process
    $process = Start-Process -FilePath "python" -ArgumentList @(
        "-m", "mcp_server",
        "--config", $ConfigFile,
        "--sse-port", $Port
    ) -NoNewWindow -PassThru
    
    if ($process) {
        Write-Status "[OK] MCP server started (PID: $($process.Id))" "Success"
        Write-Status "[OK] Listen on http://127.0.0.1:$Port/sse" "Success"
    }
    
    Pop-Location
    exit 0
}
catch {
    Write-Status "ERROR: Failed to start MCP server: $_" "Error"
    Pop-Location
    exit 1
}
