from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import current_user
from app.db.mongo import get_study_plans_collection
from app.services.mastery import get_mastery

router = APIRouter(prefix="/api/planner", tags=["planner"])


class PlanRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=31)


@router.post("")
async def create_plan(payload: PlanRequest, current: dict = Depends(current_user)):
    user_id = str(current["_id"])
    mastery = await get_mastery(user_id)
    subjects = current.get("study_subjects") or [item["topic"] for item in mastery]
    topics = [item["topic"] for item in sorted(mastery, key=lambda item: item.get("mastery", 0))]
    topics += [subject for subject in subjects if subject not in topics]
    topics = topics or ["Review core concepts"]
    minutes = current.get("daily_study_minutes") or 30
    tasks = []
    for day in range(payload.days):
        topic = topics[day % len(topics)]
        tasks.append({"day": day + 1, "topic": topic, "minutes": minutes, "activities": ["review", "practice"]})
    plan = {"user_id": user_id, "days": payload.days, "tasks": tasks, "created_at": datetime.now(timezone.utc)}
    result = await get_study_plans_collection().insert_one(plan)
    return {"id": str(result.inserted_id), "days": payload.days, "tasks": tasks, "created_at": plan["created_at"]}


@router.get("")
async def latest_plan(current: dict = Depends(current_user)):
    plan = await get_study_plans_collection().find_one({"user_id": str(current["_id"])}, sort=[("created_at", -1)])
    if not plan:
        return {"id": None, "tasks": []}
    return {"id": str(plan["_id"]), "days": plan.get("days", 0), "tasks": plan.get("tasks", []), "created_at": plan.get("created_at")}