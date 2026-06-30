"""P1 Gold-Smoke: Summary ohne Material-Echo — auch mit aktivem OPENAI_API_KEY.

Prüft Guard-Funktionen offline und die volle Pipeline mit/ohne KI-Polish.
Rein additiv — keine bestehenden Wellen ändern.
"""

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
from app.services.summary_material_guard import (  # noqa: E402
    detect_material_echo_in_summary,
    strip_material_echo_from_summary,
    summary_has_material_echo,
)
from services.ai_report_service import polish_summary_with_ai, _polished_summary_is_safe  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_summary_echo_gold_")))
_STORE = TenantStore(str(uuid.uuid4()))
_SAVED_KEY = os.environ.get("OPENAI_API_KEY", "")


def _fail(msg: str, failures: list[str]) -> None:
    failures.append(msg)


def _guard_unit_tests(failures: list[str]) -> None:
    acts = ["50 m² Pflaster verlegt"]
    mats = ["Pflastersteine"]
    bad = (
        "Am 29. Juni 2026 wurden 50 m² Pflaster verlegt. "
        "Hierbei kamen Pflastersteine zum Einsatz."
    )
    if not summary_has_material_echo(bad, mats, acts):
        _fail("Guard: Echo-Satz muss erkannt werden", failures)
    cleaned = strip_material_echo_from_summary(bad, mats, acts)
    if summary_has_material_echo(cleaned, mats, acts):
        _fail(f"Guard: nach Strip noch Echo (got={cleaned!r})", failures)
    if "zum einsatz" in cleaned.casefold():
        _fail(f"Guard: 'zum Einsatz' nach Strip noch vorhanden (got={cleaned!r})", failures)
    if "pflasterstein" in cleaned.casefold():
        _fail(f"Guard: Pflastersteine nach Strip noch in Summary (got={cleaned!r})", failures)
    if detect_material_echo_in_summary(bad, mats, acts) is None:
        _fail("Guard: detect_material_echo muss Grund liefern", failures)

    good = "29.06.2026: Auf der Baustelle wurden 50 m² Pflaster verlegt."
    if summary_has_material_echo(good, mats, acts):
        _fail("Guard: saubere Summary darf kein Echo sein", failures)

    if _polished_summary_is_safe(bad, acts, mats, good) is not False:
        _fail("Guard: _polished_summary_is_safe muss Echo ablehnen", failures)
    if _polished_summary_is_safe(good, acts, mats, good) is not True:
        _fail("Guard: _polished_summary_is_safe muss saubere Summary akzeptieren", failures)


def _pipeline_offline(failures: list[str]) -> None:
    os.environ["OPENAI_API_KEY"] = ""
    raw = (
        "Heute haben wir 50 qm2 Pflaster verlegt. "
        "Anschliessend mit der Kundin gesprochen sie war zufrieden."
    )
    body = StructureReportBody(
        projectId="p1",
        projectName="Schmitz Aussenanlage",
        customerName="Test",
        date="2026-06-29",
        employeeNames=["M"],
        startTime="08:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    s = (api_structure_report(body, store=_STORE).get("structured") or {})
    summary = str(s.get("summary") or "")
    materials = list(s.get("materials") or [])
    activities = list(s.get("activities") or [])
    if not summary or summary == "Keine Angabe":
        _fail(f"Offline-Pipeline: Summary leer (got={summary!r})", failures)
    if summary_has_material_echo(summary, materials, activities):
        _fail(f"Offline-Pipeline: Material-Echo in Summary (got={summary!r})", failures)
    for needle in ("zum einsatz", "pflastersteine verarbeitet", "dafür kamen", "dafuer kamen"):
        if needle in summary.casefold():
            _fail(f"Offline-Pipeline: verbotenes Fragment {needle!r} in Summary", failures)


def _pipeline_with_key_if_available(failures: list[str]) -> None:
    key = (_SAVED_KEY or "").strip()
    if not key:
        print("SUMMARY-MATERIAL-ECHO-GOLD: OPENAI_API_KEY nicht gesetzt — KI-Polish-Skip")
        return

    os.environ["OPENAI_API_KEY"] = key
    raw = (
        "Heute haben wir 50 qm2 Pflaster verlegt. "
        "Anschliessend mit der Kundin gesprochen sie war zufrieden."
    )
    body = StructureReportBody(
        projectId="p1-ai",
        projectName="Schmitz Aussenanlage",
        customerName="Test",
        date="2026-06-29",
        employeeNames=["M"],
        startTime="08:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    s = (api_structure_report(body, store=_STORE).get("structured") or {})
    summary = str(s.get("summary") or "")
    materials = list(s.get("materials") or [])
    activities = list(s.get("activities") or [])
    if not summary:
        _fail("KI-Pipeline: Summary leer", failures)
    if summary_has_material_echo(summary, materials, activities):
        _fail(f"KI-Pipeline: Material-Echo mit aktivem Key (got={summary!r})", failures)
    for needle in ("zum einsatz", "hierbei kamen", "dafür kamen", "dafuer kamen"):
        if needle in summary.casefold():
            _fail(f"KI-Pipeline: verbotenes Fragment {needle!r} (got={summary!r})", failures)
    if materials and "pflasterstein" in summary.casefold():
        _fail(f"KI-Pipeline: Materialname in Summary (got={summary!r})", failures)

    # Direkt polish_summary_with_ai — muss ohne Echo liefern oder None (Fallback).
    structured = {
        "activities": activities or ["50 m² Pflaster verlegt"],
        "materials": materials or ["Pflastersteine"],
        "summary": "29.06.2026: Auf der Baustelle wurden 50 m² Pflaster verlegt.",
    }
    polished = polish_summary_with_ai(
        structured, {"date": "2026-06-29", "projectName": "Schmitz Aussenanlage"}
    )
    if polished is not None:
        if summary_has_material_echo(polished, structured["materials"], structured["activities"]):
            _fail(f"polish_summary_with_ai: Echo im Ergebnis (got={polished!r})", failures)
        if "zum einsatz" in polished.casefold():
            _fail(f"polish_summary_with_ai: 'zum Einsatz' (got={polished!r})", failures)


def main() -> int:
    failures: list[str] = []
    try:
        _guard_unit_tests(failures)
        _pipeline_offline(failures)
        _pipeline_with_key_if_available(failures)
    finally:
        if _SAVED_KEY:
            os.environ["OPENAI_API_KEY"] = _SAVED_KEY
        else:
            os.environ.pop("OPENAI_API_KEY", None)

    if failures:
        print("SUMMARY-MATERIAL-ECHO-GOLD: FEHLER")
        for f in failures:
            print(" -", f)
        return 1
    print("SUMMARY-MATERIAL-ECHO-GOLD: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
