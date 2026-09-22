from fastapi import APIRouter, Depends

from app.api.dependencies import admin_user
from app.db.mongo import get_documents_collection, get_quiz_attempts_collection, get_users_collection

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
async def stats(_: dict = Depends(admin_user)):
    users = get_users_collection()
    documents = get_documents_collection()
    quizzes = get_quiz_attempts_collection()
    return {
        "users": await users.count_documents({}),
        "documents": await documents.count_documents({}),
        "completed_documents": await documents.count_documents({"status": "completed"}),
        "quiz_attempts": await quizzes.count_documents({}),
        "submitted_quizzes": await quizzes.count_documents({"submitted_at": {"$exists": True}}),
    }