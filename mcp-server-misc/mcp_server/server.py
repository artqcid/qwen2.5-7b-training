"""Core MCP Server implementation."""
import json
import asyncio
import sys
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.types import Resource, Tool, TextContent
except ImportError:
    print("ERROR: mcp package not found. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    print(
        "ERROR: Required packages not found. Install with: pip install httpx beautifulsoup4",
        file=sys.stderr,
    )
    sys.exit(1)

from .config import Config
from .context import ContextResolver


class MCPServer:
    """Generalized MCP Server for web documentation context."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize MCP Server.

        Args:
            config: Configuration object (uses environment variables if None)
        """
        self.config = config or Config.from_env()
        self.server = Server("web-context")
        self.context_sets = self.config.load_context_sets()
        self.resolver = ContextResolver(self.context_sets)
        self._setup_routes()

    def _setup_routes(self):
        """Setup MCP server routes."""

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available context set resources."""
            resources = []
            for name in self.resolver.list_sets():
                resources.append(
                    Resource(
                        uri=f"context://{name}",
                        name=f"Context Set: {name}",
                        mimeType="text/plain",
                        description=f"Documentation context for {name}",
                    )
                )
            return resources

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Load content of a context set."""
            if not uri.startswith("context://"):
                raise ValueError(f"Invalid URI: {uri}")

            context_name = uri.replace("context://", "")
            urls = self.resolver.resolve(context_name)

            if not urls:
                return f"No URLs configured for {context_name}"

            # Load all URLs in parallel
            tasks = [self._fetch_url_content(url) for url in urls]
            results = await asyncio.gather(*tasks)

            contents = []
            for url, content in zip(urls, results):
                contents.append(f"=== {url} ===\n\n{content}\n\n")

            return "\n".join(contents)

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="fetch_web_context",
                    description="Fetches documentation context from configured web sources",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "context_set": {
                                "type": "string",
                                "description": "Name of context set to fetch (e.g., '@juce', '@vue')",
                            },
                        },
                        "required": ["context_set"],
                    },
                ),
                Tool(
                    name="list_context_sets",
                    description="Lists all available context sets",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> List[TextContent]:
            """Execute a tool."""
            if name == "list_context_sets":
                context_list = "\n".join(
                    [
                        f"- {name}: {count} URLs"
                        for name, count in self.resolver.get_all_sets().items()
                    ]
                )
                return [TextContent(type="text", text=f"Available context sets:\n{context_list}")]

            elif name == "fetch_web_context":
                context_set = arguments.get("context_set", "")
                if not context_set.startswith("@"):
                    context_set = f"@{context_set}"

                content = await read_resource(f"context://{context_set[1:]}")
                return [TextContent(type="text", text=content)]

            raise ValueError(f"Unknown tool: {name}")

    async def _fetch_url_content(self, url: str) -> str:
        """Fetch and cache content from a URL."""
        # Check cache
        cached = self._load_from_cache(url)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Parse HTML and extract text
                soup = BeautifulSoup(response.text, "html.parser")

                # Remove scripts, styles, nav, footer, header
                for element in soup(["script", "style", "nav", "footer", "header"]):
                    element.decompose()

                # Extract main text
                text = soup.get_text(separator="\n", strip=True)

                # Save to cache
                self._save_to_cache(url, text)

                return text
        except Exception as e:
            return f"Error fetching {url}: {str(e)}"

    def _get_cache_path(self, url: str) -> Path:
        """Generate cache path for URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.config.cache_dir / f"{url_hash}.json"

    def _load_from_cache(self, url: str) -> Optional[str]:
        """Load cached content for URL."""
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cached_time = datetime.fromisoformat(data.get("timestamp", ""))
                    age_seconds = (datetime.now() - cached_time).total_seconds()
                    if age_seconds < self.config.cache_ttl_seconds:
                        return data.get("content", "")
            except Exception as e:
                print(f"Cache read error: {e}", file=sys.stderr)
        return None

    def _save_to_cache(self, url: str, content: str):
        """Save content to cache."""
        cache_path = self._get_cache_path(url)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "url": url,
                        "timestamp": datetime.now().isoformat(),
                        "content": content,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            print(f"Cache write error: {e}", file=sys.stderr)

    async def run_stdio(self):
        """Run server using stdio transport."""
        print("Starting Web Context MCP Server...", file=sys.stderr)
        print(f"Loaded {len(self.context_sets)} context sets", file=sys.stderr)

        try:
            from mcp.server.stdio import stdio_server

            async with stdio_server() as (read_stream, write_stream):
                print("Server ready", file=sys.stderr)
                await self.server.run(
                    read_stream, write_stream, self.server.create_initialization_options()
                )
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)
            sys.exit(1)


def create_app(config: Optional[Config] = None) -> MCPServer:
    """Factory function to create MCP server."""
    if config is None:
        config = Config.from_env()
    return MCPServer(config)
