"""Smoke: Hinweis-Fotos getrennt von Nachweis-Fotos an der Aufgabe."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from smoke_isolation import isolate_smoke_data

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_taskhint_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from app.services import site_tasks  # noqa: E402


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def main() -> int:
    store = TenantStore(str(uuid.uuid4()))
    store.write_json(
        "employees.json",
        {"employees": [{"id": "e1", "name": "Max", "active": True}]},
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
        title="Rasen mähen an der Hecke",
        due_date="2026-09-22",
        assignee_ids=["e1"],
    )
    _expect(task["photoCount"] == 0, "work photos start empty")
    _expect(task.get("hintPhotoCount") == 0, "hint photos start empty")

    site_tasks.save_task_photos(
        store,
        task["id"],
        [
            {
                "id": "work1",
                "filename": "task_work_demo.jpg",
                "originalFilename": "nachweis.jpg",
                "contentType": "image/jpeg",
                "sizeBytes": 12,
            }
        ],
    )
    site_tasks.save_task_hint_photos(
        store,
        task["id"],
        [
            {
                "id": "hint1",
                "filename": "taskhint_demo.jpg",
                "originalFilename": "lage.jpg",
                "contentType": "image/jpeg",
                "sizeBytes": 18,
            }
        ],
    )

    raw = site_tasks.find_task(store, task["id"])
    viewed = site_tasks.public_task(raw)
    _expect(viewed["photoCount"] == 1, "work photoCount stays 1")
    _expect(viewed["hintPhotoCount"] == 1, "hintPhotoCount is 1")
    work = site_tasks.task_photos_list(raw)
    hints = site_tasks.task_hint_photos_list(raw)
    _expect(len(work) == 1 and work[0]["id"] == "work1", "work list isolated")
    _expect(len(hints) == 1 and hints[0]["id"] == "hint1", "hint list isolated")
    _expect(all(p.get("id") != "hint1" for p in work), "hint not mixed into photos")
    _expect(all(p.get("id") != "work1" for p in hints), "work not mixed into hintPhotos")

    photos, _sigs = site_tasks.task_media_filenames(raw)
    _expect("task_work_demo.jpg" in photos, "delete cleanup includes work photo")
    _expect("taskhint_demo.jpg" in photos, "delete cleanup includes hint photo")

    worker = site_tasks.list_tasks_for_user(store, is_owner=False, employee_id="e1", status="open")
    _expect(worker[0]["hintPhotoCount"] == 1, "assignee sees hintPhotoCount")
    _expect(worker[0]["photoCount"] == 1, "assignee still sees work photoCount")

    print("TASKS-HINT-PHOTOS-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
