"""Pytest configuration and fixtures."""
import json
import pytest
import yaml
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import LLMClient
from embedding_client import EmbeddingClient


def pytest_configure(config):
    """Force sequential execution even if xdist is auto-enabled.

    Some environments set PYTEST_ADDOPTS with xdist options. To avoid
    swamping the LLM server with parallel requests, pin the run to a
    single process and disable distributed scheduling if present.
    """
    if hasattr(config.option, "numprocesses") and config.option.numprocesses:
        config.option.numprocesses = 1
    if hasattr(config.option, "dist") and config.option.dist != "no":
        config.option.dist = "no"


@pytest.fixture(scope="session")
def config():
    """Load test configuration."""
    config_path = Path(__file__).parent.parent / "test_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def llm_client(config):
    """Create LLM client for entire test session."""
    endpoint = config["llm"]["endpoint"]
    timeout = config["llm"]["timeout"]
    
    client = LLMClient(endpoint, timeout)
    yield client
    client.close()


@pytest.fixture(scope="session")
def web_context_sets(config):
    """Load web_context_sets.json."""
    config_path = Path(__file__).parent.parent / "test_config.yaml"
    context_file = config_path.parent / config["context_sets_file"]
    
    with open(context_file) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def embedding_client(config):
    """Create embedding client for entire test session."""
    endpoint = config["embedding"]["endpoint"]
    timeout = config["embedding"]["timeout"]
    
    client = EmbeddingClient(endpoint, timeout)
    yield client
    client.close()
