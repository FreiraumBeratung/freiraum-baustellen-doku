"""Smoke fuer additive Delete-/Edit-Endpoints (Backend-only).

Testet:
- POST/PATCH/DELETE /api/employees/{id}  (Rolle aendern + loeschen)
- POST/DELETE        /api/projects/{id}   (Baustelle loeschen)

Laeuft in-process mit isoliertem Temp-Verzeichnis; beruehrt keine echten Daten.
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

_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_delete_smoke_"))
print(f"[smoke] using tmp data dir: {_TMP_DIR}")

import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP_DIR)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _auth_headers() -> dict[str, str]:
    user_id = str(uuid.uuid4())
    main.save_users(
        [
            {
                "id": user_id,
                "tenantId": user_id,
                "companyName": "Smoke GmbH",
                "entrepreneurName": "Tester",
                "email": f"delete-smoke-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "createdAt": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    return {"Authorization": f"Bearer {user_id}"}


client = TestClient(main.app)
hdrs = _auth_headers()

# --- Mitarbeiter: anlegen -> Rolle aendern -> loeschen ---
res = client.post("/api/employees", headers=hdrs, json={"name": "Max", "role": "Vorarbeiter", "active": True})
_expect(res.status_code == 200, f"create employee: {res.status_code} {res.text}")
emp_id = res.json().get("id")
_expect(emp_id, "employee id missing")

res = client.get("/api/employees", headers=hdrs)
_expect(res.status_code == 200 and len(res.json().get("employees", [])) == 1, "employee list should have 1")

# Rolle aendern (Vorarbeiter -> Arbeiter) + Name
res = client.patch(f"/api/employees/{emp_id}", headers=hdrs, json={"name": "Max M.", "role": "Arbeiter"})
_expect(res.status_code == 200, f"patch employee: {res.text}")
_expect(res.json().get("role") == "Arbeiter", "role should be updated")
_expect(res.json().get("name") == "Max M.", "name should be updated")

# Loeschen
res = client.delete(f"/api/employees/{emp_id}", headers=hdrs)
_expect(res.status_code == 200 and res.json().get("ok") is True, f"delete employee: {res.text}")
res = client.get("/api/employees", headers=hdrs)
_expect(len(res.json().get("employees", [])) == 0, "employee list should be empty after delete")

# Doppeltes Loeschen -> 404
res = client.delete(f"/api/employees/{emp_id}", headers=hdrs)
_expect(res.status_code == 404, f"second employee delete should be 404, was {res.status_code}")

# --- Baustelle: anlegen -> loeschen ---
res = client.post("/api/projects", headers=hdrs, json={"name": "Smoke-Baustelle", "status": "aktiv"})
_expect(res.status_code == 200, f"create project: {res.status_code} {res.text}")
proj_id = res.json().get("id")
_expect(proj_id, "project id missing")

res = client.get("/api/projects", headers=hdrs)
_expect(len(res.json().get("projects", [])) == 1, "project list should have 1")

res = client.delete(f"/api/projects/{proj_id}", headers=hdrs)
_expect(res.status_code == 200 and res.json().get("ok") is True, f"delete project: {res.text}")
res = client.get("/api/projects", headers=hdrs)
_expect(len(res.json().get("projects", [])) == 0, "project list should be empty after delete")

res = client.delete(f"/api/projects/{proj_id}", headers=hdrs)
_expect(res.status_code == 404, f"second project delete should be 404, was {res.status_code}")

print("DELETE-ENDPOINTS-SMOKE: OK")
