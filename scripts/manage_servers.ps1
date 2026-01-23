#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Manages llama.cpp and embedding server instances

.DESCRIPTION
    PowerShell module for starting/stopping local AI servers (Llama + Embedding).
    MCP Server is now standalone - see scripts/start_mcp_server.ps1

.NOTES
    Used by VS Code tasks for server management
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start-embedding", "stop-embedding", "start-llama", "stop-llama", "status", "start-all", "stop-all")]
    [string]$Action,
    
    [string]$EmbeddingPort = "8001",
    [string]$LlamaPort = "8080"
)

function Write-Status {
    param($Message, $Type = "Info")
    $colors = @{
        "Success" = "Green"
        "Error" = "Red"
        "Warning" = "Yellow"
        "Info" = "Cyan"
    }
    $color = $colors[$Type]
    if (-not $color) {
        $color = "White"
    }
    Write-Host $Message -ForegroundColor $color
}

function Get-ServerStatus {
    param([int]$Port)
    
    try {
        $result = Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        return $result.TcpTestSucceeded
    }
    catch {
        return $false
    }
}

function Start-EmbeddingServer {
    Write-Status "`n[EMBEDDING SERVER] Starting on port $EmbeddingPort..." "Info"
    
    $projectRoot = "C:\Users\marku\Documents\GitHub\artqcid\ai-projects\qwen2.5-7b-training"
    $embeddingDir = Join-Path $projectRoot "embedding-server-misc"
    
    if (-not (Test-Path $embeddingDir)) {
        Write-Status "ERROR: embedding-server-misc not found at $embeddingDir" "Error"
        return $false
    }
    
    # Check if already running
    if (Get-ServerStatus $EmbeddingPort) {
        Write-Status "[OK] Embedding server already running on port $EmbeddingPort" "Success"
        return $true
    }
    
    # Start server
    $env:EMBEDDING_GPU_LAYERS = "0"
    $env:EMBEDDING_PORT = $EmbeddingPort
    
    try {
        Push-Location $embeddingDir
        Start-Process -FilePath "python" -ArgumentList "-m", "embedding_server" -NoNewWindow -PassThru
        Pop-Location
        
        # Wait for server to start
        Start-Sleep -Seconds 3
        
        if (Get-ServerStatus $EmbeddingPort) {
            Write-Status "[OK] Embedding server started successfully" "Success"
            return $true
        } else {
            Write-Status "ERROR: Embedding server failed to start" "Error"
            return $false
        }
    }
    catch {
        Write-Status "ERROR: Failed to start embedding server: $_" "Error"
        Pop-Location
        return $false
    }
}

function Stop-EmbeddingServer {
    Write-Status "`n[EMBEDDING SERVER] Stopping..." "Info"
    
    $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*embedding_server*"
    }
    
    if ($processes.Count -eq 0) {
        Write-Status "[OK] No embedding server processes running" "Success"
        return $true
    }
    
    try {
        $processes | Stop-Process -Force
        Write-Status "[OK] Embedding server stopped" "Success"
        return $true
    }
    catch {
        Write-Status "ERROR: Failed to stop embedding server: $_" "Error"
        return $false
    }
}

function Start-LlamaServer {
    Write-Status "`n[LLAMA.CPP SERVER] Starting on port $LlamaPort..." "Info"
    
    $projectRoot = "C:\Users\marku\Documents\GitHub\artqcid\ai-projects\qwen2.5-7b-training"
    $configPath = Join-Path $projectRoot "llama_config.json"
    $llamaPath = "C:\llama\llama-server.exe"
    
    # Load config
    if (-not (Test-Path $configPath)) {
        Write-Status "ERROR: llama_config.json not found at $configPath" "Error"
        return $false
    }
    $config = Get-Content $configPath | ConvertFrom-Json
    $llamaConfig = $config.llama_cpp
    
    if (-not (Test-Path $llamaPath)) {
        Write-Status "ERROR: llama-server not found at $llamaPath" "Error"
        return $false
    }
    
    if (-not (Test-Path $llamaConfig.modelPath)) {
        Write-Status "ERROR: Model file not found at $($llamaConfig.modelPath)" "Error"
        return $false
    }
    
    # Check if already running
    if (Get-ServerStatus $LlamaPort) {
        Write-Status "[OK] Llama.cpp server already running on port $LlamaPort" "Success"
        return $true
    }
    
    try {
        # Start server in background with full configuration
        $process = Start-Process -FilePath $llamaPath -ArgumentList @(
            "--model", $llamaConfig.modelPath,
            "--port", $llamaConfig.port,
            "--ctx-size", $llamaConfig.ctxSize,
            "--batch-size", $llamaConfig.batchSize,
            "--ubatch-size", $llamaConfig.ubatchSize,
            "--parallel", $llamaConfig.parallel,
            "--threads", $llamaConfig.threads,
            "--n-gpu-layers", $llamaConfig.gpuLayers,
            "--cache-type-k", $llamaConfig.cacheK,
            "--cache-type-v", $llamaConfig.cacheV,
            "--temp", $llamaConfig.temp,
            "--top-k", $llamaConfig.topK,
            "--top-p", $llamaConfig.topP,
            "--repeat-penalty", $llamaConfig.repeatPen,
            "--mirostat", $llamaConfig.mirostat,
            "--flash-attn", "auto"
        ) -NoNewWindow -PassThru
        
        # Wait for server to start
        Start-Sleep -Seconds 3
        
        if (Get-ServerStatus $LlamaPort) {
            Write-Status "[OK] Llama.cpp server started successfully" "Success"
            return $true
        } else {
            Write-Status "ERROR: Llama.cpp server failed to start" "Error"
            return $false
        }
    }
    catch {
        Write-Status "ERROR: Failed to start llama server: $_" "Error"
        return $false
    }
}

