"""Simple HTTP client for embedding server."""
import httpx
import numpy as np
from typing import List, Union


class EmbeddingClient:
    """Client for embedding server API."""
    
    def __init__(self, endpoint: str, timeout: int = 30):
        self.endpoint = endpoint
        self.timeout = timeout
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=10.0, read=timeout, write=30.0),
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
        )
    
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Get embeddings for text(s).
        
        Args:
            texts: Single text string or list of texts
            
        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        # Ensure texts is a list
        if isinstance(texts, str):
            texts = [texts]
        
        payload = {"input": texts}
        
        response = self.client.post(self.endpoint, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract embeddings from response
        # Format: {"data": [{"embedding": [...]}, ...]}
        embeddings = [item["embedding"] for item in result["data"]]
        return np.array(embeddings)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        return float(dot_product / (norm1 * norm2))
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
