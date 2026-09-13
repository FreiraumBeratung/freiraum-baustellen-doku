"""PWA-Push-Versand (Phase 5.3) — fail-soft, nie den Aufgaben-Flow blockieren."""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

from app.services import push_subscriptions
from app.services.tenant_storage import TenantStore

logger = logging.getLogger(__name__)


def vapid_private_key() -> str:
    return str(os.environ.get("FREIRAUM_VAPID_PRIVATE_KEY") or "").strip()


def vapid_subject() -> str:
    raw = str(os.environ.get("FREIRAUM_VAPID_SUBJECT") or "").strip()
    if raw.startswith("mailto:") or raw.startswith("https://"):
        return raw
    return "mailto:push@localhost"


def sending_ready() -> bool:
    return bool(push_subscriptions.vapid_public_key() and vapid_private_key())


def format_date_de(iso: str) -> str:
    s = str(iso or "").strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}.{s[5:7]}.{s[0:4]}"
    return s or ""


def payload_new_tasks(tasks: list[dict[str, Any]]) -> dict[str, str]:
    first = tasks[0] if tasks else {}
    site = str(first.get("projectName") or "Baustelle").strip() or "Baustelle"
    when = format_date_de(str(first.get("dueDate") or ""))
    if len(tasks) == 1:
        title_txt = str(first.get("title") or "Neue Aufgabe").strip() or "Neue Aufgabe"
        body = " · ".join(p for p in (title_txt, site, when) if p)
        return {"title": "Neue Aufgabe", "body": body[:180], "url": "/aufgaben"}
    body = " · ".join(p for p in (f"{len(tasks)} Aufgaben", site, when) if p)
    return {"title": "Neue Aufgaben", "body": body[:180], "url": "/aufgaben"}


def payload_task_done(task: dict[str, Any]) -> dict[str, str]:
    title_txt = str(task.get("title") or "Aufgabe").strip() or "Aufgabe"
    site = str(task.get("projectName") or "Baustelle").strip() or "Baustelle"
    body = " · ".join(p for p in (title_txt, site) if p)
    return {"title": "Aufgabe erledigt", "body": body[:180], "url": "/aufgaben"}


def _push_one(subscription: dict[str, Any], payload: dict[str, str]) -> bool:
    try:
        from pywebpush import WebPushException, webpush
    except Exception:
        logger.info("pywebpush nicht installiert — Push-Versand übersprungen.")
        return True
    keys = subscription.get("keys") if isinstance(subscription.get("keys"), dict) else {}
    try:
        webpush(
            subscription_info={
                "endpoint": str(subscription.get("endpoint") or ""),
                "keys": {
                    "p256dh": str(keys.get("p256dh") or ""),
                    "auth": str(keys.get("auth") or ""),
                },
            },
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=vapid_private_key(),
            vapid_claims={"sub": vapid_subject()},
        )
        return True
    except Exception as exc:
        gone = False
        try:
            from pywebpush import WebPushException

            if isinstance(exc, WebPushException) and getattr(exc, "response", None) is not None:
                gone = int(getattr(exc.response, "status_code", 0) or 0) in {404, 410}
        except Exception:
            gone = False
        if gone:
            return False
        logger.info("Push fehlgeschlagen: %s", exc)
        return True


def _deliver(store: TenantStore, user_ids: list[str], payload: dict[str, str]) -> None:
    if not sending_ready():
        return
    rows = push_subscriptions.subscriptions_for_users(store, user_ids)
    for row in rows:
        keep = True
        try:
            keep = _push_one(row, payload)
        except Exception:
            logger.exception("Push-Versand übersprungen")
            keep = True
        if not keep:
            try:
                push_subscriptions.drop_endpoint(store, str(row.get("endpoint") or ""))
            except Exception:
                pass


def notify_users_best_effort(
    store: TenantStore,
    user_ids: list[str],
    payload: dict[str, str],
) -> None:
    ids = [str(x).strip() for x in user_ids if str(x).strip()]
    if not ids or not payload.get("title") or not sending_ready():
        return

    def _run() -> None:
        try:
            _deliver(store, ids, payload)
        except Exception:
            logger.exception("Push-Thread übersprungen")

    threading.Thread(target=_run, daemon=True).start()
