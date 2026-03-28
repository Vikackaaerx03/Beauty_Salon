from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import get_settings


_PBKDF2_ALG = "pbkdf2_sha256"
_PBKDF2_ITERATIONS = 200_000
_PBKDF2_SALT_BYTES = 16


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def hash_password(password: str) -> str:
    """Hash a password for storage.

    Uses PBKDF2-HMAC-SHA256 with a per-password random salt.
    Stored format: `pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>`
    """
    salt = secrets.token_bytes(_PBKDF2_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{_PBKDF2_ALG}${_PBKDF2_ITERATIONS}${_b64encode(salt)}${_b64encode(dk)}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored hash.

    Supports the current PBKDF2 format and legacy SHA256 hex digests (for backwards compatibility).
    """
    if not isinstance(password_hash, str) or not password_hash:
        return False

    # Current format: pbkdf2_sha256$iterations$salt$hash
    if password_hash.startswith(f"{_PBKDF2_ALG}$"):
        try:
            _, iterations_str, salt_b64, hash_b64 = password_hash.split("$", 3)
            iterations = int(iterations_str)
            salt = _b64decode(salt_b64)
            expected = _b64decode(hash_b64)
        except Exception:
            return False

        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(candidate, expected)

    # Legacy: plain SHA256 hex digest
    if len(password_hash) == 64 and all(c in "0123456789abcdef" for c in password_hash.lower()):
        candidate = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(candidate, password_hash)

    return False


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
