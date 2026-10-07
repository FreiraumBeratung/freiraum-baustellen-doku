"""Smoke: Heute-Blick (wer hat heute einen Tagesbericht).

Chef sieht fehlende aktive Mitarbeiter. Kein Rohtext. Worker 403.
time_account-Buchung und Protokoll unangetastet.

Laeuft in-process mit isoliertem Temp-Verzeichnis; beruehrt keine echten Daten.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_today_presence_smoke_"))
print(f"[smoke] using tmp data dir: {_TMP_DIR}")

import main  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP_DIR)

BERLIN = ZoneInfo("Europe/Berlin")


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
                "email": f"today-presence-smoke-{uuid.uuid4().hex[:8]}@example.com",
                "password": "pw",
                "createdAt": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    return {"Authorization": f"Bearer {user_id}"}, user_id, TenantStore(user_id)


client = TestClient(main.app)
hdrs, owner_id, store = _owner_headers()
today = datetime.now(BERLIN).date()
today_iso = today.isoformat()
yesterday_iso = (today - timedelta(days=1)).isoformat()

# Ohne Mitarbeiter: keine Karte
res = client.get("/api/reminders/today", headers=hdrs)
_expect(res.status_code == 200, f"empty team: {res.status_code} {res.text}")
body = res.json()
_expect(body.get("due") is False, "no employees => not due")
_expect(body.get("missing") == [], f"missing: {body.get('missing')}")
_expect(body.get("present") == [], "present empty")
_expect("rawText" not in body, "no rawText envelope")

uli = client.post("/api/employees", headers=hdrs, json={"name": "Uli", "role": "", "active": True}).json()
matthias = client.post(
    "/api/employees", headers=hdrs, json={"name": "Matthias", "role": "", "active": True}
).json()
inactive = client.post(
    "/api/employees", headers=hdrs, json={"name": "Alt", "role": "", "active": False}
).json()
uli_id = uli["id"]
matthias_id = matthias["id"]
_expect(bool(uli_id and matthias_id and inactive.get("id")), "employees missing")

res = client.get("/api/reminders/today", headers=hdrs)
body = res.json()
_expect(body.get("due") is True, "two active missing => due")
missing_ids = {p["id"] for p in body.get("missing") or []}
_expect(missing_ids == {uli_id, matthias_id}, f"missing ids: {missing_ids}")
_expect(inactive["id"] not in missing_ids, "inactive must not appear")
_expect(body.get("present") == [], "nobody present yet")

# Gestriger Bericht zaehlt nicht
store.write_json(
    "reports.json",
    {
        "reports": [
            {
                "id": str(uuid.uuid4()),
                "date": yesterday_iso,
                "employees": ["Uli"],
                "employeeIds": [uli_id],
                "rawText": "GESTERN GEHEIM",
            }
        ]
    },
)
res = client.get("/api/reminders/today", headers=hdrs)
body = res.json()
_expect({p["id"] for p in body.get("missing") or []} == {uli_id, matthias_id}, "yesterday ignored")
_expect(all("rawText" not in p for p in (body.get("missing") or [])), "no rawText on people")

# Heute per employeeIds: Uli da, Matthias fehlt
store.write_json(
    "reports.json",
    {
        "reports": [
            {
                "id": str(uuid.uuid4()),
                "date": today_iso,
                "employees": ["Falscher Name"],
                "employeeIds": [uli_id],
                "rawText": "HEUTE GEHEIM",
            }
        ]
    },
)
res = client.get("/api/reminders/today", headers=hdrs)
body = res.json()
_expect(body.get("due") is True, "still due with one missing")
_expect([p["id"] for p in body.get("missing") or []] == [matthias_id], body.get("missing"))
_expect([p["id"] for p in body.get("present") or []] == [uli_id], body.get("present"))
_expect("HEUTE GEHEIM" not in res.text, "rawText must not leak")

# Namens-Fallback ohne IDs; DE-Datum
store.write_json(
    "reports.json",
    {
        "reports": [
            {
                "id": str(uuid.uuid4()),
                "date": f"{today.day:02d}.{today.month:02d}.{today.year}",
                "employees": ["Matthias"],
                "employeeIds": [],
                "rawText": "DE DATUM",
            }
        ]
    },
)
res = client.get("/api/reminders/today", headers=hdrs)
body = res.json()
_expect([p["id"] for p in body.get("present") or []] == [matthias_id], "name fallback + DE date")
_expect([p["id"] for p in body.get("missing") or []] == [uli_id], "uli still missing")

# Beide da => due false (Karte weg)
store.write_json(
    "reports.json",
    {
        "reports": [
            {
                "id": str(uuid.uuid4()),
                "date": today_iso,
                "employees": ["Uli", "Matthias"],
                "employeeIds": [uli_id, matthias_id],
                "rawText": "ALLE DA",
            }
        ]
    },
)
res = client.get("/api/reminders/today", headers=hdrs)
body = res.json()
_expect(body.get("due") is False, "all present => not due")
_expect(body.get("missing") == [], "no missing")
_expect({p["id"] for p in body.get("present") or []} == {uli_id, matthias_id}, "both present")
_expect((body.get("todos") or {}).get("openToday") == 0, "no todos yet")
_expect((body.get("todos") or {}).get("overdue") == 0, "no overdue yet")

# To-do heute / ueberfaellig / erledigt / Zukunft — nur Zaehler, kein Titel
tomorrow_iso = (today + timedelta(days=1)).isoformat()
store.write_json(
    "tasks.json",
    {
        "tasks": [
            {"id": str(uuid.uuid4()), "status": "open", "dueDate": today_iso, "title": "HEUTE GEHEIM"},
            {"id": str(uuid.uuid4()), "status": "open", "dueDate": today_iso, "title": "Noch eine"},
            {"id": str(uuid.uuid4()), "status": "open", "dueDate": yesterday_iso, "title": "ALT"},
            {"id": str(uuid.uuid4()), "status": "done", "dueDate": today_iso, "title": "fertig"},
            {"id": str(uuid.uuid4()), "status": "open", "dueDate": tomorrow_iso, "title": "spaeter"},
        ]
    },
)
res = client.get("/api/reminders/today", headers=hdrs)
body = res.json()
todos = body.get("todos") or {}
_expect(todos.get("openToday") == 2, f"openToday: {todos}")
_expect(todos.get("overdue") == 1, f"overdue: {todos}")
_expect("HEUTE GEHEIM" not in res.text, "todo title must not leak")
_expect(body.get("due") is False, "todos must not flip report-due")

# Worker darf den Chef-Blick nicht sehen
worker_id = str(uuid.uuid4())
users = main.get_users()
users.append(
    {
        "id": worker_id,
        "tenantId": owner_id,
        "accountRole": "worker",
        "employeeId": uli_id,
        "companyName": "Smoke GmbH",
        "email": f"today-worker-{uuid.uuid4().hex[:8]}@example.com",
        "password": "pw",
        "username": f"todayw{uuid.uuid4().hex[:6]}",
        "createdAt": "2026-01-01T00:00:00+00:00",
    }
)
main.save_users(users)
res = client.get("/api/reminders/today", headers={"Authorization": f"Bearer {worker_id}"})
_expect(res.status_code == 403, f"worker should 403: {res.status_code} {res.text}")

print("TODAY-PRESENCE-SMOKE: OK")
