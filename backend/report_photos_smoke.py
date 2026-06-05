"""Smoke fuer Welle F1: Baustellenfotos (Backend-only).

Testet Upload, Liste, Loeschen, 10er-Limit und Datei-Cleanup beim Bericht-Delete.
Laeuft in-process mit isoliertem Temp-Verzeichnis; beruehrt keine echten reports.json.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "")

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

_TMP_DIR = Path(tempfile.mkdtemp(prefix="freiraum_photo_smoke_"))
print(f"[smoke] using tmp data dir: {_TMP_DIR}")

import main  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(_TMP_DIR)

# 1x1 PNG
MINI_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _auth_headers(client: TestClient) -> tuple[dict[str, str], str]:
    email = f"photo-smoke-{uuid.uuid4().hex[:8]}@example.com"
    user_id = str(uuid.uuid4())
    main.save_users(
        [
            {
                "id": user_id,
                "tenantId": user_id,
                "companyName": "Smoke GmbH",
                "entrepreneurName": "Tester",
                "email": email,
                "password": "pw",
                "createdAt": "2026-01-01T00:00:00+00:00",
            }
        ]
    )
    return {"Authorization": f"Bearer {user_id}"}, user_id


def _photos_dir(user_id: str) -> Path:
    return _TMP_DIR / "uploads" / "tenants" / user_id / "photos"


def _create_min_report(store: TenantStore) -> str:
    rid = str(uuid.uuid4())
    store.write_json(
        "reports.json",
        {
            "reports": [
                {
                    "id": rid,
                    "projectName": "Smoke-Baustelle",
                    "date": "2026-05-25",
                    "exportFormat": "PDF",
                    "structured": {"summary": "", "activities": [], "materials": []},
                    "photos": [],
                    "createdAt": "2026-01-01T00:00:00+00:00",
                }
            ]
        },
    )
    return rid


def _upload_png(client: TestClient, rid: str, headers: dict[str, str], name: str = "test.png"):
    return client.post(
        f"/api/reports/{rid}/photos",
        headers=headers,
        files={"file": (name, io.BytesIO(MINI_PNG), "image/png")},
    )


client = TestClient(main.app)
hdrs, user_id = _auth_headers(client)
store = TenantStore(user_id)
report_id = _create_min_report(store)
photos_dir = _photos_dir(user_id)

# Leere Liste
res = client.get(f"/api/reports/{report_id}/photos", headers=hdrs)
_expect(res.status_code == 200, f"list empty: {res.status_code}")
_expect(res.json().get("count") == 0, "count should be 0")
_expect(res.json().get("maxPhotos") == 10, "maxPhotos should be 10")

# Upload
res = _upload_png(client, report_id, hdrs)
_expect(res.status_code == 200, f"upload: {res.status_code} {res.text}")
photo = res.json().get("photo") or {}
photo_id = photo.get("id")
_expect(photo_id, "photo id missing")
_expect(photo.get("url", "").startswith("/uploads/tenants/"), "url missing")
_expect(res.json().get("count") == 1, "count after upload should be 1")

# Datei auf Disk
fn = photo.get("filename")
_expect(fn and (photos_dir / fn).is_file(), "photo file not on disk")

# Liste mit Eintrag
res = client.get(f"/api/reports/{report_id}/photos", headers=hdrs)
_expect(res.status_code == 200 and res.json().get("count") == 1, "list after upload")

# Bericht enthaelt photos
rep = client.get(f"/api/reports/{report_id}", headers=hdrs).json()
_expect(isinstance(rep.get("photos"), list) and len(rep["photos"]) == 1, "report.photos missing")

# Delete einzelnes Foto
res = client.delete(f"/api/reports/{report_id}/photos/{photo_id}", headers=hdrs)
_expect(res.status_code == 200 and res.json().get("count") == 0, f"delete photo: {res.text}")
_expect(not (photos_dir / fn).exists(), "photo file should be removed from disk")

# 10er-Limit
for i in range(10):
    res = _upload_png(client, report_id, hdrs, name=f"p{i}.png")
    _expect(res.status_code == 200, f"upload {i}: {res.status_code} {res.text}")

res = _upload_png(client, report_id, hdrs, name="one-too-many.png")
_expect(res.status_code == 400, f"11th upload should be 400, was {res.status_code}")
_expect("10" in res.json().get("detail", ""), "limit message expected")

# Cleanup beim Bericht-Delete
photos_before = client.get(f"/api/reports/{report_id}/photos", headers=hdrs).json().get("photos") or []
filenames = [p.get("filename") for p in photos_before if p.get("filename")]
_expect(len(filenames) == 10, "should have 10 photos before report delete")

res = client.delete(f"/api/reports/{report_id}", headers=hdrs)
_expect(res.status_code == 200, "delete report")
for fn in filenames:
    _expect(not (photos_dir / fn).exists(), f"orphan file after report delete: {fn}")

# Ungueltiger Typ
report_id2 = _create_min_report(store)
res = client.post(
    f"/api/reports/{report_id2}/photos",
    headers=hdrs,
    files={"file": ("bad.txt", io.BytesIO(b"hello"), "text/plain")},
)
_expect(res.status_code == 400, "txt upload should fail")

print("REPORT-PHOTOS-SMOKE (F1): OK")
