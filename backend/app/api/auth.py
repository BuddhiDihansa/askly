from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pymongo.errors import DuplicateKeyError

from app.api.dependencies import current_user
from app.core.config import settings
from app.core.rate_limit import check_rate_limit, client_ip
from app.core.security import create_token, hash_password, verify_password
from app.db.mongo import get_users_collection
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _user_response(user: dict) -> UserResponse:
    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        is_active=user.get("is_active", True),
        education_level=user.get("education_level"),
        learning_goal=user.get("learning_goal"),
        preferred_language=user.get("preferred_language", "English"),
        study_subjects=user.get("study_subjects", []),
        daily_study_minutes=user.get("daily_study_minutes"),
        study_style=user.get("study_style"),
        onboarding_completed=user.get("onboarding_completed", False),
        role=user.get("role", "student"),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at"),
    )


@router.post("/register")
async def register(payload: RegisterRequest, request: Request) -> TokenResponse:
    # rate-limited per IP so a script can't mass-create accounts
    check_rate_limit(
        key=f"register:{client_ip(request)}",
        max_per_minute=settings.rate_limit_register_per_minute,
    )

    users = get_users_collection()
    email = _normalize_email(str(payload.email))
    existing = await users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    now = datetime.now(timezone.utc)
    user = {
        "name": payload.name.strip(),
        "email": email,
        "password_hash": hash_password(payload.password),
        "is_active": True,
        "role": "student",
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = await users.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email already registered")

    user["_id"] = result.inserted_id
    return TokenResponse(token=create_token(str(result.inserted_id)), user=_user_response(user))


@router.post("/login")
async def login(payload: LoginRequest, request: Request) -> TokenResponse:
    # SECURITY: rate-limited per IP to slow down brute-force / credential
    # stuffing attacks against the login endpoint.
    check_rate_limit(
        key=f"login:{client_ip(request)}",
        max_per_minute=settings.rate_limit_login_per_minute,
    )

    users = get_users_collection()
    user = await users.find_one({"email": _normalize_email(str(payload.email))})
    password_hash = user.get("password_hash") if user else None
    if password_hash is None and user:
        password_hash = user.get("password")

    if (
        not user
        or not password_hash
        or not verify_password(payload.password, password_hash)
        or not user.get("is_active", True)
    ):
        # deliberately the same error for "no such user" and "wrong password"
        # so an attacker can't use the error message to enumerate valid emails
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(token=create_token(str(user["_id"])), user=_user_response(user))


@router.get("/me")
async def me(current: dict = Depends(current_user)):
    return _user_response(current)
