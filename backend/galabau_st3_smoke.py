"""Smoke ST3 — Realfälle aus dem Sprach-Stresstest (10 Sätze)."""

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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_st3_smoke_")))
_SMOKE_STORE = TenantStore(str(uuid.uuid4()))

_CASES: tuple[dict[str, object], ...] = (
    {
        "name": "T1_RasenWhisper",
        "rawText": "Heute haben wir fünfzig Quadratmeter Rasse gemacht.",
        "expectedActivities": ["50 m² Rasen gemäht"],
        "forbiddenSummaryContains": ["Keine Angabe"],
    },
    {
        "name": "T2_PflegeMix",
        "rawText": "Vormittags Rasen getrimmt, danach Unkraut gezupft und zum Schluss die Hecke zurückgeschnitten.",
        "expectedActivities": ["Rasen getrimmt", "Unkraut entfernt", "Hecke geschnitten"],
        "expectedSummaryContains": ["Unkraut"],
    },
    {
        "name": "T3_HardscapePflegeMix",
        "rawText": "Erst dreißig Quadratmeter Pflaster gelegt, dann Schotter reingemacht und danach noch Laub gefegt.",
        "expectedActivities": ["30 m² Pflaster verlegt", "Schotter eingebaut", "Laub entfernt"],
        "expectedSummaryContains": ["Schotter"],
    },
    {
        "name": "T4_Rasenkantensteine",
        "rawText": "Wir haben heute fünfundzwanzig laufende Meter Rasen Kanten Steine gesetzt.",
        "expectedActivities": ["25 lfm Rasenkantensteine gesetzt"],
        "expectedMaterials": ["Rasenkantensteine"],
        "forbiddenActivities": ["Rasen verlegt"],
    },
    {
        "name": "T5_RunOnHardscape",
        "rawText": "Also fünfzig qm Pflaster gelegt dann noch zwei Kubik Schotter rein und zwei fünfer Split eingebaut.",
        "expectedActivities": ["50 m² Pflaster verlegt", "2 m³ Schotter eingebaut", "Splitt 2/5 mm"],
    },
    {
        "name": "T6_Kompletttag",
        "rawText": "Dreißig Quadratmeter Pflaster verlegt, zehn Quadratmeter Gartenmauer gebaut, Hecke geschnitten und drei Pflanzkübel mit Erde befüllt.",
        "expectedActivities": ["30 m² Pflaster verlegt", "Gartenmauer gebaut", "Hecke geschnitten", "Pflanzkübel"],
        "forbiddenSummaryContains": ["Keine Angabe"],
    },
    {
        "name": "T7_VagePflege",
        "rawText": "Heute den ganzen Garten freigeschnitten und zwischendurch Unkraut weg gemacht.",
        "expectedActivities": ["Rasen getrimmt", "Unkraut entfernt"],
        "forbiddenSummaryContains": ["Keine Angabe"],
    },
    {
        "name": "T8_RollrasenVerdichtung",
        "rawText": "Dreißig Quadratmeter Rollrasen verlegt und Untergrund verdichtet.",
        "expectedActivities": ["30 m² Rasen verlegt", "Untergrund verdichtet"],
        "expectedSummaryContains": ["Rasen verlegt"],
        "forbiddenSummaryContains": ["wurden der Untergrund"],
    },
    {
        "name": "T9_TiefbauKG",
        "rawText": "Graben gezogen, KG-Rohre gelegt und den Untergrund wieder verdichtet.",
        "expectedActivities": ["KG-Rohre verlegt", "Graben ausgehoben", "Untergrund verdichtet"],
        "forbiddenActivities": ["Wasserleitungen verlegt"],
        "expectedMaterials": ["KG-Rohre"],
    },
    {
        "name": "T10_Trockenbau",
        "rawText": "Rigips dran gemacht, Decke abgehängt und alles zugespachtelt.",
        "expectedActivities": ["Gipskartonplatten montiert", "Decke abgehängt", "Spachtelarbeiten"],
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
            projectId="p-st3",
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
        for expected in case.get("expectedSummaryContains") or []:
            if str(expected).casefold() not in summary.casefold():
                failures.append(f"{name}: summary fehlt -> {expected} (summary={summary!r})")
        for forbidden in case.get("forbiddenSummaryContains") or []:
            if str(forbidden).casefold() in summary.casefold():
                failures.append(f"{name}: summary verboten -> {forbidden} (summary={summary!r})")

    if failures:
        print("GALABAU-ST3-SMOKE: FEHLER")
        for row in failures:
            print(" -", row)
        return 1

    print("GALABAU-ST3-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
