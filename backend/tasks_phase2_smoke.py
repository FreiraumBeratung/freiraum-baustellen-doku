"""Smoke Phase-2 To-do Fortschritt — rein additiv."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import HTTPException

from smoke_isolation import isolate_smoke_data

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_tasks_p2_")))

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
        {
            "projects": [
                {
                    "id": "p1",
                    "name": "Schmitz Garten",
                    "status": "aktiv",
                    "address": "Gartenweg 4",
                    "city": "12345 Musterstadt",
                }
            ]
        },
    )

    # Phase-1-Aufgabe ohne Menge bleibt möglich.
    plain = site_tasks.create_task(
        store,
        created_by="owner1",
        project_id="p1",
        project_name="Schmitz Garten",
        title="Zaun prüfen",
        due_date="2026-09-15",
        assignee_ids=["e1"],
    )
    assert plain["targetQuantity"] is None
    assert plain["progress"] == []
    try:
        site_tasks.add_progress(
            store,
            plain["id"],
            amount=10,
            actor_name="Max",
            is_owner=False,
            employee_id="e1",
        )
        raise AssertionError("Fortschritt ohne Soll muss scheitern")
    except HTTPException as exc:
        assert exc.status_code == 400

    task = site_tasks.create_task(
        store,
        created_by="owner1",
        project_id="p1",
        project_name="Schmitz Garten",
        title="50 m² Rasen mähen",
        due_date="2026-09-15",
        assignee_ids=["e1", "e2"],
        target_quantity=50,
        unit="m2",
    )
    assert task["targetQuantity"] == 50
    assert task["unit"] == "m²"
    assert task["actualQuantity"] == 0
    assert task["remainingQuantity"] == 50

    after_max = site_tasks.add_progress(
        store,
        task["id"],
        amount=30,
        actor_name="Max",
        is_owner=False,
        employee_id="e1",
    )
    assert after_max["actualQuantity"] == 30
    assert after_max["remainingQuantity"] == 20
    assert after_max["progress"][0]["actorName"] == "Max"

    lisa_view = site_tasks.list_tasks_for_user(store, is_owner=False, employee_id="e2", status="open")
    shared = next(t for t in lisa_view if t["id"] == task["id"])
    assert shared["remainingQuantity"] == 20
    assert [p["actorName"] for p in shared["progress"]] == ["Max"]

    try:
        site_tasks.add_progress(
            store,
            task["id"],
            amount=5,
            actor_name="Fremd",
            is_owner=False,
            employee_id="e999",
        )
        raise AssertionError("Fremder darf keinen Fortschritt schreiben")
    except HTTPException as exc:
        assert exc.status_code == 403

    after_lisa = site_tasks.add_progress(
        store,
        task["id"],
        amount=20,
        actor_name="Lisa",
        is_owner=False,
        employee_id="e2",
    )
    assert after_lisa["actualQuantity"] == 50
    assert after_lisa["remainingQuantity"] == 0
    assert [p["actorName"] for p in after_lisa["progress"]] == ["Max", "Lisa"]

    done = site_tasks.complete_task(
        store,
        task["id"],
        user_id="worker-lisa",
        is_owner=False,
        employee_id="e2",
        actor_name="Lisa",
    )
    assert done["status"] == "done"
    assert done["remainingQuantity"] == 0
    assert done["projectAddress"] == "Gartenweg 4"
    assert done["projectCity"] == "12345 Musterstadt"
    assert all(p.get("source") != "complete" for p in done["progress"])

    rest_task = site_tasks.create_task(
        store,
        created_by="owner1",
        project_id="p1",
        project_name="Schmitz Garten",
        title="30 m² Hecke schneiden",
        due_date="2026-09-16",
        assignee_ids=["e1"],
        target_quantity=30,
        unit="m2",
    )
    site_tasks.add_progress(
        store,
        rest_task["id"],
        amount=10,
        actor_name="Max",
        is_owner=False,
        employee_id="e1",
    )
    filled = site_tasks.complete_task(
        store,
        rest_task["id"],
        user_id="worker-max",
        is_owner=False,
        employee_id="e1",
        actor_name="Max",
    )
    assert filled["status"] == "done"
    assert filled["actualQuantity"] == 30
    assert filled["remainingQuantity"] == 0
    assert filled["progress"][-1]["source"] == "complete"
    assert filled["progress"][-1]["amount"] == 20

    print("TASKS-PHASE2-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
