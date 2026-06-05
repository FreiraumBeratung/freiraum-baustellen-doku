"""M4 Passwort-Hashing — bcrypt mit Lazy-Migration von Klartext (password-Feld)."""

from __future__ import annotations

from typing import Any

import bcrypt

_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def is_password_hashed(value: Any) -> bool:
    s = str(value or "")
    return any(s.startswith(p) for p in _BCRYPT_PREFIXES)


def hash_password(plain: str) -> str:
    pw = str(plain or "").encode("utf-8")
    if not pw:
        raise ValueError("Passwort fehlt")
    hashed = bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12))
    return hashed.decode("ascii")


def verify_password(plain: str, user: dict[str, Any]) -> bool:
    """Prueft Passwort gegen passwordHash oder legacy password (Klartext/bcrypt)."""
    pw = str(plain or "").encode("utf-8")
    if not pw:
        return False

    stored_hash = user.get("passwordHash")
    if isinstance(stored_hash, str) and stored_hash.strip():
        if _check_bcrypt(pw, stored_hash):
            return True

    legacy = user.get("password")
    if legacy is None:
        return False
    legacy_s = str(legacy)
    if is_password_hashed(legacy_s):
        return _check_bcrypt(pw, legacy_s)
    return legacy_s == str(plain or "")


def apply_password_hash_to_user(user: dict[str, Any], plain: str) -> None:
    user["passwordHash"] = hash_password(plain)
    user.pop("password", None)


def user_needs_password_migration(user: dict[str, Any]) -> bool:
    if user.get("password") is not None:
        return True
    if not user.get("passwordHash"):
        return True
    return False


def _check_bcrypt(plain_bytes: bytes, stored: str) -> bool:
    try:
        return bcrypt.checkpw(plain_bytes, stored.encode("ascii"))
    except (ValueError, TypeError):
        return False
