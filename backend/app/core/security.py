from __future__ import annotations

import hashlib
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import get_settings


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def _serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt="beauty-salon-auth")


def create_access_token(payload: dict[str, Any]) -> str:
    return _serializer().dumps(payload)


def decode_access_token(token: str, max_age_seconds: int) -> dict[str, Any] | None:
    try:
        data = _serializer().loads(token, max_age=max_age_seconds)
        return data if isinstance(data, dict) else None
    except (BadSignature, SignatureExpired):
        return None
