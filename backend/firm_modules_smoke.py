"""Smoke: Firmen-Module pro Mandant (Admin-Haken).

Defaults = heutiges Produkt (alles an, Lieferschein aus).
Isoliertes Temp-Verzeichnis; beruehrt keine echten Daten.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP = Path(tempfile.mkdtemp(prefix="freiraum_firm_mod_"))
print(f"[smoke] tmp dir: {_TMP}")

import main  # noqa: E402
from app.services.firm_modules import DEFAULT_OFF_FIRM_MODULES, FIRM_MODULE_KEYS  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _add_owner(tag: str, *, is_admin: bool = False) -> tuple[str, dict[str, str]]:
    user_id = str(uuid.uuid4())
    email = f"{tag}-{uuid.uuid4().hex[:8]}@example.com"
    user: dict = {
        "id": user_id,
        "tenantId": user_id,
        "accountRole": "owner",
        "companyName": f"Firma {tag}",
        "entrepreneurName": f"Chef {tag}",
        "email": email,
        "password": "x",
        "licenseActive": True,
        "createdAt": "2026-06-02T00:00:00+00:00",
    }
    if is_admin:
        user["isAdmin"] = True
    users = main.get_users()
    users.append(user)
    main.save_users(users)
    TenantStore(user_id).write_json("employees.json", {"employees": []})
    return user_id, {"Authorization": f"Bearer {user_id}"}


def _add_worker(owner_id: str) -> tuple[str, dict[str, str]]:
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "tenantId": owner_id,
        "accountRole": "worker",
        "username": f"worker-{uuid.uuid4().hex[:6]}",
        "displayName": "Kollege",
        "loginActive": True,
        "password": "x",
        "permissions": ["delivery_notes"],
    }
    users = main.get_users()
    users.append(user)
    main.save_users(users)
    return user_id, {"Authorization": f"Bearer {user_id}"}


client = TestClient(main.app)

admin_id, admin_hdrs = _add_owner("admin", is_admin=True)
firm_id, firm_hdrs = _add_owner("gartenboys")
worker_id, worker_hdrs = _add_worker(firm_id)

# Nicht-Admin darf Module nicht setzen
denied = client.patch(
    f"/api/admin/users/{firm_id}/modules",
    headers=firm_hdrs,
    json={"firmModules": {"leave": False}},
)
_expect(denied.status_code == 403, f"non-admin patch: {denied.text}")

# Liste: Defaults ohne firmModules-Feld in users.json
listed = client.get("/api/admin/users", headers=admin_hdrs)
_expect(listed.status_code == 200, f"admin list: {listed.text}")
rows = listed.json().get("users") or []
firm_row = next((r for r in rows if r.get("id") == firm_id), None)
_expect(firm_row is not None, "firma in list")
mods = firm_row.get("firmModules") or {}
_expect(set(mods) == set(FIRM_MODULE_KEYS), f"keys: {mods}")
_expect(mods.get("leave") is True, "leave default on")
_expect(mods.get("delivery_notes") is False, "lieferschein default off")
_expect(all(mods[k] is True for k in FIRM_MODULE_KEYS if k not in DEFAULT_OFF_FIRM_MODULES), "rest default on")
raw_users = main.get_users()
firm_raw = next(u for u in raw_users if u.get("id") == firm_id)
_expect("firmModules" not in firm_raw, "GET darf users.json nicht beschreiben")

# Session erbt Defaults
sess = client.get("/api/auth/session", headers=firm_hdrs)
_expect(sess.status_code == 200, f"session: {sess.text}")
_expect(sess.json().get("firmModules", {}).get("leave") is True, "session leave on")
_expect(sess.json().get("firmModules", {}).get("delivery_notes") is False, "session lieferschein off")

# Default: Urlaub geht, Lieferschein API zu
leave_ok = client.get("/api/leave", headers=firm_hdrs)
_expect(leave_ok.status_code == 200, f"leave default: {leave_ok.text}")
dn_off = client.get("/api/delivery-notes", headers=firm_hdrs)
_expect(dn_off.status_code == 403, f"delivery default: {dn_off.text}")

# Worker mit Extra-Haken Lieferschein: Firma aus → trotzdem 403
dn_worker_off = client.get("/api/delivery-notes", headers=worker_hdrs)
_expect(dn_worker_off.status_code == 403, "worker extra cannot override firm off")

# Baustellen-API bleibt (Tagesbericht)
proj = client.get("/api/projects", headers=firm_hdrs)
_expect(proj.status_code == 200, f"projects still open: {proj.text}")

# Paket umstellen: Urlaub aus, Lieferschein an
patched = client.patch(
    f"/api/admin/users/{firm_id}/modules",
    headers=admin_hdrs,
    json={"firmModules": {"leave": False, "delivery_notes": True}},
)
_expect(patched.status_code == 200, f"patch modules: {patched.text}")
out = (patched.json().get("user") or {}).get("firmModules") or {}
_expect(out.get("leave") is False, "leave now off")
_expect(out.get("delivery_notes") is True, "lieferschein now on")
_expect(out.get("tasks") is True, "tasks stays default on")

leave_off = client.get("/api/leave", headers=firm_hdrs)
_expect(leave_off.status_code == 403, f"leave after off: {leave_off.text}")
allowance = client.patch(
    f"/api/leave/employees/{uuid.uuid4()}",
    headers=firm_hdrs,
    json={"days": 20},
)
_expect(allowance.status_code == 403, f"leave allowance off: {allowance.text}")
dn_on = client.get("/api/delivery-notes", headers=firm_hdrs)
_expect(dn_on.status_code == 200, f"delivery after on: {dn_on.text}")
dn_worker_on = client.get("/api/delivery-notes", headers=worker_hdrs)
_expect(dn_worker_on.status_code == 200, "worker inherits lieferschein on")

wsess = client.get("/api/auth/session", headers=worker_hdrs)
_expect(wsess.json().get("firmModules", {}).get("leave") is False, "worker inherits leave off")
_expect(wsess.json().get("firmModules", {}).get("delivery_notes") is True, "worker inherits lieferschein on")

# None-means-leave: nur leave wieder an, Lieferschein bleibt an
partial = client.patch(
    f"/api/admin/users/{firm_id}/modules",
    headers=admin_hdrs,
    json={"firmModules": {"leave": True, "unknown_mod": False}},
)
_expect(partial.status_code == 200, f"partial patch: {partial.text}")
pm = (partial.json().get("user") or {}).get("firmModules") or {}
_expect(pm.get("leave") is True, "leave back on")
_expect(pm.get("delivery_notes") is True, "lieferschein not reset")
_expect("unknown_mod" not in pm, "unknown key ignored")

# Worker-Account nicht per Module-PATCH
worker_patch = client.patch(
    f"/api/admin/users/{worker_id}/modules",
    headers=admin_hdrs,
    json={"firmModules": {"leave": False}},
)
_expect(worker_patch.status_code == 404, f"worker modules: {worker_patch.text}")

print("FIRM-MODULES-SMOKE: OK")
