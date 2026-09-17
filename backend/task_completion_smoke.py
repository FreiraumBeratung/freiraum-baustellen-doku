"""Smoke: Aufgabenabschluss-Text + PDF — ohne reports.json / ohne KI."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

os.environ["OPENAI_API_KEY"] = ""
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

from smoke_isolation import isolate_smoke_data

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_taskcomp_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from app.services import site_tasks  # noqa: E402
from app.services.task_completion_export import build_task_completion_pdf_bytes  # noqa: E402


def main() -> int:
    store = TenantStore(str(uuid.uuid4()))
    store.write_json(
        "employees.json",
        {"employees": [{"id": "e1", "name": "Max", "active": True}]},
    )
    store.write_json(
        "projects.json",
        {"projects": [{"id": "p1", "name": "Zu Hause", "status": "aktiv", "address": "Kaiserhöhe 10"}]},
    )
    reports_before = store.read_json("reports.json", {"reports": []})

    task = site_tasks.create_task(
        store,
        created_by="owner1",
        project_id="p1",
        project_name="Zu Hause",
        title="Mähen",
        due_date="2026-09-15",
        assignee_ids=["e1"],
        target_quantity=20,
        unit="m2",
    )
    assert not task.get("completionSummary")

    done = site_tasks.complete_task(
        store,
        task["id"],
        user_id="worker-max",
        is_owner=False,
        employee_id="e1",
        actor_name="Max",
    )
    summary = str(done.get("completionSummary") or "")
    assert "Mähen" in summary, summary
    assert "Zu Hause" in summary, summary
    assert "15.09.2026" in summary, summary
    assert "Max" in summary, summary
    assert "20" in summary and "m²" in summary, summary
    assert "pflaster" not in summary.casefold()
    assert "verlegt" not in summary.casefold()

    stored = site_tasks.find_task(store, task["id"])
    assert stored.get("completionSummary") == summary
    reports_after = store.read_json("reports.json", {"reports": []})
    assert reports_after == reports_before

    pdf = build_task_completion_pdf_bytes(
        site_tasks.public_task(stored, store),
        {"companyName": "Testfirma", "officeEmail": "buero@example.com"},
    )
    assert pdf.startswith(b"%PDF")

    reopened = site_tasks.reopen_task(store, task["id"])
    assert reopened["status"] == "open"
    assert not reopened.get("completionSummary")
    raw = site_tasks.find_task(store, task["id"])
    assert "completionSummary" not in raw

    print("task_completion_smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
