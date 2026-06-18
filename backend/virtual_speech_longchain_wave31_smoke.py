"""Welle 3.1: 200 Long-Chain-Faelle (additiv/defensiv)."""

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
from virtual_speech_longchain_wave3_smoke import BaseScenario, _base_scenarios  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_virtual_longchain_wave31_")))
_SMOKE_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class Case:
    name: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...]
    expect_suggestions: tuple[str, ...]
    forbid_activities: tuple[str, ...]
    forbid_suggestions: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool
    summary_contains: tuple[str, ...]


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def _to_case(base: BaseScenario, variant_tag: str, raw: str, *, expect_problem: bool, expect_open: bool, expect_customer: bool) -> Case:
    return Case(
        name=f"{base.trade}_{variant_tag}",
        raw=raw,
        expect_activities=base.expect_activities,
        expect_materials=base.expect_materials,
        expect_suggestions=base.expect_suggestions,
        forbid_activities=base.forbid_activities,
        forbid_suggestions=base.forbid_suggestions,
        expect_problem=expect_problem,
        expect_open=expect_open,
        expect_customer=expect_customer,
        summary_contains=base.summary_contains,
    )


def _build_cases() -> list[Case]:
    bases = _base_scenarios()
    cases: list[Case] = []

    variant_builders = [
        (
            "A",
            lambda text: text,
            False,
            False,
            False,
        ),
        (
            "B",
            lambda text: f"heute wir machen so: {text.lower()} dann alles fertig.",
            False,
            False,
            False,
        ),
        (
            "C",
            lambda text: (
                f"{text} Danach mit dem Kunden gesprochen, Kundin war zufrieden. "
                "Problem: Untergrund war uneben und Material fehlt. "
                "Offen bleibt, dass wir morgen nachbestellen und den Rest klären müssen."
            ),
            True,
            True,
            True,
        ),
        (
            "D",
            lambda text: f"Kurzprotokoll Schichtende: {text} Abschliessend Baustelle sauber uebergeben.",
            False,
            False,
            False,
        ),
        (
            "E",
            lambda text: f"{text} Problem: Lieferverzug bei Material und Untergrund teilweise nass.",
            True,
            False,
            False,
        ),
        (
            "F",
            lambda text: f"{text} Offen: Restmenge Material nachbestellen und Anschluss morgen finalisieren.",
            False,
            True,
            False,
        ),
        (
            "G",
            lambda text: f"{text} Kundengespraech gefuehrt, Kunde wuenscht gleiche Ausfuehrung im Nebenbereich.",
            False,
            False,
            True,
        ),
        (
            "H",
            lambda text: (
                f"{text} Danach Teambriefing gemacht, Materialbestand geprueft, Zeiten dokumentiert, "
                "Leistungsstand mit Bauleitung abgestimmt."
            ),
            False,
            False,
            False,
        ),
        (
            "I",
            lambda text: (
                f"{text} Problem: Zufahrt blockiert. Offen: Nachtrag mit Bauleitung klaeren. "
                "Mit dem Kunden gesprochen, Kunde informiert."
            ),
            True,
            True,
            True,
        ),
    ]

    # Varianten zuerst, dann Basisszenarien: so bleiben alle Gewerke breit vertreten.
    running_idx = 1
    for variant_tag, builder, exp_problem, exp_open, exp_customer in variant_builders:
        for base in bases:
            raw = builder(base.raw)
            tag = f"{running_idx:03d}_{variant_tag}"
            cases.append(
                _to_case(
                    base,
                    tag,
                    raw,
                    expect_problem=exp_problem,
                    expect_open=exp_open,
                    expect_customer=exp_customer,
                )
            )
            running_idx += 1

    return cases[:200]


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    cases = _build_cases()
    failures: list[str] = []

    for case in cases:
        body = StructureReportBody(
            projectId="p-wave31-long",
            projectName="Long Chain Matrix Wave 3.1",
            customerName="Testkunde",
            date="2026-06-18",
            employeeNames=["Max", "Ali", "Murat"],
            startTime="07:00",
            endTime="17:00",
            exportFormat="PDF",
            rawText=case.raw,
        )
        out = api_structure_report(body, store=_SMOKE_STORE)
        structured = out.get("structured") or {}
        acts = [str(x) for x in (structured.get("activities") or [])]
        mats = [str(x) for x in (structured.get("materials") or [])]
        suggs = [str(x) for x in (structured.get("materialSuggestions") or [])]
        probs = [str(x) for x in (structured.get("problems") or [])]
        opens = [str(x) for x in (structured.get("openItems") or [])]
        customer = str(structured.get("customerTalk") or "")
        summary = str(structured.get("summary") or "")

        for expected in case.expect_activities:
            if not _contains_any(acts, expected):
                failures.append(f"{case.name}: activity fehlt -> {expected} (got={acts!r})")
        for expected in case.expect_materials:
            if not _contains_any(mats, expected):
                failures.append(f"{case.name}: material fehlt -> {expected} (got={mats!r})")
        for expected in case.expect_suggestions:
            if not _contains_any(suggs, expected):
                failures.append(f"{case.name}: suggestion fehlt -> {expected} (got={suggs!r})")
        for forbidden in case.forbid_activities:
            if _contains_any(acts, forbidden):
                failures.append(f"{case.name}: activity verboten -> {forbidden} (got={acts!r})")
        for forbidden in case.forbid_suggestions:
            if _contains_any(suggs, forbidden):
                failures.append(f"{case.name}: suggestion verboten -> {forbidden} (got={suggs!r})")
        for needle in case.summary_contains:
            if needle.casefold() not in summary.casefold():
                failures.append(f"{case.name}: summary fehlt -> {needle} (summary={summary!r})")

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer trotz Problem-Text")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer trotz Offen-Text")
        if case.expect_customer and ("kund" not in customer.casefold()):
            failures.append(f"{case.name}: customerTalk leer trotz Kunden-Text (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-LONGCHAIN-WAVE31-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:320]:
            print(" -", row)
        if len(failures) > 320:
            print(f" ... weitere {len(failures) - 320} Fehler gekuerzt")
        return 1

    print("VIRTUAL-SPEECH-LONGCHAIN-WAVE31-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

