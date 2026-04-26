from __future__ import annotations

from datetime import datetime

from pymongo.collection import Collection

from app.db.database import to_mongo_id
from app.schemas.feedback_schema import FeedbackCreate


def _id_query(identifier: str) -> dict:
    return {"$or": [{"id": str(identifier)}, {"_id": to_mongo_id(identifier)}]}


class FeedbackRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def _format_doc(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.get("id") or doc.get("_id"))
        doc.pop("_id", None)
        for field in ("booking_id", "client_id", "master_id"):
            if doc.get(field) is not None:
                doc[field] = str(doc[field])
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        return doc

    def create(self, feedback: FeedbackCreate) -> str:
        data = feedback.model_dump()
        for field in ("booking_id", "client_id", "master_id"):
            if data.get(field) is not None:
                data[field] = str(data[field])
        if data.get("rating") is not None:
            data["rating"] = max(1, min(5, int(round(float(data["rating"])))))
        existing = self.collection.find_one({"booking_id": str(data["booking_id"])})
        if existing:
            raise ValueError(f"Відгук для бронювання №{data['booking_id']} вже існує!")

        data["id"] = str(self.collection.count_documents({}) + 1)
        data["created_at"] = data.get("created_at") or datetime.utcnow()
        self.collection.insert_one(data)
        return data["id"]

    def get_by_id(self, feedback_id: str) -> dict | None:
        return self._format_doc(self.collection.find_one(_id_query(feedback_id)))

    def get_all(self, client_id: str | None = None, master_id: str | None = None) -> list[dict]:
        query: dict = {}
        if client_id:
            query["client_id"] = {"$in": [str(client_id), to_mongo_id(client_id)]}
        if master_id:
            query["master_id"] = {"$in": [str(master_id), to_mongo_id(master_id)]}
        docs = [self._format_doc(doc) for doc in list(self.collection.find(query))]
        return sorted(
            [doc for doc in docs if doc is not None],
            key=lambda doc: int(str(doc.get("id") or 10**9)) if str(doc.get("id") or "").isdigit() else 10**9,
        )

    def update(self, feedback_id: str, update_data: dict) -> dict | None:
        for field in ("booking_id", "client_id", "master_id"):
            if update_data.get(field) is not None:
                update_data[field] = str(update_data[field])
        if update_data.get("rating") is not None:
            update_data["rating"] = max(1, min(5, int(round(float(update_data["rating"])))))
        self.collection.update_one(_id_query(feedback_id), {"$set": update_data})
        return self.get_by_id(feedback_id)

    def delete(self, feedback_id: str) -> int:
        return self.collection.delete_one(_id_query(feedback_id)).deleted_count
