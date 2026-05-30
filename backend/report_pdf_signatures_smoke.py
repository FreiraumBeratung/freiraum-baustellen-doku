"""Smoke fuer Welle S4: Unterschriften in PDF-Einbettung (Backend-only)."""

from __future__ import annotations

import os
import struct
import sys
import tempfile
import uuid
import zlib
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_pdf_sig_smoke_"))
print(f"[smoke] using tmp data dir: {_TMP_DIR}")

import report_export  # noqa: E402
from report_export import build_pdf_bytes  # noqa: E402

report_export.SIGNATURES_DIR = _TMP_DIR / "signatures"
report_export.SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _make_png_bytes(width: int = 120, height: int = 48) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        crc = zlib.crc32(body) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + body + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b""
    for _y in range(height):
        raw += b"\x00" + b"\xff\xff\xff" * width
    compressed = zlib.compress(raw, 9)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


BASE_REPORT = {
    "id": "pdf-smoke",
    "companyName": "Acme Bau GmbH",
    "projectName": "Testbaustelle",
    "customerName": "Musterkunde",
    "date": "2026-05-25",
    "employees": ["Anna"],
    "startTime": "07:00",
    "endTime": "16:00",
    "exportFormat": "PDF",
    "structured": {
        "summary": "Kurztest",
        "activities": ["Montage"],
        "materials": ["Schrauben"],
        "problems": [],
        "openItems": [],
        "customerTalk": "Alles ok",
    },
    "photos": [],
    "signatures": {"customer": None, "employee": None},
}

PROFILE = {"companyName": "Acme Bau GmbH", "officeEmail": "office@example.com"}


def _write_sig(name: str) -> str:
    path = report_export.SIGNATURES_DIR / name
    path.write_bytes(_make_png_bytes())
    return name


# -- 1. PDF ohne Signaturen ---------------------------------------------------
pdf_plain = build_pdf_bytes(BASE_REPORT, PROFILE)
_expect(pdf_plain.startswith(b"%PDF"), "pdf magic missing without signatures")
plain_len = len(pdf_plain)

# -- 2. PDF mit beiden Signaturen ---------------------------------------------
cust_fn = _write_sig(f"sig_customer_{uuid.uuid4().hex}.png")
emp_fn = _write_sig(f"sig_employee_{uuid.uuid4().hex}.png")
report_with_sigs = {
    **BASE_REPORT,
    "signatures": {
        "customer": {
            "id": str(uuid.uuid4()),
            "role": "customer",
            "filename": cust_fn,
            "signedAt": "2026-05-25T14:30:00+00:00",
            "signedByLabel": "Herr Meier",
        },
        "employee": {
            "id": str(uuid.uuid4()),
            "role": "employee",
            "filename": emp_fn,
            "signedAt": "2026-05-25T14:31:00+00:00",
        },
    },
}

pdf_signed = build_pdf_bytes(report_with_sigs, PROFILE)
_expect(pdf_signed.startswith(b"%PDF"), "pdf magic missing with signatures")
_expect(len(pdf_signed) > plain_len, "signed pdf should be larger than plain pdf")

# -- 3. Nur Kunde — kein Fehler -----------------------------------------------
report_customer_only = {
    **BASE_REPORT,
    "signatures": {
        "customer": report_with_sigs["signatures"]["customer"],
        "employee": None,
    },
}
pdf_customer = build_pdf_bytes(report_customer_only, PROFILE)
_expect(pdf_customer.startswith(b"%PDF"), "pdf with customer signature only failed")

# -- 4. Fehlende Datei wird still uebersprungen -------------------------------
report_missing_file = {
    **BASE_REPORT,
    "signatures": {
        "customer": {
            "id": str(uuid.uuid4()),
            "role": "customer",
            "filename": "missing-signature.png",
            "signedAt": "2026-05-25T14:30:00+00:00",
        },
        "employee": None,
    },
}
pdf_missing = build_pdf_bytes(report_missing_file, PROFILE)
_expect(pdf_missing.startswith(b"%PDF"), "pdf with missing signature file should still build")
_expect(abs(len(pdf_missing) - plain_len) < 512, "missing signature should not add block")

print("REPORT-PDF-SIGNATURES-SMOKE (S4): OK")
