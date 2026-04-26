from __future__ import annotations
import json
from functools import lru_cache
import re
from pathlib import Path
from fastapi import Depends
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.core.security import hash_password
from app.core.config import get_settings

COLLECTION_USERS = "users"
COLLECTION_SERVICES = "services"
COLLECTION_SCHEDULES = "schedules"
COLLECTION_BOOKINGS = "bookings"
COLLECTION_PAYMENTS = "payments"
COLLECTION_FEEDBACK = "feedback"

_BASE_DIR = Path(__file__).resolve().parents[2]
_SEED_DIR = _BASE_DIR / "seed"
_SEED_FILES = {
    COLLECTION_USERS: "users.json",
    COLLECTION_SERVICES: "services.json",
    COLLECTION_SCHEDULES: "schedules.json",
    COLLECTION_BOOKINGS: "bookings.json",
    COLLECTION_PAYMENTS: "payments.json",
    COLLECTION_FEEDBACK: "feedback.json",
}

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

    _seed_if_empty(db)
    _seed_missing_from_files(db)
    _apply_demo_passwords(db)
    _normalize_schedule_statuses(db)
    _normalize_feedback_and_ratings(db)


def _seed_if_empty(db: Database) -> None:
    for collection_name, filename in _SEED_FILES.items():
        collection = db[collection_name]
        if collection.count_documents({}) > 0:
            continue

        seed_path = _SEED_DIR / filename
        if not seed_path.exists():
            continue

        with seed_path.open("r", encoding="utf-8") as handle:
            documents = json.load(handle)

        if isinstance(documents, list) and documents:
            collection.insert_many(documents)


def _seed_missing_from_files(db: Database) -> None:
    for collection_name, filename in ((COLLECTION_SCHEDULES, _SEED_FILES[COLLECTION_SCHEDULES]),):
        collection = db[collection_name]
        seed_path = _SEED_DIR / filename
        if not seed_path.exists():
            continue

        with seed_path.open("r", encoding="utf-8") as handle:
            documents = json.load(handle)

        if not isinstance(documents, list):
            continue

        for document in documents:
            seed_id = document.get("_id")
            if seed_id is None:
                continue
            exists = collection.find_one({"$or": [{"_id": seed_id}, {"id": str(seed_id)}]})
            if exists is None:
                collection.insert_one(document)


def _apply_demo_passwords(db: Database) -> None:
    """Keep demo credentials predictable for seeded client/master accounts."""
    demo_passwords = {
        "master": "master_1234567890",
        "client": "user_1234567890",
    }

    users = db[COLLECTION_USERS]
    for role, password in demo_passwords.items():
        users.update_many(
            {"role": role, "email": {"$regex": r"@beauty\.local$"}},
            {"$set": {"password_hash": hash_password(password)}},
        )


def _normalize_feedback_and_ratings(db: Database) -> None:
    feedback = db[COLLECTION_FEEDBACK]
    users = db[COLLECTION_USERS]

    docs = list(feedback.find({}))
    for doc in docs:
        update: dict = {}
        for field in ("booking_id", "client_id", "master_id"):
            value = doc.get(field)
            if value is not None and not isinstance(value, str):
                update[field] = str(value)
        rating_value = doc.get("rating")
        if rating_value is not None:
            try:
                normalized_rating = max(1, min(5, int(round(float(rating_value)))))
            except (TypeError, ValueError):
                normalized_rating = 5
            if normalized_rating != rating_value:
                update["rating"] = normalized_rating
        if update:
            feedback.update_one({"_id": doc.get("_id")}, {"$set": update})

    for user in users.find({"role": "master"}):
        master_id = str(user.get("id") or user.get("_id"))
        items = list(feedback.find({"master_id": {"$in": [master_id, to_mongo_id(master_id)]}}))
        ratings = []
        for item in items:
            try:
                ratings.append(int(round(float(item.get("rating", 0)))))
            except (TypeError, ValueError):
                continue
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0.0
        users.update_one({"$or": [{"id": master_id}, {"_id": to_mongo_id(master_id)}]}, {"$set": {"rating": avg_rating}})


def _normalize_schedule_statuses(db: Database) -> None:
    schedules = db[COLLECTION_SCHEDULES]
    bookings = db[COLLECTION_BOOKINGS]

    for slot in schedules.find({}):
        booking_id = slot.get("booking_id")
        booking_exists = False
        if booking_id is not None and booking_id != "":
            booking_exists = bookings.find_one({"timeslot_id": {"$in": [str(slot.get("id") or slot.get("_id")), to_mongo_id(slot.get("id") or slot.get("_id"))]}}) is not None

        desired_status = "booked" if booking_id not in (None, "", "null") or booking_exists else "free"
        update: dict = {"status": desired_status}
        if desired_status == "free":
            update["booking_id"] = None
        schedules.update_one({"_id": slot.get("_id")}, {"$set": update})
