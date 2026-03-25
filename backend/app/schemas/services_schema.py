from __future__ import annotations
from pydantic import BaseModel

class ServiceBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    duration_minutes: int = 60


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    duration_minutes: int | None = None


class ServiceDB(ServiceBase):
    id: str
