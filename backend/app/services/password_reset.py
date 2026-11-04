"""Passwort vergessen / temporäres Passwort — Tokens getrennt von users.json.

Klartext-Passwoerter werden nie gespeichert. Reset-Token nur als SHA-256.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.password_security import apply_password_hash_to_user

logger = logging.getLogger(__name__)

TOKEN_TTL = timedelta(minutes=45)
MAX_FORGOT_PER_EMAIL_HOUR = 5
MAX_FORGOT_PER_IP_HOUR = 20
TEMP_PASSWORD_LEN = 10
MIN_NEW_PASSWORD_LEN = 8
GENERIC_FORGOT_OK = (
    "Wenn ein Konto zu dieser E-Mail existiert, senden wir einen Link zum Zurücksetzen."
)
_TEMP_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_iso(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(raw or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def generate_temporary_password() -> str:
    return "".join(secrets.choice(_TEMP_ALPHABET) for _ in range(TEMP_PASSWORD_LEN))


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def new_reset_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hash_reset_token(raw)


def validate_new_password(plain: str) -> str | None:
    pw = str(plain or "")
    if len(pw) < MIN_NEW_PASSWORD_LEN:
        return f"Neues Passwort mindestens {MIN_NEW_PASSWORD_LEN} Zeichen."
    if pw.strip() != pw:
        return "Neues Passwort darf nicht mit Leerzeichen beginnen oder enden."
    if pw.lower() in {"123456", "12345678", "password", "passwort", "freiraum"}:
        return "Bitte ein eigenes, nicht erratbares Passwort wählen."
    return None


def apply_new_password(user: dict[str, Any], plain: str, *, require_change: bool = False) -> None:
    apply_password_hash_to_user(user, plain)
    if require_change:
        user["mustChangePassword"] = True
    else:
        user.pop("mustChangePassword", None)


def _prune_doc(doc: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    stamp = now or _now()
    cutoff = stamp - timedelta(hours=24)
    tokens = []
    for item in doc.get("tokens") or []:
        if not isinstance(item, dict):
            continue
        exp = _parse_iso(str(item.get("expiresAt") or ""))
        if exp is None or exp <= stamp:
            continue
        tokens.append(item)
    requests = []
    for item in doc.get("requests") or []:
        if not isinstance(item, dict):
            continue
        at = _parse_iso(str(item.get("at") or ""))
        if at is None or at < cutoff:
            continue
        requests.append(item)
    doc["tokens"] = tokens
    doc["requests"] = requests
    return doc


def load_doc(read_json) -> dict[str, Any]:
    raw = read_json()
    if not isinstance(raw, dict):
        raw = {}
    raw.setdefault("tokens", [])
    raw.setdefault("requests", [])
    return _prune_doc(raw)


def save_doc(write_json, doc: dict[str, Any]) -> None:
    write_json(_prune_doc(doc))


def too_many_forgot_requests(doc: dict[str, Any], *, email: str, ip: str) -> bool:
    hour_ago = _now() - timedelta(hours=1)
    email_l = str(email or "").strip().lower()
    ip_s = str(ip or "").strip()
    n_email = 0
    n_ip = 0
    for item in doc.get("requests") or []:
        if not isinstance(item, dict):
            continue
        at = _parse_iso(str(item.get("at") or ""))
        if at is None or at < hour_ago:
            continue
        if str(item.get("email") or "").strip().lower() == email_l:
            n_email += 1
        if ip_s and str(item.get("ip") or "").strip() == ip_s:
            n_ip += 1
    return n_email >= MAX_FORGOT_PER_EMAIL_HOUR or n_ip >= MAX_FORGOT_PER_IP_HOUR


def record_forgot_request(doc: dict[str, Any], *, email: str, ip: str) -> None:
    reqs = list(doc.get("requests") or [])
    reqs.append(
        {
            "email": str(email or "").strip().lower(),
            "ip": str(ip or "").strip(),
            "at": _iso(_now()),
        }
    )
    doc["requests"] = reqs


def store_reset_token(doc: dict[str, Any], *, user_id: str, token_hash: str) -> None:
    uid = str(user_id or "").strip()
    kept = [
        item
        for item in (doc.get("tokens") or [])
        if isinstance(item, dict) and str(item.get("userId") or "") != uid
    ]
    kept.append(
        {
            "userId": uid,
            "tokenHash": token_hash,
            "expiresAt": _iso(_now() + TOKEN_TTL),
        }
    )
    doc["tokens"] = kept


def invalidate_user_tokens(doc: dict[str, Any], user_id: str) -> None:
    uid = str(user_id or "").strip()
    doc["tokens"] = [
        item
        for item in (doc.get("tokens") or [])
        if isinstance(item, dict) and str(item.get("userId") or "") != uid
    ]


def consume_reset_token(doc: dict[str, Any], token: str) -> str | None:
    digest = hash_reset_token(token)
    stamp = _now()
    remaining = []
    found_uid: str | None = None
    for item in doc.get("tokens") or []:
        if not isinstance(item, dict):
            continue
        stored = str(item.get("tokenHash") or "")
        exp = _parse_iso(str(item.get("expiresAt") or ""))
        if found_uid is None and stored and hmac.compare_digest(stored, digest):
            if exp is not None and exp > stamp:
                found_uid = str(item.get("userId") or "").strip() or None
            continue
        remaining.append(item)
    doc["tokens"] = remaining
    return found_uid


def public_app_base(origin: str = "", referer: str = "", env_url: str = "") -> str:
    env = str(env_url or "").strip().rstrip("/")
    if env:
        return env
    o = str(origin or "").strip().rstrip("/")
    if o.startswith("http://") or o.startswith("https://"):
        return o
    ref = str(referer or "").strip()
    if ref.startswith("http://") or ref.startswith("https://"):
        from urllib.parse import urlsplit

        parts = urlsplit(ref)
        if parts.scheme and parts.netloc:
            return f"{parts.scheme}://{parts.netloc}"
    return "http://localhost:51710"


def build_reset_url(base: str, token: str) -> str:
    root = str(base or "").rstrip("/")
    return f"{root}/passwort-zuruecksetzen?token={token}"


def send_reset_email(*, to_email: str, reset_url: str) -> bool:
    from email.message import EmailMessage

    from app.services.resend_mail import format_from_header, from_email, resend_is_configured, send_email_message

    if not resend_is_configured():
        logger.warning("Passwort-Reset: Resend nicht konfiguriert, Mail nicht gesendet")
        return False
    to_addr = str(to_email or "").strip().lower()
    if "@" not in to_addr:
        return False
    msg = EmailMessage()
    msg["Subject"] = "Passwort zurücksetzen — Freiraum Baustellen-Doku"
    msg["From"] = format_from_header({"companyName": "Freiraum"}, from_email())
    msg["To"] = to_addr
    msg.set_content(
        "Guten Tag,\n\n"
        "für Ihr Freiraum-Konto wurde „Passwort vergessen“ angefordert.\n\n"
        "Öffnen Sie diesen Link (45 Minuten gültig, nur einmal):\n"
        f"{reset_url}\n\n"
        "Wenn Sie das nicht waren, ignorieren Sie diese Mail. "
        "Ihr bisheriges Passwort bleibt dann unverändert.\n"
    )
    ok, err = send_email_message(msg)
    if not ok:
        logger.warning("Passwort-Reset: Versand fehlgeschlagen (%s)", err)
    return ok
