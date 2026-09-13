"""To-do / Aufgaben (Phase 1) — rein additiv.

GF legt Aufgaben an und weist Mitarbeiter zu.
Mitarbeiter sehen nur eigene offenen/erledigten Aufgaben und können abhaken.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.services.tenant_storage import TenantStore

TASK_STATUSES = frozenset({"open", "done"})


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


def public_task(task: dict[str, Any]) -> dict[str, Any]:
    status = str(task.get("status") or "open").strip().lower()
    if status not in TASK_STATUSES:
        status = "open"
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
    assignees = _normalize_assignee_ids(task.get("assigneeIds"))
    eid = str(employee_id or "").strip()
    if not is_owner and (not eid or eid not in assignees):
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


def delete_task(store: TenantStore, task_id: str) -> None:
    tasks = read_tasks(store)
    next_tasks = [t for t in tasks if str(t.get("id") or "") != str(task_id)]
    if len(next_tasks) == len(tasks):
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    write_tasks(store, next_tasks)