function Stop-LlamaServer {
    Write-Status "`n[LLAMA.CPP SERVER] Stopping..." "Info"
    
    $processes = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue
    
    if ($null -eq $processes) {
        Write-Status "[OK] No llama-server processes running" "Success"
        return $true
    }
    
    try {
        $processes | Stop-Process -Force
        Write-Status "[OK] Llama.cpp server stopped" "Success"
        return $true
    }
    catch {
        Write-Status "ERROR: Failed to stop llama server: $_" "Error"
        return $false
    }
}

function Show-ServerStatus {
    Write-Status "`n========== SERVER STATUS ==========" "Info"
    
    $embeddingRunning = Get-ServerStatus $EmbeddingPort
    $embeddingStatus = if ($embeddingRunning) { "[OK] RUNNING" } else { "[--] STOPPED" }
    
    $llamaRunning = Get-ServerStatus $LlamaPort
    $llamaStatus = if ($llamaRunning) { "[OK] RUNNING" } else { "[--] STOPPED" }
    
    $mcpRunning = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*mcp_server*"
    }
    $mcpStatus = if ($mcpRunning) { "[OK] RUNNING (Standalone)" } else { "[--] STOPPED" }
    
    Write-Host "Llama.cpp Server (Port $LlamaPort):     $llamaStatus"
    Write-Host "Embedding Server (Port $EmbeddingPort): $embeddingStatus"
    Write-Host "MCP Server (Standalone):        $mcpStatus"
    
    Write-Status "==================================`n" "Info"
}

# Execute action
switch ($Action) {
    "start-embedding" { 
        $result = Start-EmbeddingServer
        exit $(if ($result) { 0 } else { 1 })
    }
    "stop-embedding" { 
        $result = Stop-EmbeddingServer
        exit $(if ($result) { 0 } else { 1 })
    }
    "start-llama" { 
        $result = Start-LlamaServer
        exit $(if ($result) { 0 } else { 1 })
    }
    "stop-llama" { 
        $result = Stop-LlamaServer
        exit $(if ($result) { 0 } else { 1 })
    }
    "start-all" {
        Write-Status "`n========== STARTING ALL SERVERS ==========" "Cyan"
        $llama = Start-LlamaServer
        Start-Sleep -Seconds 2
        $embedding = Start-EmbeddingServer
        Write-Status "==========================================`n" "Cyan"
        exit $(if ($llama -and $embedding) { 0 } else { 1 })
    }
    "stop-all" {
        Write-Status "`n========== STOPPING ALL SERVERS ==========" "Yellow"
        $embedding = Stop-EmbeddingServer
        $llama = Stop-LlamaServer
        
        # Stop standalone MCP server
        Write-Status "`n[MCP SERVER] Stopping standalone MCP..." "Yellow"
        try {
            Get-Process -Name python -ErrorAction SilentlyContinue | 
                Where-Object {$_.CommandLine -match 'mcp_server'} | 
                Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Status "[OK] MCP server stopped" "Green"
            $mcp = $true
        } catch {
            Write-Status "[OK] No MCP server processes running" "Green"
            $mcp = $true
        }
        
        Write-Status "==========================================`n" "Yellow"
        exit $(if ($embedding -and $llama -and $mcp) { 0 } else { 1 })
    }
    "status" { 
        Show-ServerStatus
    }
}

