"""Mandantentrennung (Welle M1): pro Firma/User eigene JSON-Daten und Uploads.

Jeder registrierte User ist in V1 sein eigener Mandant (tenantId = user id).
Legacy-Daten aus data/*.json werden beim ersten Start in data/tenants/{id}/ kopiert.
"""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
TENANTS_DIR = DATA_DIR / "tenants"
USERS_FILE = DATA_DIR / "users.json"
MIGRATION_MARKER = DATA_DIR / ".tenant_migration_m1.done"
LEGACY_BACKUP_DIR = DATA_DIR / "legacy_pre_m1_backup"

TENANT_JSON_FILES = (
    "company_profile.json",
    "employees.json",
    "projects.json",
    "reports.json",
    "time_entries.json",
    "audio_uploads.json",
    "trade_intelligence_cases.json",
)

UPLOAD_SUBDIRS = ("logos", "photos", "signatures", "audio")


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def tenant_id_for_user(user: dict[str, Any]) -> str:
    tid = str(user.get("tenantId") or user.get("id") or "").strip()
    if not tid:
        raise ValueError("user without id")
    return tid


def tenant_data_dir(tenant_id: str) -> Path:
    tid = str(tenant_id or "").strip()
    if not tid:
        raise ValueError("missing tenant_id")
    return TENANTS_DIR / tid


def tenant_json_path(tenant_id: str, filename: str) -> Path:
    return tenant_data_dir(tenant_id) / filename


def tenant_uploads_dir(tenant_id: str, kind: str) -> Path:
    if kind not in UPLOAD_SUBDIRS:
        raise ValueError(f"unknown upload kind: {kind}")
    return BASE_DIR / "uploads" / "tenants" / tenant_id / kind


def legacy_uploads_dir(kind: str) -> Path:
    return BASE_DIR / "uploads" / kind


def ensure_tenant_dirs(tenant_id: str) -> None:
    tenant_data_dir(tenant_id).mkdir(parents=True, exist_ok=True)
    for kind in UPLOAD_SUBDIRS:
        tenant_uploads_dir(tenant_id, kind).mkdir(parents=True, exist_ok=True)


