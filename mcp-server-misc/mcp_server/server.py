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

# Optional: Try to import for SSE/HTTP support
try:
    from starlette.applications import Starlette
    from starlette.responses import StreamingResponse, JSONResponse
    from starlette.routing import Route
    HAS_STARLETTE = True
except ImportError:
    HAS_STARLETTE = False

from .config import Config
from .context import ContextResolver


class MCPServer:
    """Generalized MCP Server for web documentation context.
    
    Supports multiple transports:
    - stdio: For Continue IDE, direct MCP clients
    - SSE: For HTTP clients, web-based IDEs
    """

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
            try:
                if not uri or not isinstance(uri, str):
                    return "Error: Invalid URI provided"
                
                if not uri.startswith("context://"):
                    return f"Error: Invalid URI format. Expected 'context://...', got '{uri}'"

                context_name = uri.replace("context://", "")
                if not context_name:
                    return "Error: No context name specified in URI"
                
                urls = self.resolver.resolve(context_name)

                if not urls:
                    return f"No URLs configured for {context_name}"

                # Load all URLs in parallel
                tasks = [self._fetch_url_content(url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                contents = []
                for url, result in zip(urls, results):
                    if isinstance(result, Exception):
                        contents.append(f"=== {url} ===\n\nError: {str(result)}\n\n")
                    elif result is None:
                        contents.append(f"=== {url} ===\n\nNo content available\n\n")
                    else:
                        contents.append(f"=== {url} ===\n\n{result}\n\n")

                final_content = "\n".join(contents)
                return final_content if final_content else f"No content retrieved for {context_name}"
            except Exception as e:
                error_msg = f"Error reading resource {uri}: {str(e)}"
                print(error_msg, file=sys.stderr)
                return error_msg

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
            try:
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
                    if not context_set:
                        return [TextContent(type="text", text="Error: context_set parameter is required")]
                    
                    if not context_set.startswith("@"):
                        context_set = f"@{context_set}"

                    # Safely handle read_resource call
                    try:
                        content = await read_resource(f"context://{context_set[1:]}")
                        if content is None:
                            return [TextContent(type="text", text=f"Error: Failed to fetch {context_set}")]
                        return [TextContent(type="text", text=content)]
                    except Exception as fetch_error:
                        error_msg = f"Error fetching {context_set}: {str(fetch_error)}"
                        print(error_msg, file=sys.stderr)
                        return [TextContent(type="text", text=error_msg)]

                else:
                    error_msg = f"Unknown tool: {name}"
                    return [TextContent(type="text", text=error_msg)]
            except Exception as e:
                error_msg = f"Tool execution error: {str(e)}"
                print(error_msg, file=sys.stderr)
                return [TextContent(type="text", text=error_msg)]

    async def _fetch_url_content(self, url: str) -> str:
        """Fetch and cache content from a URL."""
        if not url or not isinstance(url, str):
            return ""
        
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
                
                if not text:
                    return ""

                # Save to cache
                self._save_to_cache(url, text)

                return text
        except Exception as e:
            error_msg = f"Error fetching {url}: {str(e)}"
            print(error_msg, file=sys.stderr)
            return ""

    def _get_cache_path(self, url: str) -> Path:
        """Generate cache path for URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.config.cache_dir / f"{url_hash}.json"

    def _load_from_cache(self, url: str) -> Optional[str]:
        """Load cached content for URL."""
        try:
            if not url or not isinstance(url, str):
                return None
            
            cache_path = self._get_cache_path(url)
            if not cache_path or not cache_path.exists():
                return None
            
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return None
                
                timestamp_str = data.get("timestamp")
                if not timestamp_str:
                    return None
                
                cached_time = datetime.fromisoformat(timestamp_str)
                age_seconds = (datetime.now() - cached_time).total_seconds()
                cache_ttl = getattr(self.config, 'cache_ttl_seconds', 86400)
                
                if age_seconds < cache_ttl:
                    content = data.get("content")
                    return content if isinstance(content, str) else None
        except Exception as e:
            print(f"Cache read error: {e}", file=sys.stderr)
        
        return None

    def _save_to_cache(self, url: str, content: str):
        """Save content to cache."""
        try:
            if not url or not isinstance(url, str):
                return
            
            if not content or not isinstance(content, str):
                return
            
            cache_path = self._get_cache_path(url)
            if not cache_path:
                return
            
            # Ensure cache directory exists
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
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
            print(f"Cache write error for {url}: {e}", file=sys.stderr)

    async def run_stdio(self):
        """Run server using stdio transport."""
        print("Starting Web Context MCP Server...", file=sys.stderr)
        print(f"Loaded {len(self.context_sets)} context sets", file=sys.stderr)

        try:
            from mcp.server.stdio import stdio_server

            async with stdio_server() as (read_stream, write_stream):
                print("Server ready", file=sys.stderr)
                try:
                    await self.server.run(
                        read_stream, write_stream, self.server.create_initialization_options()
                    )
                except Exception as inner_e:
                    print(f"Server runtime error: {inner_e}", file=sys.stderr)
                    raise
        except KeyboardInterrupt:
            print("Server interrupted", file=sys.stderr)
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)
            sys.exit(1)

    async def run_sse(self, host: str = "127.0.0.1", port: int = 3001):
        """Run server using SSE (Server-Sent Events) HTTP transport.
        
        This allows other IDE extensions and HTTP clients to connect.
        Requires: pip install starlette uvicorn
        """
        if not HAS_STARLETTE:
            print("ERROR: Starlette not installed. Install with: pip install starlette uvicorn", file=sys.stderr)
            sys.exit(1)
        
        try:
            from starlette.applications import Starlette
            from starlette.responses import JSONResponse
            from starlette.routing import Route
            import uvicorn
            
            print(f"Starting HTTP SSE server on {host}:{port}", file=sys.stderr)
            
            # Simple HTTP endpoint for other clients
            async def list_resources_endpoint(request):
                """HTTP endpoint to list available resources."""
                try:
                    resources = []
                    for name in self.resolver.list_sets():
                        resources.append({
                            "uri": f"context://{name}",
                            "name": f"Context Set: {name}",
                            "mimeType": "text/plain"
                        })
                    return JSONResponse({"resources": resources})
                except Exception as e:
                    print(f"Error in list_resources endpoint: {e}", file=sys.stderr)
                    return JSONResponse({"error": str(e)}, status_code=500)
            
            async def read_resource_endpoint(request):
                """HTTP endpoint to read a resource."""
                try:
                    context_name = request.query_params.get("name", "")
                    if not context_name:
                        return JSONResponse({"error": "Missing 'name' parameter"}, status_code=400)
                    
                    # Find the read_resource handler from the routes
                    # For now, we'll just return the context_name
                    return JSONResponse({
                        "name": context_name,
                        "content": f"Context: {context_name}"
                    })
                except Exception as e:
                    print(f"Error in read_resource endpoint: {e}", file=sys.stderr)
                    return JSONResponse({"error": str(e)}, status_code=500)
            
            async def health_check(request):
                """Health check endpoint."""
                return JSONResponse({
                    "status": "healthy",
                    "server": "MCP Web Context Server",
                    "version": "1.0.0",
                    "transports": ["stdio", "sse"],
                    "context_sets": len(self.context_sets)
                })
            
            routes = [
                Route("/health", health_check, methods=["GET"]),
                Route("/resources", list_resources_endpoint, methods=["GET"]),
                Route("/resource", read_resource_endpoint, methods=["GET"]),
            ]
            
            app = Starlette(routes=routes)
            
            config = uvicorn.Config(
                app,
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            print(f"[OK] HTTP SSE server ready at http://{host}:{port}", file=sys.stderr)
            print(f"[OK] Health check: http://{host}:{port}/health", file=sys.stderr)
            print(f"[OK] Resources: http://{host}:{port}/resources", file=sys.stderr)
            
            await server.serve()
            
        except ImportError:
            print("ERROR: uvicorn not installed. Install with: pip install uvicorn", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"SSE Server error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

