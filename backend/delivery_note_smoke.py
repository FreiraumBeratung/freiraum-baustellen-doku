"""Smoke: Lieferschein-Scan V1 — rein additiv, isoliert."""

from __future__ import annotations

import sys
import tempfile
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.delivery_note import (  # noqa: E402
    MAX_PAGES_PER_DELIVERY_NOTE,
    create_delivery_note_doc,
    delivery_note_photos_list,
    find_delivery_note,
    read_delivery_notes,
    save_delivery_note_photos,
)
from app.services.tenant_storage import TenantStore  # noqa: E402
from report_export import (  # noqa: E402
    build_delivery_note_attachment_names,
    build_delivery_note_pdf_bytes,
)
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_delivery_")))
_STORE = TenantStore(str(uuid.uuid4()))


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def main() -> int:
    _expect(MAX_PAGES_PER_DELIVERY_NOTE == 8, f"max pages: {MAX_PAGES_PER_DELIVERY_NOTE}")

    try:
        create_delivery_note_doc(
            _STORE,
            company_name="Testfirma",
            company_logo_url=None,
            office_email="buero@example.com",
            project_id="",
            project_name="",
            customer_name="",
            date="2026-07-20",
            note="",
        )
        raise SystemExit("FAIL: create ohne Baustelle hätte fehlschlagen müssen")
    except Exception as ex:
        _expect("Baustelle" in str(ex) or "400" in str(ex), f"unexpected: {ex}")

    doc = create_delivery_note_doc(
        _STORE,
        company_name="Testfirma",
        company_logo_url=None,
        office_email="buero@example.com",
        project_id="p-ls-1",
        project_name="Schmitz Außenanlage",
        customer_name="Kunde Schmitz",
        date="2026-07-20",
        note="Sand 0/32",
    )
    _expect(bool(doc.get("id")), "id missing")
    _expect(doc["projectId"] == "p-ls-1", f"projectId: {doc['projectId']}")
    _expect(doc["projectName"] == "Schmitz Außenanlage", f"name: {doc['projectName']}")
    _expect(doc.get("note") == "Sand 0/32", f"note: {doc.get('note')}")
    _expect(delivery_note_photos_list(doc) == [], "photos should start empty")

    listed = read_delivery_notes(_STORE)
    _expect(len(listed) == 1, f"list count: {len(listed)}")
    _expect(find_delivery_note(_STORE, doc["id"])["id"] == doc["id"], "find failed")

    # Mini-JPEG (1x1) als Scan-Seite schreiben
    photo_dir = _STORE.uploads_dir("photos")
    photo_dir.mkdir(parents=True, exist_ok=True)
    jpeg_name = f"photo_smoke_{uuid.uuid4().hex}.jpg"
    # Minimal gültiges JPEG
    jpeg_bytes = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
        b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
        b"\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.7"
        b"111\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
        b"\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04"
        b"\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa"
        b'\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82'
        b"\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghij"
        b"stuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97"
        b"\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5"
        b"\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3"
        b"\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9"
        b"\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01"
        b"\x01\x00\x00?\x00\xaa\xff\xd9"
    )
    (photo_dir / jpeg_name).write_bytes(jpeg_bytes)
    photo_id = str(uuid.uuid4())
    save_delivery_note_photos(
        _STORE,
        doc["id"],
        [
            {
                "id": photo_id,
                "filename": jpeg_name,
                "originalFilename": "scan.jpg",
                "contentType": "image/jpeg",
                "sizeBytes": len(jpeg_bytes),
                "uploadedAt": "2026-07-20T12:00:00+00:00",
            }
        ],
    )
    refreshed = find_delivery_note(_STORE, doc["id"])
    _expect(len(delivery_note_photos_list(refreshed)) == 1, "photo not saved")

    def resolve_photo(filename: str) -> Path | None:
        path = _STORE.resolve_upload_file("photos", filename)
        return path

    pdf = build_delivery_note_pdf_bytes(
        refreshed,
        {"companyName": "Testfirma", "officeEmail": "buero@example.com"},
        resolve_photo=resolve_photo,
    )
    _expect(pdf.startswith(b"%PDF"), "pdf build failed")
    ascii_fn, desc = build_delivery_note_attachment_names(refreshed, "pdf")
    _expect("lieferschein" in ascii_fn.casefold(), f"filename: {ascii_fn}")
    _expect("lieferschein" in desc.casefold(), f"desc: {desc}")

    print("DELIVERY-NOTE-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
