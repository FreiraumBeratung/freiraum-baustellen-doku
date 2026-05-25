"""Verschlüsseltes Storage für SMTP-Credentials pro E-Mail-Adresse.

Datenfluss:
- Beim ersten erfolgreichen Login einer Firmen-Mail wird die SMTP-Konfiguration
  (Host/Port/TLS/SSL/Quelle) + das Passwort verschlüsselt in
  ``backend/data/mail_configs.json`` abgelegt.
- Der lokale Verschlüsselungsschlüssel liegt in ``backend/data/.mail_key`` und
  wird vom Backend selbst angelegt (gitignored).
- Beim Versand liest ``office_mail.py`` die Konfiguration für die eingeloggte
  E-Mail-Adresse aus dem Store.

Keine Environment-Variablen, kein Klartext-Passwort im Repo.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_KEY_FILE = _DATA_DIR / ".mail_key"
_STORE_FILE = _DATA_DIR / "mail_configs.json"

_lock = threading.Lock()


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_or_create_key() -> bytes:
    _ensure_data_dir()
    if _KEY_FILE.exists():
        try:
            data = _KEY_FILE.read_bytes().strip()
            if data:
                return data
        except OSError:
            logger.exception("Konnte Mail-Schlüssel nicht lesen, wird neu erzeugt")
    key = Fernet.generate_key()
    try:
        _KEY_FILE.write_bytes(key)
        try:
            os.chmod(_KEY_FILE, 0o600)
        except (OSError, NotImplementedError):
            # Windows / Sandboxes: Fallback ohne chmod ist akzeptabel.
            pass
    except OSError:
        logger.exception("Konnte Mail-Schlüssel nicht schreiben")
        raise
    return key


def _fernet() -> Fernet:
    return Fernet(_load_or_create_key())


def _load_all() -> dict[str, dict[str, Any]]:
    if not _STORE_FILE.exists():
        return {}
    try:
        raw = _STORE_FILE.read_text(encoding="utf-8")
        if not raw.strip():
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        logger.exception("Mail-Config-Datei konnte nicht gelesen werden")
        return {}


def _save_all(store: dict[str, dict[str, Any]]) -> None:
    _ensure_data_dir()
    tmp = _STORE_FILE.with_suffix(".tmp")
    payload = json.dumps(store, ensure_ascii=False, indent=2)
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, _STORE_FILE)
    try:
        os.chmod(_STORE_FILE, 0o600)
    except (OSError, NotImplementedError):
        pass


def _normalize_key(email_address: str) -> str:
    return str(email_address or "").strip().lower()


def save_mail_config(
    email_address: str,
    password: str,
    *,
    host: str,
    port: int,
    use_tls: bool,
    use_ssl: bool,
    source: str = "preset",
) -> None:
    """Speichert SMTP-Konfiguration + verschlüsseltes Passwort."""
    key_email = _normalize_key(email_address)
    if not key_email:
        raise ValueError("E-Mail-Adresse fehlt")
    if not password:
        raise ValueError("Passwort fehlt")
    fernet = _fernet()
    enc_pw = fernet.encrypt(password.encode("utf-8")).decode("ascii")
    with _lock:
        store = _load_all()
        store[key_email] = {
            "email": key_email,
            "host": str(host),
            "port": int(port),
            "use_tls": bool(use_tls),
            "use_ssl": bool(use_ssl),
            "source": str(source),
            "password_encrypted": enc_pw,
        }
        _save_all(store)


def get_mail_config(email_address: str) -> dict[str, Any] | None:
    """Liest SMTP-Konfiguration für die angegebene E-Mail.

    Liefert ein Dict mit ``host/port/use_tls/use_ssl/source/password`` (Klartext
    nach Entschlüsselung) oder None, wenn kein Eintrag oder Entschlüsselung
    fehlschlägt.
    """
    key_email = _normalize_key(email_address)
    if not key_email:
        return None
    with _lock:
        store = _load_all()
        entry = store.get(key_email)
    if not entry:
        return None
    enc_pw = entry.get("password_encrypted")
    if not enc_pw:
        return None
    try:
        password = _fernet().decrypt(enc_pw.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        logger.warning("Mail-Konfiguration für %s konnte nicht entschlüsselt werden", key_email)
        return None
    return {
        "email": entry.get("email", key_email),
        "host": entry.get("host"),
        "port": int(entry.get("port") or 0),
        "use_tls": bool(entry.get("use_tls", True)),
        "use_ssl": bool(entry.get("use_ssl", False)),
        "source": entry.get("source", "preset"),
        "password": password,
    }


def delete_mail_config(email_address: str) -> bool:
    """Löscht den Eintrag, sofern vorhanden. True wenn etwas entfernt wurde."""
    key_email = _normalize_key(email_address)
    if not key_email:
        return False
    with _lock:
        store = _load_all()
        if key_email not in store:
            return False
        store.pop(key_email, None)
        _save_all(store)
    return True


def has_mail_config(email_address: str) -> bool:
    cfg = get_mail_config(email_address)
    return cfg is not None
