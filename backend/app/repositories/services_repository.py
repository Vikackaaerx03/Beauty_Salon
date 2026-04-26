from __future__ import annotations

from typing import Optional

from pymongo.collection import Collection

from app.db.database import to_mongo_id
from app.schemas.services_schema import ServiceCreate, ServiceUpdate


def _id_query(identifier: str) -> dict:
    return {"$or": [{"id": str(identifier)}, {"_id": to_mongo_id(identifier)}]}


class ServiceRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, service: ServiceCreate) -> str:
        data = service.model_dump()
        data["id"] = str(self.collection.count_documents({}) + 1)
        self.collection.insert_one(data)
        return data["id"]

    def get_by_id(self, service_id: str) -> dict | None:
        return self._format(self.collection.find_one(_id_query(service_id)))

    def get_all(self, min_price: Optional[float] = None, max_price: Optional[float] = None) -> list[dict]:
        query: dict = {}
        if min_price is not None:
            query["price"] = {"$gte": min_price}
        if max_price is not None:
            query.setdefault("price", {})["$lte"] = max_price

        docs = [self._format(doc) for doc in list(self.collection.find(query))]
        return sorted(
            docs,
            key=lambda doc: int(str(doc.get("id") or 10**9)) if str(doc.get("id") or "").isdigit() else 10**9,
        )

    def update(self, service_id: str, service: ServiceUpdate) -> int:
        result = self.collection.update_one(_id_query(service_id), {"$set": service.model_dump(exclude_unset=True)})
        return result.modified_count

    def delete(self, service_id: str) -> int:
        return self.collection.delete_one(_id_query(service_id)).deleted_count

    def _format(self, doc: dict | None) -> dict | None:
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.get("id") or doc.get("_id"))
        doc.pop("_id", None)
        return doc
