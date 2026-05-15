from bson import ObjectId
from datetime import datetime, timezone
from app.db.mongodb import get_database


def _fmt(dt) -> str:
    """Convert datetime to JS-safe UTC ISO string (Z suffix, milliseconds not microseconds).

    PyMongo returns naive datetimes from MongoDB (stored as UTC BSON DateTime but
    returned without tzinfo). On Windows/IST, astimezone(utc) misinterprets naive
    datetimes as local time. We use replace(tzinfo=utc) for naive datetimes instead,
    which stamps them as UTC without any conversion.
    """
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            utc = dt.replace(tzinfo=timezone.utc)   # naive from PyMongo = already UTC
        else:
            utc = dt.astimezone(timezone.utc)        # aware datetime — convert correctly
        ms = utc.microsecond // 1000
        return utc.strftime('%Y-%m-%dT%H:%M:%S.') + f'{ms:03d}Z'
    return str(dt)


def _serialize(doc: dict) -> dict:
    """Convert MongoDB doc to JSON-safe dict."""
    doc["id"] = str(doc.pop("_id"))
    doc["user_id"] = str(doc["user_id"])
    doc["created_at"] = _fmt(doc.get("created_at", datetime.now(timezone.utc)))
    doc["updated_at"] = _fmt(doc.get("updated_at", datetime.now(timezone.utc)))
    return doc


class ChatRepository:

    # ── Create ─────────────────────────────────────────────────────
    async def create_session(
        self,
        user_id: str,
        title: str = "New Conversation",
        account_id: str | None = None,
        region: str = "all",
    ) -> dict:
        db = get_database()
        now = datetime.now(timezone.utc)
        doc = {
            "user_id": ObjectId(user_id),
            "title": title,
            "account_id": account_id,
            "region": region,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        result = await db.chats.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _serialize(doc)

    # ── List (summary, no messages) ────────────────────────────────
    async def list_sessions(self, user_id: str) -> list[dict]:
        db = get_database()
        cursor = db.chats.find(
            {"user_id": ObjectId(user_id)},
            {
                "title": 1,
                "account_id": 1,
                "region": 1,
                "created_at": 1,
                "updated_at": 1,
                "message_count": {"$size": "$messages"},
            },
        ).sort("updated_at", -1)

        results = []
        async for doc in cursor:
            doc["_id"] = doc["_id"]
            serialized = _serialize(doc)
            # message_count won't be set via projection in Motor easily,
            # so we calculate it separately
            serialized.setdefault("message_count", 0)
            results.append(serialized)
        return results

    # ── List (fast, just metadata + message count) ─────────────────
    async def list_sessions_fast(self, user_id: str) -> list[dict]:
        """Fetch session headers with message count via aggregation pipeline."""
        db = get_database()
        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {"$sort": {"updated_at": -1}},
            {
                "$project": {
                    "title": 1,
                    "account_id": 1,
                    "region": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "user_id": 1,
                    "message_count": {"$size": "$messages"},
                }
            },
        ]
        cursor = db.chats.aggregate(pipeline)
        results = []
        async for doc in cursor:
            s = _serialize(doc)
            results.append(s)
        return results

    # ── Get single session ─────────────────────────────────────────
    async def get_session(self, session_id: str, user_id: str) -> dict | None:
        db = get_database()
        try:
            doc = await db.chats.find_one(
                {"_id": ObjectId(session_id), "user_id": ObjectId(user_id)}
            )
        except Exception:
            return None
        if not doc:
            return None
        return _serialize(doc)

    # ── Append message ─────────────────────────────────────────────
    async def append_message(
        self, session_id: str, user_id: str, message: dict
    ) -> dict | None:
        db = get_database()
        now = datetime.now(timezone.utc)
        result = await db.chats.update_one(
            {"_id": ObjectId(session_id), "user_id": ObjectId(user_id)},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": now},
            },
        )
        if result.matched_count == 0:
            return None
        return await self.get_session(session_id, user_id)

    # ── Update title ───────────────────────────────────────────────
    async def update_title(
        self, session_id: str, user_id: str, title: str
    ) -> dict | None:
        db = get_database()
        now = datetime.now(timezone.utc)
        result = await db.chats.update_one(
            {"_id": ObjectId(session_id), "user_id": ObjectId(user_id)},
            {"$set": {"title": title, "updated_at": now}},
        )
        if result.matched_count == 0:
            return None
        return await self.get_session(session_id, user_id)

    # ── Delete session ─────────────────────────────────────────────
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        db = get_database()
        try:
            result = await db.chats.delete_one(
                {"_id": ObjectId(session_id), "user_id": ObjectId(user_id)}
            )
            return result.deleted_count == 1
        except Exception:
            return False

    # ── Clear messages (keep session) ──────────────────────────────
    async def clear_messages(self, session_id: str, user_id: str) -> dict | None:
        db = get_database()
        now = datetime.now(timezone.utc)
        result = await db.chats.update_one(
            {"_id": ObjectId(session_id), "user_id": ObjectId(user_id)},
            {"$set": {"messages": [], "updated_at": now}},
        )
        if result.matched_count == 0:
            return None
        return await self.get_session(session_id, user_id)


chat_repository = ChatRepository()
