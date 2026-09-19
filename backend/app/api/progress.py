from fastapi import APIRouter, Depends

from app.api.dependencies import current_user
from app.db.mongo import (
    get_conversations_collection,
    get_documents_collection,
    get_quiz_attempts_collection,
)
from app.services.mastery import get_mastery

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("")
async def progress(current: dict = Depends(current_user)):
    user_id = str(current["_id"])
    conversations = get_conversations_collection()
    documents = get_documents_collection()
    quiz_attempts = get_quiz_attempts_collection()

    mastery_levels = await get_mastery(user_id)
    quizzes_completed = await quiz_attempts.count_documents({"user_id": user_id, "submitted_at": {"$exists": True}})
    documents_uploaded = await documents.count_documents({"user_id": user_id})
    conversations_started = await conversations.count_documents({"user_id": user_id})

    return {
        "mastery": mastery_levels,
        "stats": {
            "quizzes": quizzes_completed,
            "documents": documents_uploaded,
            "conversations": conversations_started,
        },
    }
