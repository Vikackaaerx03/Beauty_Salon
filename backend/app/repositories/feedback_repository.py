from pymongo.collection import Collection
from typing import Optional
from app.db.database import to_mongo_id
from app.schemas.feedback_schema import FeedbackCreate

class FeedbackRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, feedback: FeedbackCreate) -> str:
        return str(self.collection.insert_one(feedback.model_dump()).inserted_id)

    def get_by_id(self, feedback_id: str) -> dict | None:
        doc = self.collection.find_one({"_id": to_mongo_id(feedback_id)})
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        return doc

    def get_all(self, client_id: Optional[str] = None, master_id: Optional[str] = None) -> list[dict]:
        query = {}
        if client_id:
            query["client_id"] = client_id
        if master_id:
            query["master_id"] = master_id
        docs = list(self.collection.find(query).sort("created_at", -1))
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    def delete(self, feedback_id: str) -> int:
        result = self.collection.delete_one({"_id": to_mongo_id(feedback_id)})
        return result.deleted_count
