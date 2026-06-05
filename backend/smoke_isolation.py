"""Gemeinsame Pfad-Isolation fuer Backend-Smoke-Tests (M1 Mandanten)."""

from __future__ import annotations

from pathlib import Path


def isolate_smoke_data(tmp: Path) -> None:
    import main
    from app.services import tenant_storage as ts

    main.DATA_DIR = tmp
    main.USERS_FILE = tmp / "users.json"
    ts.DATA_DIR = tmp
    ts.TENANTS_DIR = tmp / "tenants"
    ts.USERS_FILE = tmp / "users.json"
    ts.MIGRATION_MARKER = tmp / ".tenant_migration_m1.done"
    ts.LEGACY_BACKUP_DIR = tmp / "legacy_pre_m1_backup"
    ts.BASE_DIR = tmp
    ts.MIGRATION_MARKER.write_text("{}", encoding="utf-8")
