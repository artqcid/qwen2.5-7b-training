#!/usr/bin/env python3
"""
web_mcp.py

Model Context Protocol (MCP) Server für Web-Context-Dokumentation.
Lädt Dokumentation von konfigurierten URLs und stellt sie als Context bereit.
"""

import json
import asyncio
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path
import hashlib
from datetime import datetime

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError:
    print("ERROR: mcp package not found. Please install: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Required packages not found. Please install: pip install httpx beautifulsoup4", file=sys.stderr)
    sys.exit(1)

# Konfiguration
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "web_context_sets.json"
CACHE_DIR = SCRIPT_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Server-Instanz
server = Server("web-context")

# Global state
context_sets: Dict[str, Any] = {}
cache: Dict[str, str] = {}


def load_config():
    """Lädt die Konfiguration der Context-Sets."""
    global context_sets
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            context_sets = json.load(f)
    else:
        print(f"WARNING: Config file not found: {CONFIG_FILE}", file=sys.stderr)
        context_sets = {}


def get_cache_path(url: str) -> Path:
    """Generiert Cache-Pfad für eine URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{url_hash}.json"


def load_from_cache(url: str) -> Optional[str]:
    """Lädt gecachten Content für URL."""
    cache_path = get_cache_path(url)
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Cache für 24h gültig
                cached_time = datetime.fromisoformat(data.get("timestamp", ""))
                if (datetime.now() - cached_time).total_seconds() < 86400:
                    return data.get("content", "")
        except Exception as e:
            print(f"Cache read error: {e}", file=sys.stderr)
    return None


def save_to_cache(url: str, content: str):
    """Speichert Content in Cache."""
    cache_path = get_cache_path(url)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "content": content
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Cache write error: {e}", file=sys.stderr)


async def fetch_url_content(url: str) -> str:
    """Lädt Content von einer URL."""
    # Prüfe Cache
    cached = load_from_cache(url)
    if cached:
        return cached
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Parse HTML und extrahiere Text
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Entferne Scripts und Styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extrahiere Haupttext
            text = soup.get_text(separator='\n', strip=True)
            
            # Speichere in Cache
            save_to_cache(url, text)
            
            return text
    except Exception as e:
        error_msg = f"Error fetching {url}: {str(e)}"
        print(error_msg, file=sys.stderr)
        return error_msg


def resolve_context_set(name: str, visited: Optional[set] = None) -> List[str]:
    """
    Resolved ein Context-Set zu konkreten URLs.
    Unterstützt verschachtelte Referenzen (z.B. @frontend -> @vue, @react, ...).
    """
    if visited is None:
        visited = set()
    
    if name in visited:
        return []  # Zirkuläre Referenz vermeiden
    
    visited.add(name)
    
    if name not in context_sets:
        return []
    
    urls = context_sets[name].get("urls", [])
    resolved = []
    
    for url in urls:
        if isinstance(url, str):
            if url.startswith("@"):
                # Verschachtelte Referenz
                resolved.extend(resolve_context_set(url, visited))
            else:
                # Konkrete URL
                resolved.append(url)
    
    return resolved


@server.list_resources()
async def list_resources() -> List[Resource]:
    """Listet verfügbare Context-Set Ressourcen auf."""
    resources = []
    for name in context_sets.keys():
        resources.append(
            Resource(
                uri=f"context://{name}",
                name=f"Context Set: {name}",
                mimeType="text/plain",
                description=f"Documentation context for {name}"
            )
        )
    return resources


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Lädt den Content eines Context-Sets."""
    if not uri.startswith("context://"):
        raise ValueError(f"Invalid URI: {uri}")
    
    context_name = uri.replace("context://", "")
    urls = resolve_context_set(context_name)
    
    if not urls:
        return f"No URLs configured for {context_name}"
    
    # Lade alle URLs parallel
    contents = []
    tasks = [fetch_url_content(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    for url, content in zip(urls, results):
        contents.append(f"=== {url} ===\n\n{content}\n\n")
    
    return "\n".join(contents)


@server.list_tools()
async def list_tools() -> List[Tool]:
    """Listet verfügbare Tools auf."""
    return [
        Tool(
            name="fetch_web_context",
            description="Fetches documentation context from configured web sources",
            inputSchema={
                "type": "object",
                "properties": {
                    "context_set": {
                        "type": "string",
                        "description": "Name of the context set to fetch (e.g., '@juce', '@vue', '@frontend')",
                    },
                },
                "required": ["context_set"],
            },
        ),
        Tool(
            name="list_context_sets",
            description="Lists all available context sets",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Führt ein Tool aus."""
    if name == "list_context_sets":
        context_list = "\n".join([f"- {name}: {len(resolve_context_set(name))} URLs" 
                                   for name in context_sets.keys()])
        return [TextContent(
            type="text",
            text=f"Available context sets:\n{context_list}"
        )]
    
    elif name == "fetch_web_context":
        context_set = arguments.get("context_set", "")
        if not context_set.startswith("@"):
            context_set = f"@{context_set}"
        
        content = await read_resource(f"context://{context_set}")
        
        return [TextContent(
            type="text",
            text=content
        )]
    
    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Hauptfunktion - startet den MCP Server."""
    print("Starting Web Context MCP Server...", file=sys.stderr)
    
    # Lade Konfiguration
    load_config()
    print(f"Loaded {len(context_sets)} context sets", file=sys.stderr)
    
    # Starte Server
    async with stdio_server() as (read_stream, write_stream):
        print("Server ready", file=sys.stderr)
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
