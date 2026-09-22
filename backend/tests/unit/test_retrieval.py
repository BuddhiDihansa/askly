import pytest

from app.db.mongo import get_chunks_collection
from app.services.retrieval import hybrid_retrieve, normalize_query


async def _insert_chunk(user_id, text, filename="doc.pdf", page=1, embedding=None):
    chunks = get_chunks_collection()
    await chunks.insert_one({
        "user_id": user_id,
        "text": text,
        "filename": filename,
        "page": page,
        # a real embedding would come from the sentence-transformer model;
        # here we hand-craft simple unit vectors so we can control exactly
        # how "semantically similar" each chunk is to the query, without
        # needing to download the real (large) embedding model in tests
        "embedding": embedding or [1.0, 0.0, 0.0],
    })


@pytest.mark.asyncio
async def test_no_documents_returns_empty_list(monkeypatch):
    async def fake_encode(texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    import app.services.retrieval as retrieval_module
    monkeypatch.setattr(retrieval_module, "encode", fake_encode)

    results = await hybrid_retrieve("user-with-no-docs", "any query")
    assert results == []


@pytest.mark.asyncio
async def test_keyword_match_ranks_above_unrelated_chunk(monkeypatch):
    def fake_encode(texts):
        # pretend every chunk/query has the same "meaning" (identical vector)
        # so this test isolates the *lexical* (BM25 keyword) half of the
        # fusion, rather than mixing in semantic scoring too. Sync, not
        # async - the real encode() is a plain sync function.
        return [[1.0, 0.0, 0.0] for _ in texts]

    import app.services.retrieval as retrieval_module
    monkeypatch.setattr(retrieval_module, "encode", fake_encode)

    user_id = "keyword-test-user"
    await _insert_chunk(user_id, "Photosynthesis converts sunlight into chemical energy in plants")
    await _insert_chunk(user_id, "The stock market closed higher today on strong earnings")

    results = await hybrid_retrieve(user_id, "photosynthesis sunlight energy", top_k=2)

    assert len(results) == 2
    assert "Photosynthesis" in results[0]["text"]


@pytest.mark.asyncio
async def test_results_are_scoped_to_the_requesting_user(monkeypatch):
    def fake_encode(texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    import app.services.retrieval as retrieval_module
    monkeypatch.setattr(retrieval_module, "encode", fake_encode)

    await _insert_chunk("user-a", "user A's private notes about biology")
    await _insert_chunk("user-b", "user B's private notes about chemistry")

    results = await hybrid_retrieve("user-a", "notes", top_k=5)

    # user A must never see user B's chunks, even if they'd score well
    assert all("user A" in r["text"] for r in results)


def test_query_normalization_preserves_meaning():
    assert normalize_query("  What   is Newton's 2nd law???  ") == "What is Newton's 2nd law?"
    assert normalize_query("  ") == ""


@pytest.mark.asyncio
async def test_metadata_filter_remains_scoped_to_user(monkeypatch):
    def fake_encode(texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    import app.services.retrieval as retrieval_module
    monkeypatch.setattr(retrieval_module, "encode", fake_encode)

    chunks = get_chunks_collection()
    await chunks.insert_one({
        "user_id": "user-a", "document_id": "doc-a", "text": "private chapter text",
        "filename": "a.pdf", "chapter": "Chapter 3", "embedding": [1.0, 0.0, 0.0],
    })
    await chunks.insert_one({
        "user_id": "user-b", "document_id": "doc-a", "text": "other chapter text",
        "filename": "b.pdf", "chapter": "Chapter 3", "embedding": [1.0, 0.0, 0.0],
    })

    results = await hybrid_retrieve("user-a", "chapter", filters={"chapter": "Chapter 3"})
    assert len(results) == 1
    assert results[0]["document_id"] == "doc-a"
    assert results[0]["user_id"] == "user-a"
