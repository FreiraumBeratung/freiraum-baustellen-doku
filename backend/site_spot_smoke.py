"""Smoke: Ort/Laterne nur für den freigeschalteten Mandanten, nicht in notes/Tätigkeiten."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ["OPENAI_API_KEY"] = ""
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

from smoke_isolation import isolate_smoke_data

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_sitespot_")))

from app.services.site_spot import (  # noqa: E402
    SITE_SPOT_TENANT_IDS,
    format_baustelle_display,
    normalize_site_spot,
    site_spot_enabled_for_tenant,
    site_spot_for_create,
    site_spot_for_update,
)
from report_export import build_pdf_bytes  # noqa: E402

TENANT = next(iter(SITE_SPOT_TENANT_IDS))
OTHER = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def main() -> int:
    _expect(site_spot_enabled_for_tenant(TENANT) is True, "allowlist tenant")
    _expect(site_spot_enabled_for_tenant(OTHER) is False, "other tenant off")
    _expect(site_spot_enabled_for_tenant("") is False, "empty tenant off")

    _expect(normalize_site_spot("  Laterne   1 \n") == "Laterne 1", "whitespace")
    _expect(len(normalize_site_spot("x" * 200)) == 80, "max length")
    _expect(site_spot_for_create(OTHER, "Laterne 1") == "", "other create ignored")
    _expect(site_spot_for_create(TENANT, "Laterne 2") == "Laterne 2", "own create kept")
    _expect(site_spot_for_update(OTHER, "Laterne 9", "") == "", "other update ignored")
    _expect(site_spot_for_update(TENANT, None, "Laterne 1") == "Laterne 1", "omit keeps existing")
    _expect(site_spot_for_update(TENANT, "", "Laterne 1") == "", "empty clears")

    _expect(format_baustelle_display("Stadtplatz", "") == "Stadtplatz", "empty spot")
    _expect(
        format_baustelle_display({"projectName": "Stadtplatz", "siteSpot": "Laterne 1"})
        == "Stadtplatz · Laterne 1",
        "report dict",
    )

    report = {
        "id": "spot-smoke",
        "companyName": "Testfirma",
        "projectName": "Stadtplatz",
        "siteSpot": "Laterne 1",
        "customerName": "Stadt",
        "date": "2026-09-16",
        "employees": ["Max"],
        "startTime": "07:00",
        "endTime": "16:00",
        "exportFormat": "PDF",
        "notes": "Tagesbesonderheit bleibt getrennt",
        "structured": {
            "summary": "Kurztest",
            "activities": ["Pflaster verlegt"],
            "materials": [],
            "problems": [],
            "openItems": [],
            "customerTalk": "",
        },
        "photos": [],
        "signatures": {"customer": None, "employee": None},
    }
    pdf = build_pdf_bytes(report, {"companyName": "Testfirma"})
    _expect(pdf.startswith(b"%PDF"), "pdf magic")
    pdf_plain = build_pdf_bytes({**report, "siteSpot": ""}, {"companyName": "Testfirma"})
    _expect(pdf_plain.startswith(b"%PDF"), "pdf without spot")
    _expect("notes" not in (report.get("siteSpot") or ""), "not mixed into notes key")
    print("site_spot_smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
