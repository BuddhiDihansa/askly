"""Deterministic reranking hooks for the retrieval candidate pool."""

import re


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"\w+", value.casefold()))


def rerank(query: str, candidates: list[dict], final_k: int) -> list[dict]:
    query_terms = _tokens(query)
    ranked: list[dict] = []
    for candidate in candidates:
        metadata = " ".join(
            str(candidate.get(field) or "")
            for field in ("chapter", "section", "topic", "content_type", "concepts")
        )
        metadata_match = len(query_terms & _tokens(metadata)) / max(len(query_terms), 1)
        exact_match = len(query_terms & _tokens(candidate.get("text", ""))) / max(len(query_terms), 1)
        item = dict(candidate)
        item["rerank_score"] = round(
            float(candidate.get("hybrid_score", candidate.get("score", 0.0)))
            + 0.05 * metadata_match
            + 0.05 * exact_match,
            6,
        )
        ranked.append(item)

    ranked.sort(key=lambda item: (-item["rerank_score"], str(item.get("chunk_id", ""))))
    selected: list[dict] = []
    for candidate in ranked:
        candidate_terms = _tokens(candidate.get("text", ""))
        redundant = any(
            len(candidate_terms & _tokens(existing.get("text", "")))
            / max(len(candidate_terms | _tokens(existing.get("text", ""))), 1) >= 0.85
            for existing in selected
        )
        if not redundant:
            selected.append(candidate)
        if len(selected) >= final_k:
            break
    return selected