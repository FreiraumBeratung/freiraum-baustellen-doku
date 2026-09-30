"""Smoke fuer Urlaub Baustein 1 (Backend-only).

Kontingent + Resttage, ungesetzt != 0, Worker darf lesen nicht schreiben,
genehmigte Werktage zaehlen, offene Antraege nicht.
Mitarbeiter-/Stunden-PATCH bleibt unberuehrt.

Laeuft in-process mit isoliertem Temp-Verzeichnis; beruehrt keine echten Daten.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_leave_smoke_"))
print(f"[smoke] using tmp data dir: {_TMP_DIR}")

import main  # noqa: E402
from app.services import leave as leave_service  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP_DIR)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _owner_headers() -> tuple[dict[str, str], str, TenantStore]:
    user_id = str(uuid.uuid4())
    main.save_users(
        [
            {
                "id": user_id,
                "tenantId": user_id,
                "companyName": "Smoke GmbH",
                "entrepreneurName": "Tester",
                "email": f"leave-smoke-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "createdAt": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    return {"Authorization": f"Bearer {user_id}"}, user_id, TenantStore(user_id)


client = TestClient(main.app)
hdrs, owner_id, store = _owner_headers()
year = leave_service.current_leave_year()

# Leere Firma
res = client.get("/api/leave", headers=hdrs)
_expect(res.status_code == 200, f"empty leave: {res.status_code} {res.text}")
body = res.json()
_expect(body.get("year") == year, f"year: {body.get('year')}")
_expect(body.get("people") == [], "no people yet")
_expect(body.get("selfEmployeeId") is None, "owner has no employeeId")

# Mitarbeiter anlegen — ohne Kontingent
uli = client.post("/api/employees", headers=hdrs, json={"name": "Uli", "role": "", "active": True}).json()
matthias = client.post(
    "/api/employees", headers=hdrs, json={"name": "Matthias", "role": "", "active": True}
).json()
uli_id = uli["id"]
matthias_id = matthias["id"]
_expect(bool(uli_id and matthias_id), "employees missing")

res = client.get("/api/leave", headers=hdrs)
people = {p["employeeId"]: p for p in res.json().get("people") or []}
_expect(uli_id in people and matthias_id in people, "both employees in leave overview")
_expect(people[uli_id].get("allowanceSet") is False, "unset must not look set")
_expect(people[uli_id].get("allowanceDays") is None, "unset days must be null")
_expect(people[uli_id].get("remainingDays") is None, "unset remaining must be null, not 0")
_expect(people[uli_id].get("usedDays") == 0, "used starts at 0")

# Kontingent setzen
res = client.patch(f"/api/leave/employees/{uli_id}", headers=hdrs, json={"days": 30})
_expect(res.status_code == 200, f"set 30: {res.status_code} {res.text}")
_expect(res.json().get("allowanceSet") is True, "set flag")
_expect(res.json().get("allowanceDays") == 30, "30 days")
_expect(res.json().get("remainingDays") == 30, "remaining = allowance without requests")

res = client.patch(f"/api/leave/employees/{matthias_id}", headers=hdrs, json={"days": 0})
_expect(res.status_code == 200, f"set 0: {res.text}")
_expect(res.json().get("allowanceSet") is True, "0 is a real value")
_expect(res.json().get("remainingDays") == 0, "zero remaining")

# Loeschen = wieder ungesetzt
res = client.patch(f"/api/leave/employees/{matthias_id}", headers=hdrs, json={"days": None})
_expect(res.status_code == 200, f"clear: {res.text}")
_expect(res.json().get("allowanceSet") is False, "cleared")
_expect(res.json().get("remainingDays") is None, "cleared remaining null")

# Ungueltig
res = client.patch(f"/api/leave/employees/{uli_id}", headers=hdrs, json={"days": -1})
_expect(res.status_code == 400, f"negative: {res.status_code}")
res = client.patch(f"/api/leave/employees/{uli_id}", headers=hdrs, json={"days": 100})
_expect(res.status_code == 400, f"too many: {res.status_code}")
res = client.patch(f"/api/leave/employees/{uli_id}", headers=hdrs, json={"days": 30.5})
_expect(res.status_code == 400, f"half day: {res.status_code} {res.text}")
res = client.patch(f"/api/leave/employees/missing", headers=hdrs, json={"days": 10})
_expect(res.status_code == 404, f"unknown emp: {res.status_code}")

# Mitarbeiter-PATCH (Name) darf leave.json nicht anfassen
before_doc = leave_service.read_doc(store)
res = client.patch(f"/api/employees/{uli_id}", headers=hdrs, json={"name": "Uli K."})
_expect(res.status_code == 200, f"employee patch: {res.text}")
_expect("leaveDays" not in (res.json() or {}), "employee patch must not grow leave fields")
after_doc = leave_service.read_doc(store)
_expect(before_doc == after_doc, "employee patch must not rewrite leave.json")

# Genehmigte Werktage senken Rest; offene nicht
monday = date(year, 1, 1)
while monday.weekday() != 0:
    monday += timedelta(days=1)
friday = monday + timedelta(days=4)
doc = leave_service.read_doc(store)
doc["requests"] = [
    {
        "id": "req-pending",
        "employeeId": uli_id,
        "fromDate": monday.isoformat(),
        "toDate": friday.isoformat(),
        "status": "pending",
    },
    {
        "id": "req-ok",
        "employeeId": uli_id,
        "fromDate": monday.isoformat(),
        "toDate": friday.isoformat(),
        "status": "approved",
    },
    {
        "id": "req-other",
        "employeeId": matthias_id,
        "fromDate": monday.isoformat(),
        "toDate": friday.isoformat(),
        "status": "approved",
    },
]
leave_service.write_doc(store, doc)
used = leave_service.count_weekdays(monday, friday, year=year)
_expect(used == 5, f"Mo–Fr should be 5, was {used} ({monday}–{friday})")

res = client.get("/api/leave", headers=hdrs)
people = {p["employeeId"]: p for p in res.json().get("people") or []}
_expect(people[uli_id].get("usedDays") == 5, f"approved used: {people[uli_id]}")
_expect(people[uli_id].get("remainingDays") == 25, f"30-5: {people[uli_id]}")
_expect(people[matthias_id].get("remainingDays") is None, "matthias still unset")
_expect(people[matthias_id].get("usedDays") == 5, "used can exist without allowance")

# Worker: lesen ja, schreiben nein
acc = client.post(
    f"/api/employees/{uli_id}/access",
    headers=hdrs,
    json={"username": "uli.leave", "password": "pw12", "permissions": [], "loginActive": True},
)
_expect(acc.status_code == 200, f"access: {acc.status_code} {acc.text}")
worker_id = acc.json().get("access", {}).get("userId")
_expect(worker_id, "worker id missing")
wh = {"Authorization": f"Bearer {worker_id}"}

res = client.get("/api/leave", headers=wh)
_expect(res.status_code == 200, f"worker get: {res.status_code} {res.text}")
_expect(res.json().get("selfEmployeeId") == uli_id, "self id")
_expect(res.json().get("people")[0].get("employeeId") == uli_id, "self first")

res = client.patch(f"/api/leave/employees/{uli_id}", headers=wh, json={"days": 10})
_expect(res.status_code == 403, f"worker patch must 403, was {res.status_code}")

# Anderer Mandant sieht nichts
other_id = str(uuid.uuid4())
main.save_users(
    main.get_users()
    + [
        {
            "id": other_id,
            "tenantId": other_id,
            "companyName": "Andere GmbH",
            "entrepreneurName": "Anderer",
            "email": f"leave-other-{uuid.uuid4().hex[:8]}@example.com",
            "password": "pw",
            "createdAt": "2026-01-01T00:00:00+00:00",
        }
    ]
)
oh = {"Authorization": f"Bearer {other_id}"}
res = client.get("/api/leave", headers=oh)
_expect(res.status_code == 200, f"other get: {res.status_code}")
_expect(res.json().get("people") == [], "tenant isolation")

print("LEAVE-SMOKE (B1): OK")
