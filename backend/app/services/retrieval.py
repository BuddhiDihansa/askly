"""
Hybrid retrieval: combines two different search strategies and fuses
their rankings, because each strategy is good at catching things the
other misses.

- Semantic search (embeddings + cosine similarity): finds chunks that
  mean the same thing as the query, even with different wording
  (e.g. query "car" matches a chunk about "automobile").
- Lexical search (BM25, a classic keyword-ranking algorithm): finds
  chunks that share the query's exact words - important for things
  semantic search is weak at, like specific names, codes, or numbers.

The two rankings are min-max normalized and combined with configurable
semantic and lexical weights, keeping both meaning-based and exact-term
matches useful for study questions.
"""
import re
import unicodedata

from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.db.mongo import get_chunks_collection
from app.services.embeddings import cosine, encode

def normalize_query(query: str) -> str:
    normalized = unicodedata.normalize("NFKC", query or "")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return re.sub(r"([!?.,])\1+", r"\1", normalized)


async def hybrid_retrieve(
    user_id: str,
    query: str,
    top_k: int = 6,
    filters: dict | None = None,
) -> list[dict]:
    """Returns the `top_k` most relevant chunks for `query`, scoped to
    this user's own uploaded documents only."""
    chunks = get_chunks_collection()
    query_filter = {"user_id": user_id}
    for field, value in (filters or {}).items():
        if value is not None and field in {"document_id", "chapter", "section", "topic", "content_type"}:
            query_filter[field] = value
    if filters and filters.get("page_min") is not None:
        query_filter["page_end"] = {"$gte": filters["page_min"]}
    if filters and filters.get("page_max") is not None:
        query_filter["page_start"] = {"$lte": filters["page_max"]}
    user_chunks = await chunks.find(query_filter).to_list(length=5000)
    if not user_chunks:
        return []

    # --- semantic ranking ---
    query_vector = encode([query])[0]
    semantic_scored = [(cosine(query_vector, c["embedding"]), c) for c in user_chunks if c.get("embedding")]
    semantic_scored.sort(key=lambda pair: pair[0], reverse=True)

    # --- lexical (keyword) ranking ---
    tokenized_chunks = [re.findall(r"\w+", c.get("text", "").casefold()) for c in user_chunks]
    bm25 = BM25Okapi(tokenized_chunks)
    lexical_scores = bm25.get_scores(re.findall(r"\w+", query.casefold()))
    lexical_scored = sorted(zip(lexical_scores, user_chunks), key=lambda pair: pair[0], reverse=True)

    # Normalize both score families before combining them.
    candidates: dict[str, tuple[float, dict]] = {}
    pool_size = settings.rag_candidate_pool_size
    pool = semantic_scored[:pool_size] + lexical_scored[:pool_size]
    semantic_values = [score for score, _ in semantic_scored]
    lexical_values = [score for score, _ in lexical_scored]

    def scale(value: float, values: list[float]) -> float:
        if not values or max(values) == min(values):
            return 1.0 if value > 0 else 0.0
        return (value - min(values)) / (max(values) - min(values))

    for _, chunk in pool:
        key = str(chunk["_id"])
        semantic_score = next((score for score, item in semantic_scored if str(item["_id"]) == key), 0.0)
        lexical_score = next((score for score, item in lexical_scored if str(item["_id"]) == key), 0.0)
        hybrid_score = (
            settings.rag_semantic_weight * scale(semantic_score, semantic_values)
            + settings.rag_lexical_weight * scale(lexical_score, lexical_values)
        )
        candidates[key] = (hybrid_score, chunk)

    ranked = sorted(candidates.values(), key=lambda pair: pair[0], reverse=True)[:top_k]

    return [
        {
            "chunk_id": str(chunk.get("_id")),
            "document_id": chunk.get("document_id"),
            "user_id": chunk.get("user_id"),
            "text": chunk["text"],
            "filename": chunk["filename"],
            "page": chunk.get("page", 1),
            "page_start": chunk.get("page_start", chunk.get("page", 1)),
            "page_end": chunk.get("page_end", chunk.get("page", 1)),
            "chapter": chunk.get("chapter"),
            "section": chunk.get("section"),
            "topic": chunk.get("topic"),
            "concepts": chunk.get("concepts", []),
            "content_type": chunk.get("content_type"),
            "hybrid_score": round(score, 4),
            "relevance_score": round(score, 4),
            "score": round(score, 4),
        }
        for score, chunk in ranked
    ]
