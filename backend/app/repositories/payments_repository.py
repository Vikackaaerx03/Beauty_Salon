from pymongo.collection import Collection
from typing import Optional
from app.db.database import to_mongo_id
from app.schemas.payments_schema import PaymentCreate, PaymentUpdate

class PaymentRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, payment: PaymentCreate) -> str:
        return str(self.collection.insert_one(payment.model_dump()).inserted_id)

    def get_by_id(self, payment_id: str) -> dict | None:
        doc = self.collection.find_one({"_id": to_mongo_id(payment_id)})
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        return doc

    def get_all(self, booking_id: Optional[str] = None) -> list[dict]:
        query = {}
        if booking_id:
            query["booking_id"] = booking_id
        docs = list(self.collection.find(query).sort("paid_at", -1))
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    def update(self, payment_id: str, payment: PaymentUpdate) -> int:
        result = self.collection.update_one(
            {"_id": to_mongo_id(payment_id)}, {"$set": payment.model_dump(exclude_unset=True)}
        )
        return result.modified_count

    def delete(self, payment_id: str) -> int:
        result = self.collection.delete_one({"_id": to_mongo_id(payment_id)})
        return result.deleted_count
