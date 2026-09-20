from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.db.mongo import get_users_collection


bearer = HTTPBearer(auto_error=False)


async def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    """
    Resolve the authenticated user from the JWT token.
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials are required.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    token = credentials.credentials

    # -----------------------------------------------------
    # Decode token
    # -----------------------------------------------------

    try:
        user_id = decode_token(token)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # -----------------------------------------------------
    # Validate ObjectId
    # -----------------------------------------------------

    try:
        user_object_id = ObjectId(user_id)

    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication identity.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # -----------------------------------------------------
    # Find user
    # -----------------------------------------------------

    users = get_users_collection()

    user = await users.find_one(
        {
            "_id": user_object_id,
        }
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return user


async def admin_user(user: dict = Depends(current_user)) -> dict:
    if user.get("role", "student") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user