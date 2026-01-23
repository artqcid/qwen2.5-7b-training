"""Configuration for MCP Server."""
from pathlib import Path
from typing import Optional, Dict, Any
import json
import os


class Config:
    """MCP Server configuration."""

    def __init__(
        self,
        config_file: Optional[Path] = None,
        prompts_file: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
        cache_ttl_hours: int = 24,
    ):
        """
        Initialize configuration.

        Args:
            config_file: Path to context sets JSON file
            prompts_file: Path to prompts JSON file
            cache_dir: Directory for caching fetched content
            cache_ttl_hours: Cache time-to-live in hours (default: 24)
        """
        self.config_file = config_file or Path(__file__).parent.parent / "web_context_sets.json"
        self.prompts_file = prompts_file or Path(__file__).parent.parent / "prompts.json"
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "cache"
        self.cache_ttl_hours = cache_ttl_hours
        self.cache_ttl_seconds = cache_ttl_hours * 3600

        # Create cache directory
        self.cache_dir.mkdir(exist_ok=True)

    def load_context_sets(self) -> Dict[str, Any]:
        """Load context sets from configuration file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"WARNING: Failed to load config {self.config_file}: {e}")
                return {}
        return {}

    def load_prompts(self) -> Dict[str, Any]:
        """Load prompts from prompts file."""
        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"WARNING: Failed to load prompts {self.prompts_file}: {e}")
                return {"prompts": []}
        return {"prompts": []}

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        config_file = os.getenv("MCP_CONFIG_FILE")
        if config_file:
            config_file = Path(config_file)

        prompts_file = os.getenv("MCP_PROMPTS_FILE")
        if prompts_file:
            prompts_file = Path(prompts_file)

        cache_dir = os.getenv("MCP_CACHE_DIR")
        if cache_dir:
            cache_dir = Path(cache_dir)

        cache_ttl = int(os.getenv("MCP_CACHE_TTL_HOURS", "24"))

        return cls(
            config_file=config_file,
            prompts_file=prompts_file,
            cache_dir=cache_dir,
            cache_ttl_hours=cache_ttl,
        )
