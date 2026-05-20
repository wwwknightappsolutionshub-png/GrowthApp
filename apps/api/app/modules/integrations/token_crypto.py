"""Encrypt integration tokens at rest."""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    raw = (settings.INTEGRATIONS_TOKEN_ENCRYPTION_KEY or "").strip()
    if not raw:
        raise ValueError("INTEGRATIONS_TOKEN_ENCRYPTION_KEY is not configured")
    try:
        key = base64.urlsafe_b64decode(raw + "==")
        if len(key) == 32:
            return Fernet(base64.urlsafe_b64encode(key))
    except Exception:  # noqa: BLE001
        pass
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt integration token") from exc
