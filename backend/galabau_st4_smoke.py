"""Smoke ST4 — GaLaBau Gestaltung: Palisaden, Mulch, Keramikterrasse."""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_st4_smoke_")))
_SMOKE_STORE = TenantStore(str(uuid.uuid4()))

_CASES: tuple[dict[str, object], ...] = (
    {
        "name": "T1_PalisadenLfm",
        "rawText": "Heute zwanzig laufende Meter Palisaden gesetzt.",
        "expectedActivities": ["20 lfm Palisaden gesetzt"],
        "expectedMaterials": ["Palisaden"],
        "expectedSuggestions": ["Splitt benutzt?", "Beton benutzt?"],
    },
    {
        "name": "T2_PalisadenMontiert",
        "rawText": "Palisaden montiert und Untergrund verdichtet.",
        "expectedActivities": ["Palisaden gesetzt", "Untergrund verdichtet"],
        "expectedMaterials": ["Palisaden"],
    },
    {
        "name": "T3_RindenmulchGemulcht",
        "rawText": "Vierzig Quadratmeter mit Rindenmulch gemulcht.",
        "expectedActivities": ["40 m² Rindenmulch eingedeckt"],
        "expectedMaterials": ["Rindenmulch"],
        "forbiddenActivities": ["Pflegearbeiten"],
    },
    {
        "name": "T4_MulchBestreut",
        "rawText": "Beetfläche mit Mulch bestreut.",
        "expectedActivities": ["Fläche mit Mulch eingedeckt"],
        "expectedMaterials": ["Mulch"],
        "forbiddenActivities": ["Pflegearbeiten"],
    },
    {
        "name": "T5_MulchUmgangssprache",
        "rawText": "Danach Mulch reingemacht auf der Fläche.",
        "expectedActivities": ["Fläche mit Mulch eingedeckt"],
    },
    {
        "name": "T6_Keramikterrasse2cm",
        "rawText": "Terrasse mit Keramikplatten zwei Zentimeter dick verlegt, dreißig Quadratmeter.",
        "expectedActivities": ["30 m² Keramikterrasse verlegt"],
        "expectedMaterials": ["Keramikplatten"],
        "expectedSuggestions": ["Stelzlager benutzt?"],
        "forbiddenSuggestions": ["Einkornmörtel benutzt?", "Drainagemörtel benutzt?"],
        "forbiddenActivities": ["Fliesen verlegt"],
    },
    {
        "name": "T7_Keramikterrasse3cm",
        "rawText": "Auf der Terrasse Keramikplatte 3 cm dick gelegt, fünfundzwanzig qm.",
        "expectedActivities": ["25 m² Keramikterrasse verlegt"],
        "expectedMaterials": ["Keramikplatten"],
        "expectedSuggestions": ["Einkornmörtel benutzt?", "Drainagemörtel benutzt?"],
        "forbiddenSuggestions": ["Stelzlager benutzt?"],
        "forbiddenActivities": ["Fliesen verlegt"],
    },
    {
        "name": "T8_KompletttagGestaltung",
        "rawText": "Palisaden gesetzt, danach vierzig qm gemulcht und zum Schluss Keramikterrasse mit Platten 2 cm auf der Terrasse gelegt.",
        "expectedActivities": ["Palisaden gesetzt", "Mulch eingedeckt", "Keramikterrasse verlegt"],
        "forbiddenSummaryContains": ["Keine Angabe"],
    },
    {
        "name": "T9_RegressionPflaster",
        "rawText": "Fünfzig qm Pflaster gelegt und Schotter reingemacht.",
        "expectedActivities": ["50 m² Pflaster verlegt", "Schotter eingebaut"],
        "forbiddenActivities": ["Keramikterrasse verlegt", "Palisaden gesetzt"],
    },
    {
        "name": "T10_RegressionPflege",
        "rawText": "Rasen gemacht und Unkraut gezupft.",
        "expectedActivities": ["Rasen gemäht", "Unkraut entfernt"],
        "forbiddenActivities": ["Mulch eingedeckt"],
    },
)


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    failures: list[str] = []

    for case in _CASES:
        name = str(case["name"])
        body = StructureReportBody(
            projectId="p-st4",
            projectName="Denis Garten",
            customerName="Testkunde",
            date="2026-06-09",
            employeeNames=["Max"],
            startTime="08:00",
            endTime="16:30",
            exportFormat="PDF",
            rawText=str(case["rawText"]),
        )
        out = api_structure_report(body, store=_SMOKE_STORE)
        structured = out.get("structured") or {}
        acts = [str(x) for x in (structured.get("activities") or [])]
        mats = [str(x) for x in (structured.get("materials") or [])]
        suggestions = [str(x) for x in (structured.get("materialSuggestions") or [])]
        summary = str(structured.get("summary") or "")

        for expected in case.get("expectedActivities") or []:
            if not _contains_any(acts, str(expected)):
                failures.append(f"{name}: activity fehlt -> {expected} (got={acts!r})")
        for forbidden in case.get("forbiddenActivities") or []:
            if _contains_any(acts, str(forbidden)):
                failures.append(f"{name}: activity verboten -> {forbidden}")
        for expected in case.get("expectedMaterials") or []:
            if not _contains_any(mats, str(expected)):
                failures.append(f"{name}: material fehlt -> {expected} (got={mats!r})")
        for expected in case.get("expectedSuggestions") or []:
            if not _contains_any(suggestions, str(expected)):
                failures.append(f"{name}: suggestion fehlt -> {expected} (got={suggestions!r})")
        for forbidden in case.get("forbiddenSuggestions") or []:
            if _contains_any(suggestions, str(forbidden)):
                failures.append(f"{name}: suggestion verboten -> {forbidden} (got={suggestions!r})")
        for expected in case.get("expectedSummaryContains") or []:
            if str(expected).casefold() not in summary.casefold():
                failures.append(f"{name}: summary fehlt -> {expected} (summary={summary!r})")
        for forbidden in case.get("forbiddenSummaryContains") or []:
            if str(forbidden).casefold() in summary.casefold():
                failures.append(f"{name}: summary verboten -> {forbidden} (summary={summary!r})")

    if failures:
        print("GALABAU-ST4-SMOKE: FEHLER")
        for row in failures:
            print(" -", row)
        return 1

    print("GALABAU-ST4-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
