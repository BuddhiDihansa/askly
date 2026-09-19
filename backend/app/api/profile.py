from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.auth import _user_response
from app.api.dependencies import current_user
from app.db.mongo import get_users_collection
from app.schemas.auth import UserResponse
from app.schemas.profile import OnboardingRequest, ProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _profile_updates(payload: ProfileUpdate | OnboardingRequest) -> dict:
    return payload.model_dump(exclude_unset=True)


@router.get("", response_model=UserResponse)
async def get_profile(current: dict = Depends(current_user)):
    return _user_response(current)


@router.put("", response_model=UserResponse)
async def update_profile(
    payload: ProfileUpdate,
    current: dict = Depends(current_user),
):
    updates = _profile_updates(payload)
    if not updates:
        return _user_response(current)

    updates["updated_at"] = datetime.now(timezone.utc)
    users = get_users_collection()
    await users.update_one({"_id": current["_id"]}, {"$set": updates})
    updated = {**current, **updates}
    return _user_response(updated)


@router.get("/onboarding", response_model=UserResponse)
async def get_onboarding_status(current: dict = Depends(current_user)):
    return _user_response(current)


@router.post("/onboarding", response_model=UserResponse)
async def complete_onboarding(
    payload: OnboardingRequest,
    current: dict = Depends(current_user),
):
    updates = _profile_updates(payload)
    updates["onboarding_completed"] = True
    updates["updated_at"] = datetime.now(timezone.utc)

    users = get_users_collection()
    await users.update_one({"_id": current["_id"]}, {"$set": updates})
    updated = {**current, **updates}
    return _user_response(updated)
