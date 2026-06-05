"""Smoke Welle M1: Mandantentrennung — zwei User, getrennte Berichte."""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP = Path(tempfile.mkdtemp(prefix="freiraum_tenant_m1_"))
print(f"[smoke] tmp dir: {_TMP}")

import main  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _create_tenant_user(tag: str) -> tuple[str, dict[str, str]]:
    email = f"{tag}-{uuid.uuid4().hex[:8]}@example.com"
    user_id = str(uuid.uuid4())
    users = main.get_users()
    users.append(
        {
            "id": user_id,
            "tenantId": user_id,
            "companyName": f"Firma {tag}",
            "entrepreneurName": f"Chef {tag}",
            "email": email,
            "password": "x",
            "createdAt": f"2026-01-0{1 if tag == 'alpha' else 2}T00:00:00+00:00",
        }
    )
    main.save_users(users)
    store = TenantStore(user_id)
    store.write_json(
        "company_profile.json",
        {
            "companyName": f"Firma {tag}",
            "officeEmail": email,
            "defaultRecipientEmail": email,
        },
    )
    return user_id, {"Authorization": f"Bearer {user_id}"}


client = TestClient(main.app)

id_a, hdrs_a = _create_tenant_user("alpha")
id_b, hdrs_b = _create_tenant_user("beta")
_expect(id_a != id_b, "distinct users")

body = {
    "companyName": "Firma alpha",
    "officeEmail": "a@test.de",
    "projectId": str(uuid.uuid4()),
    "projectName": "Alpha Baustelle",
    "customerName": "Kunde A",
    "date": "2026-06-01",
    "employees": ["Meier"],
    "employeeIds": [],
    "startTime": "08:00",
    "endTime": "16:00",
    "breakMinutes": 45,
    "exportFormat": "PDF",
    "rawText": "Alpha Bericht",
    "structured": {
        "summary": "Alpha",
        "activities": ["Arbeit"],
        "materials": [],
        "materialSuggestions": [],
        "machineSuggestions": [],
        "machineHours": [],
        "problems": [],
        "openItems": [],
        "customerTalk": "",
    },
}

res_a = client.post("/api/reports", headers=hdrs_a, json=body)
_expect(res_a.status_code == 200, f"alpha report: {res_a.text}")
report_a = res_a.json()["id"]

body_b = {**body, "projectId": str(uuid.uuid4()), "projectName": "Beta Baustelle", "rawText": "Beta Bericht"}
res_b = client.post("/api/reports", headers=hdrs_b, json=body_b)
_expect(res_b.status_code == 200, f"beta report: {res_b.text}")

list_a = client.get("/api/reports", headers=hdrs_a).json().get("reports") or []
list_b = client.get("/api/reports", headers=hdrs_b).json().get("reports") or []
_expect(any(r.get("id") == report_a for r in list_a), "alpha sees own report")
_expect(all(r.get("projectName") != "Alpha Baustelle" for r in list_b), "beta must not see alpha report")
_expect(any(r.get("projectName") == "Beta Baustelle" for r in list_b), "beta sees own report")

print("TENANT-M1-SMOKE: OK")
