from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import current_user
from app.core.config import settings
from app.core.rate_limit import check_rate_limit
from app.db.mongo import get_conversations_collection
from app.schemas.chat import ChatRequest
from app.services.orchestrator import answer

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(payload: ChatRequest, request: Request, current: dict = Depends(current_user)):
    user_id = str(current["_id"])
    conversations = get_conversations_collection()

    # rate-limited per user (not per IP) since each chat call spends real
    # money on the Groq/Tavily APIs - this stops one account from running
    # up the bill or hammering the endpoint
    check_rate_limit(key=f"chat:{user_id}", max_per_minute=settings.rate_limit_chat_per_minute)

    history = []
    if payload.conversation_id:
        try:
            conversation_oid = ObjectId(payload.conversation_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid conversation_id")

        conversation = await conversations.find_one({"_id": conversation_oid, "user_id": user_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        history = conversation.get("messages", [])

    try:
        reply, citations, web_sources = await answer(user_id, payload.message, history)
    except Exception:
        # don't leak internal errors (API keys, stack traces) to the client
        raise HTTPException(
            status_code=502,
            detail="The assistant is temporarily unavailable. Please try again shortly.",
        )

    now = datetime.now(timezone.utc).isoformat()
    user_message = {"role": "user", "content": payload.message, "at": now}
    assistant_message = {"role": "assistant", "content": reply, "at": now}

    if payload.conversation_id:
        await conversations.update_one(
            {"_id": conversation_oid},
            {"$push": {"messages": {"$each": [user_message, assistant_message]}}},
        )
        conversation_id = payload.conversation_id
    else:
        result = await conversations.insert_one({
            "user_id": user_id,
            "title": payload.message[:60],
            "messages": [user_message, assistant_message],
            "created_at": now,
        })
        conversation_id = str(result.inserted_id)

    return {
        "conversation_id": conversation_id,
        "answer": reply,
        "citations": citations,
        "web_sources": [{"title": s.get("title"), "url": s.get("url")} for s in web_sources],
    }


@router.get("/conversations")
async def list_conversations(current: dict = Depends(current_user)):
    conversations = get_conversations_collection()
    cursor = conversations.find({"user_id": str(current["_id"])}).sort("created_at", -1)
    docs = await cursor.to_list(50)
    return [
        {"id": str(doc["_id"]), "title": doc.get("title", "Conversation"), "messages": doc.get("messages", [])}
        for doc in docs
    ]
