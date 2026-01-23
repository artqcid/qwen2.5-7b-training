"""
Embedding Server - Local embedding service using llama.cpp

A fast, CPU-efficient embedding server for Continue IDE, RAG systems, and other projects.
Built with FastAPI and llama-cpp-python.
"""

__version__ = "1.0.0"
__author__ = "artqcid"

from .client import EmbeddingClient
from .config import Config
from .server import EmbeddingServer

__all__ = ["EmbeddingClient", "Config", "EmbeddingServer"]
