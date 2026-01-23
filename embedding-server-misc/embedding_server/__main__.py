"""CLI entry point for embedding server."""
import uvicorn
import sys
from .server import create_app
from .config import Config


def main():
    """Run embedding server."""
    try:
        config = Config.from_env()
        app = create_app(config)

        print(f"\n{'='*60}")
        print(f"  Embedding Server")
        print(f"{'='*60}")
        print(f"  Model:     {config.model_name}")
        print(f"  Path:      {config.model_path}")
        print(f"  URL:       http://{config.host}:{config.port}")
        print(f"  CPU Mode:  ✓ (no GPU layers)")
        print(f"{'='*60}\n")

        uvicorn.run(app, host=config.host, port=config.port, log_level="info")
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
