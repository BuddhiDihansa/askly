from datetime import datetime, timedelta, timezone
from typing import Literal

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import current_user
from app.db.mongo import get_flashcards_collection
from app.services.rag import retrieve

router = APIRouter(prefix="/api/flashcards", tags=["flashcards"])


class FlashcardGenerateRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=120)
    count: int = Field(default=5, ge=1, le=20)


class FlashcardReviewRequest(BaseModel):
    rating: Literal["again", "hard", "good", "easy"]


def _schedule(card: dict, rating: str) -> tuple[int, float]:
    interval = int(card.get("interval", 0))
    ease = float(card.get("ease", 2.5))
    if rating == "again":
        return 0, max(1.3, ease - 0.2)
    if rating == "hard":
        return max(1, round(interval * 1.2)), max(1.3, ease - 0.05)
    if rating == "easy":
        return max(2, round(max(interval, 1) * ease * 1.35)), ease + 0.15
    return max(1, round(max(interval, 1) * ease)), ease


def _public(card: dict) -> dict:
    return {
        "id": str(card["_id"]),
        "front": card["front"],
        "back": card["back"],
        "topic": card.get("topic"),
        "source": card.get("source"),
        "due_at": card.get("due_at"),
        "interval": card.get("interval", 0),
        "repetitions": card.get("repetitions", 0),
    }


@router.post("/generate")
async def generate(payload: FlashcardGenerateRequest, current: dict = Depends(current_user)):
    user_id = str(current["_id"])
    rag = await retrieve(user_id, payload.topic)
    if not rag["results"]:
        raise HTTPException(status_code=404, detail="No document evidence found for this topic")
    cards = get_flashcards_collection()
    created = []
    now = datetime.now(timezone.utc)
    for result in rag["results"][:payload.count]:
        card = {
            "user_id": user_id,
            "front": f"What should you remember about {payload.topic}?",
            "back": result["text"].strip()[:1200],
            "topic": payload.topic,
            "source": {"source_type": "document", "filename": result.get("filename"), "page": result.get("page", 1)},
            "due_at": now,
            "interval": 0,
            "ease": 2.5,
            "repetitions": 0,
            "created_at": now,
        }
        inserted = await cards.insert_one(card)
        card["_id"] = inserted.inserted_id
        created.append(_public(card))
    return {"cards": created, "evidence_quality": rag["retrieval_metadata"]["evidence_quality"]}


@router.get("")
async def list_flashcards(due_only: bool = False, current: dict = Depends(current_user)):
    query = {"user_id": str(current["_id"])}
    if due_only:
        query["due_at"] = {"$lte": datetime.now(timezone.utc)}
    cards = await get_flashcards_collection().find(query).sort("due_at", 1).to_list(100)
    return [_public(card) for card in cards]


@router.post("/{card_id}/review")
async def review(card_id: str, payload: FlashcardReviewRequest, current: dict = Depends(current_user)):
    try:
        object_id = ObjectId(card_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid flashcard id")
    user_id = str(current["_id"])
    cards = get_flashcards_collection()
    card = await cards.find_one({"_id": object_id, "user_id": user_id})
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    interval, ease = _schedule(card, payload.rating)
    now = datetime.now(timezone.utc)
    due_at = now + timedelta(days=interval)
    await cards.update_one(
        {"_id": object_id, "user_id": user_id},
        {"$set": {"interval": interval, "ease": ease, "due_at": due_at, "updated_at": now}, "$inc": {"repetitions": 1}},
    )
    updated = {**card, "interval": interval, "ease": ease, "due_at": due_at, "repetitions": card.get("repetitions", 0) + 1}
    return _public(updated)