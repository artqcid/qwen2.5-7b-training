"""Embedding smoke tests - verify basic embedding server functionality.

These tests check:
- Semantic similarity between related texts
- Semantic distance between unrelated texts
- Determinism (same input → same output)
- Vector dimensionality and validity
"""
import pytest
import numpy as np


def test_embedding_similarity(embedding_client, embedding_smoke_config):
    """Test that semantically similar texts have high similarity."""
    similar_pairs = embedding_smoke_config.get("similar_pairs", [])
    threshold = embedding_smoke_config.get("similarity_threshold", 0.7)
    
    assert len(similar_pairs) > 0, "No similar_pairs configured in test_config.yaml"
    
    for text1, text2 in similar_pairs:
        # Get embeddings
        embeddings = embedding_client.embed([text1, text2])
        
        # Calculate similarity
        similarity = embedding_client.cosine_similarity(embeddings[0], embeddings[1])
        
        assert similarity >= threshold, (
            f"Similar texts have low similarity!\n"
            f"Text 1: {text1}\n"
            f"Text 2: {text2}\n"
            f"Similarity: {similarity:.4f} (expected >= {threshold})"
        )


def test_embedding_distance(embedding_client, embedding_smoke_config):
    """Test that semantically different texts have low similarity."""
    different_pairs = embedding_smoke_config.get("different_pairs", [])
    threshold = embedding_smoke_config.get("distance_threshold", 0.3)
    
    assert len(different_pairs) > 0, "No different_pairs configured in test_config.yaml"
    
    for text1, text2 in different_pairs:
        # Get embeddings
        embeddings = embedding_client.embed([text1, text2])
        
        # Calculate similarity
        similarity = embedding_client.cosine_similarity(embeddings[0], embeddings[1])
        
        assert similarity <= threshold, (
            f"Different texts have high similarity!\n"
            f"Text 1: {text1}\n"
            f"Text 2: {text2}\n"
            f"Similarity: {similarity:.4f} (expected <= {threshold})"
        )


def test_embedding_determinism(embedding_client, embedding_smoke_config):
    """Test that same text produces consistent embeddings."""
    threshold = embedding_smoke_config.get("determinism_threshold", 0.999)
    test_text = "JUCE AudioProcessor prepareToPlay method"
    
    # Get embeddings 3 times
    emb1 = embedding_client.embed(test_text)[0]
    emb2 = embedding_client.embed(test_text)[0]
    emb3 = embedding_client.embed(test_text)[0]
    
    # Check pairwise similarity
    sim_12 = embedding_client.cosine_similarity(emb1, emb2)
    sim_23 = embedding_client.cosine_similarity(emb2, emb3)
    sim_13 = embedding_client.cosine_similarity(emb1, emb3)
    
    assert sim_12 >= threshold, (
        f"Embeddings not deterministic (run 1 vs 2)!\n"
        f"Similarity: {sim_12:.6f} (expected >= {threshold})"
    )
    assert sim_23 >= threshold, (
        f"Embeddings not deterministic (run 2 vs 3)!\n"
        f"Similarity: {sim_23:.6f} (expected >= {threshold})"
    )
    assert sim_13 >= threshold, (
        f"Embeddings not deterministic (run 1 vs 3)!\n"
        f"Similarity: {sim_13:.6f} (expected >= {threshold})"
    )


def test_embedding_dimensionality(embedding_client, config):
    """Test that embeddings have correct dimension and valid values."""
    expected_dim = config["embedding"]["expected_dimension"]
    test_text = "Test embedding dimensionality"
    
    # Get embedding
    embedding = embedding_client.embed(test_text)[0]
    
    # Check dimension
    assert embedding.shape[0] == expected_dim, (
        f"Unexpected embedding dimension!\n"
        f"Got: {embedding.shape[0]}, Expected: {expected_dim}"
    )
    
    # Check for NaN/Inf
    assert not np.isnan(embedding).any(), "Embedding contains NaN values"
    assert not np.isinf(embedding).any(), "Embedding contains Inf values"
    
    # Check L2 norm is reasonable (not zero, not extremely large)
    norm = np.linalg.norm(embedding)
    assert 0.1 < norm < 100.0, (
        f"Embedding L2 norm out of expected range!\n"
        f"Norm: {norm:.4f} (expected 0.1 < norm < 100.0)"
    )


def test_embedding_batch_processing(embedding_client):
    """Test that batch processing works correctly."""
    texts = [
        "First test text",
        "Second test text",
        "Third test text"
    ]
    
    # Get embeddings in batch
    embeddings = embedding_client.embed(texts)
    
    # Check shape
    assert embeddings.shape[0] == len(texts), (
        f"Batch size mismatch! Got {embeddings.shape[0]}, expected {len(texts)}"
    )
    
    # Check all embeddings are different
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            similarity = embedding_client.cosine_similarity(embeddings[i], embeddings[j])
            assert similarity < 0.95, (
                f"Different texts have nearly identical embeddings!\n"
                f"Text {i}: {texts[i]}\n"
                f"Text {j}: {texts[j]}\n"
                f"Similarity: {similarity:.4f}"
            )
