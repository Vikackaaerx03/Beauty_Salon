from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.security import get_current_admin, get_current_user, logger
from app.db.database import get_users_collection
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserDB, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(collection=Depends(get_users_collection)) -> UserService:
    return UserService(UserRepository(collection))


@router.get("/masters", response_model=list[UserDB])
def get_masters(sort: str | None = None, service: UserService = Depends(get_user_service)):
    return service.get_all(role="master", sort_by=sort)


@router.post("", response_model=UserDB, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        created = service.create(payload)
        logger.info("Адмін %s створив користувача %s", current_admin.get("email"), payload.email)
        return created
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[UserDB])
def list_users(
    role: str | None = None,
    service_id: str | None = None,
    sort_by: str | None = None,
    service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin),
):
    return service.get_all(role=role, service_id=service_id, sort_by=sort_by)


@router.get("/{user_id}", response_model=UserDB)
def get_user(user_id: str, service: UserService = Depends(get_user_service), current_admin: dict = Depends(get_current_admin)):
    try:
        return service.get_by_id(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{user_id}", response_model=UserDB)
def update_user(
    user_id: str,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin" and current_user.get("id") != str(user_id):
        raise HTTPException(status_code=403, detail="Доступ заборонено")
    try:
        return service.update(user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{user_id}/avatar", response_model=UserDB)
async def upload_avatar(
    user_id: str,
    avatar: UploadFile = File(...),
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin" and current_user.get("id") != str(user_id):
        raise HTTPException(status_code=403, detail="Доступ заборонено")

    suffix = Path(avatar.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"

    project_root = Path(__file__).resolve().parents[3]
    images_dir = project_root / "frontend" / "assets" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    try:
        target_user = service.get_by_id(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    prefix = "user_icon_" if target_user.get("role") == "client" else "icon_"

    existing_numbers = []
    for file in images_dir.glob(f"{prefix}*"):
        name = file.stem
        if name.startswith(prefix) and name[len(prefix):].isdigit():
            existing_numbers.append(int(name[len(prefix):]))

    next_number = max(existing_numbers, default=0) + 1
    filename = f"{prefix}{next_number}{suffix}"
    file_path = images_dir / filename

    content = await avatar.read()
    file_path.write_bytes(content)

    try:
        return service.update(user_id, UserUpdate(avatar=f"assets/images/{filename}"))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    current_admin: dict = Depends(get_current_admin),
):
    try:
        service.delete(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
