from __future__ import annotations

from app.repositories.booking_repository import BookingRepository
from app.repositories.schedules_repository import ScheduleRepository
from app.schemas.booking_schema import BookingCreate, BookingUpdate


class BookingService:
    def __init__(self, bookings: BookingRepository, schedules: ScheduleRepository):
        self.bookings = bookings
        self.schedules = schedules

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
        return booking

    def get(self, booking_id: str) -> dict:
        booking = self.bookings.get_by_id(booking_id)
        if booking is None:
            raise ValueError("Booking not found")
        return booking

    def list(self, client_id: str | None = None, master_id: str | None = None) -> list[dict]:
        return self.bookings.get_all(client_id=client_id, master_id=master_id)

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
        return booking

    def set_status(self, booking_id: str, status_value: str) -> dict:
        current = self.bookings.get_by_id(booking_id)
        if current is None:
            raise ValueError("Booking not found")

        updated = self.bookings.update_status(booking_id, status_value)
        if updated == 0:
            raise RuntimeError("Failed to update status")

        if status_value == "canceled":
            self.schedules.mark_free(current["timeslot_id"])

        booking = self.bookings.get_by_id(booking_id)
        if booking is None:
            raise ValueError("Booking not found")
        return booking

    def delete(self, booking_id: str) -> None:
        current = self.bookings.get_by_id(booking_id)
        if current is None:
            raise ValueError("Booking not found")

        deleted = self.bookings.delete(booking_id)
        if deleted == 0:
            raise ValueError("Booking not found")
        self.schedules.mark_free(current["timeslot_id"])
