from __future__ import annotations

from app.repositories.services_repository import ServiceRepository
from app.schemas.services_schema import ServiceCreate, ServiceUpdate


class ServicesService:
    def __init__(self, repo: ServiceRepository):
        self.repo = repo

    def create(self, payload: ServiceCreate) -> dict:
        service_id = self.repo.create(payload)
        service = self.repo.get_by_id(service_id)
        if service is None:
            raise RuntimeError("Failed to create service")
        return service

    def get(self, service_id: str) -> dict:
        service = self.repo.get_by_id(service_id)
        if service is None:
            raise ValueError("Service not found")
        return service

    def list(self, min_price: float | None = None, max_price: float | None = None) -> list[dict]:
        return self.repo.get_all(min_price=min_price, max_price=max_price)

    def update(self, service_id: str, payload: ServiceUpdate) -> dict:
        updated = self.repo.update(service_id, payload)
        if updated == 0:
            existing = self.repo.get_by_id(service_id)
            if existing is None:
                raise ValueError("Service not found")
            return existing
        service = self.repo.get_by_id(service_id)
        if service is None:
            raise ValueError("Service not found")
        return service

    def delete(self, service_id: str) -> None:
        deleted = self.repo.delete(service_id)
        if deleted == 0:
            raise ValueError("Service not found")
