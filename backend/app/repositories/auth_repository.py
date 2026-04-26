from __future__ import annotations

from datetime import datetime

from pymongo.collection import Collection

from app.core.security import hash_password
from app.db.database import to_mongo_id
from app.schemas.auth_schema import AuthRegister


def _id_query(identifier: str) -> dict:
    return {"$or": [{"id": str(identifier)}, {"_id": to_mongo_id(identifier)}]}


class AuthRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def register(self, user: AuthRegister) -> str:
        data = user.model_dump()
        data["id"] = str(self.collection.count_documents({}) + 1)
        password = data.pop("password")
        data["password_hash"] = hash_password(password)
        data.setdefault("rating", 0.0)
        data.setdefault("services_offered", [])
        data["services_offered"] = [str(service_id) for service_id in data.get("services_offered", [])]
        data["created_at"] = datetime.utcnow()

        self.collection.insert_one(data)
        return data["id"]

    def find_by_email(self, email: str) -> dict | None:
        return self.collection.find_one({"email": email.strip()})

    def get_public_by_id(self, user_id: str) -> dict | None:
        doc = self.collection.find_one(_id_query(user_id), {"password_hash": 0})
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.get("id") or doc.get("_id"))
        doc.pop("_id", None)
        doc.pop("password_hash", None)
        if doc.get("rating") is not None:
            doc["rating"] = float(doc["rating"])
        doc["services_offered"] = [str(service_id) for service_id in (doc.get("services_offered") or [])]
        return doc

    def delete(self, user_id: str) -> int:
        return self.collection.delete_one(_id_query(user_id)).deleted_count
