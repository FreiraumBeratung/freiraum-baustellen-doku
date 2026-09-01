"""Firmen-Rollen (Owner vs. Mitarbeiter-Zugang) — rein additiv.

Bestehende User ohne accountRole gelten weiterhin als Owner (Pilot-Konten).
Mitarbeiter-Logins (accountRole=worker) teilen tenantId mit dem Chef;
SMTP bleibt an der Owner-E-Mail.
"""

from __future__ import annotations

from typing import Any

# Extra-Rechte, die der Chef per Haken vergeben kann (Basis report+protocol immer).
EXTRA_PERMISSIONS = frozenset(
    {
        "projects",  # Baustellen
        "reports_list",  # Berichte-Liste
        "time_accounts",  # Stundenkonto
        "delivery_notes",  # Lieferschein
    }
)

BASE_WORKER_PERMISSIONS = frozenset({"report", "protocol"})


def is_company_owner(user: dict[str, Any] | None) -> bool:
    if not isinstance(user, dict):
        return False
    role = str(user.get("accountRole") or "owner").strip().lower()
    return role != "worker"


def is_worker(user: dict[str, Any] | None) -> bool:
    if not isinstance(user, dict):
        return False
    return str(user.get("accountRole") or "").strip().lower() == "worker"


def worker_login_active(user: dict[str, Any] | None) -> bool:
    if not is_worker(user):
        return True
    return bool(user.get("loginActive", True))


def normalize_username(raw: str) -> str:
    return str(raw or "").strip().lower()


def normalize_permissions(raw: Any) -> list[str]:
    """Nur bekannte Extra-Rechte; Basisrechte werden nicht gespeichert."""
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        key = str(item or "").strip().lower()
        if key in EXTRA_PERMISSIONS and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def effective_permissions(user: dict[str, Any] | None) -> set[str]:
    """Owner: alles. Worker: Basis + gespeicherte Extra-Haken."""
    if not isinstance(user, dict):
        return set()
    if is_company_owner(user):
        return set(BASE_WORKER_PERMISSIONS) | set(EXTRA_PERMISSIONS) | {
            "employees",
            "company_profile",
            "admin",
        }
    perms = set(BASE_WORKER_PERMISSIONS)
    perms.update(normalize_permissions(user.get("permissions")))
    return perms


def has_permission(user: dict[str, Any] | None, permission: str) -> bool:
    return str(permission or "") in effective_permissions(user)


def find_tenant_owner(users: list[dict[str, Any]], tenant_id: str) -> dict[str, Any] | None:
    tid = str(tenant_id or "").strip()
    if not tid:
        return None
    for u in users:
        if not isinstance(u, dict):
            continue
        if str(u.get("id") or "") == tid and is_company_owner(u):
            return u
    for u in users:
        if not isinstance(u, dict):
            continue
        if not is_company_owner(u):
            continue
        ut = str(u.get("tenantId") or u.get("id") or "").strip()
        if ut == tid:
            return u
    return None


def owner_email_for_smtp(users: list[dict[str, Any]], user: dict[str, Any] | None) -> str:
    """SMTP immer über Owner-Mail; Worker haben keine eigene Mail-Config."""
    if not isinstance(user, dict):
        return ""
    if is_company_owner(user):
        return str(user.get("email") or "").strip().lower()
    tid = str(user.get("tenantId") or "").strip()
    owner = find_tenant_owner(users, tid)
    if owner:
        return str(owner.get("email") or "").strip().lower()
    return ""


def find_user_by_username(users: list[dict[str, Any]], username: str) -> dict[str, Any] | None:
    """Findet Worker anhand Benutzername (firma-eindeutig). Bei Kollisionen None."""
    want = normalize_username(username)
    if not want or "@" in want:
        return None
    matches = [
        u
        for u in users
        if is_worker(u) and normalize_username(str(u.get("username") or "")) == want
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def find_workers_by_username(users: list[dict[str, Any]], username: str) -> list[dict[str, Any]]:
    want = normalize_username(username)
    if not want or "@" in want:
        return []
    return [
        u
        for u in users
        if is_worker(u) and normalize_username(str(u.get("username") or "")) == want
    ]

def username_taken_in_tenant(
    users: list[dict[str, Any]],
    tenant_id: str,
    username: str,
    *,
    exclude_user_id: str | None = None,
) -> bool:
    want = normalize_username(username)
    tid = str(tenant_id or "").strip()
    if not want or not tid:
        return False
    for u in users:
        if not is_worker(u):
            continue
        if str(u.get("tenantId") or "").strip() != tid:
            continue
        if exclude_user_id and str(u.get("id") or "") == exclude_user_id:
            continue
        if normalize_username(str(u.get("username") or "")) == want:
            return True
    return False


def find_worker_for_employee(
    users: list[dict[str, Any]],
    tenant_id: str,
    employee_id: str,
) -> dict[str, Any] | None:
    tid = str(tenant_id or "").strip()
    eid = str(employee_id or "").strip()
    if not tid or not eid:
        return None
    for u in users:
        if not is_worker(u):
            continue
        if str(u.get("tenantId") or "").strip() != tid:
            continue
        if str(u.get("employeeId") or "").strip() == eid:
            return u
    return None


def access_public_view(user: dict[str, Any] | None) -> dict[str, Any] | None:
    """Öffentliche Zugang-Infos für Mitarbeiter-UI (ohne Passwort)."""
    if not is_worker(user):
        return None
    assert user is not None
    return {
        "hasAccess": True,
        "username": str(user.get("username") or ""),
        "loginActive": worker_login_active(user),
        "permissions": normalize_permissions(user.get("permissions")),
        "userId": str(user.get("id") or ""),
    }
