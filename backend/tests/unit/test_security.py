from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.security import create_token, decode_token, hash_password, verify_password


def test_password_hash_and_verify_roundtrip():
    hashed = hash_password("mypassword123")
    assert hashed != "mypassword123"
    assert verify_password("mypassword123", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("mypassword123")
    assert verify_password("wrongpassword", hashed) is False


def test_token_roundtrip():
    token = create_token("user-abc-123")
    assert decode_token(token) == "user-abc-123"


def test_decode_rejects_garbage_token():
    with pytest.raises(ValueError):
        decode_token("this-is-not-a-real-jwt")


def test_decode_rejects_token_signed_with_different_secret():
    forged = jwt.encode({"sub": "attacker"}, "wrong-secret", algorithm="HS256")
    with pytest.raises(ValueError):
        decode_token(forged)


def test_decode_rejects_expired_token():
    from app.core.config import settings

    expired = jwt.encode(
        {
            "sub": "expired-user",
            "iat": datetime.now(timezone.utc) - timedelta(minutes=2),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(ValueError):
        decode_token(expired)
