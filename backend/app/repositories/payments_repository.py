from __future__ import annotations

from pymongo.collection import Collection

from app.db.database import to_mongo_id
from app.schemas.payments_schema import PaymentCreate, PaymentUpdate


def _id_query(identifier: str) -> dict:
    return {"$or": [{"id": str(identifier)}, {"_id": to_mongo_id(identifier)}]}


class PaymentRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def _format(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.get("id") or doc.get("_id"))
        doc.pop("_id", None)
        if doc.get("booking_id") is not None:
            doc["booking_id"] = str(doc["booking_id"])
        return doc

    def create(self, payment: PaymentCreate) -> str:
        data = payment.model_dump()
        data["id"] = str(self.collection.count_documents({}) + 1)
        self.collection.insert_one(data)
        return data["id"]

    def get_by_id(self, payment_id: str) -> dict | None:
        return self._format(self.collection.find_one(_id_query(payment_id)))

    def get_all(self, booking_id=None) -> list[dict]:
        query = {"booking_id": {"$in": [str(booking_id), to_mongo_id(booking_id)]}} if booking_id else {}
        docs = [self._format(doc) for doc in list(self.collection.find(query))]
        return sorted(
            [doc for doc in docs if doc is not None],
            key=lambda doc: int(str(doc.get("id") or 10**9)) if str(doc.get("id") or "").isdigit() else 10**9,
        )

    def update(self, payment_id: str, payment: PaymentUpdate) -> int:
        return self.collection.update_one(_id_query(payment_id), {"$set": payment.model_dump(exclude_unset=True)}).modified_count

    def delete(self, payment_id: str) -> int:
        return self.collection.delete_one(_id_query(payment_id)).deleted_count
