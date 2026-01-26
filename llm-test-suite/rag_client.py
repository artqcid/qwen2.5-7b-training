"""Simple HTTP client for RAG server."""
import httpx
from typing import List, Dict, Optional, Any


class RAGClient:
    """Client for RAG server API."""
    
    def __init__(self, endpoint: str, timeout: int = 60):
        self.endpoint = endpoint.rstrip('/')
        self.timeout = timeout
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=10.0, read=timeout, write=30.0),
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
            http2=False  # Disable HTTP/2 for compatibility
        )
    
    def health(self) -> Dict[str, Any]:
        """Check RAG server health and service connections."""
        response = self.client.get(f"{self.endpoint}/health")
        response.raise_for_status()
        return response.json()
    
    def index(self, documents: List[Dict[str, Any]], collection: str = "documents") -> Dict[str, Any]:
        """Index documents into RAG server.
        
        Args:
            documents: List of dicts with 'content' and optional 'metadata'
            collection: Collection name for Qdrant
            
        Returns:
            Dict with indexed_count, document_ids, collection
        """
        payload = {
            "documents": documents,
            "collection": collection
        }
        
        response = self.client.post(f"{self.endpoint}/v1/rag/index", json=payload)
        response.raise_for_status()
        return response.json()
    
    def search(self, query: str, limit: int = 5, collection: str = "documents", 
               min_score: Optional[float] = None) -> Dict[str, Any]:
        """Vector search for similar documents.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            collection: Collection name
            min_score: Minimum similarity score (optional)
            
        Returns:
            Dict with results (list of docs with scores), query, collection
        """
        payload = {
            "query": query,
            "limit": limit,
            "collection": collection
        }
        if min_score is not None:
            payload["min_score"] = min_score
        
        response = self.client.post(f"{self.endpoint}/v1/rag/search", json=payload)
        response.raise_for_status()
        return response.json()
    
    def query(self, query: str, limit: int = 5, collection: str = "documents",
              include_context: bool = True, max_tokens: int = 2048,
              temperature: float = 0.7) -> Dict[str, Any]:
        """RAG query: Retrieve documents and generate answer.
        
        Args:
            query: Question to answer
            limit: Number of documents to retrieve
            collection: Collection name
            include_context: Include context in response
            max_tokens: Max tokens for LLM generation
            temperature: LLM temperature
            
        Returns:
            Dict with answer, sources, query, context (optional), collection
        """
        payload = {
            "query": query,
            "limit": limit,
            "collection": collection,
            "include_context": include_context,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = self.client.post(f"{self.endpoint}/v1/rag/query", json=payload)
        response.raise_for_status()
        return response.json()
    
    def delete_collection(self, collection: str) -> Dict[str, Any]:
        """Delete a collection from Qdrant.
        
        Args:
            collection: Collection name to delete
            
        Returns:
            Dict with status and message
        """
        response = self.client.delete(f"{self.endpoint}/v1/rag/collections/{collection}")
        response.raise_for_status()
        return response.json()
    
    def list_collections(self) -> List[str]:
        """List all collections in Qdrant.
        
        Returns:
            List of collection names
        """
        response = self.client.get(f"{self.endpoint}/collections")
        response.raise_for_status()
        return response.json().get("collections", [])
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
