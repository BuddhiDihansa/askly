import pytest
from httpx import ASGITransport, AsyncClient

from app.db.mongo import get_documents_collection
from app.main import app


@pytest.mark.asyncio
async def test_malformed_pdf_is_recorded_as_failed_without_exposing_internals():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register = await client.post(
            "/api/auth/register",
            json={"name": "Document Student", "email": "document@example.com", "password": "password123"},
        )
        token = register.json()["token"]
        response = await client.post(
            "/api/documents/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("broken.pdf", b"not a real pdf", "application/pdf")},
        )
        documents = await client.get(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code in (400, 422)
    assert "Traceback" not in response.text
    assert documents.status_code == 200
    assert documents.json()[0]["status"] == "failed"
    assert documents.json()[0]["processing_error"]

    stored = await get_documents_collection().find_one({"filename": "broken.pdf"})
    assert stored["status"] == "failed"
