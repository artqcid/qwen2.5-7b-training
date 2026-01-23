"""Tests for embedding server."""
import pytest
from embedding_server.config import Config
from embedding_server.models import EmbeddingRequest, EmbeddingResponse
from pathlib import Path


def test_config_from_env():
    """Test loading config from environment."""
    config = Config.from_env()
    assert config.model_path.exists()
    assert config.n_gpu_layers == 0  # CPU only
    assert config.model_name == "nomic-embed-text-v1.5"


def test_embedding_request():
    """Test embedding request model."""
    # Single text
    req = EmbeddingRequest(input="hello world")
    assert req.input == "hello world"

    # Multiple texts
    req = EmbeddingRequest(input=["hello", "world"])
    assert len(req.input) == 2


def test_embedding_response():
    """Test embedding response model."""
    response = EmbeddingResponse(
        data=[{"object": "embedding", "embedding": [0.1, 0.2], "index": 0}],
        model="nomic-embed-text-v1.5",
        usage={"prompt_tokens": 2, "total_tokens": 2},
    )
    assert response.model == "nomic-embed-text-v1.5"
    assert len(response.data) == 1
