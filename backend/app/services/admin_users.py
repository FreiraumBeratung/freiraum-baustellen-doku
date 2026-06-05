"""M3 Admin — Account-Metadaten verwalten (ohne Mandantendaten einzusehen)."""

from __future__ import annotations

import logging
import os
import shutil
from typing import Any, Callable

from app.services.license import is_license_active
from app.services.mail_store import delete_mail_config
from app.services.tenant_storage import BASE_DIR, tenant_data_dir

logger = logging.getLogger(__name__)


def is_user_admin(user: dict[str, Any] | None) -> bool:
    if not isinstance(user, dict):
        return False
    return bool(user.get("isAdmin"))


def user_public_row(user: dict[str, Any]) -> dict[str, Any]:
    uid = str(user.get("id") or "")
    return {
        "id": uid,
        "tenantId": str(user.get("tenantId") or uid),
        "companyName": str(user.get("companyName") or ""),
        "entrepreneurName": str(user.get("entrepreneurName") or ""),
        "email": str(user.get("email") or ""),
        "createdAt": str(user.get("createdAt") or ""),
        "licenseActive": is_license_active(user),
        "isAdmin": is_user_admin(user),
    }


def list_users_public(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [user_public_row(u) for u in users if isinstance(u, dict) and u.get("id")]
    rows.sort(key=lambda r: str(r.get("createdAt") or ""), reverse=True)
    return rows


def bootstrap_admin_from_env(
    *,
    read_users: Callable[[], list[dict[str, Any]]],
    save_users: Callable[[list[dict[str, Any]]], None],
) -> None:
    """Setzt isAdmin fuer FREIRAUM_ADMIN_EMAIL (nur dieser Account, alle anderen false)."""
    admin_email = os.environ.get("FREIRAUM_ADMIN_EMAIL", "").strip().lower()
    if not admin_email:
        return

    users = read_users()
    target_id: str | None = None
    for u in users:
        if str(u.get("email", "")).strip().lower() == admin_email:
            target_id = str(u.get("id") or "")
            break

    if not target_id:
        logger.info("FREIRAUM_ADMIN_EMAIL gesetzt, User noch nicht registriert: %s", admin_email)
        return

    changed = False
    for u in users:
        should_admin = str(u.get("id") or "") == target_id
        if bool(u.get("isAdmin")) != should_admin:
            if should_admin:
                u["isAdmin"] = True
            else:
                u.pop("isAdmin", None)
            changed = True

    if changed:
        save_users(users)
        logger.info("Administrator-Zugang zugewiesen: %s", admin_email)


def _delete_tenant_files(tenant_id: str) -> None:
    tid = str(tenant_id or "").strip()
    if not tid:
        return
    data_dir = tenant_data_dir(tid)
    if data_dir.exists():
        shutil.rmtree(data_dir, ignore_errors=True)
    uploads_dir = BASE_DIR / "uploads" / "tenants" / tid
    if uploads_dir.exists():
        shutil.rmtree(uploads_dir, ignore_errors=True)


def set_user_license(
    users: list[dict[str, Any]],
    user_id: str,
    license_active: bool,
) -> dict[str, Any] | None:
    for u in users:
        if str(u.get("id") or "") != user_id:
            continue
        u["licenseActive"] = bool(license_active)
        return user_public_row(u)
    return None


def delete_user_account(
    *,
    read_users: Callable[[], list[dict[str, Any]]],
    save_users: Callable[[list[dict[str, Any]]], None],
    user_id: str,
) -> bool:
    users = read_users()
    target: dict[str, Any] | None = None
    kept: list[dict[str, Any]] = []
    for u in users:
        if str(u.get("id") or "") == user_id:
            target = u
            continue
        kept.append(u)

    if target is None:
        return False

    tenant_id = str(target.get("tenantId") or target.get("id") or "")
    email = str(target.get("email") or "")

    save_users(kept)
    _delete_tenant_files(tenant_id)
    if email:
        delete_mail_config(email)
    return True
