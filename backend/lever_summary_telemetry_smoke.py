"""Smoke fuer Hebel 1 (KI-Zusammenfassung mit Fallback) und Hebel 2 (Telemetrie).

Laeuft offline (ohne OPENAI_API_KEY): prueft die Sicherheits-Invarianten, ohne die
OpenAI-API aufzurufen.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report, _ai_structuring_enabled  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from app.services.activity_canonicalizer import collect_unmatched_chunks  # noqa: E402
from app.services.speech_telemetry import record_unmatched_speech  # noqa: E402
from services.ai_report_service import polish_summary_with_ai, _polished_summary_is_safe  # noqa: E402
from services.ai_report_service import polish_customer_talk_with_ai  # noqa: E402
from services.ai_report_service import polish_problem_open_with_ai  # noqa: E402
from app.services.problem_open_guard import problem_item_polish_is_safe  # noqa: E402
from app.services.customer_talk_guard import customer_talk_polish_is_safe  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_lever_smoke_")))
_STORE = TenantStore(str(uuid.uuid4()))


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    failures: list[str] = []

    # ---- Hebel 1: ohne Key -> None (deterministische Summary bleibt) -------------
    structured = {
        "activities": ["50 m² Pflaster verlegt", "Hecke geschnitten"],
        "materials": ["Pflastersteine"],
        "summary": "20.06.2026: Auf der Baustelle wurden 50 m² Pflaster verlegt.",
    }
    if polish_summary_with_ai(structured, {"date": "2026-06-20", "projectName": "Test"}) is not None:
        failures.append("Hebel1: ohne Key sollte None liefern")

    # ---- Hebel 1: Zahlen-Waechter -----------------------------------------------
    acts = ["50 m² Pflaster verlegt", "Hecke geschnitten"]
    mats = ["Pflastersteine"]
    det = "20.06.2026: Auf der Baustelle wurden 50 m² Pflaster verlegt."
    if _polished_summary_is_safe(
        "Am 20.06.2026 wurden 50 m² Pflaster verlegt und die Hecke geschnitten.", acts, mats, det
    ) is not True:
        failures.append("Hebel1: sauberer Text sollte akzeptiert werden")
    if _polished_summary_is_safe(
        "Es wurden 80 m² Pflaster verlegt und 3 Bäume gesetzt.", acts, mats, det
    ) is not False:
        failures.append("Hebel1: erfundene Zahl (80/3) muss abgelehnt werden")
    if _polished_summary_is_safe("zu kurz", acts, mats, det) is not False:
        failures.append("Hebel1: zu kurzer Text muss abgelehnt werden")
    if _polished_summary_is_safe('{"summary":"x"}', acts, mats, det) is not False:
        failures.append("Hebel1: JSON-Artefakt muss abgelehnt werden")
    if _polished_summary_is_safe(
        "Es wurden 50 m² Pflaster verlegt. Hierbei kamen Pflastersteine zum Einsatz.",
        acts,
        mats,
        det,
    ) is not False:
        failures.append("Hebel1: Material-Echo in Summary muss abgelehnt werden")

    # ---- Hebel 3: Kundengespraech ohne Key -> None --------------------------------
    ct_structured = {
        "customerTalk": "Mit der Kundin gesprochen; sie ist sehr zufrieden.",
        "summary": det,
    }
    if polish_customer_talk_with_ai(ct_structured, raw_text="Mit der Kundin gesprochen.") is not None:
        failures.append("Hebel3: ohne Key sollte None liefern")
    if customer_talk_polish_is_safe(
        "Mit der Kundin wurde ein kurzes Gespräch geführt; sie ist sehr zufrieden.",
        ct_structured["customerTalk"],
        raw_text="Mit der Kundin gesprochen, sie war zufrieden.",
    ) is not True:
        failures.append("Hebel3: sauberer Kundentext sollte akzeptiert werden")
    if customer_talk_polish_is_safe(
        "50 m² Pflaster verlegt, Kundin zufrieden.",
        ct_structured["customerTalk"],
        raw_text="Mit der Kundin gesprochen.",
    ) is not False:
        failures.append("Hebel3: Arbeitstext im Kundengespraech muss abgelehnt werden")

    # ---- Hebel 4: Problem/Offen ohne Key -> None -------------------------
    po_structured = {
        "problems": ["Lieferung kam verspätet."],
        "openItems": ["Letzte Reihe morgen noch offen."],
    }
    if polish_problem_open_with_ai(po_structured, raw_text="problem lieferung offen reihe") is not None:
        failures.append("Hebel4: ohne Key sollte None liefern")
    if problem_item_polish_is_safe(
        "Die Lieferung kam verspätet.",
        po_structured["problems"][0],
        raw_text="problem lieferung kam spaet",
    ) is not True:
        failures.append("Hebel4: sauberer Problemtext sollte akzeptiert werden")
    if problem_item_polish_is_safe(
        "50 m² Pflaster verlegt und Lieferung spät.",
        po_structured["problems"][0],
        raw_text="problem lieferung",
    ) is not False:
        failures.append("Hebel4: Arbeitstext im Problem muss abgelehnt werden")

    # ---- Hebel 1: ohne Key bleibt die Summary im vollen Pipeline-Lauf erhalten ---
    body = StructureReportBody(
        projectId="p", projectName="Test", customerName="K", date="2026-06-20",
        employeeNames=["Max"], startTime="07:00", endTime="16:00", exportFormat="PDF",
        rawText="Heute 50 Quadratmeter Pflaster verlegt und Hecke geschnitten.",
    )
    out = api_structure_report(body, store=_STORE)
    summary = str((out.get("structured") or {}).get("summary") or "")
    if not summary or summary == "Keine Angabe":
        failures.append(f"Hebel1: Pipeline-Summary leer (got={summary!r})")

    # ---- KI-Strukturierung: Opt-in-Schalter, Standard AUS -----------------------
    os.environ.pop("FREIRAUM_AI_STRUCTURING", None)
    if _ai_structuring_enabled() is not False:
        failures.append("Schalter: KI-Strukturierung muss standardmaessig AUS sein")
    for on in ("1", "true", "yes", "on", "ON", "True"):
        os.environ["FREIRAUM_AI_STRUCTURING"] = on
        if _ai_structuring_enabled() is not True:
            failures.append(f"Schalter: '{on}' sollte einschalten")
    for off in ("0", "", "nein", "off"):
        os.environ["FREIRAUM_AI_STRUCTURING"] = off
        if _ai_structuring_enabled() is not False:
            failures.append(f"Schalter: '{off}' sollte AUS bleiben")
    os.environ.pop("FREIRAUM_AI_STRUCTURING", None)

    # ---- Hebel 2: erkannte Saetze -> keine Telemetrie ---------------------------
    if collect_unmatched_chunks("Heute 50 Quadratmeter Pflaster verlegt.") != []:
        failures.append("Hebel2: vollstaendig erkannter Satz darf nichts melden")

    # ---- Hebel 2: Kauderwelsch-Arbeitsversuch -> wird gemeldet ------------------
    unmatched = collect_unmatched_chunks("Heute foobar gemurkst und blabla zusammengeschustert.")
    if not unmatched:
        failures.append("Hebel2: unerkannter Arbeitsversuch sollte gemeldet werden")

    # ---- Hebel 2: record schreibt + deckelt, no-op bei leer ---------------------
    store2 = TenantStore(str(uuid.uuid4()))
    record_unmatched_speech(store2, raw_text="x", unmatched=[], meta={})
    if store2.read_json("speech_telemetry.json", None) is not None:
        failures.append("Hebel2: leere unmatched darf nichts schreiben")
    record_unmatched_speech(store2, raw_text="abc", unmatched=["foobar gemurkst"], meta={"date": "2026-06-20"})
    rows = store2.read_json("speech_telemetry.json", [])
    if not (isinstance(rows, list) and len(rows) == 1 and rows[0].get("unmatched") == ["foobar gemurkst"]):
        failures.append(f"Hebel2: Telemetrie-Eintrag fehlerhaft (got={rows!r})")

    if failures:
        print("LEVER-SUMMARY-TELEMETRY-SMOKE: FEHLER")
        for f in failures:
            print(" -", f)
        return 1
    print("LEVER-SUMMARY-TELEMETRY-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
