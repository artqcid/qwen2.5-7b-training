"""Simple HTTP client for llama.cpp server."""
import httpx
from typing import Optional


class LLMClient:
    """Client for llama.cpp completion API."""
    
    def __init__(self, endpoint: str, timeout: int = 60):
        self.endpoint = endpoint
        self.timeout = timeout
        # Use explicit per-phase timeouts and modest connection limits to avoid
        # overloading the server if tests run in parallel elsewhere.
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=10.0, read=timeout, write=30.0),
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
        )
    
    def complete(
        self,
        prompt: str,
        n_predict: int = 200,
        temperature: float = 0.7,
        stop: Optional[list] = None
    ) -> dict:
        """Send completion request to llama.cpp server."""
        if stop is None:
            stop = ["</s>", "\n\n\n"]
        
        payload = {
            "prompt": prompt,
            "n_predict": n_predict,
            "temperature": temperature,
            "stop": stop
        }
        
        response = self.client.post(self.endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_content(self, prompt: str, **kwargs) -> str:
        """Get completion content text."""
        result = self.complete(prompt, **kwargs)
        return result.get("content", "")
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
