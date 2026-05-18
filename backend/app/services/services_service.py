from __future__ import annotations

from app.repositories.booking_repository import BookingRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.payments_repository import PaymentRepository
from app.repositories.schedules_repository import ScheduleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.services_repository import ServiceRepository
from app.schemas.payments_schema import PaymentUpdate
from app.schemas.services_schema import ServiceCreate, ServiceUpdate
from app.schemas.user_schema import UserUpdate


class ServicesService:
    def __init__(
        self,
        repo: ServiceRepository,
        bookings: BookingRepository | None = None,
        users: UserRepository | None = None,
        payments: PaymentRepository | None = None,
        schedules: ScheduleRepository | None = None,
        feedback: FeedbackRepository | None = None,
    ):
        self.repo = repo
        self.bookings = bookings
        self.users = users
        self.payments = payments
        self.schedules = schedules
        self.feedback = feedback

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

    def list(self, min_price: float | None = None, max_price: float | None = None, include_deleted: bool = False) -> list[dict]:
        return self.repo.get_all(min_price=min_price, max_price=max_price, include_deleted=include_deleted)

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
        if self.bookings is not None:
            related_bookings = self.bookings.get_all(include_deleted=True)
            for booking in related_bookings:
                if str(booking.get("service_id")) != str(service_id):
                    continue

                booking_status = str(booking.get("status") or "").lower()
                if booking_status not in {"canceled", "completed", "expired", "deleted"}:
                    self.bookings.update_status(str(booking.get("id")), "canceled")

                if self.schedules is not None and booking.get("timeslot_id"):
                    self.schedules.mark_free(str(booking["timeslot_id"]))

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

        if self.users is not None:
            masters = self.users.get_all(role="master", include_deleted=True)
            for master in masters:
                offered = [str(service) for service in (master.get("services_offered") or [])]
                if str(service_id) not in offered:
                    continue
                updated_services = [service for service in offered if str(service) != str(service_id)]
                self.users.update(str(master.get("id")), UserUpdate(services_offered=updated_services))

        deleted = self.repo.delete(service_id)
        if deleted == 0:
            raise ValueError("Service not found")
