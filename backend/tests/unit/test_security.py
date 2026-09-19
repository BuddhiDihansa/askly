import pytest
from fastapi import HTTPException

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
    with pytest.raises(HTTPException) as exc_info:
        decode_token("this-is-not-a-real-jwt")
    assert exc_info.value.status_code == 401


def test_decode_rejects_token_signed_with_different_secret():
    import jose.jwt as jose_jwt
    forged = jose_jwt.encode({"sub": "attacker"}, "wrong-secret", algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        decode_token(forged)
    assert exc_info.value.status_code == 401
