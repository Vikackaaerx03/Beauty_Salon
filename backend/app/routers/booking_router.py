from fastapi import APIRouter, Depends, HTTPException, status
from app.db.database import get_bookings_collection, get_schedules_collection
from app.repositories.booking_repository import BookingRepository
from app.repositories.schedules_repository import ScheduleRepository
from app.schemas.booking_schema import BookingCreate, BookingDB, BookingUpdate
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def get_booking_service(
    bookings_collection=Depends(get_bookings_collection),
    schedules_collection=Depends(get_schedules_collection),
) -> BookingService:
    return BookingService(BookingRepository(bookings_collection), ScheduleRepository(schedules_collection))


def _raise_from_value_error(exc: ValueError) -> None:
    message = str(exc)
    if "not found" in message:
        raise HTTPException(status_code=404, detail=message)
    if "does not belong" in message:
        raise HTTPException(status_code=400, detail=message)
    if "not free" in message or "booked" in message:
        raise HTTPException(status_code=409, detail=message)
    raise HTTPException(status_code=400, detail=message)


@router.post("", response_model=BookingDB, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    service: BookingService = Depends(get_booking_service),
):
    try:
        return service.create(payload)
    except ValueError as exc:
        _raise_from_value_error(exc)


@router.get("", response_model=list[BookingDB])
def list_bookings(
    client_id: str | None = None,
    master_id: str | None = None,
    service: BookingService = Depends(get_booking_service),
):
    return service.list(client_id=client_id, master_id=master_id)


@router.get("/{booking_id}", response_model=BookingDB)
def get_booking(booking_id: str, service: BookingService = Depends(get_booking_service)):
    try:
        return service.get(booking_id)
    except ValueError as exc:
        _raise_from_value_error(exc)


@router.patch("/{booking_id}", response_model=BookingDB)
def update_booking(
    booking_id: str,
    payload: BookingUpdate,
    service: BookingService = Depends(get_booking_service),
):
    try:
        return service.update(booking_id, payload)
    except ValueError as exc:
        _raise_from_value_error(exc)


@router.post("/{booking_id}/status", response_model=BookingDB)
def set_booking_status(
    booking_id: str,
    status_value: str,
    service: BookingService = Depends(get_booking_service),
):
    try:
        return service.set_status(booking_id, status_value)
    except ValueError as exc:
        _raise_from_value_error(exc)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: str,
    service: BookingService = Depends(get_booking_service),
):
    try:
        service.delete(booking_id)
    except ValueError as exc:
        _raise_from_value_error(exc)