class TenantStore:
    """JSON- und Upload-Zugriff fuer einen Mandanten."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = str(tenant_id).strip()
        if not self.tenant_id:
            raise ValueError("missing tenant_id")
        ensure_tenant_dirs(self.tenant_id)

    def read_json(self, filename: str, default: Any) -> Any:
        return read_json_file(tenant_json_path(self.tenant_id, filename), default)

    def write_json(self, filename: str, data: Any) -> None:
        write_json_file(tenant_json_path(self.tenant_id, filename), data)

    def uploads_dir(self, kind: str) -> Path:
        path = tenant_uploads_dir(self.tenant_id, kind)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def resolve_upload_file(self, kind: str, filename: str) -> Path | None:
        fn = str(filename or "").strip()
        if not fn or "/" in fn or "\\" in fn or fn != fn.strip():
            return None
        candidates = [self.uploads_dir(kind) / fn, legacy_uploads_dir(kind) / fn]
        for path in candidates:
            try:
                resolved = path.resolve()
                base = path.parent.resolve()
                resolved.relative_to(base)
            except ValueError:
                continue
            if resolved.is_file():
                return resolved
        return None

    def time_account_read_json(self, path: Path, default: Any) -> Any:
        _ = path
        return self.read_json("time_entries.json", default)

    def time_account_write_json(self, path: Path, data: Any) -> None:
        _ = path
        self.write_json("time_entries.json", data)


def _load_users() -> list[dict[str, Any]]:
    raw = read_json_file(USERS_FILE, [])
    return raw if isinstance(raw, list) else []


def _save_users(users: list[dict[str, Any]]) -> None:
    write_json_file(USERS_FILE, users)


def _legacy_data_exists() -> bool:
    return any((DATA_DIR / name).exists() for name in TENANT_JSON_FILES)


def _pick_legacy_owner_tenant_id(users: list[dict[str, Any]]) -> str | None:
    if not users:
        return None
    sorted_users = sorted(users, key=lambda u: str(u.get("createdAt") or ""))
    return tenant_id_for_user(sorted_users[0])


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def repair_owner_tenant_from_legacy_backup(
    *,
    read_users: Callable[[], list[dict[str, Any]]] | None = None,
) -> None:
    """Fuellt fehlende Mandanten-Dateien/Felder aus legacy_pre_m1_backup (idempotent)."""
    if not LEGACY_BACKUP_DIR.exists():
        return

    users = (read_users or _load_users)()
    owner_id = _pick_legacy_owner_tenant_id(users)
    if not owner_id:
        return

    ensure_tenant_dirs(owner_id)

    for name in TENANT_JSON_FILES:
        dst = tenant_json_path(owner_id, name)
        src = LEGACY_BACKUP_DIR / name
        if not src.is_file():
            continue
        if not dst.is_file():
            try:
                shutil.copy2(src, dst)
                logger.info("M1 repair: restored %s for tenant %s", name, owner_id)
            except OSError as exc:
                logger.warning("M1 repair: could not copy %s: %s", name, exc)
            continue
        if name != "company_profile.json":
            continue

        backup_prof = read_json_file(src, {})
        tenant_prof = read_json_file(dst, {})
        merged = dict(backup_prof)
        for key, value in tenant_prof.items():
            if not _is_blank(value):
                merged[key] = value
        if merged != tenant_prof:
            try:
                write_json_file(dst, merged)
                logger.info("M1 repair: merged company_profile for tenant %s", owner_id)
            except OSError as exc:
                logger.warning("M1 repair: could not write company_profile: %s", exc)


def migrate_legacy_data_if_needed(
    *,
    read_users: Callable[[], list[dict[str, Any]]] | None = None,
    save_users: Callable[[list[dict[str, Any]]], None] | None = None,
) -> None:
    """Einmalige Migration: flache data/*.json -> data/tenants/{id}/."""
    if MIGRATION_MARKER.exists():
        return

    load_users = read_users or _load_users
    persist_users = save_users or _save_users
    users = load_users()

    for user in users:
        if not user.get("tenantId"):
            user["tenantId"] = str(user.get("id") or "")

    owner_id = _pick_legacy_owner_tenant_id(users)
    if owner_id and _legacy_data_exists():
        ensure_tenant_dirs(owner_id)
        LEGACY_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        for name in TENANT_JSON_FILES:
            src = DATA_DIR / name
            if not src.exists():
                continue
            dst = tenant_json_path(owner_id, name)
            if not dst.exists():
                shutil.copy2(src, dst)
            backup_target = LEGACY_BACKUP_DIR / name
            if not backup_target.exists():
                shutil.move(str(src), str(backup_target))
            elif src.exists():
                src.unlink()

        for kind in UPLOAD_SUBDIRS:
            legacy_dir = legacy_uploads_dir(kind)
            if not legacy_dir.exists():
                continue
            target_dir = tenant_uploads_dir(owner_id, kind)
            target_dir.mkdir(parents=True, exist_ok=True)
            for item in legacy_dir.iterdir():
                dest = target_dir / item.name
                if item.is_file() and not dest.exists():
                    shutil.copy2(item, dest)
            backup_uploads = LEGACY_BACKUP_DIR / "uploads" / kind
            backup_uploads.mkdir(parents=True, exist_ok=True)
            for item in list(legacy_dir.iterdir()):
                if item.is_file():
                    moved = backup_uploads / item.name
                    if not moved.exists():
                        shutil.move(str(item), str(moved))

        logger.info("M1 migration: legacy data assigned to tenant %s", owner_id)

    for user in users:
        tid = tenant_id_for_user(user)
        ensure_tenant_dirs(tid)

    persist_users(users)
    MIGRATION_MARKER.write_text(
        json.dumps({"migratedAt": datetime.now(timezone.utc).isoformat()}, indent=2),
        encoding="utf-8",
    )
