from pymongo.collection import Collection
from typing import Optional
from app.db.database import to_mongo_id
from app.schemas.payments_schema import PaymentCreate, PaymentUpdate

class PaymentRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, payment: PaymentCreate) -> str:
        data = payment.model_dump()
        last_item = self.collection.find_one(sort=[("id", -1)])
        new_id = int(last_item["id"]) + 1 if last_item and "id" in last_item else 1
        
        data["id"] = str(new_id)
        self.collection.insert_one(data)
        return data["id"]

    def get_by_id(self, payment_id: str) -> dict | None:
        return self._format(self.collection.find_one({"id": payment_id}))

    def get_all(self, booking_id=None) -> list[dict]:
        query = {"booking_id": booking_id} if booking_id else {}
        docs = list(self.collection.find(query).sort("id", 1))
        return [self._format(doc) for doc in docs]

    def update(self, payment_id: str, payment: PaymentUpdate) -> int:
        return self.collection.update_one({"id": payment_id}, {"$set": payment.model_dump(exclude_unset=True)}).modified_count

    def delete(self, payment_id: str) -> int:
        return self.collection.delete_one({"id": payment_id}).deleted_count

    def _format(self, doc):
        if not doc: return None
        doc["id"] = str(doc.get("id"))
        if "_id" in doc: del doc["_id"]
        return doc
