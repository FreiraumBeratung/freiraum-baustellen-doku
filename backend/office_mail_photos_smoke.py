"""Smoke fuer Welle F3: Baustellenfotos als Mail-Anhaenge (Backend-only).

Mockt SMTP; prueft Anzahl der Anhaenge, Mail-Text und Erfolgsmeldung.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_office_mail_photos_"))
print(f"[smoke] using tmp data dir: {_TMP_DIR}")

from office_mail import send_report_to_office  # noqa: E402

MINI_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

MAIL_CONFIG = {
    "host": "smtp.example.com",
    "port": 587,
    "use_tls": True,
    "use_ssl": False,
    "email": "sender@example.com",
    "password": "secret",
}

PROFILE = {"companyName": "Acme Bau", "contactPerson": "Max Mustermann"}

BASE_REPORT = {
    "id": "smoke-report",
    "projectName": "Testbaustelle",
    "date": "2026-05-25",
    "exportFormat": "PDF",
    "employees": ["Anna"],
    "startTime": "07:00",
    "endTime": "16:00",
    "structured": {
        "summary": "Kurztest",
        "activities": [],
        "materials": [],
        "problems": [],
        "openItems": [],
        "customerTalk": "",
    },
    "rawText": "Test",
}


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _attachment_count(msg) -> int:  # noqa: ANN001
    return sum(1 for _ in msg.iter_attachments())


def _plain_body(msg) -> str:  # noqa: ANN001
    part = msg.get_body(preferencelist=("plain",))
    return part.get_content() if part is not None else ""


class _FakeSMTP:
    last_message = None

    def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
        _ = (args, kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args):  # noqa: ANN002
        return False

    def ehlo(self) -> None:
        return None

    def starttls(self, context=None) -> None:  # noqa: ANN001
        _ = context

    def login(self, user: str, password: str) -> None:
        _ = (user, password)

    def send_message(self, msg) -> None:  # noqa: ANN001
        _FakeSMTP.last_message = msg


photos_dir = _TMP_DIR / "photos"
photos_dir.mkdir(parents=True, exist_ok=True)

# -- 1. Ohne Fotos: nur Berichtsanhang --------------------------------------
with patch("office_mail.smtplib.SMTP", _FakeSMTP):
    ok, simulated, message = send_report_to_office(
        {**BASE_REPORT, "photos": []},
        PROFILE,
        "office@example.com",
        mail_config=MAIL_CONFIG,
        photos_upload_dir=photos_dir,
    )

_expect(ok is True, "send without photos should succeed")
_expect(simulated is False, "simulated should be false")
_expect("Foto" not in message, f"message should not mention photos: {message!r}")
msg = _FakeSMTP.last_message
_expect(msg is not None, "SMTP message missing")
_expect(_attachment_count(msg) == 1, "expected 1 attachment without photos")
body = _plain_body(msg)
_expect("Baustellenfoto" not in body, "body should not mention photos")

# -- 2. Mit Foto: Bericht + Bild ---------------------------------------------
photo_name = f"photo_{uuid.uuid4().hex}.png"
(photos_dir / photo_name).write_bytes(MINI_PNG)
report_with_photo = {
    **BASE_REPORT,
    "photos": [
        {
            "id": str(uuid.uuid4()),
            "filename": photo_name,
            "originalFilename": "baustelle_vorne.png",
            "contentType": "image/png",
            "sizeBytes": len(MINI_PNG),
        }
    ],
}

with patch("office_mail.smtplib.SMTP", _FakeSMTP):
    ok, simulated, message = send_report_to_office(
        report_with_photo,
        PROFILE,
        "office@example.com",
        mail_config=MAIL_CONFIG,
        photos_upload_dir=photos_dir,
    )

_expect(ok is True, "send with photo should succeed")
_expect("1 Foto" in message, f"success message should mention photo count: {message!r}")
msg = _FakeSMTP.last_message
_expect(_attachment_count(msg) == 2, "expected 2 attachments with one photo")
body = _plain_body(msg)
_expect("Baustellenfoto: 1 Bild(er) im Anhang." in body, "body should mention attached photo")

photo_names = []
for part in msg.iter_attachments():
    fn = part.get_filename()
    if fn and fn.endswith(".png"):
        photo_names.append(fn)
_expect(photo_names == ["baustelle_vorne.png"], f"unexpected photo filename: {photo_names!r}")

# -- 3. Fehlende Datei wird uebersprungen, Mail geht trotzdem raus -----------
report_missing_file = {
    **BASE_REPORT,
    "photos": [
        {
            "id": str(uuid.uuid4()),
            "filename": "does-not-exist.jpg",
            "originalFilename": "fehlt.jpg",
            "contentType": "image/jpeg",
            "sizeBytes": 1,
        }
    ],
}

with patch("office_mail.smtplib.SMTP", _FakeSMTP):
    ok, _, message = send_report_to_office(
        report_missing_file,
        PROFILE,
        "office@example.com",
        mail_config=MAIL_CONFIG,
        photos_upload_dir=photos_dir,
    )

_expect(ok is True, "send should succeed even if photo file missing")
_expect("Foto" not in message, "message should not claim photos when none attached")
_expect(_attachment_count(_FakeSMTP.last_message) == 1, "only report attachment expected")

print("OFFICE-MAIL-PHOTOS-SMOKE: OK")
