"""MCP-specific test fixtures."""
import pytest
import yaml
from pathlib import Path


@pytest.fixture(scope="session")
def smoke_config(config):
	"""Load MCP smoke test configuration from local config file."""
	# Load local MCP config
	mcp_config_path = Path(__file__).parent / "mcp_smoke_config.yaml"
	with open(mcp_config_path) as f:
		return yaml.safe_load(f)
