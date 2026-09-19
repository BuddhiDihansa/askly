from typing import Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
)

from app.core.config import settings


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


mongodb = MongoDB()


# ---------------------------------------------------------
# CONNECTION
# ---------------------------------------------------------

async def connect_to_mongo() -> None:
    """
    Create MongoDB connection and verify connectivity.
    """

    mongodb.client = AsyncIOMotorClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        maxPoolSize=50,
        minPoolSize=5,
    )

    mongodb.db = mongodb.client[settings.mongodb_database]

    # Verify that MongoDB is reachable.
    await mongodb.client.admin.command("ping")


async def close_mongo_connection() -> None:
    """
    Close MongoDB connection cleanly.
    """

    if mongodb.client is not None:
        mongodb.client.close()

    mongodb.client = None
    mongodb.db = None


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def get_database() -> AsyncIOMotorDatabase:
    """
    Return the active MongoDB database.
    """

    if mongodb.db is None:
        raise RuntimeError(
            "MongoDB has not been initialized. "
            "Call connect_to_mongo() during application startup."
        )

    return mongodb.db


# ---------------------------------------------------------
# COLLECTION HELPERS
# ---------------------------------------------------------

def get_users_collection() -> AsyncIOMotorCollection:
    return get_database()["users"]


def get_conversations_collection() -> AsyncIOMotorCollection:
    return get_database()["conversations"]


def get_documents_collection() -> AsyncIOMotorCollection:
    return get_database()["documents"]


def get_chunks_collection() -> AsyncIOMotorCollection:
    return get_database()["chunks"]


def get_quiz_attempts_collection() -> AsyncIOMotorCollection:
    return get_database()["quiz_attempts"]


def get_mastery_collection() -> AsyncIOMotorCollection:
    return get_database()["mastery"]