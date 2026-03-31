from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_admin, logger
from app.db.database import get_services_collection
from app.repositories.services_repository import ServiceRepository
from app.services.services_service import ServicesService
from app.schemas.services_schema import ServiceCreate, ServiceDB, ServiceUpdate

router = APIRouter(prefix="/services", tags=["Services"])


def get_services_service(collection=Depends(get_services_collection)) -> ServicesService:
    return ServicesService(ServiceRepository(collection))


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
):
    return service.list(min_price=min_price, max_price=max_price)


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
