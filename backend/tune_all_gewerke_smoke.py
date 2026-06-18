"""Tune-Smoke: additive Erweiterungen über alle aktiven Gewerke."""

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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_tune_smoke_")))
_SMOKE_STORE = TenantStore(str(uuid.uuid4()))

_CASES: tuple[dict[str, object], ...] = (
    {
        "name": "G1_GaLaPflegePlus",
        "rawText": "Heute Rasen vertikutiert, danach Rasen gedüngt und die Fläche bewässert.",
        "expectedActivities": ["Rasen vertikutiert", "Rasen gedüngt", "Fläche bewässert"],
    },
    {
        "name": "G2_GaLaWinterdienst",
        "rawText": "Heute Winterdienst gemacht, Schnee geräumt und Streugut gestreut.",
        "expectedActivities": ["Winterdienst durchgeführt"],
        "expectedMaterials": ["Streugut"],
    },
    {
        "name": "G3_GaLaWpcTerrasse",
        "rawText": "Heute 24 Quadratmeter WPC Terrasse gebaut.",
        "expectedActivities": ["24 m² Holz-/WPC-Terrasse gebaut"],
        "expectedMaterials": ["WPC-Dielen"],
    },
    {
        "name": "S1_SHKSanitaerObjekte",
        "rawText": "WC gesetzt, Waschbecken montiert, Dusche angeschlossen und Armaturen montiert.",
        "expectedActivities": ["WC montiert", "Waschbecken montiert", "Dusche montiert", "Armaturen montiert"],
        "expectedMaterials": ["WC", "Waschbecken", "Dusche", "Armaturen"],
    },
    {
        "name": "S2_SHKDruckpruefungAbgleich",
        "rawText": "Heute Druckprobe gemacht und hydraulischer Abgleich durchgeführt.",
        "expectedActivities": ["Druckprüfung durchgeführt", "Hydraulischer Abgleich durchgeführt"],
    },
    {
        "name": "F1_FliesenGrossformatNivellier",
        "rawText": "Heute 30 Quadratmeter Großformatfliesen verlegt und Ausgleichsmasse gezogen.",
        "expectedActivities": ["30 m² Großformatfliesen verlegt", "Nivelliermasse aufgetragen"],
        "expectedMaterials": ["Fliesen", "Nivelliermasse"],
    },
    {
        "name": "F2_FliesenBodenablaufNaturstein",
        "rawText": "Bodenablauf gesetzt und danach 12 qm Naturstein verlegt.",
        "expectedActivities": ["Bodenablauf eingebaut", "12 m² Naturstein verlegt"],
        "expectedMaterials": ["Bodenablauf", "Naturstein"],
    },
    {
        "name": "T1_TiefbauHausanschlussAsphalt",
        "rawText": "Heute Hausanschluss gemacht und Asphalt eingebaut.",
        "expectedActivities": ["Hausanschluss hergestellt", "Asphalt eingebaut"],
        "expectedMaterials": ["Hausanschluss", "Asphalt"],
    },
    {
        "name": "P1_PutzVarianten",
        "rawText": "Sockelputz gemacht, danach Reibputz gemacht und Kratzputz gemacht.",
        "expectedActivities": ["Sockelputz aufgetragen", "Reibputz aufgetragen", "Kratzputz aufgetragen"],
        "expectedMaterials": ["Sockelputz", "Reibputz", "Kratzputz"],
    },
    {
        "name": "R1_RegressionBestand",
        "rawText": "Heute 50 Quadratmeter Pflaster verlegt und Schotter reingemacht.",
        "expectedActivities": ["50 m² Pflaster verlegt", "Schotter eingebaut"],
        "forbiddenActivities": ["Großformatfliesen verlegt", "WC montiert"],
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
            projectId="p-tune",
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

        for expected in case.get("expectedActivities") or []:
            if not _contains_any(acts, str(expected)):
                failures.append(f"{name}: activity fehlt -> {expected} (got={acts!r})")
        for forbidden in case.get("forbiddenActivities") or []:
            if _contains_any(acts, str(forbidden)):
                failures.append(f"{name}: activity verboten -> {forbidden} (got={acts!r})")
        for expected in case.get("expectedMaterials") or []:
            if not _contains_any(mats, str(expected)):
                failures.append(f"{name}: material fehlt -> {expected} (got={mats!r})")

    if failures:
        print("TUNE-ALL-GEWERKE-SMOKE: FEHLER")
        for row in failures:
            print(" -", row)
        return 1

    print("TUNE-ALL-GEWERKE-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

