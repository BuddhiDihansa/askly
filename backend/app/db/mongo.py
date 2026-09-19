from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client.get_default_database()
users = db["users"]
conversations = db["conversations"]
documents = db["documents"]
chunks = db["chunks"]
quiz_attempts = db["quiz_attempts"]
mastery = db["mastery"]
