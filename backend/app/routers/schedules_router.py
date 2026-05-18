from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_admin, logger
from app.db.database import get_bookings_collection, get_feedback_collection, get_payments_collection, get_schedules_collection
from app.repositories.booking_repository import BookingRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.payments_repository import PaymentRepository
from app.repositories.schedules_repository import ScheduleRepository
from app.services.schedules_service import SchedulesService
from app.schemas.schedules_schema import TimeslotCreate, TimeslotDB, TimeslotUpdate

router = APIRouter(prefix="/schedules", tags=["Schedules"])


def get_schedules_service(
    collection=Depends(get_schedules_collection),
    bookings_collection=Depends(get_bookings_collection),
    payments_collection=Depends(get_payments_collection),
    feedback_collection=Depends(get_feedback_collection),
) -> SchedulesService:
    return SchedulesService(
        ScheduleRepository(collection),
        BookingRepository(bookings_collection),
        PaymentRepository(payments_collection),
        FeedbackRepository(feedback_collection),
    )


@router.post("", response_model=TimeslotDB, status_code=status.HTTP_201_CREATED)
def create_timeslot(
    payload: TimeslotCreate,
    service: SchedulesService = Depends(get_schedules_service),
    current_admin: dict = Depends(get_current_admin),
):
    created = service.create(payload)
    logger.info("Адмін %s створив слот %s", current_admin.get("email"), created)
    return created


@router.get("", response_model=list[TimeslotDB])
def list_timeslots(
    master_id: str | None = None,
    status_filter: str | None = None,
    service: SchedulesService = Depends(get_schedules_service),
    include_deleted: bool = False,
):
    return service.list(master_id=master_id, status=status_filter, include_deleted=include_deleted)


@router.get("/{timeslot_id}", response_model=TimeslotDB)
def get_timeslot(timeslot_id: str, service: SchedulesService = Depends(get_schedules_service)):
    try:
        return service.get(timeslot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{timeslot_id}", response_model=TimeslotDB)
def update_timeslot(
    timeslot_id: str,
    payload: TimeslotUpdate,
    service: SchedulesService = Depends(get_schedules_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        updated = service.update(timeslot_id, payload)
        logger.info("Адмін %s оновив слот %s", current_admin.get("email"), timeslot_id)
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{timeslot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timeslot(
    timeslot_id: str,
    service: SchedulesService = Depends(get_schedules_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        service.delete(timeslot_id)
        logger.info("Адмін %s видалив слот %s", current_admin.get("email"), timeslot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
