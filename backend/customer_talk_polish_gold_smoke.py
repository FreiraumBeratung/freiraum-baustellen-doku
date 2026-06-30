"""P2 Gold-Smoke: Kundengespräch — Isolation, deterministischer Satz, optional KI-Polish.

Prüft Guards offline und die volle Pipeline mit/ohne OPENAI_API_KEY.
Rein additiv — keine bestehenden Wellen ändern.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from app.services.customer_talk_builder import (  # noqa: E402
    enrich_thin_customer_talk,
    extract_customer_talk_from_text,
)
from app.services.customer_talk_guard import customer_talk_polish_is_safe  # noqa: E402
from services.ai_report_service import polish_customer_talk_with_ai  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_customer_polish_gold_")))
_STORE = TenantStore(str(uuid.uuid4()))
_SAVED_KEY = os.environ.get("OPENAI_API_KEY", "")


def _fail(msg: str, failures: list[str]) -> None:
    failures.append(msg)


def _has_communication_context(text: str) -> bool:
    low = text.casefold()
    return any(
        token in low
        for token in (
            "gesprochen",
            "unterhalten",
            "kundengespräch",
            "kundengespraech",
            "informiert",
            "abgestimmt",
            "rücksprache",
            "ruecksprache",
            "gespräch",
            "gespraech",
        )
    )


def _guard_unit_tests(failures: list[str]) -> None:
    raw = (
        "Heute haben wir 50 qm2 Pflaster verlegt. "
        "Anschliessend mit der Kundin gesprochen sie war zufrieden."
    )
    thin = "Die Kundin war zufrieden."
    enriched = enrich_thin_customer_talk(thin, raw, gender="f")
    if not _has_communication_context(enriched):
        _fail(f"Enrich: Gesprächskontext fehlt (got={enriched!r})", failures)
    if "pflaster" in enriched.casefold() or "50" in enriched:
        _fail(f"Enrich: Arbeitstext durchgerutscht (got={enriched!r})", failures)

    raw2 = "Kundengespräch gehabt Pflastermuster gewählt Problem Drainage."
    ext = extract_customer_talk_from_text(raw2)
    if "gehabt" in ext.casefold():
        _fail(f"Extract: 'gehabt' sollte zu 'geführt' werden (got={ext!r})", failures)
    if "pflastermuster" not in ext.casefold():
        _fail(f"Extract: Pflastermuster fehlt (got={ext!r})", failures)

    det = "Mit der Kundin gesprochen; sie ist sehr zufrieden."
    if customer_talk_polish_is_safe(
        "Mit der Kundin wurde gesprochen, sie ist sehr zufrieden.",
        det,
        raw_text=raw,
    ) is not True:
        _fail("Guard: sauberer Polish-Text sollte akzeptiert werden", failures)
    if customer_talk_polish_is_safe(
        "Heute 50 m² Pflaster verlegt und Kundin zufrieden.",
        det,
        raw_text=raw,
    ) is not False:
        _fail("Guard: Arbeitstext im Polish muss abgelehnt werden", failures)
    if customer_talk_polish_is_safe(
        "Die Kundin ist verärgert und unzufrieden.",
        det,
        raw_text=raw,
    ) is not False:
        _fail("Guard: verlorenes Fakt 'zufrieden' muss abgelehnt werden", failures)


def _pipeline_offline(failures: list[str]) -> None:
    os.environ["OPENAI_API_KEY"] = ""
    cases = [
        (
            "pflaster_kundin_runon",
            (
                "Heute haben wir 50 qm² pflaster gelegt und anschließend haben wir uns mit der Kundin "
                "unterhalten und die Kundin war sehr zufrieden und freut sich auf weitere Aufträge mit uns."
            ),
            ("Kundin", "zufrieden", "Aufträge"),
            ("50", "pflaster", "m²"),
        ),
        (
            "pflaster_kundin_punkt",
            (
                "Heute haben wir 50 qm² pflaster gelegt. Anschließend haben wir uns mit der Kundin "
                "unterhalten und die Kundin war sehr zufrieden."
            ),
            ("Kundin", "zufrieden"),
            ("50", "pflaster gelegt", "qm"),
        ),
        (
            "kunde_masculine",
            "Mit dem Kunden gesprochen, er war sehr zufrieden und möchte weiter mit uns arbeiten.",
            ("Kunde", "zufrieden"),
            ("pflaster", "m²"),
        ),
    ]
    for name, raw, must, forbid in cases:
        body = StructureReportBody(
            projectId="p2",
            projectName="GaLaBau Test",
            customerName="Musterkunde",
            date="2026-06-30",
            employeeNames=["Max"],
            startTime="06:00",
            endTime="18:00",
            exportFormat="PDF",
            rawText=raw,
        )
        structured = (api_structure_report(body, store=_STORE).get("structured") or {})
        customer = str(structured.get("customerTalk") or "").strip()
        summary = str(structured.get("summary") or "").strip()
        if not customer or customer.casefold() == "keine angabe":
            _fail(f"{name}: customerTalk leer (got={customer!r})", failures)
        for token in must:
            if token.casefold() not in customer.casefold():
                _fail(f"{name}: fehlt {token!r} (got={customer!r})", failures)
        for token in forbid:
            if token.casefold() in customer.casefold():
                _fail(f"{name}: verboten {token!r} (got={customer!r})", failures)
        if summary and customer.casefold() == summary.casefold():
            _fail(f"{name}: customerTalk ist Summary-Kopie", failures)
        if "gesprochen" in raw.casefold() or "unterhalten" in raw.casefold():
            if not _has_communication_context(customer):
                _fail(f"{name}: Gesprächskontext fehlt im Ergebnis (got={customer!r})", failures)


def _pipeline_with_key_if_available(failures: list[str]) -> None:
    key = (_SAVED_KEY or "").strip()
    if not key:
        print("CUSTOMER-TALK-POLISH-GOLD: OPENAI_API_KEY nicht gesetzt — KI-Polish-Skip")
        return

    os.environ["OPENAI_API_KEY"] = key
    raw = (
        "Heute haben wir 50 qm2 Pflaster verlegt. "
        "Anschliessend mit der Kundin gesprochen sie war zufrieden."
    )
    body = StructureReportBody(
        projectId="p2-ai",
        projectName="Schmitz Aussenanlage",
        customerName="Test",
        date="2026-06-29",
        employeeNames=["M"],
        startTime="08:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    structured = (api_structure_report(body, store=_STORE).get("structured") or {})
    customer = str(structured.get("customerTalk") or "").strip()
    summary = str(structured.get("summary") or "").strip()
    if not customer:
        _fail("KI-Pipeline: customerTalk leer", failures)
    if "pflaster" in customer.casefold() or re.search(r"\b50\b", customer):
        _fail(f"KI-Pipeline: Arbeitstext in customerTalk (got={customer!r})", failures)
    if summary and customer.casefold() == summary.casefold():
        _fail("KI-Pipeline: customerTalk ist Summary-Kopie", failures)
    if "zufrieden" not in customer.casefold():
        _fail(f"KI-Pipeline: Zufriedenheit fehlt (got={customer!r})", failures)

    det = extract_customer_talk_from_text(raw)
    polished = polish_customer_talk_with_ai(
        {"customerTalk": det, "summary": summary},
        raw_text=raw,
    )
    if polished is not None:
        if "pflaster" in polished.casefold():
            _fail(f"polish_customer_talk_with_ai: Arbeitstext (got={polished!r})", failures)
        if len(re.split(r"(?<=[.!?])\s+", polished.strip())) > 2:
            _fail(f"polish_customer_talk_with_ai: mehr als 2 Sätze (got={polished!r})", failures)


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
        print("CUSTOMER-TALK-POLISH-GOLD: FEHLER")
        for f in failures:
            print(" -", f)
        return 1
    print("CUSTOMER-TALK-POLISH-GOLD: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
