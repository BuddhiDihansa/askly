import certifi
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

client = AsyncIOMotorClient(settings.mongodb_uri, tlsCAFile=certifi.where())
db = client.get_default_database()

users = db["users"]
conversations = db["conversations"]