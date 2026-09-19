from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import current_user
from app.core.config import settings
from app.core.rate_limit import check_rate_limit, client_ip
from app.core.security import create_token, hash_password, verify_password
from app.db.mongo import users
from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(payload: RegisterRequest, request: Request):
    # rate-limited per IP so a script can't mass-create accounts
    check_rate_limit(
        key=f"register:{client_ip(request)}",
        max_per_minute=settings.rate_limit_login_per_minute,
    )

    existing = await users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    result = await users.insert_one({
        "name": payload.name,
        "email": payload.email.lower(),
        "password": hash_password(payload.password),
    })

    user_id = str(result.inserted_id)
    return {
        "token": create_token(user_id),
        "user": {"id": user_id, "name": payload.name, "email": payload.email.lower()},
    }


@router.post("/login")
async def login(payload: LoginRequest, request: Request):
    # SECURITY: rate-limited per IP to slow down brute-force / credential
    # stuffing attacks against the login endpoint.
    check_rate_limit(
        key=f"login:{client_ip(request)}",
        max_per_minute=settings.rate_limit_login_per_minute,
    )

    user = await users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password"]):
        # deliberately the same error for "no such user" and "wrong password"
        # so an attacker can't use the error message to enumerate valid emails
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "token": create_token(str(user["_id"])),
        "user": {"id": str(user["_id"]), "name": user["name"], "email": user["email"]},
    }


@router.get("/me")
async def me(current: dict = Depends(current_user)):
    return {"id": str(current["_id"]), "name": current["name"], "email": current["email"]}
