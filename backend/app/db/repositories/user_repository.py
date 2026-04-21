from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime, timezone
from app.db.mongodb import get_database

class UserRepository:
    async def create_user(self, email: str, hashed_password: str) -> dict:
        db = get_database()
        user_doc = {
            "email": email,
            "hashed_password": hashed_password,
            "created_at": datetime.now(timezone.utc),
            "is_active": True
        }
        try:
            result = await db.users.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id
            return user_doc
        except DuplicateKeyError:
            raise ValueError(f"User with email {email} already exists")

    async def get_user_by_email(self, email: str) -> dict | None:
        db = get_database()
        return await db.users.find_one({"email": email})

    async def get_user_by_id(self, user_id: str) -> dict | None:
        db = get_database()
        try:
            return await db.users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

user_repository = UserRepository()
