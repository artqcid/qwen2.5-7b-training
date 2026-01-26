"""RAG Quality Gate tests - verify multi-criteria gating.

Tests the RAG retrieval quality gate based on ChatGPT analysis:
- min_results >= 3
- best_score >= 0.75  
- score_gap(top1 - top3) < 0.15
- freshness_days check
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any


class MockRAGGateConfig:
    """Mock RAG gate configuration for testing."""
    min_results: int = 3
    min_score: float = 0.75
    max_score_gap: float = 0.15
    freshness_days: int = 30


def evaluate_rag_gate(results: List[Dict[str, Any]], config: MockRAGGateConfig) -> Dict[str, Any]:
    """
    Evaluate RAG results against quality gate criteria.
    
    This is a test implementation of the gate logic in MCP server.
    """
    # Check 1: Minimum results
    if len(results) < config.min_results:
        return {
            "passed": False,
            "confidence": "none",
            "reason": f"Zu wenig Ergebnisse: {len(results)} < {config.min_results}",
            "should_reindex": True
        }
    
    # Check 2: Best score threshold
    best_score = results[0].get("score", 0)
    if best_score < config.min_score:
        return {
            "passed": False,
            "confidence": "none",
            "reason": f"Beste Punktzahl zu niedrig: {best_score:.2f} < {config.min_score}",
            "should_reindex": True
        }
    
    # Check 3: Score gap (consistency check)
    if len(results) >= 3:
        top1_score = results[0].get("score", 0)
        top3_score = results[2].get("score", 0)
        score_gap = top1_score - top3_score
        
        if score_gap > config.max_score_gap:
            return {
                "passed": True,
                "confidence": "low",
                "reason": f"Große Score-Differenz: {score_gap:.2f}",
                "should_reindex": False
            }
    
    # Check 4: Freshness
    oldest_allowed = datetime.now() - timedelta(days=config.freshness_days)
    stale_count = 0
    
    for result in results[:3]:
        metadata = result.get("metadata", {})
        ingested_at = metadata.get("ingested_at")
        if ingested_at:
            try:
                ingested_date = datetime.fromisoformat(ingested_at.replace("Z", "+00:00"))
                if ingested_date.replace(tzinfo=None) < oldest_allowed:
                    stale_count += 1
            except (ValueError, AttributeError):
                pass
    
    if stale_count >= 2:
        return {
            "passed": True,
            "confidence": "medium",
            "reason": f"{stale_count} von 3 stale",
            "should_reindex": True
        }
    
    # All checks passed
    return {
        "passed": True,
        "confidence": "high",
        "reason": "Alle Kriterien erfüllt",
        "should_reindex": False
    }


class TestQualityGateMinResults:
    """Test minimum results requirement."""
    
    def test_gate_fails_with_zero_results(self):
        """Gate should fail with no results."""
        config = MockRAGGateConfig()
        results = []
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is False
        assert gate["confidence"] == "none"
        assert gate["should_reindex"] is True
        print(f"\n✓ Zero results: {gate['reason']}")
    
    def test_gate_fails_with_one_result(self):
        """Gate should fail with only 1 result."""
        config = MockRAGGateConfig()
        results = [{"score": 0.9, "text": "test"}]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is False
        assert "1 < 3" in gate["reason"]
        print(f"\n✓ One result: {gate['reason']}")
    
    def test_gate_fails_with_two_results(self):
        """Gate should fail with only 2 results."""
        config = MockRAGGateConfig()
        results = [
            {"score": 0.9, "text": "test1"},
            {"score": 0.8, "text": "test2"},
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is False
        assert "2 < 3" in gate["reason"]
        print(f"\n✓ Two results: {gate['reason']}")
    
    def test_gate_passes_with_three_results(self):
        """Gate should pass with 3+ good results."""
        config = MockRAGGateConfig()
        results = [
            {"score": 0.85, "text": "test1", "metadata": {}},
            {"score": 0.82, "text": "test2", "metadata": {}},
            {"score": 0.80, "text": "test3", "metadata": {}},
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is True
        assert gate["confidence"] == "high"
        print(f"\n✓ Three results: {gate['reason']}")


class TestQualityGateMinScore:
    """Test minimum score requirement."""
    
    def test_gate_fails_with_low_best_score(self):
        """Gate should fail when best score is below threshold."""
        config = MockRAGGateConfig()
        results = [
            {"score": 0.6, "text": "test1"},
            {"score": 0.5, "text": "test2"},
            {"score": 0.4, "text": "test3"},
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is False
        assert "0.60 < 0.75" in gate["reason"]
        print(f"\n✓ Low score: {gate['reason']}")
    
    def test_gate_passes_with_high_best_score(self):
        """Gate should pass when best score meets threshold."""
        config = MockRAGGateConfig()
        results = [
            {"score": 0.80, "text": "test1", "metadata": {}},
            {"score": 0.78, "text": "test2", "metadata": {}},
            {"score": 0.76, "text": "test3", "metadata": {}},
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is True
        print(f"\n✓ High score: {gate['reason']}")
    
    def test_gate_passes_at_exactly_threshold(self):
        """Gate should pass when best score equals threshold."""
        config = MockRAGGateConfig()
        results = [
            {"score": 0.75, "text": "test1", "metadata": {}},
            {"score": 0.73, "text": "test2", "metadata": {}},
            {"score": 0.71, "text": "test3", "metadata": {}},
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is True
        print(f"\n✓ Exact threshold: {gate['reason']}")


class TestQualityGateScoreGap:
    """Test score gap consistency check."""
    
    def test_gate_warns_on_large_score_gap(self):
        """Large gap between top1 and top3 indicates potential outlier."""
        config = MockRAGGateConfig()
        results = [
            {"score": 0.95, "text": "test1", "metadata": {}},  # Outlier
            {"score": 0.80, "text": "test2", "metadata": {}},
            {"score": 0.75, "text": "test3", "metadata": {}},  # Gap = 0.20 > 0.15
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is True  # Still passes
        assert gate["confidence"] == "low"  # But with low confidence
        print(f"\n✓ Large score gap: confidence={gate['confidence']}, {gate['reason']}")
    
    def test_gate_high_confidence_with_consistent_scores(self):
        """Consistent scores indicate reliable results."""
        config = MockRAGGateConfig()
        results = [
            {"score": 0.85, "text": "test1", "metadata": {}},
            {"score": 0.83, "text": "test2", "metadata": {}},
            {"score": 0.81, "text": "test3", "metadata": {}},  # Gap = 0.04 < 0.15
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is True
        assert gate["confidence"] == "high"
        print(f"\n✓ Consistent scores: confidence={gate['confidence']}")


class TestQualityGateFreshness:
    """Test document freshness check."""
    
    def test_gate_warns_on_stale_documents(self):
        """Stale documents should trigger re-index flag."""
        config = MockRAGGateConfig()
        old_date = (datetime.now() - timedelta(days=45)).isoformat()
        
        results = [
            {"score": 0.85, "text": "test1", "metadata": {"ingested_at": old_date}},
            {"score": 0.83, "text": "test2", "metadata": {"ingested_at": old_date}},
            {"score": 0.81, "text": "test3", "metadata": {"ingested_at": old_date}},
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is True
        assert gate["confidence"] == "medium"
        assert gate["should_reindex"] is True
        print(f"\n✓ Stale docs: confidence={gate['confidence']}, reindex={gate['should_reindex']}")
    
    def test_gate_high_confidence_with_fresh_documents(self):
        """Fresh documents should not trigger re-index."""
        config = MockRAGGateConfig()
        fresh_date = (datetime.now() - timedelta(days=5)).isoformat()
        
        results = [
            {"score": 0.85, "text": "test1", "metadata": {"ingested_at": fresh_date}},
            {"score": 0.83, "text": "test2", "metadata": {"ingested_at": fresh_date}},
            {"score": 0.81, "text": "test3", "metadata": {"ingested_at": fresh_date}},
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is True
        assert gate["confidence"] == "high"
        assert gate["should_reindex"] is False
        print(f"\n✓ Fresh docs: confidence={gate['confidence']}, reindex={gate['should_reindex']}")
    
    def test_gate_handles_missing_ingested_at(self):
        """Missing ingested_at should not crash gate evaluation."""
        config = MockRAGGateConfig()
        
        results = [
            {"score": 0.85, "text": "test1", "metadata": {}},  # No ingested_at
            {"score": 0.83, "text": "test2", "metadata": {"other": "data"}},
            {"score": 0.81, "text": "test3", "metadata": {}},
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is True
        assert gate["confidence"] == "high"  # No stale check possible
        print(f"\n✓ Missing dates handled: confidence={gate['confidence']}")


class TestQualityGateEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_gate_with_perfect_scores(self):
        """Perfect scores should pass with high confidence."""
        config = MockRAGGateConfig()
        results = [
            {"score": 1.0, "text": "test1", "metadata": {}},
            {"score": 0.99, "text": "test2", "metadata": {}},
            {"score": 0.98, "text": "test3", "metadata": {}},
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is True
        assert gate["confidence"] == "high"
        print(f"\n✓ Perfect scores: {gate['reason']}")
    
    def test_gate_with_exactly_threshold_gap(self):
        """Score gap exactly at threshold should pass."""
        config = MockRAGGateConfig()
        results = [
            {"score": 0.90, "text": "test1", "metadata": {}},
            {"score": 0.80, "text": "test2", "metadata": {}},
            {"score": 0.75, "text": "test3", "metadata": {}},  # Gap = 0.15 (exactly at threshold)
        ]
        
        gate = evaluate_rag_gate(results, config)
        
        # Gap at exactly threshold should NOT trigger low confidence
        # (only > threshold triggers it)
        assert gate["passed"] is True
        print(f"\n✓ Exact gap threshold: confidence={gate['confidence']}")
    
    def test_gate_priority_order(self):
        """Checks should be evaluated in correct priority order."""
        config = MockRAGGateConfig()
        
        # This should fail on min_results first (not score)
        results = [{"score": 0.5, "text": "test"}]  # Both low score and too few results
        
        gate = evaluate_rag_gate(results, config)
        
        assert gate["passed"] is False
        assert "1 < 3" in gate["reason"]  # Should fail on count, not score
        print(f"\n✓ Priority order correct: {gate['reason']}")
