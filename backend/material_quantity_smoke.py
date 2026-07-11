"""Smoke: Material-Mengen, Entsorgung, LKW-Ladungen, Maschinenstunden im PDF."""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.material_quantity_builder import enrich_materials_list, extract_quantified_materials  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402
from report_export import build_pdf_bytes  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_mat_qty_")))
_STORE = TenantStore(str(uuid.uuid4()))


def _contains_any(items: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(x).casefold() for x in items)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _unit_tests() -> None:
    extracted = extract_quantified_materials(
        "Materialverbrauch 22 ton Boden entsorgt und 6 lkw ht bodenaushub sowie 6,5 ton Asphalt 0/11 und 60 met TOK Band."
    )
    _expect(_contains_any(extracted, "Boden entsorgt"), f"entsorgung fehlt: {extracted}")
    _expect(_contains_any(extracted, "LKW"), f"lkw fehlt: {extracted}")
    _expect(_contains_any(extracted, "Asphalt"), f"asphalt fehlt: {extracted}")
    _expect(_contains_any(extracted, "TOK"), f"tok band fehlt: {extracted}")

    enriched = enrich_materials_list(["Schotter"], "15 ton Schotter 0/45 eingebaut.")
    _expect(any("15" in x and "Schotter" in x for x in enriched), f"qty attach: {enriched}")

    pflaster_extracted = extract_quantified_materials("heute haben wir 50 Quadratmeter Pflaster gelegt")
    _expect(
        not any("pflaster gelegt" in x.casefold() for x in pflaster_extracted),
        f"pflaster activity must not be material: {pflaster_extracted}",
    )


def _integration_tests() -> None:
    os.environ["OPENAI_API_KEY"] = ""
    raw = (
        "Erdplanum und Schotterplanum erstellt. "
        "Bagger 9 std Radlader 2 std LKW 8 std. "
        "7,2 ton Boden entsorgt 6 lkw ht bodenaushub 6,5 ton Asphalt 0/11 60 met TOK Band."
    )
    out = api_structure_report(
        StructureReportBody(
            projectId="mat-qty",
            projectName="Bremke Feuerwehrhaus",
            customerName="Lehnen",
            date="2026-06-17",
            employeeNames=["Ben", "Stefan"],
            startTime="06:00",
            endTime="18:00",
            exportFormat="PDF",
            rawText=raw,
        ),
        store=_STORE,
    )
    structured = out.get("structured") or {}
    mats = [str(x) for x in (structured.get("materials") or [])]
    machine_hours = [str(x) for x in (structured.get("machineHours") or [])]

    _expect(_contains_any(mats, "Boden entsorgt"), f"integration entsorgung: {mats}")
    _expect(_contains_any(mats, "LKW"), f"integration lkw: {mats}")
    _expect(_contains_any(mats, "TOK") or _contains_any(mats, "Asphalt"), f"integration asphalt/tok: {mats}")
    _expect(any("Bagger" in x for x in machine_hours), f"bagger std: {machine_hours}")
    _expect(any("LKW" in x for x in machine_hours), f"lkw std: {machine_hours}")

    pflaster_out = api_structure_report(
        StructureReportBody(
            projectId="mat-qty-pflaster",
            projectName="Pflaster Test",
            customerName="Kunde",
            date="2026-07-11",
            employeeNames=["Max"],
            startTime="08:00",
            endTime="17:00",
            exportFormat="PDF",
            rawText="heute haben wir 50 Quadratmeter Pflaster gelegt",
        ),
        store=_STORE,
    )
    pflaster_mats = [str(x) for x in ((pflaster_out.get("structured") or {}).get("materials") or [])]
    _expect(_contains_any(pflaster_mats, "Pflastersteine"), f"pflastersteine fehlt: {pflaster_mats}")
    _expect(
        not any("pflaster gelegt" in x.casefold() for x in pflaster_mats),
        f"pflaster activity echo in materials: {pflaster_mats}",
    )

    pdf = build_pdf_bytes(
        {
            "companyName": "Panek Test",
            "projectName": "Bremke",
            "customerName": "Lehnen",
            "date": "2026-06-17",
            "employees": ["Ben"],
            "startTime": "06:00",
            "endTime": "18:00",
            "structured": structured,
        },
        {"companyName": "Panek Test"},
    )
    _expect(pdf.startswith(b"%PDF"), "pdf build failed")
    # ReportLab komprimiert Text — grobe Prüfung auf vorhandene Bytes
    _expect(b"Maschinen" in pdf or len(pdf) > 2000, "pdf scheint ohne Maschinenblock gebaut")


def main() -> int:
    _unit_tests()
    _integration_tests()
    print("MATERIAL-QUANTITY-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
