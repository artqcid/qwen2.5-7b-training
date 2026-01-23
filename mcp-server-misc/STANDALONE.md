# MCP Server - Standalone Web Context Server

## Overview

The MCP (Model Context Protocol) Server is now a **fully standalone** web context documentation server that works with any IDE or text editor.

### Key Features

✅ **IDE-Agnostic** - Works with:
- Continue IDE
- Cline
- Windsurf
- Custom VS Code Extensions
- Direct HTTP/SSE Clients

✅ **Multiple Transport Modes**:
- **stdio** - Standard MCP protocol (default)
- **SSE** - HTTP Server-Sent Events for remote clients
- **HTTP** - RESTful API endpoints

✅ **Web Context Management**
- Load documentation from configured URLs
- Automatic caching (24h TTL)
- Parallel content fetching

## Quick Start

### 1. Start Standalone MCP Server

**Option A: Using VS Code Task**
```bash
# Run: "Start MCP Server" task
# Runs in background, ready for any client
```

**Option B: Direct Command**
```powershell
pwsh -NoProfile -Command "& 'scripts/start_mcp_server.ps1'"
```

**Option C: Custom Port**
```powershell
pwsh -NoProfile -Command "& 'scripts/start_mcp_server.ps1' -Port 3001"
```

### 2. Connect from Different IDEs

#### Continue IDE
```yaml
# .continue/config.yaml
experimentalMcp:
  - name: web-context
    command: python
    args:
      - -m
      - mcp_server
      - --config
      - "path/to/mcp_config.json"
```

#### Cline / Other Clients
```python
# Connect via stdio
python -m mcp_server --config mcp_config.json

# Or via HTTP/SSE
python -m mcp_server --transport sse --port 3001
```

#### HTTP Clients
```bash
# Start HTTP server
python -m mcp_server --transport sse --host 0.0.0.0 --port 3001

# Access endpoints
curl http://localhost:3001/health
curl http://localhost:3001/resources
curl http://localhost:3001/resource?name=@vue
```

## Configuration

### mcp_config.json

```json
{
  "name": "Web Context MCP Server",
  "version": "1.0.0",
  "server": {
    "transport": "stdio",
    "host": "127.0.0.1",
    "port": 3000,
    "sse_port": 3001
  },
  "context_sets_file": "web_context_sets.json",
  "cache": {
    "enabled": true,
    "directory": "cache",
    "ttl_hours": 24
  }
}
```

### web_context_sets.json

Define documentation context sets:
```json
{
  "@vue": {
    "description": "Vue.js Documentation",
    "urls": [
      "https://vuejs.org",
      "https://router.vuejs.org"
    ]
  },
  "@frontend": {
    "description": "Frontend Stack",
    "urls": ["@vue", "@react"]
  }
}
```

## API Endpoints (SSE Mode)

### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "server": "MCP Web Context Server",
  "version": "1.0.0",
  "transports": ["stdio", "sse"],
  "context_sets": 5
}
```

### List Resources
```bash
GET /resources
```

### Read Resource
```bash
GET /resource?name=@vue
```

## Integration Examples

### VS Code Extension Integration

```typescript
// my-extension.ts
import { spawn } from 'child_process';

// Start standalone MCP server
const mcp = spawn('python', [
  '-m', 'mcp_server',
  '--transport', 'sse',
  '--port', '3001'
]);

// Use HTTP endpoints
const response = await fetch('http://localhost:3001/resources');
const resources = await response.json();
```

### Cline Integration

```json
{
  "mcpServers": {
    "web-context": {
      "command": "python",
      "args": ["-m", "mcp_server", "--config", "./mcp_config.json"]
    }
  }
}
```

## Troubleshooting

### Server Already Running
```powershell
# Check for running processes
Get-Process python | Where-Object {$_.CommandLine -like "*mcp_server*"}

# Stop all MCP processes
Get-Process python | Where-Object {$_.CommandLine -like "*mcp_server*"} | Stop-Process -Force
```

### Port Already in Use
```powershell
# Find process on port 3001
Get-NetTCPConnection -LocalPort 3001

# Use different port
python -m mcp_server --sse-port 3002
```

### Cache Issues
```powershell
# Clear cache
Remove-Item "cache/" -Recurse -Force

# Disable caching
# Edit mcp_config.json: "enabled": false
```

## Command Line Options

```bash
python -m mcp_server --help

Options:
  --config FILE         Path to mcp_config.json
  --transport TYPE      stdio | sse | http (default: stdio)
  --host HOST          Server host (default: 127.0.0.1)
  --port PORT          Server port (default: 3000)
  --sse-port PORT      SSE endpoint port
  --verbose            Enable verbose logging
```

## Architecture

```
┌─────────────────────────────────────┐
│   MCP Server (Standalone)           │
│   - Independent process             │
│   - Multiple transport support      │
│   - HTTP/SSE endpoints              │
└─────────────────────────────────────┘
         ↑          ↑          ↑
         │          │          │
    ┌────┴──┐   ┌────┴──┐  ┌──┴────┐
    │Continue│   │ Cline │  │Windsurf
    └────────┘   └───────┘  └────────┘
```

## Performance Notes

- **Caching**: 24-hour TTL, automatic cleanup
- **Parallel Fetching**: All URLs loaded concurrently
- **Connection Reuse**: Persistent HTTP connections
- **Memory**: < 100MB typical usage

## Contributing

To add features:
1. Edit `mcp_server/server.py` for core logic
2. Update `mcp_config.json` for new settings
3. Test with: `python -m mcp_server --verbose`

---

**Last Updated**: 2026-01-23
**Version**: 1.0.0
