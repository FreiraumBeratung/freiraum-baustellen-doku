"""Heute-Blick: wer aus dem aktiven Team in einem Tagesbericht von heute steht.

Rein lesend. Kein neuer Speicher, kein Rohtext, Buchung unangetastet.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.services import leave as leave_service
from app.services.site_tasks import read_tasks
from app.services.tenant_storage import TenantStore
from app.services.time_account import resolve_report_employees

BERLIN = ZoneInfo("Europe/Berlin")


def _normalize_report_date(raw: Any) -> str:
    s = str(raw or "").strip()
    if not s:
        return ""
    iso = s[:10]
    if len(iso) == 10 and iso[4] == "-" and iso[7] == "-":
        try:
            return date.fromisoformat(iso).isoformat()
        except ValueError:
            pass
    parts = s.replace(" ", "").split(".")
    if len(parts) == 3 and all(parts):
        try:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            return date(year, month, day).isoformat()
        except ValueError:
            return ""
    return ""


def _todo_counts(store: TenantStore, day: str) -> dict[str, int]:
    """Offene To-dos: heute faellig vs. ueberfaellig. Keine Titel, kein Rohtext."""
    open_today = 0
    overdue = 0
    for raw in read_tasks(store):
        if str(raw.get("status") or "open").strip().lower() != "open":
            continue
        due = _normalize_report_date(raw.get("dueDate"))
        if not due:
            continue
        if due == day:
            open_today += 1
        elif due < day:
            overdue += 1
    return {"openToday": open_today, "overdue": overdue}


def _leave_pending(store: TenantStore, employees: list[dict[str, Any]]) -> dict[str, Any]:
    """Offene Urlaubsantraege — nur Zaehler plus erster Name/Zeitraum, kein Resttage-Kram."""
    names = {
        str(e.get("id") or "").strip(): str(e.get("name") or "").strip()
        for e in employees
        if str(e.get("id") or "").strip()
    }
    pending: list[dict[str, str]] = []
    for req in leave_service.read_doc(store).get("requests") or []:
        if str(req.get("status") or "").strip().lower() != "pending":
            continue
        start = leave_service.parse_iso_date(req.get("fromDate") or req.get("from"))
        end = leave_service.parse_iso_date(req.get("toDate") or req.get("to") or req.get("fromDate"))
        if start is None or end is None or end < start:
            continue
        eid = str(req.get("employeeId") or "").strip()
        pending.append(
            {
                "name": names.get(eid) or "Mitarbeiter",
                "fromDate": start.isoformat(),
                "toDate": end.isoformat(),
            }
        )
    pending.sort(key=lambda r: (r["fromDate"], r["name"].casefold()))
    first = pending[0] if pending else None
    return {
        "pending": len(pending),
        "name": first["name"] if first else "",
        "fromDate": first["fromDate"] if first else "",
        "toDate": first["toDate"] if first else "",
    }


def _is_active_employee(emp: dict[str, Any]) -> bool:
    if "active" in emp and emp.get("active") is False:
        return False
    return True


def build_today_presence(
    store: TenantStore,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    day = (today or datetime.now(BERLIN).date()).isoformat()
    raw_emps = store.read_json("employees.json", {"employees": []}).get("employees") or []
    employees = [e for e in raw_emps if isinstance(e, dict)]
    active = [
        e
        for e in employees
        if _is_active_employee(e) and str(e.get("id") or "").strip() and str(e.get("name") or "").strip()
    ]

    present_ids: set[str] = set()
    reports = store.read_json("reports.json", {"reports": []}).get("reports") or []
    for item in reports:
        if not isinstance(item, dict):
            continue
        if _normalize_report_date(item.get("date")) != day:
            continue
        matched, _, _ = resolve_report_employees(item, employees)
        for emp, _label in matched:
            eid = str(emp.get("id") or "").strip()
            if eid:
                present_ids.add(eid)

    missing: list[dict[str, str]] = []
    present: list[dict[str, str]] = []
    for emp in active:
        eid = str(emp.get("id") or "").strip()
        row = {"id": eid, "name": str(emp.get("name") or "").strip()}
        if eid in present_ids:
            present.append(row)
        else:
            missing.append(row)

    missing.sort(key=lambda r: r["name"].casefold())
    present.sort(key=lambda r: r["name"].casefold())
    return {
        "date": day,
        "due": bool(missing),
        "missing": missing,
        "present": present,
        "todos": _todo_counts(store, day),
        "leave": _leave_pending(store, employees),
    }
