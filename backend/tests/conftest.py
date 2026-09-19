import os

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/testdb")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production-32")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("TAVILY_API_KEY", "")

import pytest
from mongomock_motor import AsyncMongoMockClient


@pytest.fixture(autouse=True)
def patch_mongo(monkeypatch):
    """Every test gets a fresh in-memory MongoDB fake."""
    mock_client = AsyncMongoMockClient()
    mock_db = mock_client["testdb"]
    users = mock_db["users"]
    conversations = mock_db["conversations"]
    documents = mock_db["documents"]
    chunks = mock_db["chunks"]
    quiz_attempts = mock_db["quiz_attempts"]
    mastery = mock_db["mastery"]

    import app.db.mongo as mongo_module
    from app.core.rate_limit import _hits

    monkeypatch.setattr(mongo_module.mongodb, "client", mock_client)
    monkeypatch.setattr(mongo_module.mongodb, "db", mock_db)
    _hits.clear()

    yield

    _hits.clear()
