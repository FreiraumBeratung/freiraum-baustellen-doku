"""Smoke Phase-1 To-do/Aufgaben — rein additiv."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from smoke_isolation import isolate_smoke_data

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_tasks_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from app.services import site_tasks  # noqa: E402


def main() -> int:
    store = TenantStore(str(uuid.uuid4()))
    store.write_json(
        "employees.json",
        {
            "employees": [
                {"id": "e1", "name": "Max", "active": True},
                {"id": "e2", "name": "Lisa", "active": True},
            ]
        },
    )
    store.write_json(
        "projects.json",
        {"projects": [{"id": "p1", "name": "Schmitz Garten", "status": "aktiv"}]},
    )

    task = site_tasks.create_task(
        store,
        created_by="owner1",
        project_id="p1",
        project_name="Schmitz Garten",
        title="50 m² Rasen mähen",
        due_date="2026-09-15",
        assignee_ids=["e1", "e2"],
    )
    assert task["status"] == "open"
    assert task["assigneeNames"] == ["Max", "Lisa"]

    owner_open = site_tasks.list_tasks_for_user(store, is_owner=True, employee_id=None, status="open")
    assert len(owner_open) == 1

    max_open = site_tasks.list_tasks_for_user(store, is_owner=False, employee_id="e1", status="open")
    assert len(max_open) == 1

    stranger = site_tasks.list_tasks_for_user(store, is_owner=False, employee_id="e999", status="open")
    assert stranger == []

    done = site_tasks.complete_task(
        store,
        task["id"],
        user_id="worker-max",
        is_owner=False,
        employee_id="e1",
    )
    assert done["status"] == "done"
    assert site_tasks.open_task_count_for_user(store, is_owner=False, employee_id="e1") == 0
    assert site_tasks.open_task_count_for_user(store, is_owner=True, employee_id=None) == 0

    site_tasks.reopen_task(store, task["id"])
    assert site_tasks.open_task_count_for_user(store, is_owner=True, employee_id=None) == 1

    site_tasks.delete_task(store, task["id"])
    assert site_tasks.list_tasks_for_user(store, is_owner=True, employee_id=None) == []

    print("TASKS-PHASE1-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
