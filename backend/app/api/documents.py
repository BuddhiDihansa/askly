"""
Document upload + chunking for RAG (see app/services/retrieval.py for
how these chunks get searched later).
"""
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
from app.db.mongo import chunks, documents
from app.services.embeddings import encode

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
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    raw = await file.read()

    # SECURITY/COST FIX: reject oversized uploads before doing any expensive
    # work (parsing, embedding). Without this, a huge file could exhaust
    # memory or run up embedding-model compute for no legitimate reason.
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_mb}MB limit")

    try:
        reader = PdfReader(io.BytesIO(raw))
    except PdfReadError:
        raise HTTPException(status_code=400, detail="This file could not be read as a PDF")

    pieces = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        for chunk_index, chunk_text in enumerate(split_text(page_text)):
            pieces.append({"text": chunk_text, "page": page_number, "chunk": chunk_index})

    if not pieces:
        raise HTTPException(status_code=400, detail="No readable text found in PDF")

    vectors = encode([p["text"] for p in pieces])
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    user_id = str(current["_id"])

    doc_result = await documents.insert_one({
        "user_id": user_id,
        "filename": file.filename,
        "pages": len(reader.pages),
        "chunks": len(pieces),
        "created_at": now,
    })

    await chunks.insert_many([
        {**piece, "embedding": vector, "document_id": str(doc_result.inserted_id),
         "user_id": user_id, "filename": file.filename}
        for piece, vector in zip(pieces, vectors)
    ])

    return {
        "id": str(doc_result.inserted_id),
        "filename": file.filename,
        "pages": len(reader.pages),
        "chunks": len(pieces),
    }


@router.get("")
async def list_documents(current: dict = Depends(current_user)):
    cursor = documents.find({"user_id": str(current["_id"])}).sort("created_at", -1)
    docs = await cursor.to_list(100)
    return [
        {"id": str(d["_id"]), "filename": d["filename"], "pages": d["pages"],
         "chunks": d["chunks"], "created_at": d["created_at"]}
        for d in docs
    ]


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, current: dict = Depends(current_user)):
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
