from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, documents as documents_api, progress, quiz
from app.core.config import settings
from app.db.mongo import chunks, client, conversations, mastery


@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.admin.command("ping")
    await users_index_setup()
    yield
    client.close()


async def users_index_setup():
    from app.db.mongo import users
    await users.create_index("email", unique=True)
    await chunks.create_index([("user_id", 1)])
    await conversations.create_index([("user_id", 1)])
    await mastery.create_index([("user_id", 1), ("topic", 1)], unique=True)


app = FastAPI(title="ASKLY AI Learning Assistant", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(documents_api.router)
app.include_router(quiz.router)
app.include_router(progress.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "ASKLY", "version": "2.0.0"}


@app.get("/api/health")
async def health():
    try:
        await client.admin.command("ping")
        return {"status": "healthy", "mongodb": True}
    except Exception as e:
        return {"status": "degraded", "mongodb": False, "error": str(e)}
