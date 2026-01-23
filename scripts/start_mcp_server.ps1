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

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommandPath
$ProjectRoot = Split-Path -Parent $ScriptDir
$MCPDir = Split-Path -Parent $ScriptDir

# Resolve config file
if ([string]::IsNullOrEmpty($ConfigFile)) {
    $ConfigFile = Join-Path $ScriptDir "mcp_config.json"
}

if (-not (Test-Path $ConfigFile)) {
    Write-Host "ERROR: Config file not found: $ConfigFile" -ForegroundColor Red
    exit 1
}

# Check if already running
$running = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*mcp_server*"
}

if ($running) {
    Write-Host "MCP Server already running (PID: $($running.Id))" -ForegroundColor Yellow
    exit 0
}

Write-Host "`n========== MCP Server (Standalone) ==========" -ForegroundColor Cyan
Write-Host "Starting Web Context MCP Server" -ForegroundColor Green
Write-Host "Config:    $ConfigFile" -ForegroundColor Cyan
Write-Host "SSE Port:  $Port" -ForegroundColor Cyan
Write-Host "Mode:      Standalone (IDE-agnostic)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

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
    
    Write-Host "[OK] MCP Server started (PID: $($process.Id))" -ForegroundColor Green
    Write-Host "[OK] Listen on http://127.0.0.1:$Port/sse" -ForegroundColor Green
    Write-Host "`nPress Ctrl+C to stop" -ForegroundColor Yellow
    
    # Wait for process
    $process.WaitForExit()
    
    Pop-Location
    exit 0
}
catch {
    Write-Host "ERROR: Failed to start MCP server: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}
