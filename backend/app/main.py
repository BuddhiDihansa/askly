from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    chat,
    documents as documents_api,
    progress,
    profile,
    quiz,
)
from app.core.config import settings
from app.db.mongo import (
    close_mongo_connection,
    connect_to_mongo,
    get_chunks_collection,
    get_conversations_collection,
    get_documents_collection,
    get_mastery_collection,
    get_quiz_attempts_collection,
    get_users_collection,
)


async def create_database_indexes() -> None:
    """
    Create MongoDB indexes required by ASKLY.

    Collections are fetched at runtime instead of importing mutable
    module-level collection variables. This prevents stale None references
    during application startup.
    """

    users = get_users_collection()
    conversations = get_conversations_collection()
    documents = get_documents_collection()
    chunks = get_chunks_collection()
    quiz_attempts = get_quiz_attempts_collection()
    mastery = get_mastery_collection()

    async def ensure_index(collection, keys, *, unique=False):
        expected_keys = list(keys) if isinstance(keys, list) else [(keys, 1)]
        async for existing in collection.list_indexes():
            existing_keys = list(existing["key"].items())
            if existing_keys == expected_keys and existing.get("unique", False) == unique:
                return

        await collection.create_index(expected_keys, unique=unique)

    await ensure_index(users, "email", unique=True)
    await ensure_index(conversations, [("user_id", 1), ("created_at", -1)])
    await ensure_index(documents, [("user_id", 1), ("created_at", -1)])
    await ensure_index(chunks, [("user_id", 1)])
    await ensure_index(chunks, [("document_id", 1)])
    await ensure_index(quiz_attempts, [("user_id", 1), ("created_at", -1)])
    await ensure_index(mastery, [("user_id", 1), ("topic", 1)], unique=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.
    """

    # Startup
    await connect_to_mongo()
    await create_database_indexes()

    print(
        f"[ASKLY] Started successfully | "
        f"environment={settings.environment} | "
        f"version={settings.app_version}"
    )

    yield

    # Shutdown
    await close_mongo_connection()

    print("[ASKLY] Shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "ASKLY is an AI-powered personalized learning platform "
        "with document intelligence, adaptive learning, quizzes "
        "and mastery tracking."
    ),
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

allowed_origins = [
    origin.strip()
    for origin in settings.frontend_url.split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)


# ---------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(documents_api.router)
app.include_router(quiz.router)
app.include_router(progress.router)
app.include_router(profile.router)


# ---------------------------------------------------------
# SYSTEM
# ---------------------------------------------------------

@app.get("/", tags=["system"])
async def root():
    return {
        "service": "ASKLY",
        "status": "online",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# ---------------------------------------------------------
# HEALTH CHECKS
# ---------------------------------------------------------

@app.get("/api/health/live", tags=["health"])
async def liveness():
    return {
        "status": "alive",
        "service": "askly",
    }


@app.get("/api/health/ready", tags=["health"])
async def readiness():
    from app.db.mongo import mongodb

    try:
        if mongodb.client is None:
            return {
                "status": "not_ready",
                "database": False,
            }

        await mongodb.client.admin.command("ping")

        return {
            "status": "ready",
            "database": True,
        }

    except Exception:
        return {
            "status": "not_ready",
            "database": False,
        }


@app.get("/api/health", tags=["health"])
async def health():
    from app.db.mongo import mongodb

    database_ok = False

    try:
        if mongodb.client is not None:
            await mongodb.client.admin.command("ping")
            database_ok = True

    except Exception:
        database_ok = False

    return {
        "service": "ASKLY",
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "healthy" if database_ok else "degraded",
        "database": {
            "mongodb": database_ok,
        },
    }