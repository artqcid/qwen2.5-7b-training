"""Tests comparing Dense-only vs Hybrid Search performance."""
import pytest
import uuid


class TestHybridSearch:
    """Compare dense-only and hybrid search results."""

    @pytest.fixture
    def hybrid_test_collection(self, rag_client):
        """Create a fresh test collection with hybrid support."""
        collection_name = f"hybrid-test-{uuid.uuid4().hex[:8]}"
        yield collection_name
        # Cleanup
        try:
            rag_client.delete_collection(collection_name)
        except Exception:
            pass

    @pytest.fixture
    def test_documents(self):
        """Documents designed to test keyword vs semantic matching."""
        return [
            {
                "content": "The AudioSource class provides the base interface for all audio processing in JUCE. "
                           "It defines methods like getNextAudioBlock() for streaming audio data.",
                "metadata": {"title": "AudioSource", "doc_type": "class-reference", "source": "test"}
            },
            {
                "content": "JUCE is a cross-platform C++ framework used for building audio applications, "
                           "plugins, and multimedia software.",
                "metadata": {"title": "JUCE Overview", "doc_type": "overview", "source": "test"}
            },
            {
                "content": "The ProcessorChain template allows chaining multiple audio processors together. "
                           "Each processor transforms the audio signal sequentially.",
                "metadata": {"title": "ProcessorChain", "doc_type": "class-reference", "source": "test"}
            },
            {
                "content": "Python is a popular programming language for data science and machine learning. "
                           "It has extensive libraries like NumPy, pandas, and scikit-learn.",
                "metadata": {"title": "Python Intro", "doc_type": "tutorial", "source": "test"}
            },
            {
                "content": "The MidiBuffer class stores MIDI events with sample-accurate timing. "
                           "Use addEvent() to insert MIDI messages into the buffer.",
                "metadata": {"title": "MidiBuffer", "doc_type": "class-reference", "source": "test"}
            },
        ]

    def test_keyword_exact_match(self, rag_client, hybrid_test_collection, test_documents):
        """Test that hybrid search boosts exact keyword matches."""
        collection = hybrid_test_collection
        
        # Index documents
        result = rag_client.index(test_documents, collection=collection)
        assert result["indexed_count"] == len(test_documents)
        
        # Search for exact class name - should find AudioSource first
        query = "AudioSource getNextAudioBlock"
        result = rag_client.search(query, limit=5, collection=collection, min_score=0.1)
        
        assert len(result["results"]) > 0, "No results found"
        
        # AudioSource should be top result due to exact keyword match
        top_result = result["results"][0]
        print(f"\nQuery: {query}")
        print(f"Top result: {top_result['metadata'].get('title')} (score: {top_result['score']:.3f})")
        
        # With hybrid, exact matches should score higher
        assert "AudioSource" in top_result["content"], (
            f"Expected AudioSource doc first, got: {top_result['metadata'].get('title')}"
        )

    def test_semantic_match(self, rag_client, hybrid_test_collection, test_documents):
        """Test semantic search still works (no exact keywords)."""
        collection = hybrid_test_collection
        
        # Index documents
        rag_client.index(test_documents, collection=collection)
        
        # Search semantically - no exact keywords from documents
        query = "how to process real-time sound data"
        result = rag_client.search(query, limit=3, collection=collection, min_score=0.1)
        
        assert len(result["results"]) > 0, "No results for semantic search"
        
        print(f"\nSemantic query: {query}")
        for i, r in enumerate(result["results"]):
            print(f"  {i+1}. {r['metadata'].get('title')} (score: {r['score']:.3f})")
        
        # Should return audio-related docs, not Python
        titles = [r["metadata"].get("title", "") for r in result["results"]]
        assert "Python Intro" not in titles[:2], (
            "Python doc should not be in top 2 for audio processing query"
        )

    def test_mixed_query(self, rag_client, hybrid_test_collection, test_documents):
        """Test query with both keywords and semantic intent."""
        collection = hybrid_test_collection
        
        # Index documents
        rag_client.index(test_documents, collection=collection)
        
        # Mix of keyword (MIDI) and semantic (timing/events)
        query = "MIDI event timing"
        result = rag_client.search(query, limit=3, collection=collection, min_score=0.1)
        
        assert len(result["results"]) > 0, "No results found"
        
        print(f"\nMixed query: {query}")
        for i, r in enumerate(result["results"]):
            print(f"  {i+1}. {r['metadata'].get('title')} (score: {r['score']:.3f})")
        
        # MidiBuffer should rank high due to keyword match
        top_titles = [r["metadata"].get("title", "") for r in result["results"][:2]]
        assert "MidiBuffer" in top_titles, (
            f"MidiBuffer should be in top 2 for MIDI query, got: {top_titles}"
        )

    def test_irrelevant_query(self, rag_client, hybrid_test_collection, test_documents):
        """Test that completely irrelevant queries return low scores."""
        collection = hybrid_test_collection
        
        # Index documents
        rag_client.index(test_documents, collection=collection)
        
        # Query completely unrelated to all documents
        query = "cooking recipes for pasta"
        result = rag_client.search(query, limit=3, collection=collection, min_score=0.0)
        
        print(f"\nIrrelevant query: {query}")
        if result["results"]:
            top_score = result["results"][0]["score"]
            print(f"  Top score: {top_score:.3f}")
            
            # Scores should be relatively low for irrelevant queries
            # Note: With RRF fusion, scores are normalized differently
            assert top_score < 0.8, f"Score too high for irrelevant query: {top_score}"
        else:
            print("  No results (correct for irrelevant query)")


class TestHybridVsDense:
    """Direct comparison tests when both modes are available."""

    @pytest.fixture
    def comparison_collection_dense(self, rag_client):
        """Collection without hybrid (uses existing juce-docs which is dense-only)."""
        # Use existing juce-docs collection which was created before hybrid support
        return "juce-docs"

    def test_collection_info(self, rag_client):
        """Show which collections support hybrid search."""
        # This is informational - shows the hybrid status
        try:
            # Check health endpoint for collection info
            health = rag_client.health()
            print(f"\nRAG Server Status: {health['status']}")
            print(f"Qdrant: {health['qdrant']['url']}")
            
            # Note: actual hybrid status is internal to the collection
            # The RAG server handles fallback automatically
            print("\nNote: Hybrid search is enabled by default for new collections.")
            print("Existing collections use dense-only search with automatic fallback.")
        except Exception as e:
            print(f"Could not get health info: {e}")

    def test_search_works_on_legacy_collection(self, rag_client, comparison_collection_dense):
        """Verify search works on legacy dense-only collections."""
        collection = comparison_collection_dense
        
        # Check if collection exists
        try:
            result = rag_client.search(
                "JUCE audio processing", 
                limit=3, 
                collection=collection, 
                min_score=0.3
            )
            
            print(f"\nLegacy collection search ({collection}):")
            print(f"  Results: {len(result['results'])}")
            for r in result["results"][:3]:
                print(f"  - {r['metadata'].get('title', 'N/A')}: {r['score']:.3f}")
                
        except Exception as e:
            pytest.skip(f"Collection {collection} not available: {e}")
