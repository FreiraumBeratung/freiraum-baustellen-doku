"""Smoke fuer Welle Z1: Stundenkonto (Backend-only).

Testet Buchungslogik, Saldo, Startsaldo, Report-Delete und Idempotenz.
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

_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_time_smoke_"))
print(f"[smoke] using tmp data dir: {_TMP_DIR}")

import main  # noqa: E402
from app.services import time_account  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

main.DATA_DIR = _TMP_DIR
main.EMPLOYEES_FILE = _TMP_DIR / "employees.json"
main.REPORTS_FILE = _TMP_DIR / "reports.json"
main.TIME_ENTRIES_FILE = _TMP_DIR / "time_entries.json"
main.USERS_FILE = _TMP_DIR / "users.json"
main.COMPANY_FILE = _TMP_DIR / "company_profile.json"
time_account.configure(main.TIME_ENTRIES_FILE)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _auth_headers() -> dict[str, str]:
    user_id = str(uuid.uuid4())
    main.save_users(
        [
            {
                "id": user_id,
                "companyName": "Smoke GmbH",
                "entrepreneurName": "Tester",
                "email": f"time-smoke-{uuid.uuid4().hex[:6]}@example.com",
                "password": "pw",
                "createdAt": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    return {"Authorization": f"Bearer {user_id}"}


def _structured_payload() -> dict:
    return {
        "summary": "Test",
        "activities": ["Arbeit"],
        "materials": [],
        "materialSuggestions": [],
        "machineSuggestions": [],
        "machineHours": [],
        "problems": [],
        "openItems": [],
        "customerTalk": "",
    }


client = TestClient(main.app)
hdrs = _auth_headers()

denis = client.post("/api/employees", headers=hdrs, json={"name": "Denis", "role": "", "active": True}).json()
matthias = client.post(
    "/api/employees",
    headers=hdrs,
    json={"name": "Matthias", "role": "", "active": True, "hoursBalanceStart": 12.5, "hoursBalanceStartDate": "2026-01-01"},
).json()
denis_id = denis["id"]
matthias_id = matthias["id"]
_expect(bool(denis_id and matthias_id), "employees missing")

_expect(time_account.compute_booked_hours("08:00", "16:30", 45) == 7.75, "7.75h expected")
_expect(time_account.compute_booked_hours("16:30", "08:00", 45) is None, "invalid range expected")

report_body = {
    "companyName": "Smoke GmbH",
    "officeEmail": "office@example.com",
    "projectId": str(uuid.uuid4()),
    "projectName": "Garten Müller",
    "customerName": "Müller",
    "date": "2026-05-30",
    "employees": ["Denis", "Matthias"],
    "startTime": "08:00",
    "endTime": "16:30",
    "breakMinutes": 45,
    "exportFormat": "PDF",
    "rawText": "Rohtext",
    "structured": _structured_payload(),
}
res = client.post("/api/reports", headers=hdrs, json=report_body)
_expect(res.status_code == 200, f"create report: {res.status_code} {res.text}")
report = res.json()
report_id = report["id"]
booking = report.get("timeBooking") or {}
_expect(booking.get("created") == 2, f"expected 2 bookings, got {booking}")
_expect(booking.get("hoursPerEmployee") == 7.75, "hoursPerEmployee mismatch")

entries = client.get("/api/time-entries", headers=hdrs).json().get("entries") or []
_expect(len(entries) == 2, f"expected 2 entries, got {len(entries)}")
for entry in entries:
    _expect(entry.get("hours") == 7.75, "entry hours mismatch")
    _expect(entry.get("reportId") == report_id, "reportId mismatch")

accounts = client.get("/api/time-accounts?month=2026-05", headers=hdrs).json()
accts = {a["employeeId"]: a for a in accounts.get("accounts") or []}
_expect(accts[denis_id]["bookedHoursTotal"] == 7.75, "denis booked total")
_expect(accts[denis_id]["currentBalance"] == 7.75, "denis balance without start")
_expect(accts[matthias_id]["hoursBalanceStart"] == 12.5, "matthias start balance")
_expect(accts[matthias_id].get("hoursBalanceStartDate") == "2026-01-01", "matthias start date")
_expect(accts[matthias_id]["currentBalance"] == 20.25, "matthias current balance")

employees = client.get("/api/employees", headers=hdrs).json().get("employees") or []
sync2 = time_account.sync_entries_for_report(
    report,
    employees,
    read_json=main._read_json,
    write_json=main._write_json,
)
_expect(sync2.get("created") == 2, "resync should replace with 2 entries")
entries2 = client.get("/api/time-entries", headers=hdrs).json().get("entries") or []
_expect(len(entries2) == 2, "still 2 entries after resync")

report_body2 = {
    **report_body,
    "projectId": str(uuid.uuid4()),
    "employees": ["Denis", "Unbekannt"],
}
res2 = client.post("/api/reports", headers=hdrs, json=report_body2)
report2 = res2.json()
booking2 = report2.get("timeBooking") or {}
_expect(booking2.get("created") == 1, "only Denis should match")
_expect("Unbekannt" in (booking2.get("skippedNames") or []), "unknown name skipped")

res_del = client.delete(f"/api/reports/{report_id}", headers=hdrs)
_expect(res_del.status_code == 200, "delete report")
remaining = client.get("/api/time-entries", headers=hdrs).json().get("entries") or []
_expect(all(e.get("reportId") != report_id for e in remaining), "entries for deleted report removed")

res_patch = client.patch(
    f"/api/employees/{denis_id}",
    headers=hdrs,
    json={"hoursBalanceStart": -4.0, "hoursBalanceStartDate": "2026-01-01"},
)
_expect(res_patch.status_code == 200, "patch start balance")
accounts_after = client.get("/api/time-accounts?month=2026-05", headers=hdrs).json()
denis_acct = next(a for a in accounts_after["accounts"] if a["employeeId"] == denis_id)
_expect(denis_acct["hoursBalanceStart"] == -4.0, "patched start balance")
_expect(denis_acct.get("hoursBalanceStartDate") == "2026-01-01", "patched start date")
_expect(
    denis_acct["currentBalance"] == round(-4.0 + denis_acct["bookedHoursTotal"], 2),
    "balance includes start",
)

report_body3 = {
    **report_body,
    "projectId": str(uuid.uuid4()),
    "employees": ["Falscher Name"],
    "employeeIds": [matthias_id],
    "breakMinutes": 60,
}
res3 = client.post("/api/reports", headers=hdrs, json=report_body3)
_expect(res3.status_code == 200, f"create report with ids: {res3.text}")
booking3 = res3.json().get("timeBooking") or {}
_expect(booking3.get("created") == 1, "employeeIds booking")
_expect(booking3.get("hoursPerEmployee") == 7.5, "7.5h with 60min break")
entries3 = client.get(f"/api/time-entries?employeeId={matthias_id}", headers=hdrs).json().get("entries") or []
_expect(any(e.get("hours") == 7.5 for e in entries3), "7.5h entry for matthias")
entry_to_delete = next(e["id"] for e in entries3 if e.get("hours") == 7.5)
res_del_entry = client.delete(f"/api/time-entries/{entry_to_delete}", headers=hdrs)
_expect(res_del_entry.status_code == 200, "delete single entry")
entries_after_del = client.get(f"/api/time-entries?employeeId={matthias_id}", headers=hdrs).json().get("entries") or []
_expect(all(e.get("id") != entry_to_delete for e in entries_after_del), "entry removed")

res_corr = client.post(
    "/api/time-entries",
    headers=hdrs,
    json={
        "employeeId": matthias_id,
        "date": "2026-05-30",
        "hours": -1.0,
        "note": "Früher Feierabend",
    },
)
_expect(res_corr.status_code == 200, f"manual correction: {res_corr.text}")
corr = res_corr.json()
_expect(corr.get("source") == "manual", "manual source")
_expect(corr.get("hours") == -1.0, "correction hours")

res_csv = client.get("/api/time-accounts/export/csv?month=2026-05", headers=hdrs)
_expect(res_csv.status_code == 200, f"csv export: {res_csv.status_code}")
_expect("text/csv" in (res_csv.headers.get("content-type") or ""), "csv content type")
body = res_csv.content.decode("utf-8-sig")
_expect("Mitarbeiter;Datum" in body, "csv header")
_expect("Bericht" in body, "csv bericht column")
_expect("ZUSAMMENFASSUNG" in body, "csv summary")
_expect("Denis" in body, "csv contains employee")

res_xlsx = client.get("/api/time-accounts/export/xlsx?month=2026-05", headers=hdrs)
_expect(res_xlsx.status_code == 200, f"xlsx export: {res_xlsx.status_code}")
_expect(
    "spreadsheetml" in (res_xlsx.headers.get("content-type") or ""),
    "xlsx content type",
)
_expect(res_xlsx.content[:2] == b"PK", "xlsx zip signature")

print("TIME-ACCOUNT-SMOKE (Z1): OK")
