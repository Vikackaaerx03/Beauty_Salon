from pymongo.collection import Collection
from typing import Optional
from datetime import datetime
from app.schemas.feedback_schema import FeedbackCreate

class FeedbackRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, feedback: FeedbackCreate) -> str:
        data = feedback.model_dump()
        
        existing = self.collection.find_one({"booking_id": data["booking_id"]})
        if existing:
            raise ValueError(f"Відгук для бронювання №{data['booking_id']} вже існує!")

        last_item = self.collection.find_one(sort=[("id", -1)])
        
        if last_item and "id" in last_item:
            try:
                new_id = int(last_item["id"]) + 1
            except:
                new_id = self.collection.count_documents({}) + 1
        else:
            new_id = self.collection.count_documents({}) + 1
        
        data["id"] = str(new_id)
        
        self.collection.insert_one(data)
        return data["id"]

    def get_by_id(self, feedback_id: str) -> dict | None:
        doc = self.collection.find_one({"id": feedback_id})
        return self._format_doc(doc)

    def get_all(self, client_id: Optional[str] = None, master_id: Optional[str] = None) -> list[dict]:
        query = {}
        if client_id: query["client_id"] = client_id
        if master_id: query["master_id"] = master_id
        
        docs = list(self.collection.find(query).sort("id", 1))
        return [self._format_doc(doc) for doc in docs]

    def _format_doc(self, doc):
        """Допоміжна функція для виправлення ID перед відправкою на фронтенд"""
        if not doc: return None
        
        if "id" not in doc:
            doc["id"] = "0"
            
        if "_id" in doc:
            del doc["_id"]
            
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
            
        return doc
        
    def update(self, feedback_id: str, update_data: dict) -> dict | None:
        self.collection.update_one({"id": feedback_id}, {"$set": update_data})
        return self.get_by_id(feedback_id)

    def delete(self, feedback_id: str) -> int:
        result = self.collection.delete_one({"id": feedback_id})
        return result.deleted_count