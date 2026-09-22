from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password: str) -> str:
    """
    Securely hash a password.
    """

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain password against its bcrypt hash.
    """

    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# =========================================================
# JWT
# =========================================================


def create_token(user_id: str) -> str:
    """
    Create an authentication JWT.
    """

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.jwt_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> str:
    """
    Decode and validate JWT.

    Returns:
        user_id

    Raises:
        ValueError
    """

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")

        if not user_id:
            raise ValueError("Token does not contain a user identity.")

        return str(user_id)

    except JWTError as exc:
        raise ValueError("Invalid or expired token.") from exc