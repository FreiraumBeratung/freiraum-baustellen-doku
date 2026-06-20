"""Smoke fuer Folgebericht/Sammelbericht (Runs + Aggregation), rein additiv.

Deckt ab:
- Einzelbericht (seriesMode=False) bleibt ohne runId (bisheriges Verhalten).
- Folgebericht (seriesMode=True) bekommt Run, sammelt ueber mehrere Tage.
- Aggregation: Stunden je Mitarbeiter, Material-Dedupe, offene Punkte, Notizen, Fotos.
- close-run setzt Status abgeschlossen, Gesamtbericht weiterhin abrufbar.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ["OPENAI_API_KEY"] = ""  # offline: deterministische Gesamt-Summary

from main import (  # noqa: E402
    ProjectCreate,
    ReportCreateBody,
    StructuredBlock,
    create_project,
    create_report,
    close_project_run,
    get_collective_report,
)
from app.services.tenant_storage import TenantStore  # noqa: E402
from app.services import collective_report as collective  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_collective_smoke_")))
STORE = TenantStore(str(uuid.uuid4()))


def _mk_report(project_id: str, project_name: str, *, date: str, series: bool, acts, mats, opens, notes="", emps=("Max", "Goran"), start="07:00", end="16:00", brk=45):
    body = ReportCreateBody(
        companyName="Freiraum",
        projectId=project_id,
        projectName=project_name,
        customerName="Familie Becker",
        date=date,
        employees=list(emps),
        employeeIds=[],
        startTime=start,
        endTime=end,
        breakMinutes=brk,
        exportFormat="PDF",
        rawText="…",
        structured=StructuredBlock(
            summary=f"{date}: …",
            activities=list(acts),
            materials=list(mats),
            openItems=list(opens),
        ),
        seriesMode=series,
        notes=notes,
    )
    return create_report(body, store=STORE)


def main() -> int:
    failures: list[str] = []

    # ---- Pure-Funktionen -----------------------------------------------------
    proj: dict = {"id": "p1", "name": "Test", "status": "aktiv"}
    rid = collective.ensure_open_run(proj, now_iso="2026-06-22T07:00:00Z", new_run_id="run-1")
    if rid != "run-1" or proj.get("currentRunId") != "run-1":
        failures.append("ensure_open_run: Run nicht gesetzt")
    rid2 = collective.ensure_open_run(proj, now_iso="x", new_run_id="run-2")
    if rid2 != "run-1":
        failures.append("ensure_open_run: bestehender Run muss fortgesetzt werden")
    info = collective.close_run(proj, now_iso="2026-06-26T16:00:00Z")
    if proj.get("status") != "abgeschlossen" or proj.get("currentRunId") is not None or info["runId"] != "run-1":
        failures.append("close_run: Status/Run nicht korrekt geschlossen")
    if collective.resolve_run_id(proj, None) != "run-1":
        failures.append("resolve_run_id: letzter Run sollte greifen")

    # ---- Integration: Projekt + Folgeberichte --------------------------------
    project = create_project(ProjectCreate(name="Reihenhaus", customer="Becker"), store=STORE)
    pid = project["id"]

    # Einzelbericht -> kein runId
    single = _mk_report(pid, "Reihenhaus", date="2026-06-19", series=False, acts=["10 m² Pflaster verlegt"], mats=["Pflastersteine"], opens=[])
    if single.get("runId") is not None:
        failures.append("Einzelbericht darf keinen runId bekommen")

    # Tag 1 + Tag 2 als Folgebericht
    d1 = _mk_report(pid, "Reihenhaus", date="2026-06-22", series=True,
                    acts=["50 m² Pflaster verlegt"], mats=["Pflastersteine", "Splitt"],
                    opens=["Kante setzen"], notes="Maler kam dazu, mussten kurz unterbrechen.")
    run_id = d1.get("runId")
    if not run_id:
        failures.append("Folgebericht Tag 1: runId fehlt")
    d2 = _mk_report(pid, "Reihenhaus", date="2026-06-23", series=True,
                    acts=["Hecke geschnitten", "50 m² Pflaster verlegt"], mats=["Splitt"],
                    opens=["Abkehren"], emps=("Max",))
    if d2.get("runId") != run_id:
        failures.append("Folgebericht Tag 2: muss denselben Run fortsetzen")

    payload = get_collective_report(pid, runId=None, store=STORE)
    totals = payload.get("totals", {})

    if totals.get("reportCount") != 2:
        failures.append(f"Gesamtbericht: reportCount falsch (got={totals.get('reportCount')})")
    # Einzelbericht (kein Run) darf NICHT enthalten sein
    if any(dd.get("date") == "2026-06-19" for dd in payload.get("days", [])):
        failures.append("Gesamtbericht: Einzelbericht faelschlich enthalten")
    # Material-Dedupe ueber beide Tage
    mats = [m.casefold() for m in totals.get("materials", [])]
    if sorted(mats) != ["pflastersteine", "splitt"]:
        failures.append(f"Gesamtbericht: Material-Dedupe falsch (got={totals.get('materials')})")
    # Offene Punkte beider Tage
    if len(totals.get("openItems", [])) != 2:
        failures.append(f"Gesamtbericht: offene Punkte falsch (got={totals.get('openItems')})")
    # Stunden je Mitarbeiter: Max 2 Tage, Goran 1 Tag
    by_emp = {e["name"]: e["hours"] for e in totals.get("hoursByEmployee", [])}
    # 07:00-16:00 = 9h - 45min Pause = 8.25h pro Tag
    if abs(by_emp.get("Max", 0) - 16.5) > 0.01:
        failures.append(f"Stunden Max falsch (got={by_emp.get('Max')})")
    if abs(by_emp.get("Goran", 0) - 8.25) > 0.01:
        failures.append(f"Stunden Goran falsch (got={by_emp.get('Goran')})")
    # Notiz erhalten
    if not any("Maler" in (dd.get("notes") or "") for dd in payload.get("days", [])):
        failures.append("Gesamtbericht: Notiz (Besonderheit) fehlt")
    # Zeitraum
    if payload.get("dateFrom") != "2026-06-22" or payload.get("dateTo") != "2026-06-23":
        failures.append(f"Zeitraum falsch (got={payload.get('dateFrom')}..{payload.get('dateTo')})")
    # Summary belastbar
    if not str(payload.get("summary") or "").strip() or payload.get("summary") == "Keine Angabe":
        failures.append("Gesamtbericht: Summary leer")

    # ---- Export-Builder (PDF/DOCX) erzeugen ----------------------------------
    from report_export import build_collective_pdf_bytes, build_collective_docx_bytes  # noqa: E402

    try:
        pdf = build_collective_pdf_bytes(payload, {"companyName": "Freiraum"})
        if not isinstance(pdf, (bytes, bytearray)) or len(pdf) < 800:
            failures.append(f"PDF-Builder: zu klein/leer (len={len(pdf) if pdf else 0})")
    except Exception as e:
        failures.append(f"PDF-Builder Exception: {e!r}")
    try:
        docx = build_collective_docx_bytes(payload, {"companyName": "Freiraum"})
        if not isinstance(docx, (bytes, bytearray)) or len(docx) < 800:
            failures.append(f"DOCX-Builder: zu klein/leer (len={len(docx) if docx else 0})")
    except Exception as e:
        failures.append(f"DOCX-Builder Exception: {e!r}")

    # ---- close-run -----------------------------------------------------------
    res = close_project_run(pid, store=STORE)
    if not res.get("ok") or res.get("project", {}).get("status") != "abgeschlossen":
        failures.append("close-run: Status nicht abgeschlossen")
    # Gesamtbericht nach Abschluss weiterhin abrufbar (ueber letzten Run)
    payload2 = get_collective_report(pid, runId=None, store=STORE)
    if payload2.get("totals", {}).get("reportCount") != 2:
        failures.append("Gesamtbericht nach Abschluss nicht mehr korrekt abrufbar")

    if failures:
        print("COLLECTIVE-REPORT-SMOKE: FEHLER")
        for f in failures:
            print(" -", f)
        return 1
    print("COLLECTIVE-REPORT-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
