from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import get_settings
from app.core.security import decode_access_token, get_current_admin, logger
from app.db.database import get_bookings_collection, get_feedback_collection, get_payments_collection, get_schedules_collection, get_services_collection, get_users_collection
from app.repositories.booking_repository import BookingRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.payments_repository import PaymentRepository
from app.repositories.schedules_repository import ScheduleRepository
from app.repositories.services_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.services.services_service import ServicesService
from app.schemas.services_schema import ServiceCreate, ServiceDB, ServiceUpdate

router = APIRouter(prefix="/services", tags=["Services"])
optional_bearer = HTTPBearer(auto_error=False)


def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer)) -> dict | None:
    if credentials is None:
        return None

    settings = get_settings()
    payload = decode_access_token(credentials.credentials, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    if not payload:
        return None
    return {"id": payload.get("sub"), "role": payload.get("role")}


def get_services_service(
    services_collection=Depends(get_services_collection),
    bookings_collection=Depends(get_bookings_collection),
    users_collection=Depends(get_users_collection),
    payments_collection=Depends(get_payments_collection),
    schedules_collection=Depends(get_schedules_collection),
    feedback_collection=Depends(get_feedback_collection),
) -> ServicesService:
    return ServicesService(
        ServiceRepository(services_collection),
        BookingRepository(bookings_collection),
        UserRepository(users_collection),
        PaymentRepository(payments_collection),
        ScheduleRepository(schedules_collection),
        FeedbackRepository(feedback_collection),
    )


@router.post("", response_model=ServiceDB, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreate,
    service: ServicesService = Depends(get_services_service),
    current_admin: dict = Depends(get_current_admin),
):
    created = service.create(payload)
    logger.info("Адмін %s створив послугу %s", current_admin.get("email"), payload.name)
    return created


@router.get("", response_model=list[ServiceDB])
def list_services(
    min_price: float | None = None,
    max_price: float | None = None,
    service: ServicesService = Depends(get_services_service),
    current_user: dict | None = Depends(get_optional_user),
    include_deleted: bool = False,
):
    if current_user is not None and current_user.get("role") == "admin":
        include_deleted = True
    return service.list(min_price=min_price, max_price=max_price, include_deleted=include_deleted)


@router.get("/{service_id}", response_model=ServiceDB)
def get_service(service_id: str, service: ServicesService = Depends(get_services_service)):
    try:
        return service.get(service_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{service_id}", response_model=ServiceDB)
def update_service(
    service_id: str,
    payload: ServiceUpdate,
    service: ServicesService = Depends(get_services_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        updated = service.update(service_id, payload)
        logger.info("Адмін %s оновив послугу %s", current_admin.get("email"), service_id)
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: str,
    service: ServicesService = Depends(get_services_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        service.delete(service_id)
        logger.info("Адмін %s видалив послугу %s", current_admin.get("email"), service_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
