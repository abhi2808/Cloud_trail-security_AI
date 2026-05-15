from motor.motor_asyncio import AsyncIOMotorClient
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None

db = Database()

def get_database():
    """Returns the database instance named 'cloudtrail_ai'."""
    return db.client.cloudtrail_ai

async def connect_db():
    """FastAPI lifespan connect to DB and create indexes."""
    db.client = AsyncIOMotorClient(settings.mongodb_uri)
    database = get_database()
    
    # Create indexes
    # users: unique index on email
    await database.users.create_index("email", unique=True)
    # accounts: compound index on (user_id, nickname)
    await database.accounts.create_index([("user_id", 1), ("nickname", 1)])
    # chats: compound index on (user_id, updated_at) for fast sidebar listing
    await database.chats.create_index([("user_id", 1), ("updated_at", -1)])
    logger.info("Connected to MongoDB and initialized indexes.")

async def close_db():
    """FastAPI lifespan close DB connection."""
    if db.client:
        db.client.close()
        logger.info("Closed MongoDB connection.")
