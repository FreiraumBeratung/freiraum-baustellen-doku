"""Gemeinsame Infrastruktur für Straßenbau-Virtual-Speech-Smokes (Wellen 26–28)."""

from __future__ import annotations

import os
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402
from strassenbau_wave_scenarios import StrassenbauScenario  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_strassenbau_wave_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class Case:
    name: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...]
    expect_material_suggestions: tuple[str, ...]
    expect_machine_suggestions: tuple[str, ...]
    forbid_activities: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool
    min_activity_count: int


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def _has_customer_talk(text: str) -> bool:
    low = text.casefold()
    return any(
        h in low
        for h in (
            "kund",
            "bauherr",
            "bauleitung",
            "auftraggeber",
            "gesprochen",
            "gred",
            "informiert",
            "abgestimmt",
            "abgesprochen",
            "zufrieden",
            "weiterempfehl",
            "rücksprache",
            "ruecksprache",
            "stadt",
            "happy",
        )
    )


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bAsphalt\b", "asphalt"),
        (r"\bFrostschutz\b", "frost schutz"),
        (r"\bFrostschutzschicht\b", "frost schutz schicht"),
        (r"\bSchottertragschicht\b", "schot ter trag schicht"),
        (r"\bBitumenemulsion\b", "bitu men emulsion"),
        (r"\bHochbord\b", "hoch bord"),
        (r"\bRinnensteine\b", "rinnen steine"),
        (r"\bKaltfräse\b", "kalt fräse"),
        (r"\bKG-Rohre\b", "ka ga rohre"),
        (r"\blaufende Meter\b", "lauf ende meter"),
        (r"\bQuadratmeter\b", "quadrat meter"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bverlegt\b", "ver legt"),
        (r"\bverfüllt\b", "ver füllt"),
        (r"\bverdichtet\b", "ver dichtet"),
        (r"\basphaltiert\b", "asphalt iert"),
        (r"\bgeschnitten\b", "ge schnitten"),
        (r"\bfräsen\b", "frä sen"),
        (r"\bä", "ae"),
        (r"\bö", "oe"),
        (r"\bü", "ue"),
        (r"\bß", "ss"),
    )
    for pat, repl in extra:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out


def _broken_de(text: str) -> str:
    out = text
    for a, b in (
        ("haben wir", "hamma"),
        ("Heute", "heute"),
        ("durchgeführt", "durch gemacht"),
        ("verlegt", "ver legt"),
        ("gesprochen", "gred"),
        ("Problem:", "problem is"),
        ("Offen:", "offen is"),
        ("Asphalt", "asphalt"),
    ):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKunde\b", "Kund", out, flags=re.IGNORECASE)
    out = re.sub(r"\bdann\b", "denn", out, flags=re.IGNORECASE, count=6)
    return out


def _mega_runon(text: str) -> str:
    core = re.sub(r"[.!?]+\s*", " und also ", text)
    return (
        f"Ja also vom Tag her {core} und genau und dann Feierabend "
        f"und morgen machen wir den Rest wenn Material da ist."
    )


def build_cases(
    bases: list[StrassenbauScenario],
    *,
    prefix: str,
) -> list[Case]:
    builders: list[tuple[str, Callable[[str], str]]] = [
        ("N", lambda t: t),
        ("W", _whisper_light),
        ("H", _whisper_hard),
        ("B", _broken_de),
        ("D", _dialect_de),
        ("M", _mega_runon),
    ]
    cases: list[Case] = []
    idx = 1
    for tag, builder in builders:
        for base in bases:
            raw = builder(base.raw)
            min_count = (
                base.min_activity_count if base.min_activity_count is not None else len(base.expect_activities)
            )
            cases.append(
                Case(
                    name=f"{prefix}_{idx:03d}_{tag}",
                    raw=raw,
                    expect_activities=base.expect_activities,
                    expect_materials=base.expect_materials,
                    expect_material_suggestions=base.expect_material_suggestions,
                    expect_machine_suggestions=base.expect_machine_suggestions,
                    forbid_activities=base.forbid_activities,
                    expect_problem=base.expect_problem,
                    expect_open=base.expect_open,
                    expect_customer=base.expect_customer,
                    min_activity_count=min_count,
                )
            )
            idx += 1
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="sb-wave",
        projectName="Straßenbau Smoke",
        customerName="Testkunde",
        date="2026-07-28",
        employeeNames=["Max", "Goran", "Ahmet", "Stefan", "Murat", "Dennis"],
        startTime="06:00",
        endTime="18:00",
        exportFormat="PDF",
        rawText=case.raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


def run_smoke(cases: list[Case], label: str) -> int:
    os.environ["OPENAI_API_KEY"] = ""
    failures: list[str] = []

    for case in cases:
        structured = _run_case(case)
        acts = [str(x) for x in (structured.get("activities") or [])]
        mats = [str(x) for x in (structured.get("materials") or [])]
        suggs = [str(x) for x in (structured.get("materialSuggestions") or [])]
        machine_suggs = [str(x) for x in (structured.get("machineSuggestions") or [])]
        probs = [str(x) for x in (structured.get("problems") or [])]
        opens = [str(x) for x in (structured.get("openItems") or [])]
        customer = str(structured.get("customerTalk") or "")
        summary = str(structured.get("summary") or "")

        if len(acts) < case.min_activity_count:
            failures.append(
                f"{case.name}: zu wenige Tätigkeiten ({len(acts)} < {case.min_activity_count}) got={acts!r}"
            )
        for expected in case.expect_activities:
            if not _contains_any(acts, expected):
                failures.append(f"{case.name}: activity fehlt -> {expected} (got={acts!r})")
        for expected in case.expect_materials:
            if not _contains_any(mats, expected):
                failures.append(f"{case.name}: material fehlt -> {expected} (got={mats!r})")
        for expected in case.expect_material_suggestions:
            if not _contains_any(suggs, expected):
                failures.append(f"{case.name}: materialSuggestion fehlt -> {expected} (got={suggs!r})")
        for expected in case.expect_machine_suggestions:
            if not _contains_any(machine_suggs, expected):
                failures.append(f"{case.name}: machineSuggestion fehlt -> {expected} (got={machine_suggs!r})")
        for forbidden in case.forbid_activities:
            if _contains_any(acts, forbidden):
                failures.append(f"{case.name}: activity verboten -> {forbidden}")

        if acts and (not summary or len(summary.strip()) < 10):
            failures.append(f"{case.name}: summary leer/zu kurz (got={summary!r})")

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer")
        if case.expect_customer and not _has_customer_talk(customer):
            failures.append(f"{case.name}: customerTalk fehlt (got={customer!r})")

    if failures:
        print(f"{label}: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print(f"{label}: OK")
    print(f"Total cases: {len(cases)}")
    return 0
