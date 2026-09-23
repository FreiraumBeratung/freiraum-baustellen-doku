"""Resend-Versand fuer Kunden ohne eigenes SMTP.

Nur Backend. Der API-Key kommt ausschliesslich aus der Umgebung und
wird nie im Mail-Store, nie im Frontend und nie in Logs ausgegeben.

Bestandskunden mit gespeicherter SMTP-Config nutzen diesen Pfad nicht.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import urllib.error
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any

logger = logging.getLogger(__name__)

ALLOWED_FROM_DOMAIN = "berichte.freiraum-unternehmensberatung.de"
DEFAULT_FROM_EMAIL = f"freiraum@{ALLOWED_FROM_DOMAIN}"
RESEND_API_URL = "https://api.resend.com/emails"

MSG_NOT_CONFIGURED = "Freiraum-Versand ist nicht eingerichtet."
MSG_REJECTED = "Der Versanddienst hat die Mail abgelehnt. Bitte spaeter erneut versuchen."
MSG_NETWORK = "Netzwerkfehler beim Versand. Bitte erneut versuchen."


def _api_key() -> str:
    raw = str(os.environ.get("RESEND_API_KEY") or "").strip()
    # Nur echte Resend-Keys (re_…). Verhindert versehentliches Einsetzen anderer Keys.
    if raw.startswith("re_") and len(raw) >= 20:
        return raw
    return ""


def from_email() -> str:
    raw = str(os.environ.get("RESEND_FROM_EMAIL") or "").strip().lower()
    if not raw:
        return DEFAULT_FROM_EMAIL
    if "@" not in raw:
        return DEFAULT_FROM_EMAIL
    local, _, domain = raw.partition("@")
    if not local or domain != ALLOWED_FROM_DOMAIN:
        logger.warning("RESEND_FROM_EMAIL ignoriert (Domain nicht erlaubt)")
        return DEFAULT_FROM_EMAIL
    return raw


def resend_is_configured() -> bool:
    return bool(_api_key())


def resend_transport_config() -> dict[str, Any] | None:
    """Schlanke Versand-Config ohne Key. None, wenn Resend nicht bereit ist."""
    if not resend_is_configured():
        return None
    return {
        "transport": "resend",
        "email": from_email(),
    }


def _safe_display_name(raw: str) -> str:
    cleaned = re.sub(r"[\r\n<>\"]+", " ", str(raw or "")).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:80]


def format_from_header(profile: dict[str, Any] | None, sender_email: str) -> str:
    """Anzeigename aus Firmenprofil, technische Adresse bleibt die Freiraum-Domain."""
    prof = profile if isinstance(profile, dict) else {}
    company = _safe_display_name(str(prof.get("companyName") or ""))
    if not company:
        company = _safe_display_name(str(prof.get("contactPerson") or ""))
    display = f"{company} via Freiraum" if company else "Freiraum"
    return formataddr((display, sender_email))


def _payload_from_message(msg: EmailMessage) -> dict[str, Any]:
    body_part = msg.get_body(preferencelist=("plain",))
    text = body_part.get_content() if body_part is not None else ""
    payload: dict[str, Any] = {
        "from": str(msg.get("From") or ""),
        "to": [str(msg.get("To") or "")],
        "subject": str(msg.get("Subject") or ""),
        "text": text,
    }
    reply = str(msg.get("Reply-To") or "").strip()
    if reply:
        payload["reply_to"] = reply
    attachments: list[dict[str, str]] = []
    for part in msg.iter_attachments():
        raw = part.get_payload(decode=True)
        if not raw:
            continue
        name = str(part.get_filename() or "anhang").strip() or "anhang"
        attachments.append(
            {
                "filename": name,
                "content": base64.b64encode(raw).decode("ascii"),
            }
        )
    if attachments:
        payload["attachments"] = attachments
    return payload


def send_email_message(msg: EmailMessage) -> tuple[bool, str]:
    """Sendet eine bereits gebaute E-Mail ueber die Resend-API."""
    key = _api_key()
    if not key:
        return False, MSG_NOT_CONFIGURED

    payload = _payload_from_message(msg)
    if not payload.get("from") or not payload["to"][0] or not payload.get("subject"):
        return False, MSG_NOT_CONFIGURED

    raw = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        RESEND_API_URL,
        data=raw,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "freiraum-baustellen-doku",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if 200 <= int(resp.status) < 300:
                return True, ""
            logger.warning("Resend unerwarteter Status %s", resp.status)
            return False, MSG_REJECTED
    except urllib.error.HTTPError as exc:
        logger.warning("Resend HTTP-Fehler %s", exc.code)
        return False, MSG_REJECTED
    except (urllib.error.URLError, TimeoutError, OSError):
        logger.exception("Resend Netzwerkfehler")
        return False, MSG_NETWORK
    except Exception:
        logger.exception("Resend unerwarteter Fehler")
        return False, MSG_REJECTED
