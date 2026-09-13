"""Smoke Phase-3 To-do Medien — rein additiv."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import HTTPException

from smoke_isolation import isolate_smoke_data

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_tasks_p3_")))

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
        title="Rasen mähen und Foto machen",
        due_date="2026-09-15",
        assignee_ids=["e1", "e2"],
    )
    assert task["photoCount"] == 0
    assert task["hasSignature"] is False

    site_tasks.require_task_access(store, task["id"], is_owner=False, employee_id="e1")
    try:
        site_tasks.require_task_access(store, task["id"], is_owner=False, employee_id="e999")
        raise AssertionError("Fremder darf Aufgabe nicht sehen")
    except HTTPException as exc:
        assert exc.status_code == 403

    site_tasks.save_task_photos(
        store,
        task["id"],
        [
            {
                "id": "ph1",
                "filename": "task_demo_ph1.jpg",
                "originalFilename": "rasen.jpg",
                "contentType": "image/jpeg",
                "sizeBytes": 12,
            }
        ],
    )
    site_tasks.save_task_signature(
        store,
        task["id"],
        {"id": "sig1", "filename": "sig_task_demo.png", "role": "employee"},
    )
    viewed = site_tasks.public_task(site_tasks.find_task(store, task["id"]))
    assert viewed["photoCount"] == 1
    assert viewed["hasSignature"] is True

    lisa = site_tasks.list_tasks_for_user(store, is_owner=False, employee_id="e2", status="open")
    assert lisa[0]["photoCount"] == 1

    deleted = site_tasks.delete_task(store, task["id"])
    photos, sigs = site_tasks.task_media_filenames(deleted)
    assert photos == ["task_demo_ph1.jpg"]
    assert sigs == ["sig_task_demo.png"]
    assert site_tasks.list_tasks_for_user(store, is_owner=True, employee_id=None) == []

    batch = site_tasks.create_tasks_batch(
        store,
        created_by="owner1",
        project_id="p1",
        project_name="Schmitz Garten",
        due_date="2026-09-16",
        assignee_ids=["e1"],
        items=[
            {"title": "Rasen mähen", "targetQuantity": 50, "unit": "m²"},
            {"title": "Hecke schneiden", "targetQuantity": None, "unit": ""},
        ],
    )
    assert len(batch) == 2
    assert batch[0]["targetQuantity"] == 50
    assert batch[1]["targetQuantity"] is None

    site_tasks.complete_task(store, batch[0]["id"], user_id="w1", is_owner=False, employee_id="e1")
    badge_owner = site_tasks.badge_payload(store, is_owner=True, employee_id=None)
    badge_worker = site_tasks.badge_payload(store, is_owner=False, employee_id="e1")
    assert badge_owner["openCount"] == 0
    assert badge_owner["doneUnseenCount"] == 1
    assert badge_worker["openCount"] == 1
    assert badge_worker["doneUnseenCount"] == 0

    assert site_tasks.ack_done_for_owner(store) == 1
    assert site_tasks.badge_payload(store, is_owner=True, employee_id=None)["doneUnseenCount"] == 0

    week = site_tasks.list_tasks_for_user(
        store,
        is_owner=True,
        employee_id=None,
        from_date="2026-09-16",
        to_date="2026-09-16",
    )
    assert len(week) == 2
    only_max = site_tasks.list_tasks_for_user(
        store,
        is_owner=True,
        employee_id=None,
        assignee_id="e1",
        from_date="2026-09-16",
        to_date="2026-09-16",
    )
    assert len(only_max) == 2
    none = site_tasks.list_tasks_for_user(
        store,
        is_owner=True,
        employee_id=None,
        project_id="p-missing",
    )
    assert none == []
    stranger_week = site_tasks.list_tasks_for_user(
        store,
        is_owner=False,
        employee_id="e2",
        from_date="2026-09-16",
        to_date="2026-09-16",
    )
    assert stranger_week == []

    print("TASKS-PHASE3-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
