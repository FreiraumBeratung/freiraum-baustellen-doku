"""Admin-Nutzungssignal — nur Zeitstempel, keine Mandanten-Inhalte.

Liest pro Firma (tenantId) vorhandene createdAt/updatedAt/uploadedAt-Felder
aus den Tenant-JSONs. So gilt „heute benutzt“ auch rückwirkend ohne neuen Track.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.services.tenant_storage import tenant_data_dir, tenant_json_path

BERLIN = ZoneInfo("Europe/Berlin")

_TS_KEYS = ("createdAt", "updatedAt", "uploadedAt")

# (Dateiname, Listen-Key oder None = Root ist Liste)
_ACTIVITY_SOURCES: tuple[tuple[str, str | None], ...] = (
    ("reports.json", "reports"),
    ("protocols.json", "protocols"),
    ("delivery_notes.json", "deliveryNotes"),
    ("time_entries.json", "entries"),
    ("audio_uploads.json", None),
)


def _parse_iso(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _collect_from_item(item: Any, into: list[datetime]) -> None:
    if not isinstance(item, dict):
        return
    for key in _TS_KEYS:
        dt = _parse_iso(item.get(key))
        if dt is not None:
            into.append(dt)
    photos = item.get("photos")
    if isinstance(photos, list):
        for photo in photos:
            if isinstance(photo, dict):
                dt = _parse_iso(photo.get("uploadedAt") or photo.get("createdAt"))
                if dt is not None:
                    into.append(dt)


def _items_from_file(path, list_key: str | None) -> list[Any]:
    if not path.is_file():
        return []
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError, TypeError):
        return []
    if list_key is None:
        return data if isinstance(data, list) else []
    if isinstance(data, dict):
        raw = data.get(list_key)
        return raw if isinstance(raw, list) else []
    return []


def tenant_last_activity_at(tenant_id: str) -> datetime | None:
    tid = str(tenant_id or "").strip()
    if not tid:
        return None
    if not tenant_data_dir(tid).is_dir():
        return None

    found: list[datetime] = []
    for filename, list_key in _ACTIVITY_SOURCES:
        for item in _items_from_file(tenant_json_path(tid, filename), list_key):
            _collect_from_item(item, found)
    if not found:
        return None
    return max(found)


def activity_public_fields(tenant_id: str, *, now: datetime | None = None) -> dict[str, Any]:
    """Metadaten für Admin-Liste: lastActivityAt (UTC ISO) + usedToday (Europe/Berlin)."""
    last = tenant_last_activity_at(tenant_id)
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=timezone.utc)

    used_today = False
    last_iso = ""
    if last is not None:
        last_iso = last.astimezone(timezone.utc).isoformat()
        used_today = last.astimezone(BERLIN).date() == clock.astimezone(BERLIN).date()

    return {
        "lastActivityAt": last_iso,
        "usedToday": used_today,
    }
