from __future__ import annotations

from datetime import datetime

from pymongo.collection import Collection

from app.core.security import hash_password
from app.db.database import to_mongo_id
from app.schemas.auth_schema import AuthRegister


class AuthRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def register(self, user: AuthRegister) -> str:
        """Створення нового користувача."""
        doc = user.model_dump()
        password = doc.pop("password")
        doc["password_hash"] = hash_password(password)
        doc.setdefault("rating", 0.0)
        doc.setdefault("services_offered", [])
        doc["created_at"] = datetime.utcnow()
        return str(self.collection.insert_one(doc).inserted_id)

    def find_by_email(self, email: str) -> dict | None:
        """Знайти користувача за email (для логіну)."""
        return self.collection.find_one({"email": email})

    def get_public_by_id(self, user_id: str) -> dict | None:
        doc = self.collection.find_one({"_id": to_mongo_id(user_id)}, {"password_hash": 0})
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        return doc

    def delete(self, user_id: str) -> int:
        result = self.collection.delete_one({"_id": to_mongo_id(user_id)})
        return result.deleted_count
