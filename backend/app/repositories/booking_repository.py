from __future__ import annotations

from datetime import datetime

from pymongo.collection import Collection

from app.db.database import to_mongo_id
from app.schemas.booking_schema import BookingCreate, BookingUpdate


def _id_query(identifier: str) -> dict:
    return {"$or": [{"id": str(identifier)}, {"_id": to_mongo_id(identifier)}]}


class BookingRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def _format(self, doc: dict | None) -> dict | None:
        if doc is None:
            return None

        doc = dict(doc)
        doc["id"] = str(doc.get("id") or doc.get("_id"))
        doc.pop("_id", None)

        for field in ("client_id", "master_id", "service_id", "timeslot_id"):
            if doc.get(field) is not None:
                doc[field] = str(doc[field])

        return doc

    def create(self, booking: BookingCreate) -> str:
        now = datetime.utcnow()
        doc = booking.model_dump()
        doc["id"] = str(self.collection.count_documents({}) + 1)
        doc["created_at"] = now
        doc["updated_at"] = now
        self.collection.insert_one(doc)
        return doc["id"]

    def get_by_id(self, booking_id: str) -> dict | None:
        return self._format(self.collection.find_one(_id_query(booking_id)))

    def get_by_timeslot_id(self, timeslot_id: str) -> dict | None:
        doc = self.collection.find_one({"timeslot_id": {"$in": [str(timeslot_id), to_mongo_id(timeslot_id)]}})
        return self._format(doc)

    def get_all(self, client_id: str | None = None, master_id: str | None = None) -> list[dict]:
        query: dict = {}
        if client_id:
            query["client_id"] = {"$in": [str(client_id), to_mongo_id(client_id)]}
        if master_id:
            query["master_id"] = {"$in": [str(master_id), to_mongo_id(master_id)]}

        docs = list(self.collection.find(query).sort("created_at", -1))
        return [self._format(doc) for doc in docs if self._format(doc) is not None]

    def update(self, booking_id: str, booking: BookingUpdate) -> int:
        doc = booking.model_dump(exclude_unset=True)
        doc["updated_at"] = datetime.utcnow()
        result = self.collection.update_one(_id_query(booking_id), {"$set": doc})
        return result.modified_count

    def update_status(self, booking_id: str, status: str) -> int:
        result = self.collection.update_one(_id_query(booking_id), {"$set": {"status": status, "updated_at": datetime.utcnow()}})
        return result.modified_count

    def delete(self, booking_id: str) -> int:
        result = self.collection.delete_one(_id_query(booking_id))
        return result.deleted_count
