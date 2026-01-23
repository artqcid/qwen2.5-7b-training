#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start JUCE Embedding Server

.DESCRIPTION
    Launches the embedding server for JUCE development.
    Server listens on http://127.0.0.1:8001

.PARAMETER Port
    Port for embedding server (default: 8001)

.NOTES
    Called by JUCE Server Autostart Extension
#>

param(
    [int]$Port = 8001,
    [int]$GpuLayers = 0
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
    if (-not $color) { $color = "White" }
    Write-Host $Message -ForegroundColor $color
}

# Get script directory (robust against null MyCommandPath)
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $PSCommandPath }

# Check if already running
if ((Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue).TcpTestSucceeded) {
    Write-Status "[OK] Embedding server already running on port $Port" "Success"
    exit 0
}

Write-Status "`n===== JUCE EMBEDDING SERVER =====" "Cyan"
Write-Status "[START] Starting on port $Port..." "Info"
Write-Status "GPU Layers: $GpuLayers" "Info"
Write-Status "====================================`n" "Cyan"

# Set environment
$env:EMBEDDING_PORT = $Port
$env:EMBEDDING_GPU_LAYERS = $GpuLayers
$env:PYTHONUNBUFFERED = "1"

# Get venv python executable
$PythonExe = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Status "ERROR: Python venv not found at $PythonExe" "Error"
    Write-Status "Run: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt" "Warning"
    exit 1
}

try {
    Push-Location $ScriptDir
    
    # Start embedding server with visible output using venv python
    Write-Status "[CMD] & `"$PythonExe`" -m embedding_server" "Info"
    & $PythonExe -m embedding_server
    
    Pop-Location
}
catch {
    Write-Status "ERROR: Failed to start embedding server: $_" "Error"
    Pop-Location
    exit 1
}
