from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.mongo import client


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await client.admin.command("ping")
        print("✅ MongoDB connected successfully!")
    except Exception as e:
        print("❌ MongoDB connection failed:", e)
    yield


app = FastAPI(title="Askly API", lifespan=lifespan)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Askly backend is running"}