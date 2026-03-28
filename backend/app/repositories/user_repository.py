from pymongo.collection import Collection
from datetime import datetime
from typing import Optional
from app.db.database import to_mongo_id
from app.core.security import hash_password
from app.schemas.user_schema import UserCreate, UserUpdate

class UserRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, user: UserCreate) -> str:
        doc = user.model_dump()
        password = doc.pop("password")
        doc["password_hash"] = hash_password(password)
        doc["created_at"] = datetime.utcnow()
        return str(self.collection.insert_one(doc).inserted_id)

    def get_by_id(self, user_id: str) -> dict | None:
        doc = self.collection.find_one({"_id": to_mongo_id(user_id)}, {"password_hash": 0})
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        return doc

    def get_all(
        self,
        role: Optional[str] = None,
        service_id: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> list[dict]:
        query = {}
        if role:
            query["role"] = role
        if service_id:
            query["services_offered"] = service_id

        sort = None
        if sort_by == "name":
            sort = [("name", 1)]
        elif sort_by == "rating":
            sort = [("rating", -1), ("name", 1)]

        cursor = self.collection.find(query, {"password_hash": 0})
        if sort:
            cursor = cursor.sort(sort)
        docs = list(cursor)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    def update(self, user_id: str, user: UserUpdate) -> int:
        doc = user.model_dump(exclude_unset=True)
        if "password" in doc:
            doc["password_hash"] = hash_password(doc.pop("password"))
        result = self.collection.update_one({"_id": to_mongo_id(user_id)}, {"$set": doc})
        return result.modified_count

    def delete(self, user_id: str) -> int:
        result = self.collection.delete_one({"_id": to_mongo_id(user_id)})
        return result.deleted_count
