"""Smoke: Gedankensammlung (Protokoll-Modus thoughts) — rein additiv."""

from __future__ import annotations

import sys
import tempfile
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.site_protocol import (  # noqa: E402
    THOUGHTS_PROJECT_ID,
    THOUGHTS_PROJECT_NAME,
    create_protocol_doc,
    protocol_kind_label,
    read_protocols,
)
from app.services.tenant_storage import TenantStore  # noqa: E402
from report_export import build_protocol_attachment_names, build_protocol_pdf_bytes  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_thoughts_")))
_STORE = TenantStore(str(uuid.uuid4()))


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def main() -> int:
    doc = create_protocol_doc(
        _STORE,
        company_name="Testfirma",
        company_logo_url=None,
        office_email="buero@example.com",
        project_id="irgendwas-soll-ignoriert-werden",
        project_name="Falsche Baustelle",
        customer_name="Kunde",
        date="2026-07-20",
        mode="thoughts",
        raw_text="Idee fuer Montageablauf und Material nachbestellen",
        polished_text="Idee für Montageablauf und Material nachbestellen.",
        participants="soll weg",
        export_format="PDF",
    )
    _expect(doc["mode"] == "thoughts", f"mode: {doc['mode']}")
    _expect(doc["projectId"] == THOUGHTS_PROJECT_ID, f"projectId: {doc['projectId']}")
    _expect(doc["projectName"] == THOUGHTS_PROJECT_NAME, f"projectName: {doc['projectName']}")
    _expect(not doc.get("customerName"), f"customer: {doc.get('customerName')}")
    _expect(not doc.get("participants"), f"participants: {doc.get('participants')}")
    _expect(doc.get("sequenceNumber") is None, "sequenceNumber must be None")
    _expect(protocol_kind_label(doc) == "Gedankensammlung", protocol_kind_label(doc))

    listed = [p for p in read_protocols(_STORE) if p.get("mode") == "thoughts"]
    _expect(len(listed) == 1, f"list count: {len(listed)}")

    pdf = build_protocol_pdf_bytes(doc, {"companyName": "Testfirma", "officeEmail": "buero@example.com"})
    _expect(pdf.startswith(b"%PDF"), "pdf build failed")
    ascii_fn, desc = build_protocol_attachment_names(doc, "pdf")
    _expect("gedankensammlung" in ascii_fn.casefold(), f"filename: {ascii_fn}")
    _expect("gedankensammlung" in desc.casefold(), f"desc: {desc}")

    # Bestehende Modi unverändert: quick braucht Baustelle
    try:
        create_protocol_doc(
            _STORE,
            company_name="Testfirma",
            company_logo_url=None,
            office_email="buero@example.com",
            project_id="",
            project_name="",
            customer_name="",
            date="2026-07-20",
            mode="quick",
            raw_text="Kurze Schnellnotiz Text",
            polished_text="Kurze Schnellnotiz Text",
            participants="",
            export_format="PDF",
        )
        raise SystemExit("FAIL: quick ohne Baustelle hätte fehlschlagen müssen")
    except Exception as ex:
        _expect("Baustelle" in str(ex) or "400" in str(ex), f"unexpected: {ex}")

    quick = create_protocol_doc(
        _STORE,
        company_name="Testfirma",
        company_logo_url=None,
        office_email="buero@example.com",
        project_id="p1",
        project_name="Schmitz Außenanlage",
        customer_name="Kunde",
        date="2026-07-20",
        mode="quick",
        raw_text="Baustellen-Schnellnotiz mit Bezug",
        polished_text="Baustellen-Schnellnotiz mit Bezug",
        participants="",
        export_format="PDF",
    )
    _expect(quick["mode"] == "quick", "quick mode broken")
    _expect(quick["projectId"] == "p1", "quick projectId broken")

    print("THOUGHTS-PROTOCOL-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
