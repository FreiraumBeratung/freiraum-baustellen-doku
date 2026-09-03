"""M3 Admin — Account-Metadaten verwalten (ohne Mandantendaten einzusehen)."""

from __future__ import annotations

import logging
import os
import shutil
from typing import Any, Callable

from app.services.account_roles import is_company_owner, is_worker
from app.services.admin_activity import activity_public_fields
from app.services.license import is_license_active
from app.services.mail_store import delete_mail_config
from app.services.tenant_storage import BASE_DIR, tenant_data_dir

logger = logging.getLogger(__name__)


def is_user_admin(user: dict[str, Any] | None) -> bool:
    if not isinstance(user, dict):
        return False
    return bool(user.get("isAdmin"))


def _worker_count_for_tenant(users: list[dict[str, Any]], tenant_id: str) -> int:
    tid = str(tenant_id or "").strip()
    if not tid:
        return 0
    return sum(
        1
        for u in users
        if isinstance(u, dict) and is_worker(u) and str(u.get("tenantId") or "").strip() == tid
    )


def user_public_row(
    user: dict[str, Any],
    *,
    include_activity: bool = True,
    worker_count: int | None = None,
) -> dict[str, Any]:
    uid = str(user.get("id") or "")
    tid = str(user.get("tenantId") or uid)
    row: dict[str, Any] = {
        "id": uid,
        "tenantId": tid,
        "companyName": str(user.get("companyName") or ""),
        "entrepreneurName": str(user.get("entrepreneurName") or ""),
        "email": str(user.get("email") or ""),
        "createdAt": str(user.get("createdAt") or ""),
        "licenseActive": is_license_active(user),
        "isAdmin": is_user_admin(user),
        "workerCount": int(worker_count) if worker_count is not None else 0,
    }
    if include_activity:
        row.update(activity_public_fields(tid))
    return row


def list_users_public(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nur Firmen-Owner in der Verwaltung — Mitarbeiter-Logins als Anzahl am Owner."""
    activity_cache: dict[str, dict[str, Any]] = {}
    worker_cache: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    for u in users:
        if not isinstance(u, dict) or not u.get("id"):
            continue
        # Worker-Zugänge nicht als eigene Karten listen.
        if is_worker(u) or not is_company_owner(u):
            continue
        tid = str(u.get("tenantId") or u.get("id") or "")
        if tid not in activity_cache:
            activity_cache[tid] = activity_public_fields(tid)
        if tid not in worker_cache:
            worker_cache[tid] = _worker_count_for_tenant(users, tid)
        row = user_public_row(u, include_activity=False, worker_count=worker_cache[tid])
        row.update(activity_cache[tid])
        rows.append(row)
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
        # Lizenz nur am Firmen-Owner steuern (Worker erben über Mandant).
        if is_worker(u):
            return None
        u["licenseActive"] = bool(license_active)
        tid = str(u.get("tenantId") or u.get("id") or "")
        return user_public_row(u, worker_count=_worker_count_for_tenant(users, tid))
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
