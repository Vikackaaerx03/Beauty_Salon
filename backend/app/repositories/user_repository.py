from pymongo.collection import Collection
from typing import Optional
from datetime import datetime
from app.core.security import hash_password
from app.schemas.user_schema import UserCreate, UserUpdate

class UserRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, user_data: UserCreate) -> str:
        data = user_data.model_dump()
        
        last_item = self.collection.find_one(sort=[("id", -1)])
        try:
            if last_item and "id" in last_item:
                new_id = int(last_item["id"]) + 1
            else:
                new_id = 1
        except (ValueError, TypeError):
            new_id = self.collection.count_documents({}) + 1
            
        data["id"] = str(new_id)
        data["created_at"] = datetime.utcnow()
        
        if "password" in data:
            password = data.pop("password")
            data["password_hash"] = hash_password(password)

        self.collection.insert_one(data)
        return data["id"]

    def get_by_id(self, user_id: str) -> dict | None:
        doc = self.collection.find_one({"id": str(user_id)})
        return self._format(doc)

    def get_all(self, role: Optional[str] = None, service_id: Optional[str] = None, sort_by: Optional[str] = None) -> list[dict]:
        match_filter = {}
        if role: 
            match_filter["role"] = role
        if service_id: 
            match_filter["services_offered"] = str(service_id)

        pipeline = [
            {"$match": match_filter}, 
            {
                "$lookup": { 
                    "from": "feedback",
                    "localField": "id",
                    "foreignField": "master_id",
                    "as": "user_feedbacks"
                }
            },
            {
                "$addFields": {
                    "rating": {
                        "$cond": [
                            {"$gt": [{"$size": "$user_feedbacks"}, 0]}, 
                            {"$avg": "$user_feedbacks.rating"},
                            0.0
                        ]
                    },
                    "avatar": { "$ifNull": ["$avatar", None] }
                }
            }
        ]

        if sort_by == "name":
            pipeline.append({"$sort": {"name": 1}})
        elif sort_by == "rating":
            pipeline.append({"$sort": {"rating": -1, "name": 1}})
        else:
            pipeline.append({"$sort": {"id": 1}})

        cursor = self.collection.aggregate(pipeline)
        return [self._format(doc) for doc in list(cursor)]

    def update(self, user_id: str, user: UserUpdate) -> int:
        doc = user.model_dump(exclude_unset=True)
        if "password" in doc:
            doc["password_hash"] = hash_password(doc.pop("password"))
        
        result = self.collection.update_one({"id": str(user_id)}, {"$set": doc})
        return result.modified_count

    def delete(self, user_id: str) -> int:
        result = self.collection.delete_one({"id": str(user_id)})
        return result.deleted_count

    def _format(self, doc: dict | None) -> dict | None:
        if not doc: return None
        
        formatted = dict(doc)
        formatted["id"] = str(formatted.get("id") or formatted.get("_id"))
        
        if "_id" in formatted: del formatted["_id"]
        if "password_hash" in formatted: del formatted["password_hash"]
        if "user_feedbacks" in formatted: del formatted["user_feedbacks"]
        
        # Рейтинг
        raw_rating = formatted.get("rating", 0.0)
        formatted["rating"] = round(float(raw_rating), 1)
        
        # Аватар (якщо його немає в базі, повернемо None, щоб фронтенд поставив заглушку)
        formatted["avatar"] = formatted.get("avatar")
        
        # Послуги
        services = formatted.get("services_offered", [])
        formatted["services_offered"] = [str(s) for s in (services or [])]
        
        return formatted