"""Smoke ST1 — GaLaBau Grünpflege (Rasen, Unkraut, Hecke, Laub)."""

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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_galabau_pflege_st1_")))
_SMOKE_STORE = TenantStore(str(uuid.uuid4()))

_CASES: tuple[dict[str, object], ...] = (
    {
        "name": "RasenGemaeht",
        "rawText": "Heute haben wir 50 Quadratmeter Rasen gemäht.",
        "expectedActivities": ["50 m² Rasen gemäht"],
        "expectedSummaryContains": ["Rasen gemäht", "50"],
        "forbiddenSummaryContains": ["Keine Angabe"],
    },
    {
        "name": "RasenWhisperGemacht",
        "rawText": "50 qm Rasse gemacht.",
        "expectedActivities": ["50 m² Rasen gemäht"],
        "expectedSummaryContains": ["Rasen gemäht"],
    },
    {
        "name": "RasenGetrimmt",
        "rawText": "Danach Rasen getrimmt und Unkraut entfernt.",
        "expectedActivities": ["Rasen getrimmt", "Unkraut entfernt"],
        "expectedSummaryContains": ["Rasen getrimmt", "Unkraut"],
    },
    {
        "name": "HeckeGeschnitten",
        "rawText": "Vormittags die Hecke geschnitten.",
        "expectedActivities": ["Hecke geschnitten"],
        "expectedSummaryContains": ["Hecke"],
    },
    {
        "name": "LaubEntfernt",
        "rawText": "Laub entfernt und aufgeräumt.",
        "expectedActivities": ["Laub entfernt"],
        "expectedSummaryContains": ["Laub"],
    },
    {
        "name": "RollrasenVerlegtRegression",
        "rawText": "30 Quadratmeter Rollrasen verlegt.",
        "expectedActivities": ["30 m² Rasen verlegt"],
        "forbiddenActivities": ["Rasen gemäht"],
    },
    {
        "name": "PflasterRegression",
        "rawText": "50 Quadratmeter Pflaster verlegt.",
        "expectedActivities": ["50 m² Pflaster verlegt"],
        "forbiddenActivities": ["Rasen gemäht"],
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
            projectId="p-smoke",
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
        summary = str(structured.get("summary") or "")

        for expected in case.get("expectedActivities") or []:
            if not _contains_any(acts, str(expected)):
                failures.append(f"{name}: activity fehlt -> {expected} (got={acts!r})")
        for forbidden in case.get("forbiddenActivities") or []:
            if _contains_any(acts, str(forbidden)):
                failures.append(f"{name}: activity verboten -> {forbidden}")
        for expected in case.get("expectedSummaryContains") or []:
            if str(expected).casefold() not in summary.casefold():
                failures.append(f"{name}: summary fehlt -> {expected} (summary={summary!r})")
        for forbidden in case.get("forbiddenSummaryContains") or []:
            if str(forbidden).casefold() in summary.casefold():
                failures.append(f"{name}: summary verboten -> {forbidden}")

    if failures:
        print("GALABAU-PFLEGE-ST1-SMOKE: FEHLER")
        for row in failures:
            print(" -", row)
        return 1

    print("GALABAU-PFLEGE-ST1-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
