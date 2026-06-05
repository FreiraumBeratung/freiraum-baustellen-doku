from __future__ import annotations

import json
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_trade_smoke_")))
_SMOKE_STORE = TenantStore(str(uuid.uuid4()))


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def _norm_text(s: str) -> str:
    return " ".join(str(s or "").split()).strip()


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    data_file = Path(__file__).resolve().parent / "data" / "trade_intelligence_cases.json"
    payload = json.loads(data_file.read_text(encoding="utf-8"))
    cases = payload.get("cases") or []

    failures: list[str] = []
    for case in cases:
        name = str(case.get("name") or "unnamed")
        body = StructureReportBody(
            projectId="p-smoke",
            projectName="Denis Garten",
            customerName="Testkunde",
            date="2026-05-16",
            employeeNames=["Max"],
            startTime="08:00",
            endTime="16:30",
            exportFormat="PDF",
            rawText=str(case.get("rawText") or ""),
        )
        out = api_structure_report(body, store=_SMOKE_STORE)
        structured = out.get("structured") or {}
        acts = [str(x) for x in (structured.get("activities") or [])]
        mats = [str(x) for x in (structured.get("materials") or [])]
        suggs = [str(x) for x in (structured.get("materialSuggestions") or [])]
        machine_suggs = [str(x) for x in (structured.get("machineSuggestions") or [])]
        machine_hours = [str(x) for x in (structured.get("machineHours") or [])]
        summary = str(structured.get("summary") or "")

        for expected in case.get("expectedActivities") or []:
            if not _contains_any(acts, str(expected)):
                failures.append(f"{name}: activity fehlt -> {expected}")
        for forbidden in case.get("forbiddenActivities") or []:
            f = str(forbidden).strip().casefold()
            if any(str(a).strip().casefold() == f for a in acts):
                failures.append(f"{name}: activity soll dedupliziert werden -> {forbidden}")
        first_expected = str(case.get("expectedFirstActivity") or "").strip()
        if first_expected:
            if not acts or first_expected.casefold() not in acts[0].casefold():
                failures.append(
                    f"{name}: priorität falsch, erwartet zuerst -> {first_expected}, erhalten -> {acts[0] if acts else '(leer)'}"
                )
        for expected in case.get("expectedMaterials") or []:
            if not _contains_any(mats, str(expected)):
                failures.append(f"{name}: material fehlt -> {expected}")
        for forbidden in case.get("forbiddenMaterials") or []:
            f = str(forbidden).strip().casefold()
            if any(str(m).strip().casefold() == f for m in mats):
                failures.append(f"{name}: material darf nicht erscheinen -> {forbidden}")
        for expected in case.get("expectedMaterialSuggestions") or []:
            if not _contains_any(suggs, str(expected)):
                failures.append(f"{name}: vorschlag fehlt -> {expected}")
        for forbidden in case.get("forbiddenMaterialSuggestions") or []:
            f = str(forbidden).strip().casefold()
            if any(str(s).strip().casefold() == f for s in suggs):
                failures.append(f"{name}: vorschlag darf nicht erscheinen -> {forbidden}")
        for expected in case.get("expectedMachineSuggestions") or []:
            if not _contains_any(machine_suggs, str(expected)):
                failures.append(f"{name}: maschinen-vorschlag fehlt -> {expected}")
        for forbidden in case.get("forbiddenMachineSuggestions") or []:
            f = str(forbidden).strip().casefold()
            if any(str(s).strip().casefold() == f for s in machine_suggs):
                failures.append(f"{name}: maschinen-vorschlag darf nicht erscheinen -> {forbidden}")
        for expected in case.get("expectedMachineHours") or []:
            if not _contains_any(machine_hours, str(expected)):
                failures.append(f"{name}: maschinenstunden fehlen -> {expected}")
        for expected in case.get("expectedSummaryContains") or []:
            if str(expected).casefold() not in summary.casefold():
                failures.append(f"{name}: summary fehlt -> {expected}")
        for forbidden in case.get("forbiddenSummaryContains") or []:
            if str(forbidden).casefold() in summary.casefold():
                failures.append(f"{name}: summary darf nicht enthalten -> {forbidden}")
        expected_summary_exact = str(case.get("expectedSummaryExact") or "").strip()
        if expected_summary_exact:
            if _norm_text(summary) != _norm_text(expected_summary_exact):
                failures.append(
                    f"{name}: summary exact mismatch -> got={summary!r} expected={expected_summary_exact!r}"
                )
        expected_activities_exact = case.get("expectedActivitiesExact") or []
        if expected_activities_exact:
            got = [_norm_text(x) for x in acts]
            exp = [_norm_text(str(x)) for x in expected_activities_exact]
            if got != exp:
                failures.append(f"{name}: activities exact mismatch -> got={got!r} expected={exp!r}")

    if failures:
        print("TRADE-SMOKE: FEHLER")
        for row in failures:
            print(" -", row)
        return 1

    print("TRADE-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
