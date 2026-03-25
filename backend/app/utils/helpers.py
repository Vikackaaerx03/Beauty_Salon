import os
from uuid import uuid4
import pytest
from app.core import config as config_module
from app.db.database import (
    COLLECTION_BOOKINGS,
    COLLECTION_SCHEDULES,
    COLLECTION_SERVICES,
    COLLECTION_USERS,
    close_client,
    get_client,
    get_db,
    init_db,
)
from app.repositories.booking_repository import BookingRepository
from app.repositories.schedules_repository import ScheduleRepository
from app.repositories.services_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.booking_schema import BookingCreate, BookingUpdate
from app.schemas.schedules_schema import TimeslotCreate
from app.schemas.services_schema import ServiceCreate, ServiceUpdate
from app.schemas.user_schema import UserCreate


def _ensure_mongo_or_skip() -> None:
    try:
        get_client().admin.command("ping")
    except Exception as exc:  
        pytest.skip(f"MongoDB is not available: {exc}")


@pytest.fixture(scope="session")
def mongo_db():
    _ensure_mongo_or_skip()

    test_db_name = f"beauty_salon_test_{uuid4().hex}"
    os.environ["MONGO_DB_NAME"] = test_db_name
    os.environ["DB_NAME"] = test_db_name

    config_module.get_settings.cache_clear()
    get_client.cache_clear()

    db = get_db()
    init_db(db)

    yield db

    get_client().drop_database(test_db_name)
    close_client()
    config_module.get_settings.cache_clear()


def test_services_crud(mongo_db):
    repo = ServiceRepository(mongo_db[COLLECTION_SERVICES])

    service_id = repo.create(ServiceCreate(name="Haircut", description="Classic haircut", price=250.0, duration_minutes=45))
    service = repo.get_by_id(service_id)
    assert service is not None
    assert service["id"] == service_id

    all_services = repo.get_all()
    assert any(s["id"] == service_id for s in all_services)

    repo.update(service_id, ServiceUpdate(price=300.0))
    updated = repo.get_by_id(service_id)
    assert updated is not None and updated["price"] == 300.0

    deleted = repo.delete(service_id)
    assert deleted == 1
    assert repo.get_by_id(service_id) is None


def test_users_masters_sort_and_filter(mongo_db):
    services = ServiceRepository(mongo_db[COLLECTION_SERVICES])
    user_repo = UserRepository(mongo_db[COLLECTION_USERS])

    s1 = services.create(ServiceCreate(name="Manicure", description=None, price=400.0, duration_minutes=60))
    s2 = services.create(ServiceCreate(name="Pedicure", description=None, price=500.0, duration_minutes=75))

    m1 = user_repo.create(
        UserCreate(
            name="Anna",
            email=f"anna_{uuid4().hex}@example.com",
            password="pass",
            role="master",
            rating=4.9,
            services_offered=[s1],
        )
    )
    m2 = user_repo.create(
        UserCreate(
            name="Bohdan",
            email=f"bohdan_{uuid4().hex}@example.com",
            password="pass",
            role="master",
            rating=4.2,
            services_offered=[s2],
        )
    )

    masters_by_rating = user_repo.get_all(role="master", sort_by="rating")
    ids = [u["id"] for u in masters_by_rating]
    assert m1 in ids and m2 in ids
    assert ids.index(m1) < ids.index(m2)

    masters_for_s1 = user_repo.get_all(role="master", service_id=s1)
    assert [u["id"] for u in masters_for_s1] == [m1]


def test_schedule_and_booking_flow(mongo_db):
    services = ServiceRepository(mongo_db[COLLECTION_SERVICES])
    users = UserRepository(mongo_db[COLLECTION_USERS])
    schedules = ScheduleRepository(mongo_db[COLLECTION_SCHEDULES])
    bookings = BookingRepository(mongo_db[COLLECTION_BOOKINGS])

    service_id = services.create(ServiceCreate(name="Massage", description="Relax", price=800.0, duration_minutes=60))
    master_id = users.create(
        UserCreate(
            name="Master",
            email=f"master_{uuid4().hex}@example.com",
            password="pass",
            role="master",
            rating=5.0,
            services_offered=[service_id],
        )
    )
    client_id = users.create(
        UserCreate(
            name="Client",
            email=f"client_{uuid4().hex}@example.com",
            password="pass",
            role="client",
            rating=0.0,
            services_offered=[],
        )
    )

    timeslot_id = schedules.create(
        TimeslotCreate(
            master_id=master_id,
            start="2026-03-24T10:00:00",
            end="2026-03-24T11:00:00",
            status="free",
            booking_id=None,
        )
    )

    booking_id = bookings.create(
        BookingCreate(
            client_id=client_id,
            master_id=master_id,
            service_id=service_id,
            timeslot_id=timeslot_id,
            status="pending",
        )
    )

    assert schedules.mark_booked(timeslot_id, booking_id) == 1
    booked = schedules.get_by_id(timeslot_id)
    assert booked is not None and booked["status"] == "booked" and booked["booking_id"] == booking_id

    assert schedules.mark_booked(timeslot_id, "another") == 0

    assert bookings.update(booking_id, BookingUpdate(status="canceled")) == 1
    assert schedules.mark_free(timeslot_id) == 1
