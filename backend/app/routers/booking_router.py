from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_admin, get_current_user, logger
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
        elif current_user["role"] == "admin":
            pass
        else:
            raise HTTPException(status_code=403, detail="Доступ заборонено")

        booking = service.create(BookingCreate(**payload_data))
        logger.info("Користувач %s створив бронювання %s", current_user.get("email"), booking.get("id"))
        return booking
    except ValueError as exc:
        _raise_from_value_error(exc)

@router.get("", response_model=list[BookingDB])
def list_bookings(service: BookingService = Depends(get_booking_service)):
    return service.list()

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
