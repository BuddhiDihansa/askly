from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.db.mongo import users

bearer = HTTPBearer()


async def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    """FastAPI dependency: verifies the request's JWT and loads the
    corresponding user document. Any protected route adds
    `current: dict = Depends(current_user)` to require a valid login."""
    user_id = decode_token(credentials.credentials)  # raises 401 itself if invalid/expired

    try:
        user_oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await users.find_one({"_id": user_oid})
    if not user:
        # token was validly signed, but the account no longer exists
        # (e.g. deleted) - treat the same as "not logged in"
        raise HTTPException(status_code=401, detail="User not found")
    return user
