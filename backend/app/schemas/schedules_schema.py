from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

TimeslotStatus = Literal["free", "booked"]


class TimeslotBase(BaseModel):
    master_id: str
    start: datetime
    end: datetime
    status: TimeslotStatus = "free"
    booking_id: str | None = None


class TimeslotCreate(TimeslotBase):
    pass


class TimeslotUpdate(BaseModel):
    start: datetime | None = None
    end: datetime | None = None
    status: TimeslotStatus | None = None
    booking_id: str | None = None


class TimeslotDB(TimeslotBase):
    id: str
