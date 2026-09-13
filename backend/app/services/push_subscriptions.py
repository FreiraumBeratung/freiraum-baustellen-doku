"""PWA-Push-Abos (Phase 5.1) — nur speichern, kein Versand.

Mandantentrennung über TenantStore. Jeder User sieht nur eigene Endpoints.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException

from app.services.tenant_storage import TenantStore

MAX_SUBS_PER_USER = 8
MAX_ENDPOINT_LEN = 2048
MAX_KEY_LEN = 255


def vapid_public_key() -> str:
    return str(os.environ.get("FREIRAUM_VAPID_PUBLIC_KEY") or "").strip()


def push_public_config() -> dict[str, Any]:
    pub = vapid_public_key()
    return {"enabled": bool(pub), "publicKey": pub or None}


def _read(store: TenantStore) -> list[dict[str, Any]]:
    data = store.read_json("push_subscriptions.json", {"subscriptions": []})
    return [s for s in list(data.get("subscriptions") or []) if isinstance(s, dict)]


def _write(store: TenantStore, rows: list[dict[str, Any]]) -> None:
    store.write_json("push_subscriptions.json", {"subscriptions": rows})


def _valid_endpoint(raw: str) -> str:
    endpoint = str(raw or "").strip()
    if not endpoint or len(endpoint) > MAX_ENDPOINT_LEN:
        raise HTTPException(status_code=400, detail="Push-Endpoint ungültig.")
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Push-Endpoint ungültig.")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise HTTPException(status_code=400, detail="Push-Endpoint muss HTTPS sein.")
    return endpoint


def _valid_key(raw: Any, *, name: str) -> str:
    val = str(raw or "").strip()
    if not val or len(val) > MAX_KEY_LEN:
        raise HTTPException(status_code=400, detail=f"Push-Schlüssel {name} ungültig.")
    return val


def upsert_subscription(
    store: TenantStore,
    *,
    user_id: str,
    account_role: str,
    employee_id: str | None,
    endpoint: str,
    p256dh: str,
    auth: str,
    user_agent: str = "",
) -> dict[str, Any]:
    uid = str(user_id or "").strip()
    if not uid:
        raise HTTPException(status_code=401, detail="Ungültiges Token")
    ep = _valid_endpoint(endpoint)
    key_p = _valid_key(p256dh, name="p256dh")
    key_a = _valid_key(auth, name="auth")
    ua = str(user_agent or "").strip()[:240]

    rows = _read(store)
    now = datetime.now(timezone.utc).isoformat()
    existing = next((r for r in rows if str(r.get("endpoint") or "") == ep), None)
    if existing and str(existing.get("userId") or "") != uid:
        raise HTTPException(status_code=403, detail="Endpoint gehört zu einem anderen Zugang.")

    if existing:
        existing["keys"] = {"p256dh": key_p, "auth": key_a}
        existing["enabled"] = True
        existing["updatedAt"] = now
        existing["userAgent"] = ua
        existing["accountRole"] = str(account_role or "")[:32]
        existing["employeeId"] = str(employee_id or "").strip() or None
        _write(store, rows)
        return public_subscription(existing)

    mine = [r for r in rows if str(r.get("userId") or "") == uid]
    if len(mine) >= MAX_SUBS_PER_USER:
        raise HTTPException(status_code=400, detail="Zu viele Geräte für Hinweise.")

    row = {
        "id": str(uuid.uuid4()),
        "userId": uid,
        "accountRole": str(account_role or "")[:32],
        "employeeId": str(employee_id or "").strip() or None,
        "endpoint": ep,
        "keys": {"p256dh": key_p, "auth": key_a},
        "enabled": True,
        "createdAt": now,
        "updatedAt": now,
        "userAgent": ua,
    }
    rows.append(row)
    _write(store, rows)
    return public_subscription(row)


def disable_subscription(store: TenantStore, *, user_id: str, endpoint: str) -> None:
    uid = str(user_id or "").strip()
    ep = _valid_endpoint(endpoint)
    rows = _read(store)
    next_rows: list[dict[str, Any]] = []
    found = False
    for row in rows:
        if str(row.get("endpoint") or "") != ep:
            next_rows.append(row)
            continue
        if str(row.get("userId") or "") != uid:
            raise HTTPException(status_code=403, detail="Keine Berechtigung für dieses Gerät.")
        found = True
    if not found:
        return
    _write(store, next_rows)


def user_has_subscription(store: TenantStore, user_id: str) -> bool:
    uid = str(user_id or "").strip()
    return any(str(r.get("userId") or "") == uid and r.get("enabled", True) for r in _read(store))


def public_subscription(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id") or ""),
        "enabled": bool(row.get("enabled", True)),
        "createdAt": str(row.get("createdAt") or ""),
    }
