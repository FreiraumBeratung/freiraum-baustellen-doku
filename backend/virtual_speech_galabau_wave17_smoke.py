"""Welle 17: GaLaBau-only — Herz-Nieren-Test inkl. Maschinenstunden (Bagger/Radlader).

Nur GaLaBau: kurz/lang, Umgangssprache, ASR/Whisper, Dialekt, gebrochenes Deutsch,
Kundengespräch, Problem, Offen. Hin und wieder Bagger/Radlader mit oder ohne Stunden.
Rein additiv — keine bestehenden Smoke-Dateien ändern.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_galabau_wave17_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class BaseScenario:
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...] = field(default_factory=tuple)
    forbid_activities: tuple[str, ...] = field(default_factory=tuple)
    expect_problem: bool = False
    expect_open: bool = False
    expect_customer: bool = False
    min_activity_count: int | None = None
    expect_machine_hours: tuple[str, ...] = field(default_factory=tuple)
    expect_machine_suggestions: tuple[str, ...] = field(default_factory=tuple)
    expect_machine_activities: tuple[str, ...] = field(default_factory=tuple)
    forbid_machine_hours: bool = False


@dataclass(frozen=True)
class Case:
    name: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...]
    forbid_activities: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool
    min_activity_count: int
    expect_machine_hours: tuple[str, ...]
    expect_machine_suggestions: tuple[str, ...]
    expect_machine_activities: tuple[str, ...]
    forbid_machine_hours: bool


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
        )
    )


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ── Komplett-Tagesbericht ──
        BaseScenario(
            (
                "Morgens 50 Quadratmeter Pflaster verlegt drei Kubikmeter Schotter eingebaut "
                "Hecke zurückgeschnitten Rindenmulch eingedeckt Bauherr kurz da "
                "Problem Lieferung kam spät Offen letzte Reihe morgen Kundengespräch lief gut."
            ),
            (
                "50 m² Pflaster verlegt",
                "Schotter eingebaut",
                "Hecke geschnitten",
                "Rindenmulch eingedeckt",
            ),
            expect_materials=("Pflastersteine", "Schotter"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Wir haben den Rasen gemäht vertikutiert und anschließend gedüngt sowie die Fläche bewässert.",
            ("Rasen gemäht", "Rasen vertikutiert", "Rasen gedüngt", "Fläche bewässert"),
        ),
        BaseScenario(
            (
                "Heute haben wir 60 Quadratmeter Pflaster verlegt 25 laufende Meter Rasenkantensteine gesetzt "
                "die Hecke geschnitten und zum Schluss Rindenmulch eingedeckt."
            ),
            (
                "60 m² Pflaster verlegt",
                "Rasenkantensteine gesetzt",
                "Hecke geschnitten",
                "Rindenmulch eingedeckt",
            ),
            expect_materials=("Pflastersteine", "Rasenkantensteine"),
        ),
        # ── Maschine: Bagger mit Stunden ──
        BaseScenario(
            (
                "3 Stunden mit dem Bagger Erdaushub für die neue Terrasse gemacht "
                "danach 40 Quadratmeter Pflaster verlegt und zwei Kubikmeter Schotter eingebaut."
            ),
            ("40 m² Pflaster verlegt", "Schotter eingebaut"),
            expect_materials=("Pflastersteine", "Schotter"),
            expect_machine_hours=("Bagger: 3",),
            expect_machine_activities=("Baggerarbeiten",),
        ),
        # ── Keramik / Terrasse ──
        BaseScenario(
            "30 Quadratmeter Keramikterrasse verlegt Geotextil verlegt und Splitt 2/5 mm eingebaut.",
            ("30 m² Keramikterrasse verlegt", "Geotextil verlegt", "Splitt 2/5 mm eingebaut"),
            expect_materials=("Keramikplatten", "Geotextil", "Splitt"),
        ),
        # ── Maschine: Radlader mit Stunden ──
        BaseScenario(
            (
                "2,5 Stunden Radlader Schotter verteilt und Untergrund verdichtet "
                "anschließend 35 Quadratmeter Pflaster verlegt."
            ),
            ("Schotter eingebaut", "Untergrund verdichtet", "35 m² Pflaster verlegt"),
            expect_materials=("Pflastersteine", "Schotter"),
            expect_machine_hours=("Radlader: 2,5",),
            expect_machine_activities=("Radlader eingesetzt",),
        ),
        # ── Winterdienst / WPC ──
        BaseScenario(
            (
                "Winterdienst durchgeführt Schnee geräumt Streugut gestreut "
                "danach 12 Quadratmeter WPC Terrasse gebaut und zwei Pflanzkübel mit Erde befüllt."
            ),
            (
                "Winterdienst durchgeführt",
                "12 m² Holz-/WPC-Terrasse gebaut",
                "Pflanzkübel",
            ),
            expect_materials=("Streugut",),
        ),
        # ── Gartenmauer / Palisaden ──
        BaseScenario(
            (
                "30 Quadratmeter Pflaster verlegt 10 Quadratmeter Gartenmauer gebaut "
                "15 laufende Meter Palisaden gesetzt und Hecke geschnitten."
            ),
            (
                "30 m² Pflaster verlegt",
                "Gartenmauer gebaut",
                "Palisaden gesetzt",
                "Hecke geschnitten",
            ),
        ),
        BaseScenario(
            "heute ich hab gemacht 15 meter Palisaden gesetzt und 30 quadrat Rollrasen verlegt.",
            ("Palisaden gesetzt", "30 m² Rasen verlegt"),
        ),
        # ── Maschine: Bagger ohne Stunden ──
        BaseScenario(
            (
                "Mit dem Bagger die Fläche vorbereitet dann 25 Quadratmeter Pflaster verlegt "
                "und Schotter eingebaut."
            ),
            ("25 m² Pflaster verlegt", "Schotter eingebaut"),
            expect_machine_activities=("Baggerarbeiten",),
            expect_machine_suggestions=("Baggerstunden",),
            forbid_machine_hours=True,
        ),
        # ── Maschine: Radlader ohne Stunden ──
        BaseScenario(
            "Radlader Mulch verteilt 20 Quadratmeter Pflaster verlegt und Hecke geschnitten.",
            ("20 m² Pflaster verlegt", "Hecke geschnitten"),
            expect_machine_activities=("Radlader eingesetzt",),
            expect_machine_suggestions=("Radladerstunden",),
            forbid_machine_hours=True,
        ),
        # ── Pflege / Laub ──
        BaseScenario(
            "Vormittags Rasen getrimmt danach Unkraut gezupft und zum Schluss die Hecke zurückgeschnitten.",
            ("Rasen getrimmt", "Unkraut entfernt", "Hecke geschnitten"),
        ),
        BaseScenario(
            "Erst 30 Quadratmeter Pflaster gelegt dann Schotter reingemacht und danach noch Laub gefegt.",
            ("30 m² Pflaster verlegt", "Schotter eingebaut", "Laub entfernt"),
            expect_materials=("Pflastersteine", "Schotter"),
        ),
        BaseScenario(
            "Heute den ganzen Garten freigeschnitten und zwischendurch Unkraut weg gemacht.",
            ("Rasen getrimmt", "Unkraut entfernt"),
        ),
        # ── Kurzberichte ──
        BaseScenario(
            "Wir haben heute fünfundzwanzig laufende Meter Rasenkantensteine gesetzt.",
            ("Rasenkantensteine gesetzt",),
            expect_materials=("Rasenkantensteine",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Drei Pflanzkübel mit Erde befüllt und Beet angelegt Pflanzen gesetzt.",
            ("Pflanzkübel", "Pflanzen gesetzt"),
            min_activity_count=1,
        ),
        BaseScenario(
            "Dreißig Quadratmeter Rollrasen verlegt und Untergrund verdichtet.",
            ("30 m² Rasen verlegt", "Untergrund verdichtet"),
        ),
        # ── Gebrochenes Deutsch ──
        BaseScenario(
            "heute ich machen 50 quadrat Pflaster und Hecke schneiden und Unkraut weg machen.",
            ("50 m² Pflaster verlegt", "Hecke geschnitten", "Unkraut entfernt"),
        ),
        BaseScenario(
            "heute auf baustell ich hab gearbeitet 30 quadrat Pflaster.",
            ("30 m² Pflaster verlegt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "heute ich hab gemacht 8 quadrat Gartenmauer.",
            ("Gartenmauer gebaut",),
            min_activity_count=1,
        ),
        # ── Großprojekt + Bagger mit Stunden ──
        BaseScenario(
            (
                "An der Hotelanlage 3 Stunden mit dem Bagger Erdaushub gemacht "
                "55 Quadratmeter Pflaster verlegt 20 laufende Meter Rasenkantensteine gesetzt "
                "Hecke geschnitten Bauherr zufrieden Problem Regen Offen letzte Fläche Montag."
            ),
            (
                "55 m² Pflaster verlegt",
                "Rasenkantensteine gesetzt",
                "Hecke geschnitten",
            ),
            expect_materials=("Pflastersteine",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            expect_machine_hours=("Bagger: 3",),
            expect_machine_activities=("Baggerarbeiten",),
        ),
        # ── Beide Maschinen mit Stunden ──
        BaseScenario(
            (
                "Morgens 2 Stunden mit dem Bagger Aushub für die Einfahrt "
                "nachmittags 2,5 Stunden Radlader Schotter eingebaut "
                "und 45 Quadratmeter Pflaster verlegt."
            ),
            ("Schotter eingebaut", "45 m² Pflaster verlegt"),
            expect_materials=("Pflastersteine", "Schotter"),
            expect_machine_hours=("Bagger: 2", "Radlader: 2,5"),
            expect_machine_activities=("Baggerarbeiten", "Radlader eingesetzt"),
        ),
        # ── Ketten / formell ──
        BaseScenario(
            (
                "Heute haben wir 40 Quadratmeter Pflaster verlegt zwei Kubikmeter Schotter eingebaut "
                "die Hecke geschnitten und Mulch eingedeckt."
            ),
            (
                "40 m² Pflaster verlegt",
                "Schotter eingebaut",
                "Hecke geschnitten",
            ),
            expect_materials=("Pflastersteine", "Schotter"),
        ),
        BaseScenario(
            (
                "Also fünfzig qm Pflaster gelegt dann noch zwei Kubik Schotter rein "
                "und zwei fünfer Split eingebaut."
            ),
            ("50 m² Pflaster verlegt", "2 m³ Schotter eingebaut", "Splitt 2/5 mm"),
            expect_materials=("Pflastersteine", "Schotter", "Splitt"),
        ),
        BaseScenario(
            "ich hab gemacht Beet und Pflanzen gesetzt und Fläche bewässert.",
            ("Pflanzen gesetzt", "Fläche bewässert"),
        ),
        BaseScenario(
            "heute ich machen Rasen mähen 100 quadrat.",
            ("100 m² Rasen gemäht",),
            min_activity_count=1,
        ),
        BaseScenario(
            "heute ich hab gemacht 20 quadrat Rollrasen verlegt.",
            ("20 m² Rasen verlegt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Kundengespräch gehabt Pflastermuster gewählt Problem Drainage Offen Rest nächste Woche.",
            (),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            min_activity_count=0,
        ),
        BaseScenario(
            "Laub entfernt und Gehweg kehren fertig.",
            ("Laub entfernt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "15 Quadratmeter Naturstein verlegt und Fugen verfugt.",
            ("Naturstein verlegt", "Fliesen verfugt"),
        ),
    ]


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bRasenkantensteine\b", "rasen kanten steine"),
        (r"\bKeramikterrasse\b", "keramik terrasse"),
        (r"\bGeotextil\b", "geo textil"),
        (r"\bRollrasen\b", "roll rasen"),
        (r"\blaufende Meter\b", "lauf ende meter"),
        (r"\bPflanzkübel\b", "pflanz kübel"),
        (r"\bWinterdienst\b", "winter dienst"),
        (r"\bSchotter\b", "schot ter"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bverlegt\b", "ver legt"),
        (r"\bgedüngt\b", "ge düngt"),
        (r"\bvertikutiert\b", "verti kutiert"),
        (r"\bgeschnitten\b", "ge schnitten"),
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


def _build_cases() -> list[Case]:
    bases = _base_scenarios()
    cases: list[Case] = []
    idx = 1
    builders = [
        ("N", lambda t: t),
        ("W", _whisper_light),
        ("H", _whisper_hard),
        ("B", _broken_de),
        ("D", _dialect_de),
        ("M", _mega_runon),
    ]
    for tag, builder in builders:
        for base in bases:
            raw = builder(base.raw)
            min_count = base.min_activity_count if base.min_activity_count is not None else len(base.expect_activities)
            cases.append(
                Case(
                    name=f"GaLaBau_{idx:03d}_{tag}",
                    raw=raw,
                    expect_activities=base.expect_activities,
                    expect_materials=base.expect_materials,
                    forbid_activities=base.forbid_activities,
                    expect_problem=base.expect_problem,
                    expect_open=base.expect_open,
                    expect_customer=base.expect_customer,
                    min_activity_count=min_count,
                    expect_machine_hours=base.expect_machine_hours,
                    expect_machine_suggestions=base.expect_machine_suggestions,
                    expect_machine_activities=base.expect_machine_activities,
                    forbid_machine_hours=base.forbid_machine_hours,
                )
            )
            idx += 1
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="gl-wave17",
        projectName="GaLaBau Welle 17",
        customerName="Testkunde",
        date="2026-07-25",
        employeeNames=["Max", "Goran", "Ahmet", "Stefan", "Murat", "Dennis"],
        startTime="06:00",
        endTime="18:00",
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
        probs = [str(x) for x in (structured.get("problems") or [])]
        opens = [str(x) for x in (structured.get("openItems") or [])]
        customer = str(structured.get("customerTalk") or "")
        summary = str(structured.get("summary") or "")
        machine_hours = [str(x) for x in (structured.get("machineHours") or [])]
        machine_suggs = [str(x) for x in (structured.get("machineSuggestions") or [])]

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
        for forbidden in case.forbid_activities:
            if _contains_any(acts, forbidden):
                failures.append(f"{case.name}: activity verboten -> {forbidden}")

        for expected in case.expect_machine_hours:
            if not _contains_any(machine_hours, expected):
                failures.append(f"{case.name}: maschinenstunden fehlen -> {expected} (got={machine_hours!r})")
        if case.forbid_machine_hours and machine_hours:
            failures.append(f"{case.name}: maschinenstunden unerwartet -> {machine_hours!r}")
        for expected in case.expect_machine_suggestions:
            if not _contains_any(machine_suggs, expected):
                failures.append(f"{case.name}: maschinen-vorschlag fehlt -> {expected} (got={machine_suggs!r})")
        for expected in case.expect_machine_activities:
            if not _contains_any(acts, expected):
                failures.append(f"{case.name}: maschinen-activity fehlt -> {expected} (got={acts!r})")

        if acts and (not summary or len(summary.strip()) < 10):
            failures.append(f"{case.name}: summary leer/zu kurz (got={summary!r})")

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer")
        if case.expect_customer and not _has_customer_talk(customer):
            failures.append(f"{case.name}: customerTalk fehlt (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-GALABAU-WAVE17-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-GALABAU-WAVE17-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
