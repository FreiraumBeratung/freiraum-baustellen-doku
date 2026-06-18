"""Welle 4: 150 ASR-Patzer-Faelle ueber alle aktiven Gewerke."""

from __future__ import annotations

import os
import re
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_virtual_asr_patzer_wave4_")))
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


def _to_case(
    base: BaseScenario,
    tag: str,
    raw: str,
    *,
    expect_problem: bool,
    expect_open: bool,
    expect_customer: bool,
) -> Case:
    return Case(
        name=f"{base.trade}_{tag}",
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


def _apply_noise(text: str, mode: str) -> str:
    out = text

    if mode in {"soft", "heavy", "dup", "context"}:
        replacements = (
            (r"\bHecke\b", "Ecke"),
            (r"\bhec?ke\b", "ecke"),
            (r"\bgedüngt\b", "gedungt"),
            (r"\bbewässert\b", "bewassert"),
            (r"\bDruckprüfung\b", "Druckprufung"),
            (r"\bFugenmörtel\b", "Fugen mortel"),
            (r"\bGroßformatfliesen\b", "Grossformat Fliesen"),
            (r"\bGeotextil\b", "Geotextiel"),
            (r"\bSchimmel\b", "Schimel"),
            (r"\bBewehrung\b", "Bewahrung"),
        )
        for pattern, repl in replacements:
            out = re.sub(pattern, repl, out, flags=re.IGNORECASE)

    if mode == "heavy":
        out = re.sub(r"\bdanach\b", "danach danach", out, flags=re.IGNORECASE)
        out = re.sub(r"\bhaben wir\b", "ham wa", out, flags=re.IGNORECASE)

    if mode == "dup":
        out = re.sub(r"\bdanach\b", "danach danach", out, flags=re.IGNORECASE)

    if mode == "compact":
        out = out.lower()
        out = re.sub(r"\s+", " ", out).strip()
        out = f"heute wir haben so gemacht: {out}"

    return out


def _build_cases() -> list[Case]:
    bases = _base_scenarios()
    cases: list[Case] = []

    variants = [
        ("A", "soft", False, False, False),
        ("B", "heavy", False, False, False),
        ("C", "context", True, True, True),
        ("D", "dup", False, False, False),
        ("E", "compact", False, False, False),
    ]

    running = 1
    for suffix, mode, exp_problem, exp_open, exp_customer in variants:
        for base in bases:
            noisy = _apply_noise(base.raw, mode)
            if mode == "context":
                noisy = (
                    f"{noisy} Kunde meinte passt soweit. "
                    "Problem: Material fehlt teilweise und Zufahrt war blockiert. "
                    "Offen: Rest morgen nachziehen und mit Bauleitung abstimmen."
                )
            tag = f"{running:03d}_{suffix}"
            cases.append(
                _to_case(
                    base,
                    tag,
                    noisy,
                    expect_problem=exp_problem,
                    expect_open=exp_open,
                    expect_customer=exp_customer,
                )
            )
            running += 1

    # 5 Varianten x 28 Basisszenarien = 140, plus 10 Zusatzfaelle.
    extra_bases = bases[:10]
    for idx, base in enumerate(extra_bases, start=1):
        noisy = _apply_noise(base.raw, "heavy")
        noisy = f"kurz durchsage ohne pause {noisy} problem material knapp offen rest morgen"
        cases.append(
            _to_case(
                base,
                f"{140 + idx:03d}_F",
                noisy,
                expect_problem=True,
                expect_open=True,
                expect_customer=False,
            )
        )

    return cases[:150]


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    cases = _build_cases()
    failures: list[str] = []

    for case in cases:
        body = StructureReportBody(
            projectId="p-wave4-asr",
            projectName="ASR Patzer Matrix",
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
        print("VIRTUAL-SPEECH-ASR-PATZER-WAVE4-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:340]:
            print(" -", row)
        if len(failures) > 340:
            print(f" ... weitere {len(failures) - 340} Fehler gekuerzt")
        return 1

    print("VIRTUAL-SPEECH-ASR-PATZER-WAVE4-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

