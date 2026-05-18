from __future__ import annotations
from typing import List, Optional
from app.repositories.booking_repository import BookingRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.payments_repository import PaymentRepository
from app.repositories.schedules_repository import ScheduleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.payments_schema import PaymentUpdate
from app.schemas.user_schema import UserCreate, UserUpdate

class UserService:
    def __init__(
        self,
        repo: UserRepository,
        bookings: BookingRepository | None = None,
        payments: PaymentRepository | None = None,
        schedules: ScheduleRepository | None = None,
        feedback: FeedbackRepository | None = None,
    ):
        self.repo = repo
        self.bookings = bookings
        self.payments = payments
        self.schedules = schedules
        self.feedback = feedback

    def get_all(self, role: str | None = None, service_id: str | None = None, sort_by: str | None = None, include_deleted: bool = False) -> List[dict]:
        return self.repo.get_all(role=role, service_id=service_id, sort_by=sort_by, include_deleted=include_deleted)

    def get_by_id(self, user_id: str) -> dict:
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise ValueError("Користувача не знайдено")
        return user

    def create(self, payload: UserCreate) -> dict:
        user_id = self.repo.create(payload)
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise RuntimeError("Не вдалося створити користувача")
        return user

    def update(self, user_id: str, payload: UserUpdate) -> dict:
        self.repo.update(user_id, payload)
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise ValueError("Користувача не знайдено")
        return user

    def delete(self, user_id: str) -> None:
        user = self.repo.get_by_id(user_id)
        if user is None:
            raise ValueError("Користувача не знайдено")

        if self.bookings is not None:
            user_role = str(user.get("role") or "").lower()
            related_bookings: list[dict] = []
            if user_role == "client":
                related_bookings = self.bookings.get_all(client_id=user_id, include_deleted=True)
            elif user_role == "master":
                related_bookings = self.bookings.get_all(master_id=user_id, include_deleted=True)

            for booking in related_bookings:
                booking_status = str(booking.get("status") or "").lower()
                if booking_status in {"completed", "expired", "canceled", "deleted"}:
                    continue
                self.bookings.update_status(str(booking.get("id")), "canceled")

                if self.schedules is not None and booking.get("timeslot_id"):
                    if user_role == "client":
                        self.schedules.mark_free(str(booking["timeslot_id"]))
                    else:
                        self.schedules.delete(str(booking["timeslot_id"]))

                if self.payments is not None:
                    payments = self.payments.get_all(booking_id=str(booking.get("id")), include_deleted=True)
                    for payment in payments:
                        payment_status = str(payment.get("status") or "").lower()
                        if payment_status == "paid":
                            self.payments.update(str(payment.get("id")), PaymentUpdate(status="refunded"))
                        elif payment_status != "deleted":
                            self.payments.update(str(payment.get("id")), PaymentUpdate(status="deleted"))

                if self.feedback is not None:
                    feedbacks = self.feedback.get_all(include_deleted=True)
                    for item in feedbacks:
                        if str(item.get("booking_id")) == str(booking.get("id")):
                            self.feedback.delete(str(item.get("id")))

            if user_role == "master" and self.schedules is not None:
                for slot in self.schedules.get_all(master_id=user_id, include_deleted=True):
                    self.schedules.delete(str(slot.get("id")))

        if self.repo.delete(user_id) == 0:
            raise ValueError("Користувача не знайдено")
