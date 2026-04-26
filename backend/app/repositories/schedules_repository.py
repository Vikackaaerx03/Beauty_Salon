from __future__ import annotations

from pymongo.collection import Collection

from app.db.database import to_mongo_id
from app.schemas.schedules_schema import TimeslotCreate, TimeslotUpdate


def _id_query(identifier: str) -> dict:
    return {"$or": [{"id": str(identifier)}, {"_id": to_mongo_id(identifier)}]}


class ScheduleRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def _format(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.get("id") or doc.get("_id"))
        doc.pop("_id", None)
        if doc.get("master_id") is not None:
            doc["master_id"] = str(doc["master_id"])
        if doc.get("booking_id") is not None:
            doc["booking_id"] = str(doc["booking_id"])
        return doc

    def create(self, timeslot: TimeslotCreate) -> str:
        data = timeslot.model_dump()
        data["id"] = str(self.collection.count_documents({}) + 1)
        self.collection.insert_one(data)
        return data["id"]

    def get_by_id(self, timeslot_id: str) -> dict | None:
        return self._format(self.collection.find_one(_id_query(timeslot_id)))

    def get_all(self, master_id=None, status=None) -> list[dict]:
        query: dict = {}
        if master_id:
            query["master_id"] = {"$in": [str(master_id), to_mongo_id(master_id)]}
        if status:
            query["status"] = status
        docs = [self._format(doc) for doc in list(self.collection.find(query))]
        return sorted(
            [doc for doc in docs if doc is not None],
            key=lambda doc: int(str(doc.get("id") or 10**9)) if str(doc.get("id") or "").isdigit() else 10**9,
        )

    def update(self, timeslot_id: str, timeslot: TimeslotUpdate) -> int:
        result = self.collection.update_one(_id_query(timeslot_id), {"$set": timeslot.model_dump(exclude_unset=True)})
        return result.modified_count

    def mark_booked(self, timeslot_id: str, booking_id: str) -> int:
        return self.collection.update_one(
            _id_query(timeslot_id),
            {"$set": {"status": "booked", "booking_id": str(booking_id)}},
        ).modified_count

    def mark_free(self, timeslot_id: str) -> int:
        return self.collection.update_one(_id_query(timeslot_id), {"$set": {"status": "free", "booking_id": None}}).modified_count

    def delete(self, timeslot_id: str) -> int:
        return self.collection.delete_one(_id_query(timeslot_id)).deleted_count
