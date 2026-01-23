@echo off
REM Wrapper to start MCP server with clean stdio
REM No PowerShell profile, no terminal pollution

"C:\Users\marku\Documents\GitHub\artqcid\ai-projects\qwen2.5-7b-training\mcp-server-misc\.venv\Scripts\python.exe" -m mcp_server --config "C:\Users\marku\Documents\GitHub\artqcid\ai-projects\qwen2.5-7b-training\mcp-server-misc\mcp_config.json" %*
