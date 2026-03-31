from pymongo.collection import Collection
from typing import Optional
from app.db.database import to_mongo_id
from app.schemas.services_schema import ServiceCreate, ServiceUpdate

class ServiceRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, service: ServiceCreate) -> str:
        data = service.model_dump()
        last_item = self.collection.find_one(sort=[("id", -1)])
        new_id = int(last_item["id"]) + 1 if last_item and "id" in last_item else 1
        
        data["id"] = str(new_id)
        self.collection.insert_one(data)
        return data["id"]

    def get_by_id(self, service_id: str) -> dict | None:
        return self._format(self.collection.find_one({"id": service_id}))

    def get_all(self, min_price: Optional[float] = None, max_price: Optional[float] = None) -> list[dict]:
        query = {}
        if min_price is not None: query["price"] = {"$gte": min_price}
        if max_price is not None: query.setdefault("price", {})["$lte"] = max_price
        
        docs = list(self.collection.find(query).sort("id", 1))
        return [self._format(doc) for doc in docs]

    def update(self, service_id: str, service: ServiceUpdate) -> int:
        result = self.collection.update_one({"id": service_id}, {"$set": service.model_dump(exclude_unset=True)})
        return result.modified_count

    def delete(self, service_id: str) -> int:
        return self.collection.delete_one({"id": service_id}).deleted_count

    def _format(self, doc):
        if not doc: return None
        doc["id"] = str(doc.get("id"))
        if "_id" in doc: del doc["_id"]
        return doc