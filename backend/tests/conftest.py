import os

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/testdb")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("TAVILY_API_KEY", "")

import pytest
from mongomock_motor import AsyncMongoMockClient


@pytest.fixture(autouse=True)
def patch_mongo(monkeypatch):
    """Every test gets a fresh in-memory MongoDB fake instead of touching
    a real database.

    Why this needs so many monkeypatch calls: several modules do
    `from app.db.mongo import users` (etc.) at import time, which binds
    their OWN local name to whatever object existed at that moment. If we
    only patched app.db.mongo's attributes, those already-bound local
    names in auth.py/chat.py/etc. would keep pointing at the original
    (real, unreachable-in-tests) MongoDB client. So we patch the name in
    every module that imported it directly.
    """
    mock_client = AsyncMongoMockClient()
    mock_db = mock_client["testdb"]
    users = mock_db["users"]
    conversations = mock_db["conversations"]
    documents = mock_db["documents"]
    chunks = mock_db["chunks"]
    quiz_attempts = mock_db["quiz_attempts"]
    mastery = mock_db["mastery"]

    import app.db.mongo as mongo_module
    monkeypatch.setattr(mongo_module, "client", mock_client)
    monkeypatch.setattr(mongo_module, "db", mock_db)
    monkeypatch.setattr(mongo_module, "users", users)
    monkeypatch.setattr(mongo_module, "conversations", conversations)
    monkeypatch.setattr(mongo_module, "documents", documents)
    monkeypatch.setattr(mongo_module, "chunks", chunks)
    monkeypatch.setattr(mongo_module, "quiz_attempts", quiz_attempts)
    monkeypatch.setattr(mongo_module, "mastery", mastery)

    import app.api.auth as auth_module
    monkeypatch.setattr(auth_module, "users", users)

    import app.api.dependencies as dependencies_module
    monkeypatch.setattr(dependencies_module, "users", users)

    import app.api.chat as chat_module
    monkeypatch.setattr(chat_module, "conversations", conversations)

    import app.api.documents as documents_api_module
    monkeypatch.setattr(documents_api_module, "chunks", chunks)
    monkeypatch.setattr(documents_api_module, "documents", documents)

    import app.api.quiz as quiz_module
    monkeypatch.setattr(quiz_module, "quiz_attempts", quiz_attempts)

    import app.api.progress as progress_module
    monkeypatch.setattr(progress_module, "conversations", conversations)
    monkeypatch.setattr(progress_module, "documents", documents)
    monkeypatch.setattr(progress_module, "quiz_attempts", quiz_attempts)

    import app.services.mastery as mastery_service
    monkeypatch.setattr(mastery_service, "mastery", mastery)

    import app.services.retrieval as retrieval_service
    monkeypatch.setattr(retrieval_service, "chunks", chunks)

    yield
