"""Smoke Welle M3: Admin-Panel API — Liste, Lizenz, Löschen."""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP = Path(tempfile.mkdtemp(prefix="freiraum_admin_m3_"))
print(f"[smoke] tmp dir: {_TMP}")

import main  # noqa: E402
from app.services.admin_users import bootstrap_admin_from_env  # noqa: E402
from app.services.tenant_storage import TenantStore, tenant_data_dir  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _add_user(
    tag: str,
    *,
    is_admin: bool = False,
    license_active: bool = True,
) -> tuple[str, dict[str, str]]:
    user_id = str(uuid.uuid4())
    email = f"{tag}-{uuid.uuid4().hex[:8]}@example.com"
    user: dict = {
        "id": user_id,
        "tenantId": user_id,
        "companyName": f"Firma {tag}",
        "entrepreneurName": f"Chef {tag}",
        "email": email,
        "password": "x",
        "licenseActive": license_active,
        "createdAt": f"2026-06-0{1 if tag == 'admin' else 2}T00:00:00+00:00",
    }
    if is_admin:
        user["isAdmin"] = True
    users = main.get_users()
    users.append(user)
    main.save_users(users)
    store = TenantStore(user_id)
    store.write_json("reports.json", {"reports": [{"id": "r1", "projectName": tag}]})
    return user_id, {"Authorization": f"Bearer {user_id}"}


client = TestClient(main.app)

admin_id, admin_hdrs = _add_user("admin", is_admin=True)
user_id, user_hdrs = _add_user("pilot")
other_id, other_hdrs = _add_user("other")

# Nicht-Admin: 403
denied = client.get("/api/admin/users", headers=user_hdrs)
_expect(denied.status_code == 403, f"non-admin list: {denied.text}")

# Admin: Liste ohne Passwort
listed = client.get("/api/admin/users", headers=admin_hdrs)
_expect(listed.status_code == 200, f"admin list: {listed.text}")
rows = listed.json().get("users") or []
_expect(len(rows) == 3, "three users listed")
_expect(all("password" not in r for r in rows), "no passwords in admin list")
_expect(any(r.get("id") == user_id for r in rows), "pilot in list")

# Lizenz pausieren
pause = client.patch(
    f"/api/admin/users/{user_id}/license",
    headers=admin_hdrs,
    json={"licenseActive": False},
)
_expect(pause.status_code == 200, f"pause license: {pause.text}")
_expect(pause.json().get("user", {}).get("licenseActive") is False, "license false in response")

# Gesperrter User: Lesen ok, Schreiben blockiert
read_ok = client.get("/api/reports", headers=user_hdrs)
_expect(read_ok.status_code == 200, "paused user can read")
write_blocked = client.post(
    "/api/projects",
    headers=user_hdrs,
    json={"name": "Neu", "customer": "", "address": "", "contactPerson": "", "note": "", "status": "aktiv"},
)
_expect(write_blocked.status_code == 403, "paused user write blocked")

# Admin kann sich nicht selbst pausieren
self_pause = client.patch(
    f"/api/admin/users/{admin_id}/license",
    headers=admin_hdrs,
    json={"licenseActive": False},
)
_expect(self_pause.status_code == 400, "admin cannot pause self")

# Admin kann sich nicht selbst löschen
self_del = client.delete(f"/api/admin/users/{admin_id}", headers=admin_hdrs)
_expect(self_del.status_code == 400, "admin cannot delete self")

# User löschen inkl. Mandanten-Daten
tenant_path = tenant_data_dir(user_id)
_expect(tenant_path.is_dir(), "tenant dir exists before delete")
deleted = client.delete(f"/api/admin/users/{user_id}", headers=admin_hdrs)
_expect(deleted.status_code == 200, f"delete user: {deleted.text}")
_expect(not tenant_path.exists(), "tenant dir removed after delete")
remaining = client.get("/api/admin/users", headers=admin_hdrs).json().get("users") or []
_expect(all(r.get("id") != user_id for r in remaining), "deleted user gone from list")

# Bootstrap via FREIRAUM_ADMIN_EMAIL
os.environ["FREIRAUM_ADMIN_EMAIL"] = str(main.get_users()[0]["email"]).lower()
for u in main.get_users():
    u.pop("isAdmin", None)
main.save_users(main.get_users())
bootstrap_admin_from_env(read_users=main.get_users, save_users=main.save_users)
boot_user = next(u for u in main.get_users() if u.get("email") == os.environ["FREIRAUM_ADMIN_EMAIL"])
_expect(boot_user.get("isAdmin") is True, "bootstrap sets isAdmin for env email")
_expect(sum(1 for u in main.get_users() if u.get("isAdmin")) == 1, "exactly one admin after bootstrap")

print("ADMIN-M3-SMOKE: OK")
