from __future__ import annotations
from datetime import datetime
from pymongo.collection import Collection
from app.core.security import hash_password
from app.schemas.auth_schema import AuthRegister

class AuthRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def register(self, user: AuthRegister) -> str:
        """Створення нового користувача з числовим ID."""
        data = user.model_dump()
        
        last_item = self.collection.find_one(sort=[("id", -1)])
        new_id = int(last_item["id"]) + 1 if last_item and "id" in last_item else 1
        
        data["id"] = str(new_id)
        password = data.pop("password")
        data["password_hash"] = hash_password(password)
        data.setdefault("rating", 0.0)
        data.setdefault("services_offered", [])
        data["created_at"] = datetime.utcnow()
        
        self.collection.insert_one(data)
        return data["id"]

    def find_by_email(self, email: str) -> dict | None:
        """Знайти користувача за email (для логіну)."""
        return self.collection.find_one({"email": email})

    def get_public_by_id(self, user_id: str) -> dict | None:
        """Отримати дані користувача за нашим числовим ID."""
        doc = self.collection.find_one({"id": user_id}, {"password_hash": 0})
        if not doc:
            return None
        doc["id"] = str(doc.get("id"))
        if "_id" in doc:
            del doc["_id"]
        return doc

    def delete(self, user_id: str) -> int:
        """Видалити за числовим ID."""
        return self.collection.delete_one({"id": user_id}).deleted_count