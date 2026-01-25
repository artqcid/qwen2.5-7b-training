"""RAG smoke tests - verify basic RAG functionality with Vue.js docs."""
import pytest


def test_health_check(rag_client):
    """Test RAG server health and service connections."""
    health = rag_client.health()
    
    assert health["status"] == "healthy", "RAG server not healthy"
    assert health["qdrant"]["connected"], "Qdrant not connected"
    assert health["embedding"]["connected"], "Embedding server not connected"
    assert health["llm"]["connected"], "LLM server not connected"
    
    print(f"\n✓ All services connected:")
    print(f"  - Qdrant: {health['qdrant']['url']}")
    print(f"  - Embedding: {health['embedding']['url']}")
    print(f"  - LLM: {health['llm']['url']}")


def test_index_documents(rag_client, rag_smoke_config, clean_test_collection):
    """Test indexing Vue.js documentation into RAG."""
    collection = clean_test_collection
    docs = rag_smoke_config["test_documents"]
    
    result = rag_client.index(docs, collection=collection)
    
    assert result["indexed_count"] == len(docs), (
        f"Expected {len(docs)} documents indexed, got {result['indexed_count']}"
    )
    assert result["collection"] == collection
    assert len(result["document_ids"]) == len(docs)
    
    print(f"\n✓ Indexed {result['indexed_count']} Vue.js documents")


def test_vector_search(rag_client, rag_smoke_config, clean_test_collection):
    """Test vector search for Vue.js concepts."""
    collection = clean_test_collection
    docs = rag_smoke_config["test_documents"]
    threshold = rag_smoke_config.get("search_threshold", 0.5)
    
    # Index documents first
    rag_client.index(docs, collection=collection)
    
    # Search for Vue reactive concepts
    result = rag_client.search("reactive state management", limit=3, collection=collection)
    
    assert len(result["results"]) > 0, "No search results found"
    assert result["query"] == "reactive state management"
    
    # Check that results have good similarity scores
    top_result = result["results"][0]
    assert top_result["score"] >= threshold, (
        f"Top result score {top_result['score']:.3f} below threshold {threshold}"
    )
    
    print(f"\n✓ Found {len(result['results'])} relevant documents")
    print(f"  Top score: {top_result['score']:.3f}")
    print(f"  Content preview: {top_result['content'][:100]}...")


def test_rag_query(rag_client, rag_smoke_config, clean_test_collection):
    """Test RAG query: retrieve context and generate answer."""
    collection = clean_test_collection
    docs = rag_smoke_config["test_documents"]
    
    # Index documents first
    rag_client.index(docs, collection=collection)
    
    # Test query from config
    test_query = rag_smoke_config["test_queries"][0]
    query_text = test_query["query"]
    expected_keywords = test_query["expected_keywords"]
    
    result = rag_client.query(query_text, limit=3, collection=collection)
    
    assert "answer" in result, "No answer generated"
    assert len(result["sources"]) > 0, "No source documents retrieved"
    
    answer = result["answer"].lower()
    
    # Check that answer contains expected keywords
    found_keywords = [kw for kw in expected_keywords if kw.lower() in answer]
    assert len(found_keywords) >= 2, (
        f"Answer should contain at least 2 of {expected_keywords}, "
        f"but only found {found_keywords}\nAnswer: {result['answer']}"
    )
    
    print(f"\n✓ RAG Query successful")
    print(f"  Query: {query_text}")
    print(f"  Answer: {result['answer'][:200]}...")
    print(f"  Sources: {len(result['sources'])}")
    print(f"  Keywords found: {found_keywords}")


def test_search_relevance(rag_client, rag_smoke_config, clean_test_collection):
    """Test that search returns relevant documents with metadata."""
    collection = clean_test_collection
    docs = rag_smoke_config["test_documents"]
    
    # Index documents
    rag_client.index(docs, collection=collection)
    
    # Search for specific topic
    result = rag_client.search("component props and events", limit=5, collection=collection)
    
    assert len(result["results"]) > 0
    
    # Check that top result has metadata
    top_result = result["results"][0]
    assert "metadata" in top_result
    assert "topic" in top_result["metadata"]
    
    # For component query, expect components topic in top results
    top_topics = [r["metadata"]["topic"] for r in result["results"][:2]]
    assert "components" in top_topics, (
        f"Expected 'components' topic in top 2 results for component query, got {top_topics}"
    )
    
    print(f"\n✓ Search relevance verified")
    print(f"  Query: component props and events")
    print(f"  Top topics: {top_topics}")
    print(f"  Top score: {top_result['score']:.3f}")
