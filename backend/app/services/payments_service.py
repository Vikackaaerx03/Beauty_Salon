from __future__ import annotations
from datetime import datetime
from app.repositories.payments_repository import PaymentRepository
from app.schemas.payments_schema import PaymentCreate, PaymentUpdate


class PaymentsService:
    def __init__(self, repo: PaymentRepository):
        self.repo = repo

    def create(self, payload: PaymentCreate) -> dict:
        if payload.method == "card":
            payload = payload.model_copy(update={"status": "paid", "paid_at": payload.paid_at or datetime.utcnow()})
        elif payload.method == "cash":
            payload = payload.model_copy(update={"status": "unpaid", "paid_at": None})

        payment_id = self.repo.create(payload)
        payment = self.repo.get_by_id(payment_id)
        if payment is None:
            raise RuntimeError("Failed to create payment")
        return payment

    def get(self, payment_id: str) -> dict:
        payment = self.repo.get_by_id(payment_id)
        if payment is None:
            raise ValueError("Payment not found")
        return payment

    def list(self, booking_id: str | None = None) -> list[dict]:
        return self.repo.get_all(booking_id=booking_id)

    def update(self, payment_id: str, payload: PaymentUpdate) -> dict:
        if payload.method == "card":
            payload = payload.model_copy(update={"status": payload.status or "paid", "paid_at": payload.paid_at or datetime.utcnow()})
        elif payload.method == "cash":
            payload = payload.model_copy(update={"status": payload.status or "unpaid", "paid_at": None})
        elif payload.status == "paid" and payload.paid_at is None:
            payload = payload.model_copy(update={"paid_at": datetime.utcnow()})

        updated = self.repo.update(payment_id, payload)
        if updated == 0:
            existing = self.repo.get_by_id(payment_id)
            if existing is None:
                raise ValueError("Payment not found")
            return existing
        payment = self.repo.get_by_id(payment_id)
        if payment is None:
            raise ValueError("Payment not found")
        return payment

    def delete(self, payment_id: str) -> None:
        deleted = self.repo.delete(payment_id)
        if deleted == 0:
            raise ValueError("Payment not found")
