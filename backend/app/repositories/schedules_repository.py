from pymongo.collection import Collection
from typing import Optional
from app.db.database import to_mongo_id
from app.schemas.schedules_schema import TimeslotCreate, TimeslotUpdate

class ScheduleRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, timeslot: TimeslotCreate) -> str:
        return str(self.collection.insert_one(timeslot.model_dump()).inserted_id)

    def get_by_id(self, timeslot_id: str) -> dict | None:
        doc = self.collection.find_one({"_id": to_mongo_id(timeslot_id)})
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        return doc

    def get_all(
        self,
        master_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        query: dict = {}
        if master_id:
            query["master_id"] = master_id
        if status:
            query["status"] = status

        docs = list(self.collection.find(query).sort("start", 1))
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    def update(self, timeslot_id: str, timeslot: TimeslotUpdate) -> int:
        result = self.collection.update_one(
            {"_id": to_mongo_id(timeslot_id)}, {"$set": timeslot.model_dump(exclude_unset=True)}
        )
        return result.modified_count

    def mark_booked(self, timeslot_id: str, booking_id: str) -> int:
        result = self.collection.update_one(
            {"_id": to_mongo_id(timeslot_id), "status": "free"},
            {"$set": {"status": "booked", "booking_id": booking_id}},
        )
        return result.modified_count

    def mark_free(self, timeslot_id: str) -> int:
        result = self.collection.update_one(
            {"_id": to_mongo_id(timeslot_id)},
            {"$set": {"status": "free", "booking_id": None}},
        )
        return result.modified_count

    def delete(self, timeslot_id: str) -> int:
        result = self.collection.delete_one({"_id": to_mongo_id(timeslot_id)})
        return result.deleted_count
