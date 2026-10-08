"""Firmen-Module (Paket pro Mandant) — rein additiv.

Fehlender Eintrag = heutiges Produkt: alles an, Lieferschein aus.
Worker erben die Haken vom Firmen-Owner. Tagesbericht bleibt Kern.
"""

from __future__ import annotations

from typing import Any

from app.services.account_roles import find_tenant_owner, is_company_owner
from app.services.tenant_storage import tenant_id_for_user

FIRM_MODULE_KEYS = (
    "tasks",
    "protocol",
    "reports_list",
    "time_accounts",
    "leave",
    "projects",
    "employees",
    "delivery_notes",
)

DEFAULT_OFF_FIRM_MODULES = frozenset({"delivery_notes"})

MODULE_DISABLED_DETAIL = "Dieses Modul ist für diese Firma nicht freigeschaltet."


def normalize_firm_modules(raw: Any) -> dict[str, bool]:
    src = raw if isinstance(raw, dict) else {}
    out: dict[str, bool] = {}
    for key in FIRM_MODULE_KEYS:
        if key in src:
            out[key] = bool(src[key])
        else:
            out[key] = key not in DEFAULT_OFF_FIRM_MODULES
    return out


def merge_firm_modules(existing_raw: Any, patch: Any) -> dict[str, bool]:
    """None-means-leave: fehlende Keys im Patch bleiben unverändert."""
    current = normalize_firm_modules(existing_raw)
    if not isinstance(patch, dict):
        return current
    for key in FIRM_MODULE_KEYS:
        if key not in patch or patch[key] is None:
            continue
        current[key] = bool(patch[key])
    return current


def firm_modules_for_user(
    users: list[dict[str, Any]],
    user: dict[str, Any] | None,
) -> dict[str, bool]:
    if not isinstance(user, dict):
        return normalize_firm_modules(None)
    if is_company_owner(user):
        return normalize_firm_modules(user.get("firmModules"))
    owner = find_tenant_owner(users, tenant_id_for_user(user))
    if not owner:
        return normalize_firm_modules(None)
    return normalize_firm_modules(owner.get("firmModules"))


def firm_module_allows(
    users: list[dict[str, Any]],
    user: dict[str, Any] | None,
    permission: str,
) -> bool:
    key = str(permission or "").strip()
    if key not in FIRM_MODULE_KEYS:
        return True
    mods = firm_modules_for_user(users, user)
    return bool(mods.get(key))
