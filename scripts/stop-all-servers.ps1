#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Stop all workspace servers (Llama, Embedding, MCP)
#>

Write-Host "`n=== STOPPING ALL SERVERS ===" -ForegroundColor Cyan

# Stop Llama Server
$llamaProcs = Get-Process llama-server -ErrorAction SilentlyContinue
if ($llamaProcs) {
    $llamaProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Llama Server stopped" -ForegroundColor Green
} else {
    Write-Host "[INFO] Llama Server not running" -ForegroundColor Yellow
}

# Stop Embedding Server
$embeddingProcs = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
    $_.Path -like '*embedding-server-misc*' 
}
if ($embeddingProcs) {
    $embeddingProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Embedding Server stopped" -ForegroundColor Green
} else {
    Write-Host "[INFO] Embedding Server not running" -ForegroundColor Yellow
}

# Stop MCP Server
$mcpProcs = Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
    $_.Path -like '*mcp-server-misc*' 
}
if ($mcpProcs) {
    $mcpProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] MCP Server stopped" -ForegroundColor Green
} else {
    Write-Host "[INFO] MCP Server not running" -ForegroundColor Yellow
}

Write-Host "=== ALL SERVERS STOPPED ===`n" -ForegroundColor Cyan
exit 0
