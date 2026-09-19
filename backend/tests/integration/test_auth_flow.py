import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_token, hash_password
from app.db.mongo import get_users_collection
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_register_login_and_me_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register_res = await client.post(
            "/api/auth/register",
            json={"name": "Student One", "email": "student1@example.com", "password": "password123"},
        )
        assert register_res.status_code == 200
        token = register_res.json()["token"]

        login_res = await client.post(
            "/api/auth/login",
            json={"email": "student1@example.com", "password": "password123"},
        )
        assert login_res.status_code == 200

        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "student1@example.com"
        assert "password" not in register_res.json()["user"]
        assert "password_hash" not in register_res.json()["user"]


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email_case_insensitively():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post(
            "/api/auth/register",
            json={"name": "Student One", "email": "Student1@example.com", "password": "password123"},
        )
        duplicate = await client.post(
            "/api/auth/register",
            json={"name": "Student Two", "email": " student1@EXAMPLE.com ", "password": "password123"},
        )

    assert first.status_code == 200
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_register_rejects_short_password():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={"name": "Student One", "email": "short@example.com", "password": "short"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_rejects_wrong_password():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/auth/register",
            json={"name": "Student Two", "email": "student2@example.com", "password": "correctpass"},
        )
        response = await client.post(
            "/api/auth/login",
            json={"email": "student2@example.com", "password": "wrongpass"},
        )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_me_rejects_nonexistent_user():
    token = create_token("507f1f77bcf86cd799439011")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_inactive_user_cannot_login_or_access_me():
    users = get_users_collection()
    result = await users.insert_one({
        "name": "Inactive Student",
        "email": "inactive@example.com",
        "password_hash": hash_password("password123"),
        "is_active": False,
    })
    token = create_token(str(result.inserted_id))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login",
            json={"email": "inactive@example.com", "password": "password123"},
        )
        me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert login.status_code == 401
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/auth/me")
    assert response.status_code in (401, 403)  # HTTPBearer returns 403 when no header is sent at all


@pytest.mark.asyncio
async def test_login_is_rate_limited(monkeypatch):
    from app.core.rate_limit import _hits
    _hits.clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/auth/register",
            json={"name": "Rate Limited", "email": "ratelimited@example.com", "password": "password123"},
        )
        # default limit is 5/minute - the 6th attempt in the same minute should be blocked
        for _ in range(5):
            await client.post(
                "/api/auth/login",
                json={"email": "ratelimited@example.com", "password": "wrongpass"},
            )
        blocked_response = await client.post(
            "/api/auth/login",
            json={"email": "ratelimited@example.com", "password": "wrongpass"},
        )
    assert blocked_response.status_code == 429
    _hits.clear()
