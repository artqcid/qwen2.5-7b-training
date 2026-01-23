"""CLI entry point for MCP Server."""
import asyncio
import sys
import argparse
from pathlib import Path
from .server import create_app
from .config import Config


def create_arg_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Standalone MCP Server - Works with any IDE/Editor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default stdio transport (for Continue IDE)
  python -m mcp_server

  # Start with custom config
  python -m mcp_server --config /path/to/mcp_config.json

  # Start SSE HTTP endpoint (for other clients)
  python -m mcp_server --sse-port 3001

  # Custom transport
  python -m mcp_server --transport sse --host 0.0.0.0 --port 3001
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to mcp_config.json (default: from env or ./mcp_config.json)",
    )
    
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)",
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Server port (default: 3000)",
    )
    
    parser.add_argument(
        "--sse-port",
        type=int,
        dest="sse_port",
        help="SSE endpoint port (for HTTP mode)",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    return parser


def main():
    """Run MCP server from command line."""
    parser = create_arg_parser()
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = Config.from_env()
        if args.config:
            config.config_file = Path(args.config)
        
        app = create_app(config)

        print(f"\n{'='*70}", file=sys.stderr)
        print(f"  MCP Server - Standalone Web Context Server", file=sys.stderr)
        print(f"{'='*70}", file=sys.stderr)
        print(f"  Version:     1.0.0", file=sys.stderr)
        print(f"  Config File: {config.config_file}", file=sys.stderr)
        print(f"  Cache Dir:   {config.cache_dir}", file=sys.stderr)
        print(f"  Cache TTL:   {config.cache_ttl_hours} hours", file=sys.stderr)
        print(f"  Transport:   {args.transport}", file=sys.stderr)
        print(f"{'='*70}", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"  Status: Ready", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"  Compatible with:", file=sys.stderr)
        print(f"    ✓ Continue IDE", file=sys.stderr)
        print(f"    ✓ Cline", file=sys.stderr)
        print(f"    ✓ Windsurf", file=sys.stderr)
        print(f"    ✓ Custom IDE Extensions", file=sys.stderr)
        print(f"    ✓ Direct HTTP/SSE Clients", file=sys.stderr)
        print(f"{'='*70}\n", file=sys.stderr)

        # Run server with selected transport
        try:
            if args.transport == "stdio":
                print(f"  [INFO] Using stdio transport (Continue IDE mode)", file=sys.stderr)
                asyncio.run(app.run_stdio())
            elif args.transport in ["sse", "http"]:
                print(f"  [INFO] Using HTTP SSE transport on {args.host}:{args.sse_port or args.port}", file=sys.stderr)
                asyncio.run(app.run_sse(
                    host=args.host,
                    port=args.sse_port or args.port
                ))
            else:
                print(f"  [ERROR] Unknown transport: {args.transport}", file=sys.stderr)
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n[INFO] Server stopped by user", file=sys.stderr)
            sys.exit(0)
        except Exception as run_error:
            print(f"[ERROR] Runtime error: {str(run_error)}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc(file=sys.stderr)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

