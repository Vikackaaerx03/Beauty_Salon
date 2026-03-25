from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PaymentMethod = Literal["card", "cash"]
PaymentStatus = Literal["paid", "unpaid", "refunded"]

class PaymentBase(BaseModel):
    booking_id: str
    amount: float
    method: PaymentMethod = "card"
    status: PaymentStatus = "paid"
    paid_at: datetime | None = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    amount: float | None = None
    paid_at: datetime | None = None
    method: PaymentMethod | None = None
    status: PaymentStatus | None = None


class PaymentDB(PaymentBase):
    id: str
