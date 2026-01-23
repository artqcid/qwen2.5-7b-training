"""Configuration for Embedding Server."""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
import os


class Config(BaseModel):
    """Server configuration."""

    model_path: Path
    model_name: str = "nomic-embed-text-v1.5"
    n_ctx: int = 256  # Small context for embeddings
    n_gpu_layers: int = 0  # CPU only!
    n_threads: Optional[int] = None
    verbose: bool = False
    host: str = "127.0.0.1"
    port: int = 8001

    @classmethod
    def from_env(cls) -> "Config":
        """Load config from environment variables."""
        return cls(
            model_path=Path(
                os.getenv(
                    "EMBEDDING_MODEL_PATH",
                    r"d:\AI-Models\embedding\nomic\nomic-embed-text-v1.5.Q5_K_M.gguf",
                )
            ),
            model_name=os.getenv("EMBEDDING_MODEL_NAME", "nomic-embed-text-v1.5"),
            n_ctx=int(os.getenv("EMBEDDING_CTX_SIZE", "256")),
            n_gpu_layers=int(os.getenv("EMBEDDING_GPU_LAYERS", "0")),  # CPU!
            verbose=os.getenv("EMBEDDING_VERBOSE", "").lower() == "true",
            host=os.getenv("EMBEDDING_HOST", "127.0.0.1"),
            port=int(os.getenv("EMBEDDING_PORT", "8001")),
        )

    class Config:
        arbitrary_types_allowed = True
