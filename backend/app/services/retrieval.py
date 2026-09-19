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

The two rankings are merged with Reciprocal Rank Fusion (RRF): each
chunk gets a score based on its *rank position* in each list (not the
raw score, since BM25 scores and cosine scores live on different
scales and can't be compared directly). A chunk ranked #1 by both
methods scores highest; a chunk that only one method found still gets
some credit.
"""
from rank_bm25 import BM25Okapi

from app.db.mongo import chunks
from app.services.embeddings import encode, cosine

# RRF damping constant. 60 is the standard value from the original RRF
# paper (Cormack et al., 2009) - it just softens the impact of rank
# position so #1 vs #2 isn't wildly more important than #20 vs #21.
RRF_K = 60

# How much weight semantic vs. lexical ranking gets in the fused score.
# Weighted slightly toward semantic search (0.6) because for a study
# assistant, matching the *meaning* of a student's question usually
# matters more than matching its exact wording (0.4).
SEMANTIC_WEIGHT = 0.6
LEXICAL_WEIGHT = 0.4

# Only the top N results from each method are considered candidates for
# the final fused ranking - this keeps things fast and is standard
# practice, since a chunk ranked #500 by a method is never going to win.
CANDIDATE_POOL_SIZE = 30


async def hybrid_retrieve(user_id: str, query: str, top_k: int = 6) -> list[dict]:
    """Returns the `top_k` most relevant chunks for `query`, scoped to
    this user's own uploaded documents only."""
    user_chunks = await chunks.find({"user_id": user_id}).to_list(length=5000)
    if not user_chunks:
        return []

    # --- semantic ranking ---
    query_vector = encode([query])[0]
    semantic_scored = [(cosine(query_vector, c["embedding"]), c) for c in user_chunks]
    semantic_scored.sort(key=lambda pair: pair[0], reverse=True)
    semantic_rank = {str(c["_id"]): rank for rank, (_, c) in enumerate(semantic_scored)}

    # --- lexical (keyword) ranking ---
    tokenized_chunks = [c["text"].lower().split() for c in user_chunks]
    bm25 = BM25Okapi(tokenized_chunks)
    lexical_scores = bm25.get_scores(query.lower().split())
    lexical_scored = sorted(zip(lexical_scores, user_chunks), key=lambda pair: pair[0], reverse=True)
    lexical_rank = {str(c["_id"]): rank for rank, (_, c) in enumerate(lexical_scored)}

    # --- fuse the two rankings with RRF ---
    candidates: dict[str, tuple[float, dict]] = {}
    pool = semantic_scored[:CANDIDATE_POOL_SIZE] + lexical_scored[:CANDIDATE_POOL_SIZE]
    for _, chunk in pool:
        key = str(chunk["_id"])
        # a chunk missing from one list (rank 999 = "effectively last")
        # still gets some credit from the list it *does* appear in
        rrf_score = (
            SEMANTIC_WEIGHT / (RRF_K + semantic_rank.get(key, 999))
            + LEXICAL_WEIGHT / (RRF_K + lexical_rank.get(key, 999))
        )
        candidates[key] = (rrf_score, chunk)

    ranked = sorted(candidates.values(), key=lambda pair: pair[0], reverse=True)[:top_k]

    return [
        {
            "text": chunk["text"],
            "filename": chunk["filename"],
            "page": chunk.get("page", 1),
            "score": round(score, 4),
        }
        for score, chunk in ranked
    ]
