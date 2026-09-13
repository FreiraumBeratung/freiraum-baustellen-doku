"""To-do / Aufgaben (Phase 1–3) — rein additiv.

GF legt Aufgaben an und weist Mitarbeiter zu.
Mitarbeiter sehen nur eigene offenen/erledigten Aufgaben und können abhaken.
Phase 2: optionale Soll-Menge, Ist-Meldung, Rest und gemeinsame Historie.
Phase 3: Fotos und optionale Unterschrift an der Aufgabe.
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
MAX_PHOTOS_PER_TASK = 10
MAX_TASKS_PER_BATCH = 20
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


def require_task_access(
    store: TenantStore,
    task_id: str,
    *,
    is_owner: bool,
    employee_id: str | None,
) -> dict[str, Any]:
    task = find_task(store, task_id)
    if not _can_mutate_task(task, is_owner=is_owner, employee_id=employee_id):
        raise HTTPException(status_code=403, detail="Keine Berechtigung für diese Aufgabe.")
    return task


def task_photos_list(task: dict[str, Any]) -> list[dict[str, Any]]:
    raw = task.get("photos")
    if not isinstance(raw, list):
        return []
    return [p for p in raw if isinstance(p, dict) and p.get("filename")]


def task_signature_doc(task: dict[str, Any]) -> dict[str, Any] | None:
    raw = task.get("signature")
    if isinstance(raw, dict) and raw.get("filename"):
        return raw
    return None


def save_task_photos(store: TenantStore, task_id: str, photos: list[dict[str, Any]]) -> dict[str, Any]:
    tasks = read_tasks(store)
    for item in tasks:
        if str(item.get("id") or "") == str(task_id):
            item["photos"] = photos
            write_tasks(store, tasks)
            return item
    raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")


def save_task_signature(
    store: TenantStore,
    task_id: str,
    signature: dict[str, Any] | None,
) -> dict[str, Any]:
    tasks = read_tasks(store)
    for item in tasks:
        if str(item.get("id") or "") == str(task_id):
            item["signature"] = signature
            write_tasks(store, tasks)
            return item
    raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")


def task_media_filenames(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    photos: list[str] = []
    for entry in task_photos_list(task):
        fn = str(entry.get("filename") or "").strip()
        if fn:
            photos.append(fn)
    signatures: list[str] = []
    sig = task_signature_doc(task)
    if sig:
        fn = str(sig.get("filename") or "").strip()
        if fn:
            signatures.append(fn)
    return photos, signatures


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
        "photoCount": len(task_photos_list(task)),
        "hasSignature": task_signature_doc(task) is not None,
        "ownerSeen": bool(task.get("ownerSeen", True)),
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


def owner_unseen_done_count(store: TenantStore) -> int:
    n = 0
    for raw in read_tasks(store):
        pub = public_task(raw)
        if pub["status"] == "done" and not pub["ownerSeen"]:
            n += 1
    return n


def badge_payload(
    store: TenantStore,
    *,
    is_owner: bool,
    employee_id: str | None,
) -> dict[str, int]:
    if is_owner:
        return {
            "openCount": 0,
            "doneUnseenCount": owner_unseen_done_count(store),
        }
    return {
        "openCount": open_task_count_for_user(
            store,
            is_owner=False,
            employee_id=employee_id,
        ),
        "doneUnseenCount": 0,
    }


def ack_done_for_owner(store: TenantStore) -> int:
    tasks = read_tasks(store)
    changed = 0
    for item in tasks:
        if str(item.get("status") or "") != "done":
            continue
        if item.get("ownerSeen", True):
            continue
        item["ownerSeen"] = True
        changed += 1
    if changed:
        write_tasks(store, tasks)
    return changed


def _resolved_create_context(
    store: TenantStore,
    *,
    project_id: str,
    project_name: str,
    due_date: str,
    assignee_ids: list[str],
) -> tuple[str, str, str, list[str], list[str]]:
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
    return pid, pname, due, ids, _assignee_names_for_ids(store, ids)


def _normalize_task_item(title: str, target_quantity: float | None, unit: str) -> tuple[str, float | None, str]:
    title_clean = str(title or "").strip()
    if len(title_clean) < 3:
        raise HTTPException(status_code=400, detail="Aufgaben-Text zu kurz (min. 3 Zeichen).")
    if len(title_clean) > 2000:
        raise HTTPException(status_code=400, detail="Aufgaben-Text zu lang.")
    target = _coerce_quantity(target_quantity)
    if target_quantity not in (None, "") and target is None:
        raise HTTPException(status_code=400, detail="Soll-Menge ungültig.")
    unit_clean = _normalize_unit(unit, has_target=target is not None)
    return title_clean, target, unit_clean


def _new_task_record(
    *,
    created_by: str,
    project_id: str,
    project_name: str,
    title: str,
    due_date: str,
    assignee_ids: list[str],
    assignee_names: list[str],
    target_quantity: float | None,
    unit: str,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "projectId": project_id,
        "projectName": project_name,
        "title": title,
        "dueDate": due_date,
        "assigneeIds": assignee_ids,
        "assigneeNames": assignee_names,
        "status": "open",
        "createdBy": str(created_by or "").strip(),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "completedAt": None,
        "completedBy": None,
        "ownerSeen": True,
        "targetQuantity": target_quantity,
        "unit": unit,
        "progress": [],
        "photos": [],
        "signature": None,
    }


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
    created = create_tasks_batch(
        store,
        created_by=created_by,
        project_id=project_id,
        project_name=project_name,
        due_date=due_date,
        assignee_ids=assignee_ids,
        items=[{"title": title, "targetQuantity": target_quantity, "unit": unit}],
    )
    return created[0]


def create_tasks_batch(
    store: TenantStore,
    *,
    created_by: str,
    project_id: str,
    project_name: str,
    due_date: str,
    assignee_ids: list[str],
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise HTTPException(status_code=400, detail="Mindestens eine Aufgabe angeben.")
    if len(items) > MAX_TASKS_PER_BATCH:
        raise HTTPException(status_code=400, detail=f"Maximal {MAX_TASKS_PER_BATCH} Aufgaben auf einmal.")

    pid, pname, due, ids, names = _resolved_create_context(
        store,
        project_id=project_id,
        project_name=project_name,
        due_date=due_date,
        assignee_ids=assignee_ids,
    )
    built: list[dict[str, Any]] = []
    for raw in items:
        if not isinstance(raw, dict):
            raise HTTPException(status_code=400, detail="Ungültige Aufgabenzeile.")
        title_clean, target, unit_clean = _normalize_task_item(
            str(raw.get("title") or ""),
            raw.get("targetQuantity"),
            str(raw.get("unit") or ""),
        )
        built.append(
            _new_task_record(
                created_by=created_by,
                project_id=pid,
                project_name=pname,
                title=title_clean,
                due_date=due,
                assignee_ids=ids,
                assignee_names=names,
                target_quantity=target,
                unit=unit_clean,
            )
        )
    tasks = read_tasks(store)
    tasks.extend(built)
    write_tasks(store, tasks)
    return [public_task(t) for t in built]


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
    task["ownerSeen"] = False
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
    task["ownerSeen"] = True
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


def delete_task(store: TenantStore, task_id: str) -> dict[str, Any]:
    tasks = read_tasks(store)
    target = next((t for t in tasks if str(t.get("id") or "") == str(task_id)), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Aufgabe nicht gefunden")
    write_tasks(store, [t for t in tasks if str(t.get("id") or "") != str(task_id)])
    return target
