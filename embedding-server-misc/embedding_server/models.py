"""Pydantic models for API."""
from pydantic import BaseModel
from typing import List, Union, Dict, Any


class EmbeddingRequest(BaseModel):
    """Request model for embedding endpoint."""

    input: Union[str, List[str]]
    model: str = "nomic-embed-text-v1.5"


class EmbeddingResponse(BaseModel):
    """Response model for embedding endpoint."""

    object: str = "list"
    data: List[Dict[str, Any]]
    model: str
    usage: Dict[str, int]


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    model_loaded: bool
    model_path: str
    model_name: str
    cpu_only: bool = True


class ModelInfo(BaseModel):
    """Information about an available model."""

    id: str
    object: str = "model"
    owned_by: str = "local"
