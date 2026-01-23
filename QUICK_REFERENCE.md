# Quick Reference Card - Server Autostart

## 🚀 Getting Started

### First Time Setup
```powershell
# 1. Navigate to workspace
cd "C:\Users\marku\Documents\GitHub\artqcid\ai-projects\qwen2.5-7b-training"

# 2. Build extension
cd vscode-autostart-extension
npm install
npm run compile

# 3. Load in VS Code
# - Open VS Code
# - Extension loads automatically
# - Servers start within 5 seconds
```

### Quick Start After Installation
```
1. Open VS Code
2. Wait 2 seconds (auto-startup delay)
3. Check "Server Autostart" output channel
4. See "AI Servers" and "MCP Server" terminals launch
5. All three servers ready after ~5 seconds
```

---

## 📋 Server Ports

| Server | Port | Status Command |
|--------|------|-----------------|
| Llama | 8080 | `curl http://localhost:8080/health` |
| Embedding | 8001 | `curl http://localhost:8001/health` |
| MCP | 3001 | Check SSE endpoint in logs |

---

## 🎮 Commands (Command Palette)

```
Ctrl+Shift+P (or Cmd+Shift+P on Mac)

Then type and select:
- "Server Autostart: Start All Servers"
- "Server Autostart: Stop All Servers"  
- "Server Autostart: Show Server Status"
```

---

## 📂 Key Files Reference

```
Workspace Root/
├── scripts/
│   ├── manage_servers.ps1          ← Llama + Embedding launcher
│   └── start_mcp_server.ps1        ← MCP server launcher
│
├── mcp-server-misc/
│   ├── mcp_config.json             ← MCP configuration
│   ├── __main__.py                 ← MCP CLI entry point
│   └── server.py                   ← MCP core server
│
├── llama_config.json               ← Llama configuration
└── .continue/config.yaml           ← Continue IDE config
```

---

## 🔍 Output Channel Format

```
[INFO]  - Information message
[WARN]  - Warning (e.g., already started)
[ERROR] - Error condition
[OK]    - Success confirmation
[CMD]   - Command being executed
```

---

## ⚙️ Manual Configuration

### Change Auto-Start Delay
In VS Code Settings (Ctrl+,):
```json
"serverAutostart.autoStartDelay": 2000,        // milliseconds
"serverAutostart.mcpStartDelay": 3000          // milliseconds
```

### Change MCP Port
Edit `mcp-server-misc/mcp_config.json`:
```json
"server": {
  "port": 3001,          // Change this
  "sse_port": 3001
}
```

### Change Llama Port
Edit `llama_config.json`:
```json
{
  "port": 8080           // Change this
}
```

---

## 🛠️ Troubleshooting

### Servers don't start
```powershell
# 1. Check output channel
#    Look for [ERROR] messages

# 2. Verify scripts exist
Test-Path "scripts/manage_servers.ps1"
Test-Path "scripts/start_mcp_server.ps1"

# 3. Check PowerShell version (need 7+)
$PSVersionTable.PSVersion

# 4. Manually start
& "scripts/manage_servers.ps1" -Action "start-all"
& "scripts/start_mcp_server.ps1"
```

### Port conflicts
```powershell
# Check what's using ports
Get-NetTCPConnection -LocalPort 8080 | Select-Object OwningProcess
Get-NetTCPConnection -LocalPort 8001 | Select-Object OwningProcess
Get-NetTCPConnection -LocalPort 3001 | Select-Object OwningProcess

# Kill process using a port (e.g., 8080)
Get-Process -Id <PID> | Stop-Process -Force
```

### Extension won't load
```
1. Check: Extensions view → Server Autostart is enabled
2. Reload: Ctrl+Shift+P → "Reload Window"
3. Verify: VS Code 1.108+ installed
```

---

## 📊 Startup Timeline

```
T+0s:  VS Code launches
T+0s:  Extension activates
T+2s:  Auto-startup begins
T+2s:  Llama + Embedding start
T+5s:  MCP Server starts
T+10s: All servers ready
```

---

## 🔐 Security Notes

- All servers bind to localhost (127.0.0.1) only
- No external network exposure by default
- MCP uses SSE (Server-Sent Events) for Continue IDE
- Configuration files are JSON/YAML (plaintext)

---

## 📈 Performance Tips

1. **Faster Startup**: Reduce delays in Settings
2. **Lower Memory**: Disable unused servers in config
3. **Better Embedding**: Use CUDA if GPU available
4. **Llama Tuning**: Adjust `n_gpu_layers` in llama_config.json

---

## 🔗 Integration Points

### Continue IDE
- Connects to MCP on port 3001
- Uses SSE transport
- Auto-configured in .continue/config.yaml

### External Tools
- Llama API: `http://localhost:8080`
- Embedding API: `http://localhost:8001`
- MCP Endpoint: `http://localhost:3001/sse`

---

## 📝 Log Locations

| Source | Location |
|--------|----------|
| Extension | VS Code Output → "Server Autostart" |
| Llama | Terminal: "AI Servers" |
| Embedding | Terminal: "AI Servers" |
| MCP | Terminal: "MCP Server" |

---

## 🚨 Emergency Stop

```powershell
# Quick stop all servers
Get-Process llama-server -EA SilentlyContinue | Stop-Process -Force
Get-Process python -EA SilentlyContinue | Where-Object {$_.CommandLine -like '*embedding*' -or $_.CommandLine -like '*mcp*'} | Stop-Process -Force
```

---

## 📞 Getting Help

1. **Check Output Channel**: "Server Autostart"
2. **Review Logs**: Check terminal output
3. **Read Docs**: 
   - COMPLETE_GUIDE.md (comprehensive)
   - EXTENSION_UPDATE.md (extension specific)
   - STANDALONE.md (MCP specific)
4. **Verify Scripts**: Check syntax with `Invoke-ScriptAnalyzer`

---

## ✅ Health Check

```powershell
# Verify all servers running
netstat -ano | findstr /C:"8080" /C:"8001" /C:"3001"

# OR use PowerShell
Get-NetTCPConnection -LocalPort 8080,8001,3001 -ErrorAction SilentlyContinue | Select-Object LocalPort, State, OwningProcess
```

---

## 🎯 Command Quick Reference

| Action | Method 1 | Method 2 |
|--------|----------|----------|
| Start Servers | Ctrl+Shift+P → Start | Script: manage_servers.ps1 start-all |
| Stop Servers | Ctrl+Shift+P → Stop | PowerShell: Stop-Process |
| Status | Ctrl+Shift+P → Status | Script: manage_servers.ps1 status |
| View Logs | Output Channel | Terminal |

---

## 🔄 Update Process

```powershell
# 1. Pull latest changes
git pull

# 2. Rebuild extension
npm run compile

# 3. Reload VS Code
Ctrl+Shift+P → "Reload Window"

# 4. Test startup
# Wait 5 seconds and verify servers
```

---

## 📊 System Requirements

- **OS**: Windows 10/11
- **PowerShell**: 7.x (pwsh, not legacy)
- **Python**: 3.8+
- **VS Code**: 1.108+
- **RAM**: 8GB minimum (16GB+ recommended)
- **GPU**: NVIDIA CUDA 11+ (optional, for acceleration)

---

**Version**: 0.0.5  
**Status**: Production Ready  
**Last Updated**: 2024

*For detailed information, see COMPLETE_GUIDE.md*
