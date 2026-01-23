# Setup script for Web Context MCP Server
# Erstellt Virtual Environment und installiert Dependencies

$ErrorActionPreference = "Stop"

Write-Host "=== Web Context MCP Server Setup ===" -ForegroundColor Cyan

# Wechsel zum MCP-Verzeichnis
Set-Location "c:\mcp"

# Prüfe ob Python verfügbar ist
Write-Host "`nChecking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Erstelle Virtual Environment wenn nicht vorhanden
if (-not (Test-Path ".venv")) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "`nVirtual environment already exists" -ForegroundColor Green
}

# Aktiviere Virtual Environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Installiere Dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Erstelle Cache-Verzeichnis
if (-not (Test-Path "cache")) {
    New-Item -ItemType Directory -Path "cache" | Out-Null
    Write-Host "`nCache directory created" -ForegroundColor Green
}

# Test Server
Write-Host "`n=== Testing MCP Server ===" -ForegroundColor Cyan
Write-Host "You can test the server by running:" -ForegroundColor Yellow
Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python web_mcp.py" -ForegroundColor White

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "The MCP server is ready to use!" -ForegroundColor Green
Write-Host "It should auto-start in VSCode (configured in User/mcp.json)" -ForegroundColor Cyan
