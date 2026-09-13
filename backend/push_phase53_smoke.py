"""Smoke Phase-5.3 Push-Versand — Texte, Empfänger, kein echter Versand."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

from smoke_isolation import isolate_smoke_data

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_push53_")))

from app.services import push_send  # noqa: E402
from app.services import push_subscriptions as push  # noqa: E402
from app.services.account_roles import find_tenant_owner, find_worker_for_employee  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402


def main() -> int:
    os.environ.pop("FREIRAUM_VAPID_PUBLIC_KEY", None)
    os.environ.pop("FREIRAUM_VAPID_PRIVATE_KEY", None)
    assert push_send.sending_ready() is False
    empty = push.push_public_config()
    assert empty == {"enabled": False, "publicKey": None}

    os.environ["FREIRAUM_VAPID_PUBLIC_KEY"] = "pub-demo-only"
    os.environ["FREIRAUM_VAPID_PRIVATE_KEY"] = "priv-demo-secret"
    cfg = push.push_public_config()
    assert cfg["enabled"] is True
    assert cfg["publicKey"] == "pub-demo-only"
    assert "priv-demo-secret" not in str(cfg)
    assert "privateKey" not in cfg
    os.environ.pop("FREIRAUM_VAPID_PUBLIC_KEY", None)
    os.environ.pop("FREIRAUM_VAPID_PRIVATE_KEY", None)
    assert push_send.sending_ready() is False

    one = push_send.payload_new_tasks(
        [
            {
                "title": "Rasen mähen",
                "projectName": "Denis Außenanlage",
                "dueDate": "2026-09-13",
            }
        ]
    )
    assert one["title"] == "Neue Aufgabe"
    assert one["body"] == "Rasen mähen · Denis Außenanlage · 13.09.2026"
    assert one["url"] == "/aufgaben"

    many = push_send.payload_new_tasks(
        [
            {"title": "A", "projectName": "Hof", "dueDate": "2026-09-13"},
            {"title": "B", "projectName": "Hof", "dueDate": "2026-09-13"},
            {"title": "C", "projectName": "Hof", "dueDate": "2026-09-13"},
        ]
    )
    assert many["title"] == "Neue Aufgaben"
    assert many["body"] == "3 Aufgaben · Hof · 13.09.2026"

    done = push_send.payload_task_done(
        {"title": "Rasen mähen", "projectName": "Denis Außenanlage"}
    )
    assert done["title"] == "Aufgabe erledigt"
    assert done["body"] == "Rasen mähen · Denis Außenanlage"
    assert done["url"] == "/aufgaben"

    users = [
        {"id": "t1", "accountRole": "owner", "tenantId": "t1"},
        {"id": "w1", "accountRole": "worker", "tenantId": "t1", "employeeId": "e1"},
        {"id": "w2", "accountRole": "worker", "tenantId": "t1", "employeeId": "e2"},
    ]
    assert find_worker_for_employee(users, "t1", "e1")["id"] == "w1"
    assert find_tenant_owner(users, "t1")["id"] == "t1"

    store = TenantStore(str(uuid.uuid4()))
    push.upsert_subscription(
        store,
        user_id="w1",
        account_role="worker",
        employee_id="e1",
        endpoint="https://push.example.test/sub/w1",
        p256dh="p256-demo-key",
        auth="auth-demo-key",
    )
    push.upsert_subscription(
        store,
        user_id="t1",
        account_role="owner",
        employee_id=None,
        endpoint="https://push.example.test/sub/owner",
        p256dh="p256-owner",
        auth="auth-owner",
    )
    rows = push.subscriptions_for_users(store, ["w1"])
    assert len(rows) == 1
    assert rows[0]["userId"] == "w1"
    assert push.subscriptions_for_users(store, ["missing"]) == []

    push.drop_endpoint(store, "https://push.example.test/sub/w1")
    assert push.subscriptions_for_users(store, ["w1"]) == []
    assert len(push.subscriptions_for_users(store, ["t1"])) == 1

    push_send.notify_users_best_effort(store, ["w1"], one)

    print("PUSH-PHASE53-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
