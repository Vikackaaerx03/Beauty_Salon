from pymongo.collection import Collection
from typing import Optional
from app.db.database import to_mongo_id
from app.schemas.services_schema import ServiceCreate, ServiceUpdate

class ServiceRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, service: ServiceCreate) -> str:
        return str(self.collection.insert_one(service.model_dump()).inserted_id)

    def get_by_id(self, service_id: str) -> dict | None:
        doc = self.collection.find_one({"_id": to_mongo_id(service_id)})
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        return doc

    def get_all(self, min_price: Optional[float] = None, max_price: Optional[float] = None) -> list[dict]:
        query = {}
        if min_price is not None:
            query["price"] = {"$gte": min_price}
        if max_price is not None:
            query.setdefault("price", {})["$lte"] = max_price
        docs = list(self.collection.find(query).sort("name", 1))
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    def update(self, service_id: str, service: ServiceUpdate) -> int:
        result = self.collection.update_one(
            {"_id": to_mongo_id(service_id)}, {"$set": service.model_dump(exclude_unset=True)}
        )
        return result.modified_count

    def delete(self, service_id: str) -> int:
        result = self.collection.delete_one({"_id": to_mongo_id(service_id)})
        return result.deleted_count
