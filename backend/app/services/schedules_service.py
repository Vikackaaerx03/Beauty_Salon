from __future__ import annotations

from app.repositories.booking_repository import BookingRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.payments_repository import PaymentRepository
from app.repositories.schedules_repository import ScheduleRepository
from app.schemas.schedules_schema import TimeslotCreate, TimeslotUpdate


class SchedulesService:
    def __init__(
        self,
        repo: ScheduleRepository,
        bookings: BookingRepository | None = None,
        payments: PaymentRepository | None = None,
        feedback: FeedbackRepository | None = None,
    ):
        self.repo = repo
        self.bookings = bookings
        self.payments = payments
        self.feedback = feedback

    def create(self, payload: TimeslotCreate) -> dict:
        timeslot_id = self.repo.create(payload)
        timeslot = self.repo.get_by_id(timeslot_id)
        if timeslot is None:
            raise RuntimeError("Failed to create timeslot")
        return timeslot

    def get(self, timeslot_id: str) -> dict:
        timeslot = self.repo.get_by_id(timeslot_id)
        if timeslot is None:
            raise ValueError("Timeslot not found")
        return timeslot

    def list(self, master_id: str | None = None, status: str | None = None, include_deleted: bool = False) -> list[dict]:
        return self.repo.get_all(master_id=master_id, status=status, include_deleted=include_deleted)

    def update(self, timeslot_id: str, payload: TimeslotUpdate) -> dict:
        updated = self.repo.update(timeslot_id, payload)
        if updated == 0:
            existing = self.repo.get_by_id(timeslot_id)
            if existing is None:
                raise ValueError("Timeslot not found")
            return existing
        timeslot = self.repo.get_by_id(timeslot_id)
        if timeslot is None:
            raise ValueError("Timeslot not found")
        return timeslot

    def delete(self, timeslot_id: str) -> None:
        timeslot = self.repo.get_by_id(timeslot_id)
        if timeslot is None:
            raise ValueError("Timeslot not found")

        booking_id = str(timeslot.get("booking_id") or "")
        if booking_id and self.bookings is not None:
            booking = self.bookings.get_by_id(booking_id)
            if booking is not None and str(booking.get("status") or "").lower() not in {"canceled", "completed", "expired", "deleted"}:
                self.bookings.update_status(booking_id, "canceled")

            if self.payments is not None:
                payments = self.payments.get_all(booking_id=booking_id, include_deleted=True)
                for payment in payments:
                    payment_status = str(payment.get("status") or "").lower()
                    if payment_status == "paid":
                        from app.schemas.payments_schema import PaymentUpdate
                        self.payments.update(str(payment.get("id")), PaymentUpdate(status="refunded"))
                    elif payment_status != "deleted":
                        from app.schemas.payments_schema import PaymentUpdate
                        self.payments.update(str(payment.get("id")), PaymentUpdate(status="deleted"))

            if self.feedback is not None:
                feedbacks = self.feedback.get_all(include_deleted=True)
                for item in feedbacks:
                    if str(item.get("booking_id")) == booking_id:
                        self.feedback.delete(str(item.get("id")))

        deleted = self.repo.delete(timeslot_id)
        if deleted == 0:
            raise ValueError("Timeslot not found")
