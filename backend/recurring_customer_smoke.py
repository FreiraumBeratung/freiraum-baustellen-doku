"""Smoke fuer Dauerkunde-Felder am Projekt (Backend-only).

Testet additiv:
- Default ohne Flag bleibt aus
- Anlegen mit Markierung + naechstem Datum
- PATCH None laesst bestehende Felder
- Toggle aus raeumt das Datum
- Ungueltiges Datum -> 400, kein Eintrag
- Status-PATCH zerstoert Dauerkunde nicht

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

_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_recurring_smoke_"))
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
                "email": f"recurring-smoke-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "createdAt": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    return {"Authorization": f"Bearer {user_id}"}


client = TestClient(main.app)
hdrs = _auth_headers()

# Default: ohne Flag kein Dauerkunde
res = client.post("/api/projects", headers=hdrs, json={"name": "Normal-Baustelle", "status": "aktiv"})
_expect(res.status_code == 200, f"create default: {res.status_code} {res.text}")
plain = res.json()
_expect(plain.get("recurringCustomer") is False, "default recurring should be false")
_expect(plain.get("recurringNextDate") == "", "default next date should be empty")
plain_id = plain.get("id")

# Anlegen mit Markierung + Datum (ISO)
res = client.post(
    "/api/projects",
    headers=hdrs,
    json={
        "name": "Hecke Mueller",
        "customer": "Mueller",
        "status": "aktiv",
        "recurringCustomer": True,
        "recurringNextDate": "2026-11-15",
    },
)
_expect(res.status_code == 200, f"create recurring: {res.status_code} {res.text}")
rec = res.json()
rec_id = rec.get("id")
_expect(rec.get("recurringCustomer") is True, "recurring flag missing")
_expect(rec.get("recurringNextDate") == "2026-11-15", f"next date: {rec.get('recurringNextDate')}")

# DE-Datum wird ISO
res = client.post(
    "/api/projects",
    headers=hdrs,
    json={
        "name": "Rasen Meier",
        "recurringCustomer": True,
        "recurringNextDate": "03.04.2027",
    },
)
_expect(res.status_code == 200, f"create DE date: {res.status_code} {res.text}")
_expect(res.json().get("recurringNextDate") == "2027-04-03", "DE date should normalize to ISO")
de_id = res.json().get("id")

# Flag aus + Datum im Body: Datum wird verworfen
res = client.post(
    "/api/projects",
    headers=hdrs,
    json={"name": "Ohne Flag", "recurringCustomer": False, "recurringNextDate": "2026-12-01"},
)
_expect(res.status_code == 200, f"create off with date: {res.status_code} {res.text}")
_expect(res.json().get("recurringCustomer") is False, "off should stay off")
_expect(res.json().get("recurringNextDate") == "", "date without flag should be cleared")

# Ungueltiges Datum + Flag an -> 400, Liste waechst nicht
before = client.get("/api/projects", headers=hdrs).json().get("projects") or []
res = client.post(
    "/api/projects",
    headers=hdrs,
    json={"name": "Kaputt", "recurringCustomer": True, "recurringNextDate": "2026-13-40"},
)
_expect(res.status_code == 400, f"invalid date should 400, was {res.status_code} {res.text}")
after = client.get("/api/projects", headers=hdrs).json().get("projects") or []
_expect(len(after) == len(before), "invalid create must not insert a project")

res = client.post(
    "/api/projects",
    headers=hdrs,
    json={"name": "Muell", "recurringCustomer": True, "recurringNextDate": "kein-datum"},
)
_expect(res.status_code == 400, f"garbage date should 400, was {res.status_code}")

# PATCH nur Status: Dauerkunde bleibt
res = client.patch(f"/api/projects/{rec_id}", headers=hdrs, json={"status": "pausiert"})
_expect(res.status_code == 200, f"patch status: {res.text}")
_expect(res.json().get("status") == "pausiert", "status should update")
_expect(res.json().get("recurringCustomer") is True, "status patch must keep recurring")
_expect(res.json().get("recurringNextDate") == "2026-11-15", "status patch must keep date")

# PATCH nur Datum
res = client.patch(f"/api/projects/{rec_id}", headers=hdrs, json={"recurringNextDate": "2026-12-01"})
_expect(res.status_code == 200, f"patch date: {res.text}")
_expect(res.json().get("recurringNextDate") == "2026-12-01", "date should update")
_expect(res.json().get("recurringCustomer") is True, "date patch must keep flag")

# PATCH Toggle aus raeumt Datum
res = client.patch(f"/api/projects/{rec_id}", headers=hdrs, json={"recurringCustomer": False})
_expect(res.status_code == 200, f"patch off: {res.text}")
_expect(res.json().get("recurringCustomer") is False, "flag should be off")
_expect(res.json().get("recurringNextDate") == "", "toggle off must clear date")

# PATCH Datum bei ausgeschaltetem Flag wird ignoriert
res = client.patch(
    f"/api/projects/{rec_id}",
    headers=hdrs,
    json={"recurringNextDate": "2027-01-01"},
)
_expect(res.status_code == 200, f"patch date while off: {res.text}")
_expect(res.json().get("recurringNextDate") == "", "date while off must stay empty")

# Toggle an ohne Datum
res = client.patch(f"/api/projects/{rec_id}", headers=hdrs, json={"recurringCustomer": True})
_expect(res.status_code == 200, f"patch on: {res.text}")
_expect(res.json().get("recurringCustomer") is True, "flag should be on")
_expect(res.json().get("recurringNextDate") == "", "on without date stays empty")

# Bestehende Baustelle ohne Keys bleibt PATCH-bar
res = client.patch(f"/api/projects/{plain_id}", headers=hdrs, json={"status": "abgeschlossen"})
_expect(res.status_code == 200, f"plain status patch: {res.text}")
_expect(res.json().get("status") == "abgeschlossen", "plain status should update")

# Aufraeumen
for pid in (plain_id, rec_id, de_id):
    client.delete(f"/api/projects/{pid}", headers=hdrs)

print("RECURRING-CUSTOMER-SMOKE: OK")
