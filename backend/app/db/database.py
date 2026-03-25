from __future__ import annotations
from functools import lru_cache
import re
from fastapi import Depends
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.core.config import get_settings

COLLECTION_USERS = "users"
COLLECTION_SERVICES = "services"
COLLECTION_SCHEDULES = "schedules"
COLLECTION_BOOKINGS = "bookings"
COLLECTION_PAYMENTS = "payments"
COLLECTION_FEEDBACK = "feedback"

_HEX_24_RE = re.compile(r"^[0-9a-fA-F]{24}$")


def to_mongo_id(value: str | int | ObjectId) -> str | int | ObjectId:
    """Convert an incoming id into a MongoDB-friendly _id value.

    - 24-hex string -> ObjectId
    - numeric/string ids (e.g. "1") -> keep as-is

    This allows using simple ids in seed data while keeping ObjectId support.
    """
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, str) and _HEX_24_RE.match(value):
        return ObjectId(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


@lru_cache
def get_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.MONGO_URI)


def close_client() -> None:
    try:
        get_client().close()
    finally:
        get_client.cache_clear()


def get_db() -> Database:
    settings = get_settings()
    return get_client()[settings.MONGO_DB_NAME]


def get_collection(name: str, db: Database | None = None) -> Collection:
    if db is None:
        db = get_db()
    return db[name]


def get_users_collection(db: Database = Depends(get_db)) -> Collection:
    return db[COLLECTION_USERS]


def get_services_collection(db: Database = Depends(get_db)) -> Collection:
    return db[COLLECTION_SERVICES]


def get_schedules_collection(db: Database = Depends(get_db)) -> Collection:
    return db[COLLECTION_SCHEDULES]


def get_bookings_collection(db: Database = Depends(get_db)) -> Collection:
    return db[COLLECTION_BOOKINGS]


def get_payments_collection(db: Database = Depends(get_db)) -> Collection:
    return db[COLLECTION_PAYMENTS]


def get_feedback_collection(db: Database = Depends(get_db)) -> Collection:
    return db[COLLECTION_FEEDBACK]


def init_db(db: Database | None = None) -> None:
    if db is None:
        db = get_db()

    db[COLLECTION_USERS].create_index("email", unique=True)
    db[COLLECTION_USERS].create_index([("role", 1), ("name", 1)])
    db[COLLECTION_USERS].create_index([("role", 1), ("rating", -1)])

    db[COLLECTION_SERVICES].create_index("name")
    db[COLLECTION_SERVICES].create_index("price")

    db[COLLECTION_SCHEDULES].create_index([("master_id", 1), ("start", 1)])
    db[COLLECTION_SCHEDULES].create_index([("master_id", 1), ("status", 1)])

    db[COLLECTION_BOOKINGS].create_index([("client_id", 1), ("created_at", -1)])
    db[COLLECTION_BOOKINGS].create_index([("master_id", 1), ("created_at", -1)])
    db[COLLECTION_BOOKINGS].create_index([("timeslot_id", 1)], unique=True, sparse=True)

    db[COLLECTION_PAYMENTS].create_index("booking_id")
    db[COLLECTION_PAYMENTS].create_index("paid_at")

    db[COLLECTION_FEEDBACK].create_index([("master_id", 1), ("created_at", -1)])
    db[COLLECTION_FEEDBACK].create_index("booking_id", unique=True, sparse=True)
