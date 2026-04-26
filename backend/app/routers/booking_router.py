from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_admin, get_current_master_or_admin, get_current_user, logger
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
    status_code = 400
    if "not found" in message:
        status_code = 404
    if "not free" in message or "booked" in message:
        status_code = 409
    raise HTTPException(status_code=status_code, detail=message)


@router.post("", response_model=BookingDB, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    service: BookingService = Depends(get_booking_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        payload_data = payload.model_dump()
        if current_user["role"] == "client":
            payload_data["client_id"] = current_user["id"]
        elif current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Доступ заборонено")

        booking = service.create(BookingCreate(**payload_data))
        logger.info("Користувач %s створив бронювання %s", current_user.get("email"), booking.get("id"))
        return booking
    except ValueError as exc:
        _raise_from_value_error(exc)


@router.get("", response_model=list[BookingDB])
def list_bookings(
    service: BookingService = Depends(get_booking_service),
    current_admin: dict = Depends(get_current_admin),
):
    return service.list()


@router.get("/user/{user_id}", response_model=list[BookingDB])
def list_user_bookings(
    user_id: str,
    service: BookingService = Depends(get_booking_service),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin" and current_user.get("id") != str(user_id):
        raise HTTPException(status_code=403, detail="Доступ заборонено")
    return service.list(client_id=str(user_id))


@router.get("/master/{master_id}", response_model=list[BookingDB])
def list_master_bookings(
    master_id: str,
    service: BookingService = Depends(get_booking_service),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin" and current_user.get("id") != str(master_id):
        raise HTTPException(status_code=403, detail="Доступ заборонено")
    return service.list(master_id=str(master_id))


@router.patch("/{booking_id}", response_model=BookingDB)
def update_booking(
    booking_id: str,
    payload: BookingUpdate,
    service: BookingService = Depends(get_booking_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        return service.update(booking_id, payload)
    except ValueError as exc:
        _raise_from_value_error(exc)


@router.patch("/{booking_id}/status", response_model=BookingDB)
def update_booking_status(
    booking_id: str,
    payload: dict,
    service: BookingService = Depends(get_booking_service),
    current_user: dict = Depends(get_current_master_or_admin),
):
    status_value = str(payload.get("status", "")).strip()
    if not status_value:
        raise HTTPException(status_code=400, detail="Статус обов'язковий")
    try:
        current_booking = service.get(booking_id)
        if current_user.get("role") == "master" and str(current_booking.get("master_id")) != str(current_user.get("id")):
            raise HTTPException(status_code=403, detail="Доступ заборонено")
        updated = service.set_status(booking_id, status_value)
        logger.info("%s %s оновив статус бронювання %s на %s", current_user.get("role"), current_user.get("email"), booking_id, status_value)
        return updated
    except ValueError as exc:
        _raise_from_value_error(exc)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: str,
    service: BookingService = Depends(get_booking_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        service.delete(booking_id)
        logger.info("Адмін %s видалив бронювання %s", current_admin.get("email"), booking_id)
    except ValueError as exc:
        _raise_from_value_error(exc)
