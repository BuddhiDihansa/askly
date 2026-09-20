"""Structured retrieval contract and bounded context assembly."""

import time

from app.core.config import settings
from app.services.reranker import rerank
from app.services.retrieval import hybrid_retrieve, normalize_query

_cache: dict[tuple, tuple[float, dict]] = {}
_CACHE_TTL_SECONDS = 30
_CACHE_MAX_ENTRIES = 256


def _quality(results: list[dict]) -> str:
    if not results:
        return "insufficient"
    strongest = max(float(item.get("relevance_score", 0.0)) for item in results)
    if strongest >= 0.55 and len(results) >= 2:
        return "strong"
    if strongest >= 0.3:
        return "moderate"
    return "weak"


def build_context(results: list[dict], max_chars: int | None = None) -> str:
    limit = max_chars or settings.rag_context_max_chars
    blocks: list[str] = []
    used = 0
    for index, result in enumerate(results, start=1):
        block = (
            f"[Source {index}]\n"
            f"Document: {result.get('filename', 'Uploaded document')}\n"
            f"Page: {result.get('page_start', result.get('page', 1))}"
            f"-{result.get('page_end', result.get('page', 1))}\n"
            f"Chapter: {result.get('chapter') or 'Unspecified'}\n"
            f"Section: {result.get('section') or 'Unspecified'}\n"
            f"Topic: {result.get('topic') or 'Unspecified'}\n\n"
            f"{result.get('text', '')}"
        )
        if used + len(block) > limit:
            break
        blocks.append(block)
        used += len(block) + 2
    return "\n\n".join(blocks)


async def retrieve(user_id: str, query: str, filters: dict | None = None) -> dict:
    normalized = normalize_query(query)
    cache_key = (user_id, normalized, tuple(sorted((filters or {}).items())))
    cached = _cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < _CACHE_TTL_SECONDS:
        return dict(cached[1])
    candidates = await hybrid_retrieve(
        user_id,
        normalized,
        top_k=max(settings.rag_candidate_pool_size, settings.rag_final_k),
        filters=filters,
    ) if normalized else []
    results = rerank(normalized, candidates, settings.rag_final_k)
    sources = [
        {
            "source_type": "document",
            "filename": result.get("filename"),
            "page": result.get("page", result.get("page_start", 1)),
            "page_start": result.get("page_start", result.get("page", 1)),
            "page_end": result.get("page_end", result.get("page", 1)),
            "chapter": result.get("chapter"),
            "section": result.get("section"),
            "topic": result.get("topic"),
            "relevance_score": result.get("relevance_score", result.get("score", 0.0)),
        }
        for result in results
    ]
    result = {
        "query": query,
        "normalized_query": normalized,
        "results": results,
        "context": build_context(results),
        "sources": sources,
        "document_grounded": True,
        "retrieval_metadata": {
            "candidate_count": len(candidates),
            "result_count": len(results),
            "evidence_quality": _quality(results),
        },
    }
    if len(_cache) >= _CACHE_MAX_ENTRIES:
        _cache.pop(next(iter(_cache)))
    _cache[cache_key] = (time.monotonic(), result)
    return result