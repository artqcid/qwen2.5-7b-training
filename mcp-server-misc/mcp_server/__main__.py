"""CLI entry point for MCP Server."""
import asyncio
import sys
from pathlib import Path
from .server import create_app
from .config import Config


def main():
    """Run MCP server from command line."""
    try:
        config = Config.from_env()
        app = create_app(config)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"  MCP Server Misc - Web Context Server", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"  Config File: {config.config_file}", file=sys.stderr)
        print(f"  Cache Dir:   {config.cache_dir}", file=sys.stderr)
        print(f"  Cache TTL:   {config.cache_ttl_hours} hours", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)

        # Run server
        asyncio.run(app.run_stdio())

    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
