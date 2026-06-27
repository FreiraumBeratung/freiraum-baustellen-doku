"""Welle 18: Hochbau-only — Herz-Nieren-Test für das komplette Gewerk.

Nur Hochbau: kurz/lang, Umgangssprache, ASR/Whisper, Dialekt, gebrochenes Deutsch,
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_hochbau_wave18_")))
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
        # ── Komplett-Tagesbericht ──
        BaseScenario(
            (
                "Morgens Schalung erstellt Bewehrung eingebaut acht Kubikmeter Beton eingebracht "
                "zwölf Quadratmeter Mauerwerk gemauert Bauleitung kurz da "
                "Problem Regen zwischendurch Schalung abgedeckt Offen Schalung Freitag abbauen "
                "nach dem Kundengespräch Feierabend."
            ),
            (
                "Schalung erstellt",
                "Bewehrung eingebaut",
                "Beton eingebracht",
                "Mauerwerk erstellt",
            ),
            expect_materials=("Beton",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            (
                "Fundamentplatte geschalt 15er Poroton hochgemauert Bewehrungsstahl gebunden "
                "8 Kubikmeter Beton gegossen Schalung abgebaut "
                "Bauherr zufrieden Problem Frost nachts Offen Nachbehandlung Plane."
            ),
            (
                "Schalung erstellt",
                "Mauerwerk erstellt",
                "Bewehrung eingebaut",
                "Beton eingebracht",
            ),
            expect_materials=("Beton",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Schalung erstellt Bewehrung eingebaut und 10 Kubikmeter Beton eingebracht.",
            ("Schalung erstellt", "Bewehrung eingebaut", "Beton eingebracht"),
            expect_materials=("Beton",),
        ),
        BaseScenario(
            "Fundament erstellt 12 Quadratmeter Mauerwerk gemauert und Betondecke gegossen.",
            ("Fundament erstellt", "Mauerwerk erstellt", "Beton eingebracht"),
        ),
        BaseScenario(
            "Bewehrung eingebaut Schalung gestellt und Beton eingebracht.",
            ("Bewehrung eingebaut", "Schalung erstellt", "Beton eingebracht"),
        ),
        # ── Kurzberichte ──
        BaseScenario(
            "Heute 20 Quadratmeter Mauerwerk mit Poroton erstellt.",
            ("20 m² Mauerwerk erstellt",),
            min_activity_count=1,
        ),
        BaseScenario("5 Kubikmeter Beton eingebracht fertig.", ("Beton eingebracht",), min_activity_count=1),
        BaseScenario(
            "Fundament erstellt und Filigrandecke montiert.",
            ("Fundament erstellt", "Filigrandecke montiert"),
        ),
        BaseScenario("Schalung erstellt.", ("Schalung erstellt",), min_activity_count=1),
        BaseScenario("Bewehrung eingebaut.", ("Bewehrung eingebaut",), min_activity_count=1),
        # ── Materialspezifisch ──
        BaseScenario(
            "11,5er Poroton hochgemauert und Mauerwerk fertiggestellt.",
            ("Mauerwerk erstellt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Kalksandstein gemauert 18 Quadratmeter Mauerwerk erstellt.",
            ("18 m² Mauerwerk erstellt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Ytong-Steine gesetzt und Wand hochgezogen.",
            ("Mauerwerk erstellt",),
            min_activity_count=1,
        ),
        # ── Gebrochenes Deutsch ──
        BaseScenario(
            "heute ich hab gemacht 5 kubik beton.",
            ("Beton eingebracht",),
            min_activity_count=1,
        ),
        BaseScenario(
            "ich hab gemacht Schalung und Bewehrung eingebaut.",
            ("Schalung erstellt", "Bewehrung eingebaut"),
        ),
        BaseScenario(
            "heute auf baustell ich hab gearbeitet 12 quadrat mauerwerk.",
            ("Mauerwerk erstellt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "heute ich machen 6 kubik beton und schalung.",
            ("Beton eingebracht", "Schalung erstellt"),
        ),
        # ── Großprojekt / Hotel ──
        BaseScenario(
            (
                "An der Hotel-Baustelle Fundament erstellt Schalung gestellt Bewehrungsstahl verbaut "
                "14 Kubikmeter Beton gegossen 25 Quadratmeter Mauerwerk gemauert "
                "Bauherr zufrieden Problem Lieferung spät Offen Decke nächste Woche."
            ),
            (
                "Fundament erstellt",
                "Schalung erstellt",
                "Bewehrung eingebaut",
                "Beton eingebracht",
                "Mauerwerk erstellt",
            ),
            expect_materials=("Beton",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        # ── Ketten / formell ──
        BaseScenario(
            (
                "Heute haben wir die Schalung erstellt die Bewehrung eingebaut "
                "und sechs Kubikmeter Beton eingebracht."
            ),
            ("Schalung erstellt", "Bewehrung eingebaut", "Beton eingebracht"),
            expect_materials=("Beton",),
        ),
        BaseScenario(
            "Heute haben wir das Fundament erstellt und die Filigrandecke montiert.",
            ("Fundament erstellt", "Filigrandecke montiert"),
        ),
        BaseScenario(
            "Bewehrungsstahl gebunden Schalung aufgestellt Betondecke gegossen.",
            ("Bewehrung eingebaut", "Schalung erstellt", "Beton eingebracht"),
        ),
        BaseScenario(
            "Erdarbeiten gemacht Schalung gestellt Betondecke gegossen Fundament erstellt.",
            ("Erdarbeiten durchgeführt", "Schalung erstellt", "Beton eingebracht", "Fundament erstellt"),
        ),
        BaseScenario(
            "Fundament erstellt und Bodenplatte betoniert.",
            ("Fundament erstellt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Porit-Steine vermauert Wand erstellt.",
            ("Mauerwerk erstellt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Schalung für die Decke gestellt Bewehrung verlegt und Beton eingebracht.",
            ("Schalung erstellt", "Bewehrung eingebaut", "Beton eingebracht"),
        ),
        BaseScenario(
            "Kundengespräch gehabt Betonqualität besprochen Problem Lieferzeit Offen Rest nächste Woche.",
            (),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            min_activity_count=0,
        ),
        BaseScenario(
            "Zehn Kubik Beton gegossen und Schalung stehen gelassen.",
            ("Beton eingebracht", "Schalung erstellt"),
        ),
        BaseScenario(
            "24er Kalksandstein Mauerwerk hochgezogen fertig.",
            ("Mauerwerk erstellt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Fundamentplatte betoniert Bewehrung eingebaut.",
            ("Beton eingebracht", "Bewehrung eingebaut"),
        ),
        BaseScenario(
            "Schalung für die Bodenplatte erstellt und Beton eingebracht.",
            ("Schalung erstellt", "Beton eingebracht"),
        ),
    ]


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bBewehrungsstahl\b", "bewehrungs stahl"),
        (r"\bBewehrung\b", "bewehrung"),
        (r"\bFundamentplatte\b", "fundament platte"),
        (r"\bFiligrandecke\b", "filigran decke"),
        (r"\bBetondecke\b", "beton decke"),
        (r"\bKalksandstein\b", "kalk sandstein"),
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\bKubikmeter\b", "kubik meter"),
        (r"\bPoroton\b", "poro ton"),
        (r"\bSchalung\b", "schal ung"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bgegossen\b", "ge gossen"),
        (r"\beingebaut\b", "ein gebaut"),
        (r"\bverbaut\b", "ver baut"),
        (r"\bgeschalt\b", "ge schalt"),
        (r"\bgebunden\b", "ge bunden"),
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
        ("eingebaut", "ein gebaut"),
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
                    name=f"Hochbau_{idx:03d}_{tag}",
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
        projectId="hb-wave18",
        projectName="Hochbau Welle 18",
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
        print("VIRTUAL-SPEECH-HOCHBAU-WAVE18-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-HOCHBAU-WAVE18-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
