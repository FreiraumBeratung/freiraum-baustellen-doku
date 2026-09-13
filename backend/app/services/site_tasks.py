"""To-do / Aufgaben (Phase 1+2) — rein additiv.

GF legt Aufgaben an und weist Mitarbeiter zu.
Mitarbeiter sehen nur eigene offenen/erledigten Aufgaben und können abhaken.
Phase 2: optionale Soll-Menge, Ist-Meldung, Rest und gemeinsame Historie.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.services.tenant_storage import TenantStore

TASK_STATUSES = frozenset({"open", "done"})
MAX_TARGET_QUANTITY = 1_000_000.0
MAX_PROGRESS_ENTRIES = 80
UNIT_ALIASES = {
    "m2": "m²",
    "qm": "m²",
    "m3": "m³",
    "cbm": "m³",
}


def read_tasks(store: TenantStore) -> list[dict[str, Any]]:
    data = store.read_json("tasks.json", {"tasks": []})
    return [t for t in list(data.get("tasks") or []) if isinstance(t, dict)]


def write_tasks(store: TenantStore, tasks: list[dict[str, Any]]) -> None:
    store.write_json("tasks.json", {"tasks": tasks})


def find_task(store: TenantStore, task_id: str) -> dict[str, Any]:
    tid = str(task_id or "").strip()
    for item in read_tasks(store):
        if str(item.get("id") or "") == tid:
            return item
    raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")


def _normalize_assignee_ids(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        eid = str(item or "").strip()
        if eid and eid not in seen:
            seen.add(eid)
            out.append(eid)
    return out


def _assignee_names_for_ids(store: TenantStore, assignee_ids: list[str]) -> list[str]:
    data = store.read_json("employees.json", {"employees": []})
    name_by_id: dict[str, str] = {}
    for emp in list(data.get("employees") or []):
        if not isinstance(emp, dict):
            continue
        eid = str(emp.get("id") or "").strip()
        if eid:
            name_by_id[eid] = str(emp.get("name") or eid).strip() or eid
    return [name_by_id.get(eid, eid) for eid in assignee_ids]


def employee_name_for_id(store: TenantStore, employee_id: str | None) -> str:
    eid = str(employee_id or "").strip()
    if not eid:
        return ""
    names = _assignee_names_for_ids(store, [eid])
    return names[0] if names else eid


def _normalize_unit(raw: Any, *, has_target: bool) -> str:
    if not has_target:
        return ""
    unit = str(raw or "").strip()
    if not unit:
        return "m²"
    if len(unit) > 16:
        raise HTTPException(status_code=400, detail="Einheit zu lang.")
    return UNIT_ALIASES.get(unit.lower(), unit)


def _coerce_quantity(raw: Any) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    if val <= 0:
        return None
    if val > MAX_TARGET_QUANTITY:
        return MAX_TARGET_QUANTITY
    return round(val, 3)


def _require_quantity(raw: Any, *, field: str) -> float:
    try:
        val = float(raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"{field} ungültig.") from None
    if val <= 0:
        raise HTTPException(status_code=400, detail=f"{field} muss größer als 0 sein.")
    if val > MAX_TARGET_QUANTITY:
        raise HTTPException(status_code=400, detail=f"{field} zu groß.")
    return round(val, 3)


def _progress_entries(task: dict[str, Any]) -> list[dict[str, Any]]:
    raw = task.get("progress")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        amount = _coerce_quantity(item.get("amount"))
        if amount is None:
            continue
        actor = str(item.get("actorName") or "").strip()
        if not actor:
            continue
        out.append(
            {
                "id": str(item.get("id") or ""),
                "employeeId": str(item.get("employeeId") or ""),
                "actorName": actor,
                "amount": amount,
                "createdAt": str(item.get("createdAt") or ""),
            }
        )
    return out


def _actual_quantity(entries: list[dict[str, Any]]) -> float:
    return round(sum(float(e.get("amount") or 0) for e in entries), 3)


def _can_mutate_task(
    task: dict[str, Any],
    *,
    is_owner: bool,
    employee_id: str | None,
) -> bool:
    assignees = _normalize_assignee_ids(task.get("assigneeIds"))
    eid = str(employee_id or "").strip()
    return bool(is_owner or (eid and eid in assignees))


def public_task(task: dict[str, Any]) -> dict[str, Any]:
    status = str(task.get("status") or "open").strip().lower()
    if status not in TASK_STATUSES:
        status = "open"
    entries = _progress_entries(task)
    target = _coerce_quantity(task.get("targetQuantity"))
    actual = _actual_quantity(entries) if target is not None else 0.0
    remaining = None if target is None else round(max(0.0, target - actual), 3)
    unit = str(task.get("unit") or "").strip()
    if target is not None and not unit:
        unit = "m²"
    if target is None:
        unit = ""
    return {
        "id": str(task.get("id") or ""),
        "projectId": str(task.get("projectId") or ""),
        "projectName": str(task.get("projectName") or ""),
        "title": str(task.get("title") or ""),
        "dueDate": str(task.get("dueDate") or ""),
        "assigneeIds": _normalize_assignee_ids(task.get("assigneeIds")),
        "assigneeNames": [str(x) for x in (task.get("assigneeNames") or []) if str(x).strip()],
        "status": status,
        "createdBy": str(task.get("createdBy") or ""),
        "createdAt": str(task.get("createdAt") or ""),
        "completedAt": str(task.get("completedAt") or "") or None,
        "completedBy": str(task.get("completedBy") or "") or None,
        "targetQuantity": target,
        "actualQuantity": actual if target is not None else None,
        "remainingQuantity": remaining,
        "unit": unit,
        "progress": entries,
    }


def list_tasks_for_user(
    store: TenantStore,
    *,
    is_owner: bool,
    employee_id: str | None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    want_status = str(status or "").strip().lower()
    if want_status and want_status not in TASK_STATUSES:
        want_status = ""

    out: list[dict[str, Any]] = []
    eid = str(employee_id or "").strip()
    for raw in read_tasks(store):
        task = public_task(raw)
        if want_status and task["status"] != want_status:
            continue
        if is_owner:
            out.append(task)
            continue
        if eid and eid in task["assigneeIds"]:
            out.append(task)
    out.sort(key=lambda t: (t.get("dueDate") or "", t.get("createdAt") or ""), reverse=True)
    return out


def open_task_count_for_user(
    store: TenantStore,
    *,
    is_owner: bool,
    employee_id: str | None,
) -> int:
    return len(
        list_tasks_for_user(
            store,
            is_owner=is_owner,
            employee_id=employee_id,
            status="open",
        )
    )


def create_task(
    store: TenantStore,
    *,
    created_by: str,
    project_id: str,
    project_name: str,
    title: str,
    due_date: str,
    assignee_ids: list[str],
    target_quantity: float | None = None,
    unit: str = "",
) -> dict[str, Any]:
    title_clean = str(title or "").strip()
    if len(title_clean) < 3:
        raise HTTPException(status_code=400, detail="Aufgaben-Text zu kurz (min. 3 Zeichen).")
    if len(title_clean) > 2000:
        raise HTTPException(status_code=400, detail="Aufgaben-Text zu lang.")
    pid = str(project_id or "").strip()
    if not pid:
        raise HTTPException(status_code=400, detail="Baustelle fehlt.")
    due = str(due_date or "").strip()
    if not due:
        raise HTTPException(status_code=400, detail="Datum fehlt.")
    ids = _normalize_assignee_ids(assignee_ids)
    if not ids:
        raise HTTPException(status_code=400, detail="Mindestens einen Mitarbeiter zuweisen.")

    emp_data = store.read_json("employees.json", {"employees": []})
    known = {
        str(e.get("id") or "").strip()
        for e in list(emp_data.get("employees") or [])
        if isinstance(e, dict)
    }
    unknown = [x for x in ids if x not in known]
    if unknown:
        raise HTTPException(status_code=400, detail="Unbekannte Mitarbeiter-ID.")

    proj_data = store.read_json("projects.json", {"projects": []})
    pname = str(project_name or "").strip()
    for p in list(proj_data.get("projects") or []):
        if isinstance(p, dict) and str(p.get("id") or "") == pid:
            pname = str(p.get("name") or pname).strip() or pname
            break
    if not pname:
        pname = "Baustelle"

    target = _coerce_quantity(target_quantity)
    if target_quantity not in (None, "") and target is None:
        raise HTTPException(status_code=400, detail="Soll-Menge ungültig.")
    unit_clean = _normalize_unit(unit, has_target=target is not None)

    task = {
        "id": str(uuid.uuid4()),
        "projectId": pid,
        "projectName": pname,
        "title": title_clean,
        "dueDate": due,
        "assigneeIds": ids,
        "assigneeNames": _assignee_names_for_ids(store, ids),
        "status": "open",
        "createdBy": str(created_by or "").strip(),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "completedAt": None,
        "completedBy": None,
        "targetQuantity": target,
        "unit": unit_clean,
        "progress": [],
    }
    tasks = read_tasks(store)
    tasks.append(task)
    write_tasks(store, tasks)
    return public_task(task)


def complete_task(
    store: TenantStore,
    task_id: str,
    *,
    user_id: str,
    is_owner: bool,
    employee_id: str | None,
) -> dict[str, Any]:
    tasks = read_tasks(store)
    idx = next((i for i, t in enumerate(tasks) if str(t.get("id") or "") == str(task_id)), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    task = dict(tasks[idx])
    if not _can_mutate_task(task, is_owner=is_owner, employee_id=employee_id):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aufgabe.")
    if str(task.get("status") or "") == "done":
        return public_task(task)
    task["status"] = "done"
    task["completedAt"] = datetime.now(timezone.utc).isoformat()
    task["completedBy"] = str(user_id or "").strip()
    tasks[idx] = task
    write_tasks(store, tasks)
    return public_task(task)


def reopen_task(store: TenantStore, task_id: str) -> dict[str, Any]:
    tasks = read_tasks(store)
    idx = next((i for i, t in enumerate(tasks) if str(t.get("id") or "") == str(task_id)), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    task = dict(tasks[idx])
    task["status"] = "open"
    task["completedAt"] = None
    task["completedBy"] = None
    tasks[idx] = task
    write_tasks(store, tasks)
    return public_task(task)


def add_progress(
    store: TenantStore,
    task_id: str,
    *,
    amount: float,
    actor_name: str,
    is_owner: bool,
    employee_id: str | None,
) -> dict[str, Any]:
    qty = _require_quantity(amount, field="Menge")
    name = str(actor_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name für Fortschritt fehlt.")
    if len(name) > 120:
        name = name[:120]

    tasks = read_tasks(store)
    idx = next((i for i, t in enumerate(tasks) if str(t.get("id") or "") == str(task_id)), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    task = dict(tasks[idx])
    if not _can_mutate_task(task, is_owner=is_owner, employee_id=employee_id):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aufgabe.")
    if str(task.get("status") or "") == "done":
        raise HTTPException(status_code=400, detail="Aufgabe ist bereits erledigt.")
    if _coerce_quantity(task.get("targetQuantity")) is None:
        raise HTTPException(status_code=400, detail="Keine Soll-Menge hinterlegt.")

    entries = _progress_entries(task)
    if len(entries) >= MAX_PROGRESS_ENTRIES:
        raise HTTPException(status_code=400, detail="Zu viele Fortschritts-Einträge.")
    entries.append(
        {
            "id": str(uuid.uuid4()),
            "employeeId": str(employee_id or "").strip(),
            "actorName": name,
            "amount": qty,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
    )
    task["progress"] = entries
    tasks[idx] = task
    write_tasks(store, tasks)
    return public_task(task)


def delete_task(store: TenantStore, task_id: str) -> None:
    tasks = read_tasks(store)
    next_tasks = [t for t in tasks if str(t.get("id") or "") != str(task_id)]
    if len(next_tasks) == len(tasks):
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    write_tasks(store, next_tasks)
