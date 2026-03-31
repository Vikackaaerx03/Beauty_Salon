from pymongo.collection import Collection
from typing import Optional
from app.db.database import to_mongo_id
from app.schemas.schedules_schema import TimeslotCreate, TimeslotUpdate

class ScheduleRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, timeslot: TimeslotCreate) -> str:
        data = timeslot.model_dump()
        last_item = self.collection.find_one(sort=[("id", -1)])
        new_id = int(last_item["id"]) + 1 if last_item and "id" in last_item else 1
        
        data["id"] = str(new_id)
        self.collection.insert_one(data)
        return data["id"]

    def get_by_id(self, timeslot_id: str) -> dict | None:
        return self._format(self.collection.find_one({"id": timeslot_id}))

    def get_all(self, master_id=None, status=None) -> list[dict]:
        query = {}
        if master_id: query["master_id"] = master_id
        if status: query["status"] = status
        docs = list(self.collection.find(query).sort("id", 1))
        return [self._format(doc) for doc in docs]

    def update(self, timeslot_id: str, timeslot: TimeslotUpdate) -> int:
        result = self.collection.update_one({"id": timeslot_id}, {"$set": timeslot.model_dump(exclude_unset=True)})
        return result.modified_count

    def mark_booked(self, timeslot_id: str, booking_id: str) -> int:
        return self.collection.update_one({"id": timeslot_id, "status": "free"}, {"$set": {"status": "booked", "booking_id": booking_id}}).modified_count

    def mark_free(self, timeslot_id: str) -> int:
        return self.collection.update_one({"id": timeslot_id}, {"$set": {"status": "free", "booking_id": None}}).modified_count

    def delete(self, timeslot_id: str) -> int:
        return self.collection.delete_one({"id": timeslot_id}).deleted_count

    def _format(self, doc):
        if not doc: return None
        doc["id"] = str(doc.get("id"))
        if "_id" in doc: del doc["_id"]
        return doc
