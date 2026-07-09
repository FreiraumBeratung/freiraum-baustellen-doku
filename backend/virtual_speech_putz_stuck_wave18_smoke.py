"""Welle 18: Putz & Stuck — 100 Basisszenarien × 6 = 600 Smoke-Fälle.

PANZEK-Style: kurz/lang, Whisper, gebrochenes Deutsch, Dialekt, Mega-Run-on.
Felder: Tätigkeiten, Materialien, Maschinenstunden, Problem, Offen, Kunde, Summary.
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
from putz_stuck_wave18_scenarios import all_base_scenarios  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_putz_stuck_wave18_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class Case:
    name: str
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
            "happy",
            "termin",
            "einverstanden",
        )
    )


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bWDVS\b", "wdvs"),
        (r"\bUnterputz\b", "unter putz"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bAltputz\b", "alt putz"),
        (r"\bGrundputz\b", "grund putz"),
        (r"\bInnenputz\b", "innen putz"),
        (r"\bAußenputz\b", "außen putz"),
        (r"\bAussenputz\b", "aussen putz"),
        (r"\bSanierputz\b", "sanier putz"),
        (r"\bSockelputz\b", "sockel putz"),
        (r"\bReibputz\b", "reib putz"),
        (r"\bKratzputz\b", "kratz putz"),
        (r"\bArmierungsgewebe\b", "armierungs gewebe"),
        (r"\bArmierung\b", "armierung"),
        (r"\bGrundierung\b", "grundierung"),
        (r"\bSchimmel\b", "schim mel"),
        (r"\bFassade\b", "fas sade"),
        (r"\bGipsputz\b", "gipsputz"),
        (r"\bKalkputz\b", "kalkputz"),
        (r"\bFeinputz\b", "feinputz"),
        (r"\bSilikatputz\b", "silikatputz"),
        (r"\bSilikonharzputz\b", "silikonharzputz"),
        (r"\bDämmplatten\b", "dämmplatten"),
        (r"\bTellerdübel\b", "tellerdübel"),
        (r"\bAPU-Leiste\b", "apu-leiste"),
        (r"\bAnputzleiste\b", "anputzleiste"),
        (r"\bEckschutzschiene\b", "eckschutzschiene"),
        (r"\bLeibungsprofil\b", "leibungsprofil"),
        (r"\bLaibungsprofil\b", "laibungsprofil"),
        (r"\bSockelprofil\b", "sockelprofil"),
        (r"\bTropfkantenprofil\b", "tropfkantenprofil"),
        (r"\bPutzmaschine\b", "putzmaschine"),
        (r"\bQuadratmeter\b", "quadrat meter"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\baufgetragen\b", "auf getragen"),
        (r"\baufgebracht\b", "auf gebracht"),
        (r"\bgeschliffen\b", "ge schliffen"),
        (r"\bangeklebt\b", "an geklebt"),
        (r"\bgedübelt\b", "ge dübelt"),
        (r"\beingebettet\b", "ein gebettet"),
        (r"\bgedämmt\b", "ge daemmt"),
        (r"\bglätten\b", "glä tten"),
        (r"\bfilziert\b", "fil ziert"),
        (r"\bstuckiert\b", "stuck iert"),
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
        ("Problem:", "problem is"),
        ("Offen:", "offen is"),
        ("gesprochen", "gred"),
        ("aufgetragen", "auf getragen"),
        ("abgetragen", "ab getragen"),
        ("eingebettet", "ein gebettet"),
    ):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKunde\b", "Kund", out, flags=re.IGNORECASE)
    out = re.sub(r"\bdann\b", "denn", out, flags=re.IGNORECASE, count=8)
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
    idx = 1
    for spec in all_base_scenarios():
        acts = tuple(spec.get("acts") or ())
        min_count = spec["min_act"] if spec.get("min_act") is not None else len(acts)
        for tag, fn in builders:
            cases.append(
                Case(
                    name=f"PutzStuck18_{idx:03d}_{tag}",
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
            idx += 1
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="ps-wave18",
        projectName="Putz Stuck Welle 18",
        customerName="Testkunde",
        date="2026-07-09",
        employeeNames=["Max", "Goran", "Ahmet", "Stefan", "Murat", "Dennis"],
        startTime="06:00",
        endTime="17:30",
        exportFormat="PDF",
        rawText=case.raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    cases = _build_cases()
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
        print("VIRTUAL-SPEECH-PUTZ-STUCK-WAVE18-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print(f"VIRTUAL-SPEECH-PUTZ-STUCK-WAVE18-SMOKE: OK ({len(cases)}/{len(cases)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
