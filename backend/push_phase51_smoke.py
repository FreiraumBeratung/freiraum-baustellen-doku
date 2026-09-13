"""Smoke Phase-5.1 Push-Abos — nur Speichern, kein Versand."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import HTTPException

from smoke_isolation import isolate_smoke_data

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_push_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from app.services import push_subscriptions as push  # noqa: E402


def main() -> int:
    store = TenantStore(str(uuid.uuid4()))
    cfg = push.push_public_config()
    assert "enabled" in cfg
    assert "publicKey" in cfg

    saved = push.upsert_subscription(
        store,
        user_id="u1",
        account_role="worker",
        employee_id="e1",
        endpoint="https://push.example.test/sub/1",
        p256dh="p256-demo-key",
        auth="auth-demo-key",
        user_agent="smoke",
    )
    assert saved["enabled"] is True
    assert push.user_has_subscription(store, "u1") is True
    assert push.user_has_subscription(store, "u2") is False

    try:
        push.upsert_subscription(
            store,
            user_id="u2",
            account_role="owner",
            employee_id=None,
            endpoint="https://push.example.test/sub/1",
            p256dh="other",
            auth="other",
        )
        raise AssertionError("fremder User darf Endpoint nicht übernehmen")
    except HTTPException as exc:
        assert exc.status_code == 403

    try:
        push.upsert_subscription(
            store,
            user_id="u1",
            account_role="worker",
            employee_id="e1",
            endpoint="http://evil.example/x",
            p256dh="p",
            auth="a",
        )
        raise AssertionError("http ohne localhost muss scheitern")
    except HTTPException as exc:
        assert exc.status_code == 400

    push.disable_subscription(store, user_id="u1", endpoint="https://push.example.test/sub/1")
    assert push.user_has_subscription(store, "u1") is False

    print("PUSH-PHASE51-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
