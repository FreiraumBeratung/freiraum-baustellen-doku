"""Urlaub (Baustein 1): Jahreskontingent und Resttage — additiv.

Antraege liegen in derselben Datei (requests), zaehlen in V1 nur wenn status=approved.
Ohne Kontingent bleibt Rest ungesetzt — nicht still 0.
Tagesbericht, Stundenkonto und To-do bleiben unberuehrt.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import HTTPException

from app.services.tenant_storage import TenantStore

LEAVE_FILE = "leave.json"
LEAVE_STATUSES = frozenset({"pending", "approved", "rejected"})
MAX_LEAVE_DAYS = 99
MAX_RANGE_DAYS = 400


def current_leave_year() -> int:
    return date.today().year


def empty_doc() -> dict[str, Any]:
    return {"allowances": [], "requests": []}


def read_doc(store: TenantStore) -> dict[str, Any]:
    data = store.read_json(LEAVE_FILE, empty_doc())
    if not isinstance(data, dict):
        return empty_doc()
    allowances = data.get("allowances")
    requests = data.get("requests")
    return {
        "allowances": [a for a in allowances if isinstance(a, dict)] if isinstance(allowances, list) else [],
        "requests": [r for r in requests if isinstance(r, dict)] if isinstance(requests, list) else [],
    }


def write_doc(store: TenantStore, doc: dict[str, Any]) -> None:
    store.write_json(
        LEAVE_FILE,
        {
            "allowances": list(doc.get("allowances") or []),
            "requests": list(doc.get("requests") or []),
        },
    )


def parse_iso_date(raw: Any) -> date | None:
    s = str(raw or "").strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def count_weekdays(start: date, end: date, *, year: int | None = None) -> int:
    """Mo–Fr zwischen start und end inklusive. Optional nur Tage eines Jahres."""
    if end < start:
        return 0
    n = 0
    d = start
    guard = 0
    while d <= end and guard < MAX_RANGE_DAYS:
        if d.weekday() < 5 and (year is None or d.year == year):
            n += 1
        d += timedelta(days=1)
        guard += 1
    return n


def _parse_days(raw: Any) -> int | None:
    """None = Kontingent loeschen. 0 ist ein gesetzter Wert."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise HTTPException(status_code=400, detail="Ungültige Tageszahl")
    if isinstance(raw, float):
        if not raw.is_integer():
            raise HTTPException(status_code=400, detail="Nur ganze Urlaubstage")
        raw = int(raw)
    if isinstance(raw, int):
        n = raw
    else:
        s = str(raw).strip().replace(",", ".")
        if not s:
            return None
        if "." in s:
            try:
                f = float(s)
            except ValueError:
                raise HTTPException(status_code=400, detail="Ungültige Tageszahl") from None
            if not f.is_integer():
                raise HTTPException(status_code=400, detail="Nur ganze Urlaubstage")
            n = int(f)
        else:
            try:
                n = int(s)
            except ValueError:
                raise HTTPException(status_code=400, detail="Ungültige Tageszahl") from None
    if n < 0 or n > MAX_LEAVE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"Urlaubstage müssen zwischen 0 und {MAX_LEAVE_DAYS} liegen",
        )
    return n


def _employees(store: TenantStore) -> list[dict[str, Any]]:
    data = store.read_json("employees.json", {"employees": []})
    return [e for e in list(data.get("employees") or []) if isinstance(e, dict)]


def _find_employee(store: TenantStore, employee_id: str) -> dict[str, Any] | None:
    eid = str(employee_id or "").strip()
    if not eid:
        return None
    for emp in _employees(store):
        if str(emp.get("id") or "") == eid:
            return emp
    return None


def _allowance_days(doc: dict[str, Any], employee_id: str, year: int) -> int | None:
    eid = str(employee_id or "").strip()
    for row in doc.get("allowances") or []:
        if str(row.get("employeeId") or "") != eid:
            continue
        try:
            row_year = int(row.get("year"))
        except (TypeError, ValueError):
            continue
        if row_year != year:
            continue
        try:
            return int(row.get("days"))
        except (TypeError, ValueError):
            return None
    return None


def used_days(doc: dict[str, Any], employee_id: str, year: int) -> int:
    """Nur genehmigte Antraege, nur Werktage im Kalenderjahr."""
    eid = str(employee_id or "").strip()
    total = 0
    for req in doc.get("requests") or []:
        if str(req.get("employeeId") or "") != eid:
            continue
        if str(req.get("status") or "").strip().lower() != "approved":
            continue
        start = parse_iso_date(req.get("fromDate") or req.get("from"))
        end = parse_iso_date(req.get("toDate") or req.get("to"))
        if start is None or end is None:
            continue
        total += count_weekdays(start, end, year=year)
    return total


def person_payload(
    emp: dict[str, Any],
    doc: dict[str, Any],
    *,
    year: int,
) -> dict[str, Any]:
    eid = str(emp.get("id") or "").strip()
    allowance = _allowance_days(doc, eid, year)
    used = used_days(doc, eid, year)
    remaining: int | None
    if allowance is None:
        remaining = None
    else:
        remaining = max(0, allowance - used)
    return {
        "employeeId": eid,
        "name": str(emp.get("name") or "").strip() or eid,
        "active": bool(emp.get("active", True)),
        "allowanceSet": allowance is not None,
        "allowanceDays": allowance,
        "usedDays": used,
        "remainingDays": remaining,
    }


def build_overview(
    store: TenantStore,
    *,
    year: int,
    self_employee_id: str | None,
) -> dict[str, Any]:
    doc = read_doc(store)
    self_id = str(self_employee_id or "").strip()
    people = [person_payload(emp, doc, year=year) for emp in _employees(store) if emp.get("id")]
    people.sort(
        key=lambda p: (
            0 if p["employeeId"] == self_id else 1,
            0 if p.get("active") else 1,
            str(p.get("name") or "").casefold(),
        )
    )
    return {
        "year": year,
        "selfEmployeeId": self_id or None,
        "people": people,
    }


def set_allowance(
    store: TenantStore,
    employee_id: str,
    raw_days: Any,
    *,
    year: int,
) -> dict[str, Any]:
    emp = _find_employee(store, employee_id)
    if emp is None:
        raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
    days = _parse_days(raw_days)
    doc = read_doc(store)
    eid = str(emp.get("id") or "").strip()
    kept: list[dict[str, Any]] = []
    for row in doc.get("allowances") or []:
        if str(row.get("employeeId") or "") == eid:
            try:
                row_year = int(row.get("year"))
            except (TypeError, ValueError):
                kept.append(row)
                continue
            if row_year == year:
                continue
        kept.append(row)
    if days is not None:
        kept.append({"employeeId": eid, "year": year, "days": days})
    doc["allowances"] = kept
    write_doc(store, doc)
    return person_payload(emp, doc, year=year)
