"""Smoke fuer Welle S1: Unterschriften (Backend-only).

Testet Speichern, Liste, Ersetzen, Loeschen und Cleanup beim Bericht-Delete.
"""

from __future__ import annotations

import io
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

_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_signature_smoke_"))
print(f"[smoke] using tmp data dir: {_TMP_DIR}")

import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

main.DATA_DIR = _TMP_DIR
main.REPORTS_FILE = _TMP_DIR / "reports.json"
main.USERS_FILE = _TMP_DIR / "users.json"
main.COMPANY_FILE = _TMP_DIR / "company_profile.json"
main.SIGNATURES_UPLOAD_DIR = _TMP_DIR / "signatures"
main.SIGNATURES_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _make_png_bytes(width: int = 32, height: int = 32) -> bytes:
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


SIG_PNG = _make_png_bytes()


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"sig-smoke-{uuid.uuid4().hex[:8]}@example.com"
    user_id = str(uuid.uuid4())
    main.save_users(
        [
            {
                "id": user_id,
                "companyName": "Smoke GmbH",
                "entrepreneurName": "Tester",
                "email": email,
                "password": "pw",
                "createdAt": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    return {"Authorization": f"Bearer {user_id}"}


def _create_min_report(client: TestClient, headers: dict[str, str]) -> str:
    rid = str(uuid.uuid4())
    main._write_json(
        main.REPORTS_FILE,
        {
            "reports": [
                {
                    "id": rid,
                    "projectName": "Smoke-Baustelle",
                    "date": "2026-05-25",
                    "exportFormat": "PDF",
                    "structured": {"summary": "", "activities": [], "materials": []},
                    "photos": [],
                    "signatures": {"customer": None, "employee": None},
                    "createdAt": "2026-01-01T00:00:00+00:00",
                }
            ]
        },
    )
    return rid


def _upload_sig(client: TestClient, rid: str, role: str, headers: dict[str, str], label: str | None = None):
    data = {}
    if label:
        data["signedByLabel"] = label
    return client.post(
        f"/api/reports/{rid}/signatures/{role}",
        headers=headers,
        data=data,
        files={"file": ("signature.png", io.BytesIO(SIG_PNG), "image/png")},
    )


client = TestClient(main.app)
hdrs = _auth_headers(client)
report_id = _create_min_report(client, hdrs)

# Leere Liste
res = client.get(f"/api/reports/{report_id}/signatures", headers=hdrs)
_expect(res.status_code == 200, f"list empty: {res.status_code}")
body = res.json()
_expect(body.get("count") == 0, "count should be 0")
_expect(body.get("signatures", {}).get("customer") is None, "customer should be null")
_expect(body.get("signatures", {}).get("employee") is None, "employee should be null")

# Kunden-Signatur speichern
res = _upload_sig(client, report_id, "customer", hdrs, label="Herr Meier")
_expect(res.status_code == 200, f"upload customer: {res.status_code} {res.text}")
sig = res.json().get("signature") or {}
sig_id = sig.get("id")
fn = sig.get("filename")
_expect(sig.get("role") == "customer", "role customer")
_expect(sig.get("signedByLabel") == "Herr Meier", "label missing")
_expect(sig.get("url", "").startswith("/uploads/signatures/"), "url missing")
_expect(fn and (main.SIGNATURES_UPLOAD_DIR / fn).is_file(), "signature file not on disk")
_expect(res.json().get("count") == 1, "count after customer upload")

# Bericht enthaelt signatures
rep = client.get(f"/api/reports/{report_id}", headers=hdrs).json()
_expect(isinstance(rep.get("signatures"), dict), "report.signatures missing")
_expect(rep["signatures"].get("customer") is not None, "customer signature in report")

# Mitarbeiter-Signatur
res = _upload_sig(client, report_id, "employee", hdrs)
_expect(res.status_code == 200, f"upload employee: {res.status_code}")
_expect(res.json().get("count") == 2, "count after employee upload")

# Ersetzen der Kunden-Signatur loescht alte Datei
old_fn = fn
res = _upload_sig(client, report_id, "customer", hdrs)
_expect(res.status_code == 200, "replace customer signature")
new_fn = (res.json().get("signature") or {}).get("filename")
_expect(new_fn and new_fn != old_fn, "filename should change on replace")
_expect(not (main.SIGNATURES_UPLOAD_DIR / old_fn).exists(), "old signature file should be removed")
_expect((main.SIGNATURES_UPLOAD_DIR / new_fn).is_file(), "new signature file missing")

# Ungueltige Rolle
res = client.post(
    f"/api/reports/{report_id}/signatures/boss",
    headers=hdrs,
    files={"file": ("signature.png", io.BytesIO(SIG_PNG), "image/png")},
)
_expect(res.status_code == 400, "invalid role should fail")

# Zu kleine/leere Datei
res = client.post(
    f"/api/reports/{report_id}/signatures/customer",
    headers=hdrs,
    files={"file": ("tiny.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
)
_expect(res.status_code == 400, "tiny png should fail")

# Delete employee signature
res = client.delete(f"/api/reports/{report_id}/signatures/employee", headers=hdrs)
_expect(res.status_code == 200 and res.json().get("count") == 1, f"delete employee: {res.text}")

# Cleanup beim Bericht-Delete
files_before = list(main.SIGNATURES_UPLOAD_DIR.glob("sig_*.png"))
_expect(len(files_before) >= 1, "should have signature files before report delete")

res = client.delete(f"/api/reports/{report_id}", headers=hdrs)
_expect(res.status_code == 200, "delete report")
for path in files_before:
    _expect(not path.exists(), f"orphan signature after report delete: {path.name}")

print("REPORT-SIGNATURES-SMOKE (S1): OK")
