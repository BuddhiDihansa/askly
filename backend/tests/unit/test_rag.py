from app.services.rag import build_context
from app.services.reranker import rerank


def test_context_preserves_source_metadata_and_limit():
    result = build_context([
        {
            "filename": "physics.pdf", "page_start": 84, "page_end": 85,
            "chapter": "Newton's Laws", "section": "Second law", "topic": "Force",
            "text": "F = ma",
        },
    ], max_chars=1000)
    assert "[Source 1]" in result
    assert "Page: 84-85" in result
    assert "Newton's Laws" in result


def test_reranker_suppresses_near_duplicate_chunks():
    candidates = [
        {"chunk_id": "1", "text": "force equals mass times acceleration", "hybrid_score": 0.8},
        {"chunk_id": "2", "text": "force equals mass times acceleration", "hybrid_score": 0.7},
        {"chunk_id": "3", "text": "momentum is mass times velocity", "hybrid_score": 0.6},
    ]
    ranked = rerank("force", candidates, final_k=3)
    assert [item["chunk_id"] for item in ranked] == ["1", "3"]