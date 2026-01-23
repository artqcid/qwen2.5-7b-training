"""Python client for Embedding Server."""
import httpx
from typing import List, Union, Optional


class EmbeddingClient:
    """Async client for embedding server."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        Initialize client.

        Args:
            base_url: Base URL of the embedding server (default: http://localhost:8001)
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)

    async def embed(
        self, texts: Union[str, List[str]], model: str = "nomic-embed-text-v1.5"
    ) -> List[List[float]]:
        """
        Generate embeddings for text(s).

        Args:
            texts: A string or list of strings to embed
            model: Model name

        Returns:
            List of embedding vectors (List[List[float]])

        Raises:
            httpx.HTTPError: If request fails
            RuntimeError: If server returns error
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/embeddings",
                json={"input": texts, "model": model},
            )
            response.raise_for_status()

            data = response.json()
            return [item["embedding"] for item in data["data"]]
        except httpx.HTTPError as e:
            raise RuntimeError(f"Embedding request failed: {str(e)}")

    async def health(self) -> dict:
        """Check server health."""
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    async def list_models(self) -> dict:
        """List available models."""
        response = await self.client.get(f"{self.base_url}/models")
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close client connection."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


# Sync wrapper for convenience
class SyncEmbeddingClient:
    """Synchronous wrapper for EmbeddingClient (useful for simple scripts)."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        import asyncio

        self.base_url = base_url
        self.loop = asyncio.new_event_loop()

    def embed(
        self, texts: Union[str, List[str]], model: str = "nomic-embed-text-v1.5"
    ) -> List[List[float]]:
        """Synchronous embedding."""
        async def _embed():
            async with EmbeddingClient(self.base_url) as client:
                return await client.embed(texts, model)

        return self.loop.run_until_complete(_embed())

    def health(self) -> dict:
        """Synchronous health check."""
        async def _health():
            async with EmbeddingClient(self.base_url) as client:
                return await client.health()

        return self.loop.run_until_complete(_health())

    def close(self):
        """Close client."""
        self.loop.close()
