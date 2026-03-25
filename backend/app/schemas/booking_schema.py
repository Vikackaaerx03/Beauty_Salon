from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel

class BookingBase(BaseModel):
    client_id: str
    master_id: str
    service_id: str
    timeslot_id: str
    status: str = "pending"  # pending, confirmed, completed, canceled


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    timeslot_id: str | None = None
    status: str | None = None


class BookingDB(BookingBase):
    id: str
    created_at: datetime
    updated_at: datetime
