"""Welle 32: PANZEK-Pilot GaLaBau + Tiefbau + Straßenbau — 150 × 6 = 900.

PANZEK-Tagesstunden-Sphäre: Planum, Graben/Kabel, Entsorgung, LKW, Maschinenstunden.
"""

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
from pilot_gala_tief_strasse_wave32_scenarios import all_base_scenarios  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_pilot_wave32_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class Case:
    name: str
    trade: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...]
    expect_machine_hours: tuple[str, ...]
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
            "termin",
            "einverstanden",
            "lehnen",
        )
    )


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bAsphalt\b", "asphalt"),
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\blaufende Meter\b", "lauf ende meter"),
        (r"\bRandsteine\b", "rand steine"),
        (r"\bDrainagerohr\b", "drainage rohr"),
        (r"\bNoppenbahn\b", "noppen bahn"),
        (r"\bDickbeschichtung\b", "dick beschichtung"),
        (r"\bSchotterplanum\b", "schotter planum"),
        (r"\bErdplanum\b", "erd planum"),
        (r"\bTOK-Band\b", "tok band"),
        (r"\bWasserleitung\b", "wasser leitung"),
        (r"\bZementmörtel\b", "zement moertel"),
        (r"\bBauschutt\b", "bau schutt"),
        (r"\bBodenaushub\b", "boden aushub"),
        (r"\bGehwegpflaster\b", "geh weg pflaster"),
        (r"\bMerkstein\b", "merk stein"),
        (r"\bFallrohre\b", "fall rohre"),
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
        (r"\bgehäckselt\b", "ge haeck selt"),
        (r"\beingesandet\b", "ein ge sandet"),
        (r"\babgedichtet\b", "ab ge dichtet"),
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
        ("Problem:", "problem is"),
        ("Offen:", "offen is"),
        ("Asphalt", "asphalt"),
        ("Pflaster", "pflaster"),
        ("gesprochen", "gred"),
        ("entsorgt", "entsorgt"),
    ):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKunde\b", "Kund", out, flags=re.IGNORECASE)
    return out


def _mega_runon(text: str) -> str:
    core = re.sub(r"[.!?]+\s*", " und also ", text)
    return (
        f"Ja also vom Tag her {core} und genau und dann Feierabend "
        f"und morgen machen wir den Rest wenn Material da ist."
    )


def _build_cases() -> list[Case]:
    builders: list[tuple[str, Callable[[str], str]]] = [
        ("N", lambda t: t),
        ("W", _whisper_light),
        ("H", _whisper_hard),
        ("B", _broken_de),
        ("D", _dialect_de),
        ("M", _mega_runon),
    ]
    cases: list[Case] = []
    per: dict[str, int] = {}
    for trade, spec in all_base_scenarios():
        per[trade] = per.get(trade, 0) + 1
        idx = per[trade]
        acts = tuple(spec.get("acts") or ())
        min_count = spec["min_act"] if spec.get("min_act") is not None else len(acts)
        for tag, fn in builders:
            cases.append(
                Case(
                    name=f"Pilot32_{trade}_{idx:03d}_{tag}",
                    trade=trade,
                    raw=fn(spec["raw"]),
                    expect_activities=acts,
                    expect_materials=tuple(spec.get("mats") or ()),
                    expect_machine_hours=tuple(spec.get("mach") or ()),
                    forbid_activities=tuple(spec.get("forbid_acts") or ()),
                    expect_problem=bool(spec.get("problem")),
                    expect_open=bool(spec.get("open_")),
                    expect_customer=bool(spec.get("customer")),
                    min_activity_count=min_count,
                )
            )
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="pilot-wave32",
        projectName=f"PANZEK W32 {case.trade}",
        customerName="Lehnen",
        date="2026-06-17",
        employeeNames=["Manush", "Egzon", "Ben", "Stefan"],
        startTime="06:15",
        endTime="18:15",
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
        machine_hours = [str(x) for x in (structured.get("machineHours") or [])]
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
        for expected in case.expect_machine_hours:
            if not _contains_any(machine_hours, expected):
                failures.append(f"{case.name}: maschinenstunden fehlen -> {expected} (got={machine_hours!r})")
        for forbidden in case.forbid_activities:
            if _contains_any(acts, forbidden):
                failures.append(f"{case.name}: activity verboten -> {forbidden}")

        if acts and case.min_activity_count > 0 and (not summary or len(summary.strip()) < 8):
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
        for row in failures[:400]:
            print(" -", row)
        if len(failures) > 400:
            print(f" ... und {len(failures) - 400} weitere")
        return 1

    print(f"{label}: OK")
    print(f"Total cases: {len(cases)}")
    return 0


def main() -> int:
    cases = _build_cases()
    return run_smoke(cases, "VIRTUAL-SPEECH-PILOT-GALA-TIEF-STRASSE-WAVE32-SMOKE")


if __name__ == "__main__":
    raise SystemExit(main())
