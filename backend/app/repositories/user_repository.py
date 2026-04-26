from __future__ import annotations

from datetime import datetime
from typing import Optional

from pymongo.collection import Collection

from app.core.security import hash_password
from app.db.database import to_mongo_id
from app.schemas.user_schema import UserCreate, UserUpdate


def _id_query(identifier: str) -> dict:
    return {"$or": [{"id": str(identifier)}, {"_id": to_mongo_id(identifier)}]}


class UserRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, user_data: UserCreate) -> str:
        data = user_data.model_dump()
        data["id"] = str(self.collection.count_documents({}) + 1)
        data["created_at"] = datetime.utcnow()

        password = data.pop("password")
        data["password_hash"] = hash_password(password)
        data["services_offered"] = [str(service_id) for service_id in data.get("services_offered", [])]

        self.collection.insert_one(data)
        return data["id"]

    def get_by_id(self, user_id: str) -> dict | None:
        return self._format(self.collection.find_one(_id_query(user_id)))

    def get_all(self, role: Optional[str] = None, service_id: Optional[str] = None, sort_by: Optional[str] = None) -> list[dict]:
        match_filter: dict = {}
        if role:
            match_filter["role"] = role
        if service_id:
            match_filter["services_offered"] = {"$in": [str(service_id), to_mongo_id(service_id)]}

        pipeline = [
            {"$match": match_filter},
            {
                "$lookup": {
                    "from": "feedback",
                    "localField": "id",
                    "foreignField": "master_id",
                    "as": "user_feedbacks",
                }
            },
            {
                "$addFields": {
                    "rating": {
                        "$cond": [
                            {"$gt": [{"$size": "$user_feedbacks"}, 0]},
                            {"$avg": "$user_feedbacks.rating"},
                            0.0,
                        ]
                    },
                    "avatar": {"$ifNull": ["$avatar", None]},
                }
            },
        ]

        docs = [self._format(doc) for doc in list(self.collection.aggregate(pipeline))]

        def sort_key(doc: dict) -> tuple:
            raw_id = doc.get("id")
            try:
                numeric_id = int(str(raw_id))
            except (TypeError, ValueError):
                numeric_id = 10**9

            if sort_by == "name":
                return (str(doc.get("name", "")).lower(), numeric_id)
            if sort_by == "rating":
                return (-float(doc.get("rating", 0.0)), str(doc.get("name", "")).lower(), numeric_id)
            return (numeric_id, str(doc.get("name", "")).lower())

        return sorted(docs, key=sort_key)

    def update(self, user_id: str, user: UserUpdate) -> int:
        doc = user.model_dump(exclude_unset=True)
        if "password" in doc:
            doc["password_hash"] = hash_password(doc.pop("password"))
        if "services_offered" in doc and doc["services_offered"] is not None:
            doc["services_offered"] = [str(service_id) for service_id in doc["services_offered"]]

        result = self.collection.update_one(_id_query(user_id), {"$set": doc})
        return result.modified_count

    def delete(self, user_id: str) -> int:
        result = self.collection.delete_one(_id_query(user_id))
        return result.deleted_count

    def _format(self, doc: dict | None) -> dict | None:
        if not doc:
            return None

        formatted = dict(doc)
        formatted["id"] = str(formatted.get("id") or formatted.get("_id"))

        formatted.pop("_id", None)
        formatted.pop("password_hash", None)
        formatted.pop("user_feedbacks", None)

        formatted["rating"] = round(float(formatted.get("rating", 0.0) or 0.0), 1)
        formatted["services_offered"] = [str(service_id) for service_id in (formatted.get("services_offered") or [])]
        return formatted
