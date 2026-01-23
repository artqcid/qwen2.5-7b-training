#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Manages embedding server and MCP server instances

.DESCRIPTION
    PowerShell module for starting/stopping local AI servers

.NOTES
    Used by VS Code tasks for server management
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start-embedding", "stop-embedding", "start-mcp", "stop-mcp", "start-llama", "stop-llama", "status", "start-all", "stop-all")]
    [string]$Action,
    
    [string]$EmbeddingPort = "8001",
    [string]$MCPPort = "8000",
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
    Write-Host $Message -ForegroundColor $colors[$Type]
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
        Write-Status "✓ Embedding server already running on port $EmbeddingPort" "Success"
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
            Write-Status "✓ Embedding server started successfully" "Success"
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
        Write-Status "✓ No embedding server processes running" "Success"
        return $true
    }
    
    try {
        $processes | Stop-Process -Force
        Write-Status "✓ Embedding server stopped" "Success"
        return $true
    }
    catch {
        Write-Status "ERROR: Failed to stop embedding server: $_" "Error"
        return $false
    }
}

function Start-MCPServer {
    Write-Status "`n[MCP SERVER] Starting..." "Info"
    
    $projectRoot = "C:\Users\marku\Documents\GitHub\artqcid\ai-projects\qwen2.5-7b-training"
    $mcpDir = Join-Path $projectRoot "mcp-server-misc"
    
    if (-not (Test-Path $mcpDir)) {
        Write-Status "ERROR: mcp-server-misc not found at $mcpDir" "Error"
        return $false
    }
    
    # MCP server is started as experimental MCP in Continue
    Write-Status "ℹ MCP server is managed by Continue IDE (experimentalMcp)" "Info"
    Write-Status "✓ MCP server configuration is active" "Success"
    return $true
}

function Stop-MCPServer {
    Write-Status "`n[MCP SERVER] Stopping..." "Info"
    
    $processes = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*mcp_server*"
    }
    
    if ($processes.Count -eq 0) {
        Write-Status "✓ No MCP server processes running" "Success"
        return $true
    }
    
    try {
        $processes | Stop-Process -Force
        Write-Status "✓ MCP server stopped" "Success"
        return $true
    }
    catch {
        Write-Status "ERROR: Failed to stop MCP server: $_" "Error"
        return $false
    }
}

function Start-LlamaServer {
    Write-Status "`n[LLAMA.CPP SERVER] Starting on port $LlamaPort..." "Info"
    
    $llamaPath = "C:\llama\server.exe"
    
    if (-not (Test-Path $llamaPath)) {
        Write-Status "ERROR: llama-server not found at $llamaPath" "Error"
        return $false
    }
    
    # Check if already running
    if (Get-ServerStatus $LlamaPort) {
        Write-Status "✓ Llama.cpp server already running on port $LlamaPort" "Success"
        return $true
    }
    
    try {
        # Start server in background
        Start-Process -FilePath $llamaPath -ArgumentList @(
            "-m", "models/qwen2.5-7b-chat.gguf",
            "--port", $LlamaPort,
            "-ngl", "33"
        ) -NoNewWindow -PassThru
        
        # Wait for server to start
        Start-Sleep -Seconds 3
        
        if (Get-ServerStatus $LlamaPort) {
            Write-Status "✓ Llama.cpp server started successfully" "Success"
            return $true
        } else {
            Write-Status "ERROR: Llama.cpp server failed to start (check C:\llama)" "Error"
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
    
    $processes = Get-Process -Name "server" -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -like "*llama*"
    }
    
    if ($processes.Count -eq 0) {
        Write-Status "✓ No llama-server processes running" "Success"
        return $true
    }
    
    try {
        $processes | Stop-Process -Force
        Write-Status "✓ Llama.cpp server stopped" "Success"
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
    $embeddingStatus = if ($embeddingRunning) { "✓ RUNNING" } else { "✗ STOPPED" }
    
    $llamaRunning = Get-ServerStatus $LlamaPort
    $llamaStatus = if ($llamaRunning) { "✓ RUNNING" } else { "✗ STOPPED" }
    
    Write-Host "Llama.cpp Server (Port $LlamaPort):     $llamaStatus"
    Write-Host "Embedding Server (Port $EmbeddingPort): $embeddingStatus"
    Write-Host "MCP Server (Continue IDE):     Check Continue settings"
    
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
    "start-mcp" { 
        $result = Start-MCPServer
        exit $(if ($result) { 0 } else { 1 })
    }
    "stop-mcp" { 
        $result = Stop-MCPServer
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
        Start-Sleep -Seconds 2
        $mcp = Start-MCPServer
        Write-Status "==========================================`n" "Cyan"
        exit $(if ($llama -and $embedding -and $mcp) { 0 } else { 1 })
    }
    "stop-all" {
        Write-Status "`n========== STOPPING ALL SERVERS ==========" "Yellow"
        $embedding = Stop-EmbeddingServer
        $mcp = Stop-MCPServer
        $llama = Stop-LlamaServer
        Write-Status "==========================================`n" "Yellow"
        exit $(if ($embedding -and $mcp -and $llama) { 0 } else { 1 })
    }
    "status" { 
        Show-ServerStatus
    }
}
