"""Smoke: Fotos in Tagesbericht-PDF nur bei Profil-Schalter (Default aus)."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("OPENAI_API_KEY", "")

from office_mail import send_report_to_office
from report_export import build_pdf_bytes

MINI_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

REPORT = {
    "id": "pdf-photo-smoke",
    "projectName": "Testbaustelle",
    "customerName": "Kunde",
    "date": "2026-09-27",
    "employees": ["Anna"],
    "startTime": "07:00",
    "endTime": "16:00",
    "exportFormat": "PDF",
    "structured": {
        "summary": "Kurztest",
        "activities": ["Arbeit"],
        "materials": [],
        "problems": [],
        "openItems": [],
        "customerTalk": "",
    },
    "rawText": "Test",
}

MAIL_CONFIG = {
    "host": "smtp.example.com",
    "port": 587,
    "use_tls": True,
    "use_ssl": False,
    "email": "sender@example.com",
    "password": "secret",
}


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


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _attachment_count(msg) -> int:  # noqa: ANN001
    return sum(1 for _ in msg.iter_attachments())


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="freiraum_pdf_photos_"))
    photos_dir = tmp / "photos"
    photos_dir.mkdir(parents=True)
    photo_name = f"photo_{uuid.uuid4().hex}.png"
    (photos_dir / photo_name).write_bytes(MINI_PNG)
    report = {
        **REPORT,
        "photos": [
            {
                "id": str(uuid.uuid4()),
                "filename": photo_name,
                "originalFilename": "baustelle.png",
                "contentType": "image/png",
            }
        ],
    }

    def resolve_photo(fn: str) -> Path | None:
        path = photos_dir / fn
        return path if path.is_file() else None

    pdf_off = build_pdf_bytes(report, {}, resolve_photo=resolve_photo)
    pdf_off_flag = build_pdf_bytes(
        report, {"includePhotosInPdf": False}, resolve_photo=resolve_photo
    )
    pdf_on = build_pdf_bytes(report, {"includePhotosInPdf": True}, resolve_photo=resolve_photo)
    pdf_on_no_resolver = build_pdf_bytes(report, {"includePhotosInPdf": True})
    pdf_missing = build_pdf_bytes(
        {
            **REPORT,
            "photos": [{"filename": "fehlt.png"}],
        },
        {"includePhotosInPdf": True},
        resolve_photo=lambda _fn: None,
    )

    _expect(isinstance(pdf_off, (bytes, bytearray)) and len(pdf_off) > 800, "PDF aus zu klein")
    _expect(len(pdf_off_flag) > 800, "PDF Schalter-aus zu klein")
    _expect(len(pdf_on) > len(pdf_off), "PDF mit Fotos sollte groesser sein")
    _expect(abs(len(pdf_on_no_resolver) - len(pdf_off)) < 200, "ohne Resolver keine Fotos")
    _expect(isinstance(pdf_missing, (bytes, bytearray)) and len(pdf_missing) > 800, "fehlendes Foto darf PDF nicht killen")

    with patch("office_mail.smtplib.SMTP", _FakeSMTP):
        ok, _, message = send_report_to_office(
            report,
            {"companyName": "Acme", "includePhotosInPdf": True},
            "office@example.com",
            mail_config=MAIL_CONFIG,
            photos_upload_dir=photos_dir,
            resolve_photo=resolve_photo,
        )
    _expect(ok is True, "Mail mit Schalter an muss gehen")
    _expect("Foto" not in message, f"keine Extra-Foto-Meldung: {message!r}")
    _expect(_attachment_count(_FakeSMTP.last_message) == 1, "nur PDF-Anhang, keine Extra-Fotos")

    with patch("office_mail.smtplib.SMTP", _FakeSMTP):
        ok, _, message = send_report_to_office(
            report,
            {"companyName": "Acme"},
            "office@example.com",
            mail_config=MAIL_CONFIG,
            photos_upload_dir=photos_dir,
        )
    _expect(ok is True, "Mail Default muss gehen")
    _expect("1 Foto" in message, f"Default weiter Extra-Anhang: {message!r}")
    _expect(_attachment_count(_FakeSMTP.last_message) == 2, "Default: PDF + Foto")

    print("REPORT-PDF-PHOTOS-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
