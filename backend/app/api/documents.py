"""
Document upload + chunking for RAG (see app/services/retrieval.py for
how these chunks get searched later).
"""
import asyncio
import datetime
import io
import re

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.api.dependencies import current_user
from app.core.config import settings
from app.db.mongo import get_chunks_collection, get_documents_collection
from app.services.embeddings import encode
from app.services.document_intelligence import (
    DocumentProcessingError,
    analyze_pages,
    build_chunks,
    extract_pages,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])

CHUNK_SIZE = 900       # characters per chunk - big enough for context, small enough to stay focused
CHUNK_OVERLAP = 120    # characters shared between consecutive chunks, so a sentence that gets
                       # cut at a chunk boundary still appears whole in at least one chunk


def split_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Splits `text` into overlapping chunks, preferring to break on a
    sentence or word boundary (not mid-word) where possible."""
    text = re.sub(r"\s+", " ", text).strip()
    pieces = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        piece = text[start:end]
        if end < len(text):
            # try to end this chunk at a sentence (". ") or word boundary
            # instead of cutting a word in half
            boundary = max(piece.rfind(". "), piece.rfind(" "))
            end = start + max(boundary, 400)  # never make a chunk smaller than 400 chars
            piece = text[start:end]
        if piece.strip():
            pieces.append(piece.strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)  # +1 guarantees forward progress even if overlap >= chunk
    return pieces


@router.post("/upload")
async def upload(file: UploadFile = File(...), current: dict = Depends(current_user)):
    chunks = get_chunks_collection()
    documents = get_documents_collection()
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    raw = await file.read()

    # SECURITY/COST FIX: reject oversized uploads before doing any expensive
    # work (parsing, embedding). Without this, a huge file could exhaust
    # memory or run up embedding-model compute for no legitimate reason.
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_mb}MB limit")

    user_id = str(current["_id"])
    now = datetime.datetime.now(datetime.timezone.utc)
    doc_result = await documents.insert_one({
        "user_id": user_id,
        "filename": file.filename,
        "status": "uploaded",
        "pages": 0,
        "chunks": 0,
        "processing_error": None,
        "created_at": now,
        "updated_at": now,
    })

    document_id = doc_result.inserted_id
    try:
        await documents.update_one(
            {"_id": document_id, "user_id": user_id},
            {"$set": {"status": "extracting", "processing_started_at": datetime.datetime.now(datetime.timezone.utc)}},
        )
        reader = PdfReader(io.BytesIO(raw))
        pages = extract_pages(reader)
        await documents.update_one(
            {"_id": document_id, "user_id": user_id},
            {"$set": {"status": "processing", "pages": len(reader.pages)}},
        )
        units, chapters = analyze_pages(pages)
        pieces = build_chunks(units)
        if not pieces:
            raise DocumentProcessingError("No learning content could be created from this PDF")

        # embedding a whole PDF is slow CPU work: run it in a worker thread so
        # other users' requests are not frozen while this upload is processed
        vectors = await asyncio.to_thread(encode, [piece["text"] for piece in pieces])
        created_at = datetime.datetime.now(datetime.timezone.utc)
        chunk_documents = [
            {
                **piece,
                "chunk": piece["source_order"],
                "embedding": vector,
                "document_id": str(document_id),
                "user_id": user_id,
                "filename": file.filename,
                "created_at": created_at,
            }
            for piece, vector in zip(pieces, vectors)
        ]
        await chunks.insert_many(chunk_documents)

        stored_count = await chunks.count_documents({"document_id": str(document_id), "user_id": user_id})
        if stored_count != len(chunk_documents):
            raise DocumentProcessingError("Document chunks failed validation")

        await documents.update_one(
            {"_id": document_id, "user_id": user_id},
            {"$set": {
                "status": "completed",
                "pages": len(reader.pages),
                "chunks": stored_count,
                "chapters": chapters,
                "topics": sorted({unit.topic for unit in units if unit.topic}),
                "processing_completed_at": datetime.datetime.now(datetime.timezone.utc),
                "updated_at": datetime.datetime.now(datetime.timezone.utc),
            }},
        )
    except (PdfReadError, DocumentProcessingError):
        await chunks.delete_many({"document_id": str(document_id), "user_id": user_id})
        await documents.update_one(
            {"_id": document_id, "user_id": user_id},
            {"$set": {
                "status": "failed",
                "processing_error": "This PDF could not be processed into readable learning content.",
                "updated_at": datetime.datetime.now(datetime.timezone.utc),
            }},
        )
        raise HTTPException(status_code=400, detail="This PDF could not be processed into readable learning content")
    except Exception:
        await chunks.delete_many({"document_id": str(document_id), "user_id": user_id})
        await documents.update_one(
            {"_id": document_id, "user_id": user_id},
            {"$set": {
                "status": "failed",
                "processing_error": "Document processing failed. Please try again.",
                "updated_at": datetime.datetime.now(datetime.timezone.utc),
            }},
        )
        raise HTTPException(status_code=422, detail="Document processing failed. Please try again.")

    return {
        "id": str(document_id),
        "filename": file.filename,
        "pages": len(reader.pages),
        "chunks": stored_count,
        "status": "completed",
        "chapters": chapters,
        "topics": sorted({unit.topic for unit in units if unit.topic}),
    }


@router.get("")
async def list_documents(current: dict = Depends(current_user)):
    documents = get_documents_collection()
    cursor = documents.find({"user_id": str(current["_id"])}).sort("created_at", -1)
    docs = await cursor.to_list(100)
    return [
        {"id": str(d["_id"]), "filename": d["filename"], "pages": d.get("pages", 0),
         "chunks": d.get("chunks", 0), "status": d.get("status", "completed"),
         "processing_error": d.get("processing_error"), "chapters": d.get("chapters", []),
         "topics": d.get("topics", []), "created_at": d["created_at"]}
        for d in docs
    ]


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, current: dict = Depends(current_user)):
    chunks = get_chunks_collection()
    documents = get_documents_collection()
    try:
        doc_oid = ObjectId(doc_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid document id")

    user_id = str(current["_id"])
    await chunks.delete_many({"document_id": doc_id, "user_id": user_id})
    result = await documents.delete_one({"_id": doc_oid, "user_id": user_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"ok": True}
