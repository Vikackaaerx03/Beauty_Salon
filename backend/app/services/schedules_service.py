from __future__ import annotations

from app.repositories.schedules_repository import ScheduleRepository
from app.schemas.schedules_schema import TimeslotCreate, TimeslotUpdate


class SchedulesService:
    def __init__(self, repo: ScheduleRepository):
        self.repo = repo

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

    def list(self, master_id: str | None = None, status: str | None = None) -> list[dict]:
        return self.repo.get_all(master_id=master_id, status=status)

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
        deleted = self.repo.delete(timeslot_id)
        if deleted == 0:
            raise ValueError("Timeslot not found")
