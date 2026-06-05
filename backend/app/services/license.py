"""M2 Lizenzstatus — Schreib-Sperre bei pausiertem Zugang (Read-only-Modus)."""

from __future__ import annotations

from typing import Any

LICENSE_SUSPENDED_DETAIL = (
    "Ihr Zugang ist pausiert. Bitte wenden Sie sich an Freiraum Unternehmensberatung."
)


def is_license_active(user: dict[str, Any] | None) -> bool:
    """Fehlendes Feld = aktiv (bestehende User ohne Migration)."""
    if not isinstance(user, dict):
        return True
    value = user.get("licenseActive")
    if value is None:
        return True
    return bool(value)


def license_active_for_user_id(user_id: str, read_users) -> bool:
    for u in read_users():
        if u.get("id") == user_id:
            return is_license_active(u)
    return False
