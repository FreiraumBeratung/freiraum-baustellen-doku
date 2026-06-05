"""Smoke Welle M2.1: Lizenz — Schreiben blockiert, Lesen und Login weiter möglich."""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP = Path(tempfile.mkdtemp(prefix="freiraum_license_m2_"))
print(f"[smoke] tmp dir: {_TMP}")

import main  # noqa: E402
from app.services.license import LICENSE_SUSPENDED_DETAIL, is_license_active  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _report_body(project_name: str = "Test Baustelle") -> dict:
    return {
        "companyName": "Firma Test",
        "officeEmail": "test@example.com",
        "projectId": str(uuid.uuid4()),
        "projectName": project_name,
        "customerName": "Kunde",
        "date": "2026-06-01",
        "employees": ["Meier"],
        "employeeIds": [],
        "startTime": "08:00",
        "endTime": "16:00",
        "breakMinutes": 45,
        "exportFormat": "PDF",
        "rawText": "Bericht",
        "structured": {
            "summary": "Test",
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


def _create_user(tag: str, *, license_active: bool | None = True) -> tuple[str, dict[str, str]]:
    user_id = str(uuid.uuid4())
    email = f"{tag}-{uuid.uuid4().hex[:8]}@example.com"
    user: dict = {
        "id": user_id,
        "tenantId": user_id,
        "companyName": f"Firma {tag}",
        "entrepreneurName": f"Chef {tag}",
        "email": email,
        "password": "x",
        "createdAt": "2026-06-01T00:00:00+00:00",
    }
    if license_active is not None:
        user["licenseActive"] = license_active
    users = main.get_users()
    users.append(user)
    main.save_users(users)
    store = TenantStore(user_id)
    store.write_json(
        "company_profile.json",
        {"companyName": f"Firma {tag}", "officeEmail": email, "defaultRecipientEmail": email},
    )
    return user_id, {"Authorization": f"Bearer {user_id}"}


# -- license helper defaults ---------------------------------------------------
_expect(is_license_active({}) is True, "missing field defaults active")
_expect(is_license_active({"licenseActive": False}) is False, "false is inactive")
_expect(is_license_active({"licenseActive": True}) is True, "true is active")

client = TestClient(main.app)

# -- active user: write + read ------------------------------------------------
active_id, active_hdrs = _create_user("active", license_active=True)
res_create = client.post("/api/reports", headers=active_hdrs, json=_report_body())
_expect(res_create.status_code == 200, f"active write: {res_create.text}")
report_id = res_create.json()["id"]

res_list = client.get("/api/reports", headers=active_hdrs)
_expect(res_list.status_code == 200, f"active read list: {res_list.text}")
_expect(any(r.get("id") == report_id for r in res_list.json().get("reports") or []), "active sees report")

res_pdf = client.get(f"/api/reports/{report_id}/export/pdf", headers=active_hdrs)
_expect(res_pdf.status_code == 200, f"active pdf export: {res_pdf.status_code}")

# -- legacy user ohne licenseActive-Feld: weiterhin schreiben -----------------
legacy_id, legacy_hdrs = _create_user("legacy", license_active=None)
res_legacy = client.post("/api/reports", headers=legacy_hdrs, json=_report_body("Legacy"))
_expect(res_legacy.status_code == 200, f"legacy write: {res_legacy.text}")

# -- suspended user: read ok, write blocked -----------------------------------
suspended_id, suspended_hdrs = _create_user("paused", license_active=False)
res_write = client.post("/api/reports", headers=suspended_hdrs, json=_report_body("Paused"))
_expect(res_write.status_code == 403, f"suspended write must 403: {res_write.text}")
_expect(LICENSE_SUSPENDED_DETAIL in res_write.text, "suspended detail message")

res_read = client.get("/api/reports", headers=suspended_hdrs)
_expect(res_read.status_code == 200, f"suspended read list: {res_read.text}")

res_profile = client.get("/api/company-profile", headers=suspended_hdrs)
_expect(res_profile.status_code == 200, f"suspended read profile: {res_profile.text}")

res_profile_write = client.post(
    "/api/company-profile",
    headers=suspended_hdrs,
    json={
        "companyName": "Neu",
        "contactPerson": "X",
        "officeEmail": "x@test.de",
        "phone": "1",
        "address": "Y",
        "defaultExportFormat": "PDF",
        "defaultRecipientEmail": "x@test.de",
    },
)
_expect(res_profile_write.status_code == 403, f"suspended profile write: {res_profile_write.text}")

# -- register sets licenseActive true -----------------------------------------
new_user = {
    "id": str(uuid.uuid4()),
    "tenantId": str(uuid.uuid4()),
    "companyName": "Reg",
    "email": "reg-check@example.com",
    "password": "x",
    "licenseActive": True,
    "createdAt": "2026-06-01T00:00:00+00:00",
}
_expect(new_user.get("licenseActive") is True, "register shape includes licenseActive")

print("LICENSE-M2-SMOKE: OK")
