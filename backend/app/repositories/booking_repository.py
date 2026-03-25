from pymongo.collection import Collection
from datetime import datetime
from typing import Optional
from app.db.database import to_mongo_id
from app.schemas.booking_schema import BookingCreate, BookingUpdate

class BookingRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, booking: BookingCreate) -> str:
        now = datetime.utcnow()
        doc = booking.model_dump()
        doc["created_at"] = now
        doc["updated_at"] = now
        return str(self.collection.insert_one(doc).inserted_id)

    def get_by_id(self, booking_id: str) -> dict | None:
        doc = self.collection.find_one({"_id": to_mongo_id(booking_id)})
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

    def update(self, booking_id: str, booking: BookingUpdate) -> int:
        doc = booking.model_dump(exclude_unset=True)
        doc["updated_at"] = datetime.utcnow()
        result = self.collection.update_one({"_id": to_mongo_id(booking_id)}, {"$set": doc})
        return result.modified_count

    def update_status(self, booking_id: str, status: str) -> int:
        result = self.collection.update_one(
            {"_id": to_mongo_id(booking_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}},
        )
        return result.modified_count

    def delete(self, booking_id: str) -> int:
        result = self.collection.delete_one({"_id": to_mongo_id(booking_id)})
        return result.deleted_count
