"""Welle 16: Tiefbau-only — Herz-Nieren-Test für das komplette Gewerk.

Nur Tiefbau: kurz/lang, Umgangssprache, ASR/Whisper, Dialekt, gebrochenes Deutsch,
Kundengespräch, Problem, Offen. Rein additiv — keine bestehenden Smoke-Dateien ändern.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_tiefbau_wave16_")))
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
        # ── Komplett-Tagesbericht (Pilot-Kette) ──
        BaseScenario(
            (
                "Morgens mit dem Bagger Graben ausgehoben 25 laufende Meter KG-Rohre DN 110 verlegt "
                "drei Kubikmeter Schotter eingebaut Graben verfüllt und Planum verdichtet "
                "Bauleitung kurz da Problem Leitungsplan fehlt Offen Schacht setzen morgen "
                "nach dem Kundengespräch Feierabend."
            ),
            (
                "Graben ausgehoben",
                "KG-Rohre",
                "Schotter eingebaut",
                "Graben verfüllt",
                "Untergrund verdichtet",
            ),
            expect_materials=("KG-Rohre", "Schotter"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            (
                "Erdaushub gemacht 22 laufende Meter KG Rohre DN 125 verlegt Splittschicht reingepackt "
                "Graben verfüllt Planum verdichtet Auftraggeber informiert Problem Material knapp "
                "Offen Rest morgen."
            ),
            (
                "Graben ausgehoben",
                "KG-Rohre",
                "Splitt eingebaut",
                "Graben verfüllt",
                "Untergrund verdichtet",
            ),
            expect_materials=("KG-Rohre",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            (
                "Boden ausgeschachtet 35 laufende Meter KG-Rohre DN 110 verlegt Sand eingebaut "
                "Schotter eingebaut Untergrund verdichtet Bauherr war vor Ort "
                "Problem es hat geregnet Offen morgen Rest verfüllen Kundengespräch lief gut."
            ),
            (
                "Boden ausgeschachtet",
                "KG-Rohre",
                "Sand eingebaut",
                "Schotter eingebaut",
                "Untergrund verdichtet",
            ),
            expect_materials=("KG-Rohre",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        # ── Kanal / Drainage / Leitungen ──
        BaseScenario(
            "Baugrube ausgehoben Kanal angeschlossen Drainage verlegt Leitungstrasse angelegt.",
            (
                "Graben ausgehoben",
                "Kanal-/Schachtarbeiten durchgeführt",
                "Drainage/Entwässerung eingebaut",
                "Leitungstrasse hergestellt",
            ),
        ),
        BaseScenario(
            "Graben ausgehoben Drainage verlegt Hausanschluss hergestellt Leitungstrasse hergestellt.",
            (
                "Graben ausgehoben",
                "Drainage/Entwässerung eingebaut",
                "Hausanschluss hergestellt",
                "Leitungstrasse hergestellt",
            ),
        ),
        BaseScenario(
            (
                "An der Neubau-Strecke Kanal angeschlossen Schacht gesetzt "
                "18 laufende Meter KG-Rohre DN 110 verlegt und Baugrube verdichtet."
            ),
            (
                "Kanal-/Schachtarbeiten durchgeführt",
                "KG-Rohre",
                "Untergrund verdichtet",
            ),
            expect_materials=("KG-Rohre",),
        ),
        # ── KG-Fittings / Kurzberichte ──
        BaseScenario(
            (
                "Graben gezogen KG-Rohre gelegt zwei KG-Bögen und einen KG-Abzweig eingebaut "
                "Untergrund wieder verdichtet."
            ),
            ("Graben ausgehoben", "KG-Rohre", "KG-Bögen", "KG-Abzweig", "Untergrund verdichtet"),
            expect_materials=("KG-Rohre",),
        ),
        BaseScenario(
            "Heute haben wir den Graben ausgehoben 30 laufende Meter KG-Rohre DN 160 verlegt und den Graben wieder verfüllt.",
            ("Graben ausgehoben", "30 lfm KG-Rohre DN 160 verlegt", "Graben verfüllt"),
            expect_materials=("KG-Rohre",),
        ),
        BaseScenario("15 Meter KG verlegt fertig.", ("KG-Rohre",), min_activity_count=1),
        BaseScenario("20 Meter Graben ausgehoben fertig.", ("Graben ausgehoben",), min_activity_count=1),
        # ── Untergrund / Materialschichten ──
        BaseScenario("Sand reingepackt und verdichtet.", ("Sand eingebaut", "Untergrund verdichtet")),
        BaseScenario("Frostschutz eingebaut verdichtet.", ("Frostschutz eingebaut", "Untergrund verdichtet")),
        BaseScenario(
            "Wir haben die Drainage eingebaut Filtervlies verlegt und den Untergrund verdichtet.",
            ("Drainage/Entwässerung eingebaut", "Geotextil verlegt", "Untergrund verdichtet"),
        ),
        BaseScenario("Geotextil verlegt Splitt eingebaut.", ("Geotextil verlegt", "Splitt eingebaut")),
        BaseScenario("3 Kubikmeter Schotter eingebaut fertig.", ("Schotter eingebaut",), min_activity_count=1),
        # ── Verbau / Asphalt / Erdarbeiten ──
        BaseScenario("Verbau gesetzt und Untergrund verdichtet.", ("Verbau gesetzt", "Untergrund verdichtet")),
        BaseScenario("Asphalt auf der Straße eingebaut.", ("Asphalt eingebaut",), min_activity_count=1),
        BaseScenario(
            "Erdarbeiten durchgeführt und Baugrube ausgehoben.",
            ("Erdarbeiten durchgeführt", "Graben ausgehoben"),
        ),
        BaseScenario(
            "Mit dem Bagger gebaggert Baugrube ausgeschachtet und Graben verfüllt.",
            ("Graben ausgehoben", "Graben verfüllt"),
        ),
        # ── Gebrochenes Deutsch / Slang ──
        BaseScenario(
            "heute ich graben gemacht 15 meter und dann graben wieder verfüllt.",
            ("Graben ausgehoben", "Graben verfüllt"),
        ),
        BaseScenario(
            "heute ich hab gemacht Hausanschluss und Leitungstrasse.",
            ("Hausanschluss hergestellt", "Leitungstrasse hergestellt"),
        ),
        BaseScenario(
            "ich hab gemacht KG Bögen und KG Abzweig.",
            ("KG-Bögen eingebaut", "KG-Abzweig eingebaut"),
        ),
        BaseScenario(
            "heute auf baustell ich hab gearbeitet 20 laufende meter kg rohre verlegt.",
            ("KG-Rohre",),
            min_activity_count=1,
        ),
        # ── Großprojekt / Hotel ──
        BaseScenario(
            (
                "An der Hotel-Baustelle Leitungstrasse hergestellt 40 laufende Meter KG-Rohre DN 160 verlegt "
                "drei KG-Bögen eingebaut Drainage verlegt Graben verfüllt Untergrund verdichtet "
                "Bauherr zufrieden Problem Wind nachts Offen letzte Trasse Montag."
            ),
            (
                "Leitungstrasse hergestellt",
                "KG-Rohre",
                "KG-Bögen",
                "Drainage/Entwässerung eingebaut",
                "Graben verfüllt",
                "Untergrund verdichtet",
            ),
            expect_materials=("KG-Rohre",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        # ── Ketten / formell ──
        BaseScenario(
            (
                "Heute haben wir den Graben ausgehoben die KG-Rohre verlegt den Graben verfüllt "
                "und den Untergrund verdichtet."
            ),
            ("Graben ausgehoben", "KG-Rohre", "Graben verfüllt", "Untergrund verdichtet"),
        ),
        BaseScenario(
            "Graben ausgehoben Frostschutz verlegt Sand eingebaut und verdichtet.",
            ("Graben ausgehoben", "Frostschutz eingebaut", "Sand eingebaut", "Untergrund verdichtet"),
        ),
        BaseScenario(
            "Baugrube ausgehoben Verbau gesetzt Entwässerung eingebaut.",
            ("Graben ausgehoben", "Verbau gesetzt", "Drainage/Entwässerung eingebaut"),
        ),
        BaseScenario(
            "Erdaushub gemacht Schotter eingebaut Planum verdichtet.",
            ("Graben ausgehoben", "Schotter eingebaut", "Untergrund verdichtet"),
        ),
        BaseScenario(
            "KG-Rohre DN 125 verlegt Graben verfüllt fertig.",
            ("KG-Rohre", "Graben verfüllt"),
            expect_materials=("KG-Rohre",),
        ),
        BaseScenario(
            "Kundengespräch gehabt Leitungsplan besprochen Problem Grundwasser Offen Rest nächste Woche.",
            (),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            min_activity_count=0,
        ),
    ]


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bKG-Rohre\b", "ka ga rohre"),
        (r"\bKG Rohre\b", "ka ga rohre"),
        (r"\bKG-Rohr\b", "ka ga rohr"),
        (r"\bKG-Bögen\b", "ka ga bögen"),
        (r"\bKG-Bogen\b", "ka ga bogen"),
        (r"\bKG-Abzweig\b", "ka ga abzweig"),
        (r"\blaufende Meter\b", "lauf ende meter"),
        (r"\bGeotextil\b", "geo textil"),
        (r"\bSchotter\b", "schot ter"),
        (r"\bUntergrund\b", "unter grund"),
        (r"\bPlanum\b", "pla num"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bverlegt\b", "ver legt"),
        (r"\bverfüllt\b", "ver füllt"),
        (r"\bverfuellt\b", "ver fuellt"),
        (r"\bverdichtet\b", "ver dichtet"),
        (r"\bausgehoben\b", "aus ge hoben"),
        (r"\beingebaut\b", "ein gebaut"),
        (r"\bgebaggert\b", "ge baggert"),
        (r"\bangeschlossen\b", "an geschlossen"),
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
                    name=f"Tiefbau_{idx:03d}_{tag}",
                    raw=raw,
                    expect_activities=base.expect_activities,
                    expect_materials=base.expect_materials,
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
        projectId="tb-wave16",
        projectName="Tiefbau Welle 16",
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

        if acts and (not summary or len(summary.strip()) < 10):
            failures.append(f"{case.name}: summary leer/zu kurz (got={summary!r})")

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer")
        if case.expect_customer and not _has_customer_talk(customer):
            failures.append(f"{case.name}: customerTalk fehlt (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-TIEFBAU-WAVE16-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-TIEFBAU-WAVE16-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
