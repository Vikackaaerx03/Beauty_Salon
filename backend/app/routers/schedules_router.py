from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import get_schedules_collection
from app.repositories.schedules_repository import ScheduleRepository
from app.services.schedules_service import SchedulesService
from app.schemas.schedules_schema import TimeslotCreate, TimeslotDB, TimeslotUpdate

router = APIRouter(prefix="/schedules", tags=["Schedules"])


def get_schedules_service(collection=Depends(get_schedules_collection)) -> SchedulesService:
    return SchedulesService(ScheduleRepository(collection))


@router.post("", response_model=TimeslotDB, status_code=status.HTTP_201_CREATED)
def create_timeslot(payload: TimeslotCreate, service: SchedulesService = Depends(get_schedules_service)):
    return service.create(payload)


@router.get("", response_model=list[TimeslotDB])
def list_timeslots(
    master_id: str | None = None,
    status_filter: str | None = None,
    service: SchedulesService = Depends(get_schedules_service),
):
    return service.list(master_id=master_id, status=status_filter)


@router.get("/{timeslot_id}", response_model=TimeslotDB)
def get_timeslot(timeslot_id: str, service: SchedulesService = Depends(get_schedules_service)):
    try:
        return service.get(timeslot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{timeslot_id}", response_model=TimeslotDB)
def update_timeslot(timeslot_id: str, payload: TimeslotUpdate, service: SchedulesService = Depends(get_schedules_service)):
    try:
        return service.update(timeslot_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{timeslot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timeslot(timeslot_id: str, service: SchedulesService = Depends(get_schedules_service)):
    try:
        service.delete(timeslot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
