from __future__ import annotations

import logging
from datetime import datetime, timezone
from app.repositories.booking_repository import BookingRepository
from app.repositories.schedules_repository import ScheduleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.services_repository import ServiceRepository
from app.schemas.booking_schema import BookingCreate, BookingUpdate
from app.utils.email_utils import send_feedback_request_email

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self, bookings: BookingRepository, schedules: ScheduleRepository,
                 users: UserRepository = None, services: ServiceRepository = None):
        self.bookings = bookings
        self.schedules = schedules
        self.users = users
        self.services = services

    def _enrich_booking(self, booking: dict | None) -> dict | None:
        if booking is None:
            return None

        enriched = dict(booking)
        if self.users:
            client = self.users.get_by_id(enriched.get("client_id"))
            master = self.users.get_by_id(enriched.get("master_id"))
            if client:
                enriched["client_name"] = client.get("name")
            if master:
                enriched["master_name"] = master.get("name")

        if self.services:
            service = self.services.get_by_id(enriched.get("service_id"))
            if service:
                enriched["service_name"] = service.get("name")

        if self.schedules:
            timeslot = self.schedules.get_by_id(enriched.get("timeslot_id"))
            if timeslot:
                enriched["timeslot_start"] = timeslot.get("start")
                enriched["timeslot_end"] = timeslot.get("end")
                enriched["timeslot_status"] = timeslot.get("status")

        status_value = str(enriched.get("status", "")).strip().lower()
        slot_cutoff = enriched.get("timeslot_end") or enriched.get("timeslot_start")
        if status_value == "pending" and self._is_past(slot_cutoff):
            if self.bookings:
                self.bookings.update_status(str(enriched.get("id")), "expired")
            enriched["status"] = "expired"

        return enriched

    def _is_past(self, value) -> bool:
        if not value:
            return False

        if isinstance(value, str):
            text = value.strip().replace("Z", "+00:00")
            try:
                value = datetime.fromisoformat(text)
            except ValueError:
                return False

        if not isinstance(value, datetime):
            return False

        current = datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc) < current
        return value.astimezone(timezone.utc) < current

    def _enrich_many(self, bookings: list[dict]) -> list[dict]:
        return [booking for booking in (self._enrich_booking(item) for item in bookings) if booking is not None]

    def create(self, payload: BookingCreate) -> dict:
        if not payload.client_id:
            raise ValueError("Client ID is required")

        timeslot = self.schedules.get_by_id(payload.timeslot_id)
        if timeslot is None:
            raise ValueError("Timeslot not found")
        if str(timeslot.get("master_id")) != str(payload.master_id):
            raise ValueError("Timeslot does not belong to this master")
        if timeslot.get("status") != "free" or timeslot.get("booking_id") not in (None, "", "null"):
            raise ValueError("Timeslot is not free")
        existing_booking = self.bookings.get_by_timeslot_id(payload.timeslot_id)
        if existing_booking is not None:
            raise ValueError("Timeslot is not free")

        booking_id = self.bookings.create(payload)
        booked = self.schedules.mark_booked(payload.timeslot_id, booking_id)
        if booked == 0:
            self.bookings.delete(booking_id)
            raise ValueError("Timeslot was booked by someone else")

        booking = self.bookings.get_by_id(booking_id)
        if booking is None:
            raise RuntimeError("Failed to create booking")
        return self._enrich_booking(booking)

    def get(self, booking_id: str) -> dict:
        booking = self.bookings.get_by_id(booking_id)
        if booking is None:
            raise ValueError("Booking not found")
        return self._enrich_booking(booking)

    def list(self, client_id: str | None = None, master_id: str | None = None) -> list[dict]:
        return self._enrich_many(self.bookings.get_all(client_id=client_id, master_id=master_id))

    def update(self, booking_id: str, payload: BookingUpdate) -> dict:
        current = self.bookings.get_by_id(booking_id)
        if current is None:
            raise ValueError("Booking not found")

        old_timeslot_id = current["timeslot_id"]
        new_timeslot_id = payload.timeslot_id

        if new_timeslot_id and new_timeslot_id != old_timeslot_id:
            timeslot = self.schedules.get_by_id(new_timeslot_id)
            if timeslot is None:
                raise ValueError("New timeslot not found")
            if str(timeslot.get("master_id")) != str(current["master_id"]):
                raise ValueError("New timeslot does not belong to this master")
            booked = self.schedules.mark_booked(new_timeslot_id, booking_id)
            if booked == 0:
                raise ValueError("New timeslot is not free")

            updated = self.bookings.update(booking_id, payload)
            if updated == 0:
                self.schedules.mark_free(new_timeslot_id)
                raise RuntimeError("Failed to update booking")

            self.schedules.mark_free(old_timeslot_id)
        else:
            self.bookings.update(booking_id, payload)

        booking = self.bookings.get_by_id(booking_id)
        if booking is None:
            raise ValueError("Booking not found")
        return self._enrich_booking(booking)

    def set_status(self, booking_id: str, status_value: str) -> dict:
        current = self.bookings.get_by_id(booking_id)
        if current is None:
            raise ValueError("Booking not found")

        updated = self.bookings.update_status(booking_id, status_value)
        if updated == 0:
            raise RuntimeError("Failed to update status")

        if status_value == "canceled":
            self.schedules.mark_free(current["timeslot_id"])

        if status_value == "completed" and self.users and self.services:
            try:
                client = self.users.get_by_id(current.get("client_id"))
                master = self.users.get_by_id(current.get("master_id"))
                service = self.services.get_by_id(current.get("service_id"))

                if client and master and service:
                    client_email = client.get("email")
                    client_name = client.get("name", "Клієнте")
                    master_name = master.get("name", "майстра")
                    service_name = service.get("name", "послугу")

                    if client_email:
                        send_feedback_request_email(
                            client_email=client_email,
                            client_name=client_name,
                            master_name=master_name,
                            service_name=service_name,
                            booking_id=booking_id
                        )
            except Exception as e:
                logger.error("Помилка відправки email: %s", e)

        booking = self.bookings.get_by_id(booking_id)
        if booking is None:
            raise ValueError("Booking not found")
        return self._enrich_booking(booking)

    def delete(self, booking_id: str) -> None:
        current = self.bookings.get_by_id(booking_id)
        if current is None:
            raise ValueError("Booking not found")

        deleted = self.bookings.delete(booking_id)
        if deleted == 0:
            raise ValueError("Booking not found")
        self.schedules.mark_free(current["timeslot_id"])
