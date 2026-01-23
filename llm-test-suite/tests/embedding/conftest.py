"""Embedding-specific test fixtures."""
import pytest
import yaml
from pathlib import Path


@pytest.fixture(scope="session")
def embedding_smoke_config(config):
	"""Load embedding smoke test configuration from local config file."""
	# Load local embedding config
	embedding_config_path = Path(__file__).parent / "embedding_smoke_config.yaml"
	with open(embedding_config_path) as f:
		return yaml.safe_load(f)
