"""Smoke: Kundengespräch-Isolation — nur Kundeninhalt, nicht Summary/Arbeit."""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_customer_talk_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class Case:
    name: str
    raw: str
    must_contain: tuple[str, ...]
    must_not_contain: tuple[str, ...] = ()
    expect_customer: bool = True


def _cases() -> list[Case]:
    return [
        Case(
            "pflaster_kundin_punkt",
            (
                "Heute haben wir 50 qm² pflaster gelegt. Anschließend haben wir uns mit der Kundin "
                "unterhalten und die Kunden war sehr zufrieden und freut sich auf weitere Aufträge mit uns."
            ),
            ("Kundin", "zufrieden", "weitere Aufträge"),
            ("50", "pflaster gelegt", "qm"),
        ),
        Case(
            "pflaster_kundin_runon",
            (
                "Heute haben wir 50 qm² pflaster gelegt und anschließend haben wir uns mit der Kundin "
                "unterhalten und die Kundin war sehr zufrieden und freut sich auf weitere Aufträge mit uns."
            ),
            ("Kundin", "zufrieden"),
            ("50", "pflaster", "m²"),
        ),
        Case(
            "kunde_masculine",
            "Mit dem Kunden gesprochen, er war sehr zufrieden und möchte weiter mit uns arbeiten.",
            ("Kunde", "zufrieden"),
            ("pflaster", "m²"),
        ),
        Case(
            "kundin_only",
            "Die Kundin ist sehr zufrieden und freut sich auf weitere Aufträge.",
            ("Kundin", "zufrieden"),
            (),
        ),
        Case(
            "no_customer",
            "Heute 40 Quadratmeter Pflaster verlegt und Feierabend.",
            (),
            ("Kundin", "Kunde"),
            expect_customer=False,
        ),
    ]


def _contains_any(haystack: str, needle: str) -> bool:
    return needle.casefold() in haystack.casefold()


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["FREIRAUM_AI_STRUCTURING"] = ""
    failures: list[str] = []

    for case in _cases():
        body = StructureReportBody(
            projectId="ct-smoke",
            projectName="GaLaBau Test",
            customerName="Musterkunde",
            date="2026-06-30",
            employeeNames=["Max"],
            startTime="06:00",
            endTime="18:00",
            exportFormat="PDF",
            rawText=case.raw,
        )
        structured = (api_structure_report(body, store=_STORE).get("structured") or {})
        customer = str(structured.get("customerTalk") or "").strip()
        summary = str(structured.get("summary") or "").strip()

        if case.expect_customer:
            if not customer or customer.casefold() == "keine angabe":
                failures.append(f"{case.name}: customerTalk leer (got={customer!r})")
            for token in case.must_contain:
                if not _contains_any(customer, token):
                    failures.append(f"{case.name}: customerTalk fehlt {token!r} (got={customer!r})")
            for token in case.must_not_contain:
                if _contains_any(customer, token):
                    failures.append(f"{case.name}: customerTalk enthält verboten {token!r} (got={customer!r})")
            if summary and customer.casefold() == summary.casefold():
                failures.append(f"{case.name}: customerTalk ist Summary-Kopie")
        else:
            if customer.casefold() not in {"", "keine angabe"} and _contains_any(customer, "kund"):
                failures.append(f"{case.name}: customerTalk unerwartet (got={customer!r})")

    if failures:
        print("CUSTOMER-TALK-ISOLATION-SMOKE: FEHLER")
        for row in failures:
            print(" -", row)
        return 1

    print("CUSTOMER-TALK-ISOLATION-SMOKE: OK")
    print(f"Total cases: {len(_cases())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
