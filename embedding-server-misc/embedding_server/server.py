"""Embedding Server - FastAPI based embedding service."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sys

try:
    from llama_cpp import Llama
except ImportError:
    print("ERROR: llama-cpp-python not found. Install with: pip install llama-cpp-python")
    sys.exit(1)

from .config import Config
from .models import EmbeddingRequest, EmbeddingResponse, HealthResponse, ModelInfo


class EmbeddingServer:
    """Reusable embedding server."""

    def __init__(self, config: Config):
        self.config = config
        self.app = FastAPI(
            title="Embedding Server",
            description="Local embedding service using llama.cpp (CPU optimized)",
            version="1.0.0",
        )
        self.llm: Optional[Llama] = None
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """Setup CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Register API routes."""

        @self.app.on_event("startup")
        async def startup():
            await self.load_model()

        @self.app.get("/health", response_model=HealthResponse)
        async def health():
            return HealthResponse(
                status="ok" if self.llm else "error",
                model_loaded=self.llm is not None,
                model_path=str(self.config.model_path),
                model_name=self.config.model_name,
                cpu_only=True,
            )

        @self.app.post("/v1/embeddings", response_model=EmbeddingResponse)
        async def create_embeddings(request: EmbeddingRequest):
            return await self.embed(request)

        @self.app.get("/models")
        async def list_models():
            """List available models."""
            return {
                "object": "list",
                "data": [
                    ModelInfo(
                        id=self.config.model_name,
                        owned_by="local",
                    ).dict()
                ],
            }

    async def load_model(self):
        """Load embedding model."""
        print(f"Loading embedding model: {self.config.model_path}")

        if not self.config.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.config.model_path}")

        try:
            self.llm = Llama(
                model_path=str(self.config.model_path),
                embedding=True,
                n_ctx=self.config.n_ctx,
                n_gpu_layers=self.config.n_gpu_layers,
                n_threads=self.config.n_threads,
                verbose=self.config.verbose,
            )
            print(f"✓ Model loaded successfully (CPU mode)")
            print(f"  Context size: {self.config.n_ctx}")
            print(f"  Model: {self.config.model_name}")
        except Exception as e:
            print(f"ERROR loading model: {e}")
            raise

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings."""
        if self.llm is None:
            raise HTTPException(status_code=503, detail="Model not loaded")

        texts = request.input if isinstance(request.input, list) else [request.input]

        embeddings = []
        total_tokens = 0

        for idx, text in enumerate(texts):
            try:
                embedding = self.llm.embed(text)
                embeddings.append(
                    {"object": "embedding", "embedding": embedding, "index": idx}
                )
                total_tokens += len(text.split())
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Error embedding text: {str(e)}"
                )

        return EmbeddingResponse(
            data=embeddings,
            model=request.model or self.config.model_name,
            usage={"prompt_tokens": total_tokens, "total_tokens": total_tokens},
        )


def create_app(config: Optional[Config] = None) -> FastAPI:
    """Factory function to create FastAPI app."""
    if config is None:
        config = Config.from_env()

    server = EmbeddingServer(config)
    return server.app
