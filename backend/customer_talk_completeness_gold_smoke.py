"""Gold-Smoke: Kundengespräch-Vollständigkeit — Nutzer-Beispiel + Guards.

Permanent verankertes Live-Beispiel (GaLaBau Run-on mit reichem Kundentail).
Rein additiv.
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
from app.services.customer_talk_builder import extract_customer_talk_from_text  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_customer_completeness_gold_")))
_STORE = TenantStore(str(uuid.uuid4()))

USER_EXAMPLE_RAW = (
    "Heute haben wir 50 Quadratmeter Pflaster gelegt 5 Quadratmeter Gartenmauer gebaut "
    "und danach haben wir 15 Meter Hecke geschnitten Nach den Arbeiten haben wir uns "
    "mit der Kundin unterhalten und die Kundinnen hat unsere Arbeit gelobt und freut "
    "sich auf weitere Auftraege und wird uns bei ihren Kollegen und Freunden weiterempfehlen."
)


def _fail(msg: str, failures: list[str]) -> None:
    failures.append(msg)


def _must_contain(text: str, *tokens: str) -> bool:
    low = text.casefold()
    return all(t.casefold() in low for t in tokens)


def _must_not_contain(text: str, *tokens: str) -> bool:
    low = text.casefold()
    return not any(t.casefold() in low for t in tokens)


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["FREIRAUM_AI_STRUCTURING"] = ""
    failures: list[str] = []

    # Deterministischer Extract
    customer_det = extract_customer_talk_from_text(USER_EXAMPLE_RAW)
    if not customer_det or len(customer_det) < 80:
        _fail(f"Extract zu kurz (got={customer_det!r})", failures)
    if "; ;" in customer_det:
        _fail(f"Doppel-Semikolon (got={customer_det!r})", failures)
    if not _must_contain(customer_det, "gelobt", "weiterempfehl") or "auftrae" not in customer_det.casefold():
        _fail(f"Reicher Kundentail fehlt (got={customer_det!r})", failures)
    if not _must_not_contain(customer_det, "50", "pflaster", "gartenmauer", "hecke", "quadratmeter"):
        _fail(f"Arbeitstext in customerTalk (got={customer_det!r})", failures)
    if re.search(r"\bkundinnen\b", customer_det, re.I):
        _fail(f"Tippfehler Kundinnen (got={customer_det!r})", failures)

    # Volle Pipeline
    body = StructureReportBody(
        projectId="customer-completeness-gold",
        projectName="GaLaBau Gold",
        customerName="Testkunde",
        date="2026-07-29",
        employeeNames=["Max"],
        startTime="07:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=USER_EXAMPLE_RAW,
    )
    structured = (api_structure_report(body, store=_STORE).get("structured") or {})
    customer = str(structured.get("customerTalk") or "")
    summary = str(structured.get("summary") or "")

    if not _must_contain(customer, "gelobt", "weiterempfehl"):
        _fail(f"Pipeline customerTalk unvollständig (got={customer!r})", failures)
    if not _must_not_contain(customer, "50", "pflaster", "hecke"):
        _fail(f"Pipeline Arbeit in customerTalk (got={customer!r})", failures)
    if not summary or "pflaster" not in summary.casefold():
        _fail(f"Pipeline summary ohne Arbeiten (got={summary!r})", failures)
    thin = re.match(r"^(mit der kundin gesprochen)\.?$", customer.casefold().strip())
    if thin:
        _fail(f"Pipeline nur Dünnsatz (got={customer!r})", failures)

    if failures:
        print("CUSTOMER-TALK-COMPLETENESS-GOLD-SMOKE: FEHLER")
        for row in failures:
            print(" -", row)
        return 1

    print("CUSTOMER-TALK-COMPLETENESS-GOLD-SMOKE: OK")
    print(f"customerTalk={customer!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
