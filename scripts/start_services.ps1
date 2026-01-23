#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start all required services for Qwen2.5-7B Training project
    - Embedding Server (CPU-only, Port 8001)
    - Chat Server (GPU, Port 8000) - optional, started separately
    
.DESCRIPTION
    This script orchestrates starting the embedding server for Continue IDE integration.
    The chat server (llama.cpp with Qwen2.5-7B) should be started separately in another terminal.
    
.PARAMETER EmbeddingOnly
    If specified, only start the embedding server (default behavior)
    
.PARAMETER InstallDeps
    If specified, install Python dependencies first

.EXAMPLE
    .\scripts\start_services.ps1
    # Starts embedding server on port 8001
    
.EXAMPLE
    .\scripts\start_services.ps1 -InstallDeps
    # Installs dependencies and starts embedding server
#>

param(
    [switch]$EmbeddingOnly = $true,
    [switch]$InstallDeps
)

# Color output
function Write-Color {
    param($Text, $Color)
    Write-Host $Text -ForegroundColor $Color
}

# Get script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommandPath
$ProjectRoot = Split-Path -Parent $ScriptDir
$EmbeddingServerDir = Join-Path $ProjectRoot "embedding-server-misc"

Write-Color "`n========================================" "Cyan"
Write-Color "Qwen2.5-7B Training - Service Manager" "Cyan"
Write-Color "========================================`n" "Cyan"

# Check if embedding server exists
if (-not (Test-Path $EmbeddingServerDir)) {
    Write-Color "ERROR: embedding-server-misc not found at $EmbeddingServerDir" "Red"
    Write-Color "Run: git submodule update --init --recursive" "Yellow"
    exit 1
}

Write-Color "Project Root: $ProjectRoot" "Green"
Write-Color "Embedding Server: $EmbeddingServerDir" "Green"

# Install dependencies if requested
if ($InstallDeps) {
    Write-Color "`n[1/2] Installing Python dependencies..." "Yellow"
    
    $RequirementsFile = Join-Path $EmbeddingServerDir "requirements.txt"
    
    if (Test-Path $RequirementsFile) {
        pip install -r $RequirementsFile
        if ($LASTEXITCODE -ne 0) {
            Write-Color "ERROR: Failed to install dependencies" "Red"
            exit 1
        }
        Write-Color "✓ Dependencies installed" "Green"
    } else {
        Write-Color "ERROR: requirements.txt not found" "Red"
        exit 1
    }
}

# Start embedding server
Write-Color "`n[Starting] Embedding Server (CPU mode)" "Yellow"
Write-Color "Port: http://localhost:8001" "Cyan"
Write-Color "Model: nomic-embed-text-v1.5 (CPU-only)" "Cyan"
Write-Color "`nPress Ctrl+C to stop`n" "Yellow"

# Set environment variables for CPU-only mode
$env:EMBEDDING_GPU_LAYERS = "0"
$env:EMBEDDING_HOST = "127.0.0.1"
$env:EMBEDDING_PORT = "8001"

# Start embedding server
Push-Location $EmbeddingServerDir
python -m embedding_server
Pop-Location
