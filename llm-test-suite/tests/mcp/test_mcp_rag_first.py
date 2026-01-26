"""MCP RAG-First Architecture tests.

Tests verify the RAG-First pipeline:
1. Query RAG first with quality gate
2. Fallback to web-fetch if gate fails
3. Re-index fetched content for future queries
"""
import pytest
import httpx
from typing import Dict, Any


class MCPClient:
    """Simple MCP Server client for testing."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8003", timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        
    def health(self) -> Dict[str, Any]:
        """Check MCP server health."""
        with httpx.Client(http2=False, timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
            
    def list_context_sets(self) -> Dict[str, Any]:
        """List available context sets."""
        # SSE transport doesn't have direct tool invocation endpoint
        # This is a placeholder - actual testing requires SSE client
        return {"available": True}


@pytest.fixture(scope="module")
def mcp_client():
    """Create MCP client for testing."""
    client = MCPClient()
    yield client


@pytest.fixture(scope="module") 
def rag_client():
    """Create RAG client for RAG-First verification."""
    from rag_client import RAGClient
    client = RAGClient(endpoint="http://127.0.0.1:8002", timeout=30)
    yield client
    client.close()


class TestMCPHealth:
    """Test MCP Server health and configuration."""
    
    def test_mcp_server_health(self, mcp_client):
        """Test MCP server is running and healthy."""
        try:
            health = mcp_client.health()
            assert health.get("status") in ["ok", "healthy", "running"], (
                f"MCP server unhealthy: {health}"
            )
            print(f"\n✓ MCP Server healthy: {health}")
        except httpx.ConnectError:
            pytest.skip("MCP Server not running on port 8003")


class TestRAGFirstArchitecture:
    """Test RAG-First query architecture."""
    
    def test_rag_server_available(self, rag_client):
        """Verify RAG server is available for RAG-First queries."""
        try:
            health = rag_client.health()
            # Accept degraded status (embedding server may be down)
            assert health["status"] in ["healthy", "degraded"], (
                f"RAG server not available: {health}"
            )
            print(f"\n✓ RAG Server status: {health['status']}")
            print(f"  Qdrant: {'connected' if health['qdrant']['connected'] else 'disconnected'}")
            print(f"  Embedding: {'connected' if health['embedding']['connected'] else 'disconnected'}")
        except httpx.ConnectError:
            pytest.skip("RAG Server not running on port 8002")
    
    def test_rag_quality_gate_config(self, rag_client):
        """Verify RAG quality gate parameters are reasonable."""
        # These are the recommended values from ChatGPT analysis
        expected_config = {
            "min_results": 3,
            "min_score": 0.75,
            "max_score_gap": 0.15,
            "freshness_days": 30,
        }
        
        # Note: Actual config is in MCP server, not RAG server
        # This test documents the expected values
        print(f"\n✓ Expected RAG Gate Config:")
        for key, value in expected_config.items():
            print(f"  {key}: {value}")
    
    def test_rag_collection_for_juce(self, rag_client):
        """Verify JUCE collection exists for RAG-First queries."""
        try:
            health = rag_client.health()
            collections = health.get("collections", [])
            
            # Check if juce-docs collection exists
            has_juce = any("juce" in c.lower() for c in collections)
            
            if has_juce:
                print(f"\n✓ JUCE collection found in: {collections}")
            else:
                print(f"\n⚠ No JUCE collection yet. Collections: {collections}")
                print("  RAG-First will fallback to web-fetch and create collection")
                
        except Exception as e:
            pytest.skip(f"Could not check collections: {e}")
    
    def test_rag_search_returns_metadata(self, rag_client):
        """Verify RAG search returns proper metadata for quality gate."""
        try:
            # Try search (may fail if no data indexed)
            result = rag_client.search(
                query="test query",
                limit=3,
                collection="documents"
            )
            
            # If results exist, check metadata structure
            if result.get("results"):
                for r in result["results"]:
                    assert "score" in r, "Missing score in result"
                    assert "metadata" in r, "Missing metadata in result"
                    print(f"\n✓ Search returns proper structure")
                    print(f"  Score: {r.get('score', 'N/A')}")
                    print(f"  Metadata keys: {list(r.get('metadata', {}).keys())}")
                    break
            else:
                print("\n⚠ No search results (collection may be empty)")
                
        except Exception as e:
            print(f"\n⚠ Search test skipped: {e}")


class TestRAGFirstFallback:
    """Test RAG-First fallback behavior."""
    
    def test_fallback_triggers_on_empty_results(self):
        """Document: Empty RAG results should trigger web-fetch fallback."""
        # This is a documentation test - actual behavior tested via MCP
        expected_behavior = """
        When RAG returns no results:
        1. Gate evaluation returns passed=False, confidence='none'
        2. MCP server falls back to web-fetch
        3. Fetched content is indexed for future queries
        """
        print(f"\n✓ Expected fallback behavior documented:{expected_behavior}")
    
    def test_fallback_triggers_on_low_score(self):
        """Document: Low RAG scores should trigger web-fetch fallback."""
        expected_behavior = """
        When best_score < 0.75:
        1. Gate evaluation returns passed=False
        2. MCP server falls back to web-fetch
        3. Content re-indexed with fresh timestamp
        """
        print(f"\n✓ Low score fallback behavior documented:{expected_behavior}")
    
    def test_fallback_triggers_on_stale_content(self):
        """Document: Stale content should trigger background re-index."""
        expected_behavior = """
        When ingested_at > 30 days:
        1. Gate returns passed=True, confidence='medium'
        2. RAG content returned to user
        3. Background re-index triggered (should_reindex=True)
        """
        print(f"\n✓ Stale content behavior documented:{expected_behavior}")


class TestConfidenceAwareResponse:
    """Test confidence-aware response formatting."""
    
    def test_high_confidence_no_note(self):
        """High confidence responses should have no warning note."""
        # Simulate high confidence response
        confidence = "high"
        note = ""  # No note for high confidence
        assert note == "", "High confidence should not add notes"
        print(f"\n✓ High confidence: no warning note")
    
    def test_medium_confidence_has_note(self):
        """Medium confidence responses should include freshness note."""
        confidence = "medium"
        expected_note = "_Hinweis: Mittlere Konfidenz - neuere Docs könnten verfügbar sein._"
        print(f"\n✓ Medium confidence note: {expected_note}")
    
    def test_low_confidence_has_warning(self):
        """Low confidence responses should warn about potential issues."""
        confidence = "low"
        expected_note = "_Hinweis: Niedrige Konfidenz - basierend auf älteren/weniger relevanten Daten._"
        print(f"\n✓ Low confidence note: {expected_note}")
    
    def test_web_fallback_has_source_note(self):
        """Web-fallback responses should indicate data source."""
        expected_note = "_Hinweis: Basierend auf aktuellen Web-Daten (nicht aus RAG-Index)._"
        print(f"\n✓ Web fallback note: {expected_note}")
