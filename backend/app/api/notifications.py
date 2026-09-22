from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import current_user
from app.db.mongo import get_notifications_collection

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _public(item: dict) -> dict:
    return {"id": str(item["_id"]), "title": item["title"], "message": item["message"], "read": item.get("read", False), "created_at": item["created_at"]}


@router.get("")
async def list_notifications(current: dict = Depends(current_user)):
    items = await get_notifications_collection().find({"user_id": str(current["_id"])}).sort("created_at", -1).to_list(50)
    return [_public(item) for item in items]


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, current: dict = Depends(current_user)):
    try:
        object_id = ObjectId(notification_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid notification id")
    result = await get_notifications_collection().update_one({"_id": object_id, "user_id": str(current["_id"])}, {"$set": {"read": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}


async def create_notification(user_id: str, title: str, message: str) -> None:
    await get_notifications_collection().insert_one({"user_id": user_id, "title": title, "message": message, "read": False, "created_at": datetime.now(timezone.utc)})