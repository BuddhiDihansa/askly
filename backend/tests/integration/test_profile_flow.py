from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_token, hash_password
from app.db.mongo import get_users_collection
from app.main import app


async def _register(client: AsyncClient, email: str = "profile@example.com") -> str:
    response = await client.post(
        "/api/auth/register",
        json={"name": "Profile Student", "email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


@pytest.mark.asyncio
async def test_profile_requires_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/profile")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_profile_update_and_safe_response():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register(client)
        response = await client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Updated Student",
                "education_level": "undergraduate",
                "learning_goal": "Build stronger study habits",
                "preferred_language": "English",
                "study_subjects": ["Databases", "Python"],
                "daily_study_minutes": 45,
                "study_style": "practice",
                "password_hash": "must-not-be-stored",
                "is_active": False,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Student"
    assert data["study_subjects"] == ["Databases", "Python"]
    assert data["onboarding_completed"] is False
    assert "password" not in data
    assert "password_hash" not in data

    users = get_users_collection()
    stored = await users.find_one({"email": "profile@example.com"})
    assert stored["is_active"] is True
    assert stored["password_hash"] != "must-not-be-stored"
    assert stored["updated_at"] >= stored["created_at"]


@pytest.mark.asyncio
async def test_onboarding_marks_profile_completed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register(client, "onboarding@example.com")
        response = await client.post(
            "/api/profile/onboarding",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "education_level": "postgraduate",
                "learning_goal": "Prepare for exams",
                "preferred_language": "English",
                "study_subjects": ["Machine Learning"],
                "daily_study_minutes": 60,
                "study_style": "mixed",
            },
        )
        profile = await client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["onboarding_completed"] is True
    assert profile.json()["onboarding_completed"] is True


@pytest.mark.asyncio
async def test_profile_rejects_invalid_data():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _register(client, "invalid-profile@example.com")
        response = await client.put(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "daily_study_minutes": 0,
                "study_subjects": ["", "Python"],
                "study_style": "invalid",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_legacy_user_gets_safe_profile_defaults():
    users = get_users_collection()
    result = await users.insert_one({
        "name": "Legacy Student",
        "email": "legacy@example.com",
        "password_hash": hash_password("password123"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })
    token = create_token(str(result.inserted_id))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["onboarding_completed"] is False
    assert data["study_subjects"] == []
    assert "password_hash" not in data
    assert "_id" not in data
