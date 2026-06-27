"""Welle 10: Maximale Pilot-Abdeckung — Kurz, lang, Mega-Run-on, ASR, Mischtext.

Erweitert Welle 8/9 additiv:
- Sehr kurze Einzeiler („50 m² Pflaster gelegt fertig“)
- Sehr lange Ketten + Run-on-Sätze
- Doppelte Whisper-Variante (W + W2 hart)
- Kunde / Problem / Offen in einem Diktat
- Alle Gewerke gleichwertig

Rein additiv. Rot → patchen → grün → weiter.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_pilot_wave10_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class BaseScenario:
    trade: str
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
        )
    )


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ═══ PUTZ / STUCK ═══
        BaseScenario(
            "Putz",
            (
                "Also heute früh erst den alten Putz abgetragen dann die Wand geschliffen "
                "danach grundiert Unterputz aufgetragen während der Unterputz trocknete "
                "haben wir mit der Kundin gesprochen sie ist mega zufrieden und empfiehlt uns weiter "
                "Problem war der Untergrund total uneben da ist viel Material draufgegangen "
                "Offen bleibt morgen nochmal spachteln am Fenster "
                "nach dem Kundengespräch Oberputz aufgetragen und Feierabend."
            ),
            ("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Putz",
            "Grundputz aufgetragen Innenputz aufgebracht Sockelputz verarbeitet Reibputz aufgetragen.",
            ("Grundputz aufgetragen", "Innenputz aufgetragen", "Sockelputz aufgetragen", "Reibputz aufgetragen"),
        ),
        BaseScenario("Putz", "40 Quadratmeter Unterputz aufgetragen fertig.", ("Unterputz aufgetragen",)),
        BaseScenario("Putz", "Oberputz gemacht.", ("Oberputz aufgetragen",), min_activity_count=1),
        BaseScenario(
            "Stuck",
            "WDVS montiert Armierung eingebaut Reibputz aufgetragen Kunde war da und happy Problem Folie knapp Offen Rest morgen.",
            ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),

        # ═══ TIEFBAU ═══
        BaseScenario(
            "Tiefbau",
            (
                "Boden ausgeschachtet 35 laufende Meter KG-Rohre DN 110 verlegt Sand eingebaut "
                "Schotter eingebaut Untergrund verdichtet Planum hergestellt "
                "Bauherr war vor Ort Problem es hat geregnet Graben war nass "
                "Offen morgen Rest verfüllen Kundengespräch lief gut."
            ),
            ("Boden ausgeschachtet", "KG-Rohre", "Sand eingebaut", "Untergrund verdichtet"),
            expect_materials=("KG-Rohre",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Tiefbau",
            "Graben ausgehoben Drainage verlegt Hausanschluss hergestellt Leitungstrasse hergestellt Kanal angeschlossen.",
            ("Graben ausgehoben", "Drainage/Entwässerung eingebaut", "Hausanschluss hergestellt", "Leitungstrasse hergestellt"),
        ),
        BaseScenario("Tiefbau", "Frostschutz eingebaut verdichtet.", ("Frostschutz eingebaut", "Untergrund verdichtet")),
        BaseScenario("Tiefbau", "20 Meter Graben ausgehoben fertig.", ("Graben ausgehoben",)),

        # ═══ GaLaBau ═══
        BaseScenario(
            "GaLaBau",
            (
                "50 Quadratmeter Pflaster verlegt 3 Kubikmeter Schotter eingebaut "
                "20 laufende Meter Rasenkantensteine gesetzt Hecke geschnitten "
                "Rindenmulch eingedeckt Unkraut entfernt "
                "Kundin sehr zufrieden Problem Lieferung zu spät Offen eine Palette Nachschub."
            ),
            ("Pflaster verlegt", "Schotter eingebaut", "Rasenkantensteine gesetzt", "Hecke geschnitten", "Rindenmulch eingedeckt"),
            expect_materials=("Pflastersteine", "Schotter"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "GaLaBau",
            "Rasen gemäht vertikutiert gedüngt bewässert Rollrasen verlegt Palisaden gesetzt.",
            ("Rasen gemäht", "Rasen vertikutiert", "Rasen gedüngt", "Fläche bewässert", "Palisaden gesetzt"),
        ),
        BaseScenario(
            "GaLaBau",
            "Keramikterrasse verlegt Geotextil verlegt Splitt eingebaut Stelzlager gesetzt.",
            ("Keramikterrasse verlegt", "Geotextil verlegt", "Splitt eingebaut"),
        ),
        BaseScenario("GaLaBau", "50 Quadratmeter Pflaster gelegt fertig.", ("Pflaster verlegt",), min_activity_count=1),
        BaseScenario("GaLaBau", "Hecke zurückgeschnitten.", ("Hecke geschnitten",), min_activity_count=1),

        # ═══ SHK ═══
        BaseScenario(
            "SHK",
            (
                "20 laufende Meter KG-Rohre DN 160 verlegt HT-Rohre verlegt Heizkörper montiert "
                "WC gesetzt Waschbecken montiert Druckprüfung durchgeführt "
                "mit dem Kunden gesprochen Problem ein Bogen fehlte Offen morgen Bogen nachlegen."
            ),
            ("KG-Rohre", "Heizkörper montiert", "WC montiert", "Waschbecken montiert", "Druckprüfung durchgeführt"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "SHK",
            "Wasserleitungen verlegt Fußbodenheizung verlegt hydraulischen Abgleich durchgeführt.",
            ("Wasserleitungen verlegt", "Fußbodenheizung verlegt", "Hydraulischer Abgleich durchgeführt"),
        ),
        BaseScenario("SHK", "Heizkörper montiert fertig.", ("Heizkörper montiert",), min_activity_count=1),
        BaseScenario("SHK", "WC montiert.", ("WC montiert",), min_activity_count=1),

        # ═══ FLIESEN ═══
        BaseScenario(
            "Fliesen",
            (
                "Wand grundiert Abdichtung hergestellt Nivelliermasse aufgetragen "
                "40 Quadratmeter Fliesen verlegt verfugt Silikonfugen gezogen "
                "Kundin hat Farbe bestätigt Problem Untergrund uneben viel Masse nötig "
                "Offen Restfugen morgen."
            ),
            ("Grundierung aufgetragen", "Abdichtung hergestellt", "Nivelliermasse aufgetragen", "Fliesen verlegt", "Fliesen verfugt"),
            expect_materials=("Fliesen",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Fliesen",
            "Fliesenkleber aufgetragen Großformatfliesen verlegt Bodenablauf eingebaut.",
            ("Fliesenkleber aufgetragen", "Großformatfliesen verlegt", "Bodenablauf eingebaut"),
        ),
        BaseScenario("Fliesen", "25 Quadratmeter Fliesen verlegt fertig.", ("Fliesen verlegt",), min_activity_count=1),

        # ═══ TROCKENBAU ═══
        BaseScenario(
            "Trockenbau",
            (
                "Ständerwerk montiert Dämmung eingebaut Gipskartonplatten beplankt "
                "Fugen verspachtelt Decke abgehängt Trockenbauwand geschlossen "
                "mit Bauleitung abgestimmt Problem Rigips kam spät Offen Revisionsklappe morgen."
            ),
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Fugen verspachtelt", "Decke abgehängt"),
            expect_materials=("Gipskartonplatten",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario("Trockenbau", "Gipskarton montiert fertig.", ("Gipskartonplatten montiert",), min_activity_count=1),

        # ═══ HOCHBAU ═══
        BaseScenario(
            "Hochbau",
            (
                "Schalung erstellt Bewehrung eingebaut 10 Kubikmeter Beton eingebracht "
                "Mauerwerk gemauert Fundament erstellt "
                "Bauherr zufrieden Problem Regen Schalung abgedeckt Offen Schalung Freitag abbauen."
            ),
            ("Schalung erstellt", "Bewehrung eingebaut", "Beton eingebracht", "Mauerwerk erstellt"),
            expect_materials=("Beton",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Hochbau",
            "Bewehrung eingebaut Schalung gestellt Beton eingebracht.",
            ("Bewehrung eingebaut", "Schalung erstellt", "Beton eingebracht"),
        ),
        BaseScenario("Hochbau", "6 Kubikmeter Beton eingebracht fertig.", ("Beton eingebracht",), min_activity_count=1),
    ]


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bUnterputz\b", "unter putz"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bAltputz\b", "alt putz"),
        (r"\bHecke\b", "Ecke"),
        (r"\bGeotextil\b", "geo textil"),
        (r"\bDruckprüfung\b", "druck prüfung"),
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\blaufende Meter\b", "lauf ende meter"),
        (r"\bKG-Rohre\b", "ka ga rohre"),
        (r"\bFußbodenheizung\b", "fuss boden heizung"),
        (r"\bGipskartonplatten\b", "gips karton platten"),
        (r"\bNivelliermasse\b", "nivellier masse"),
        (r"\bausgeschachtet\b", "aus geschachtet"),
        (r"\bSilikonfugen\b", "silikon fugen"),
        (r"\bGroßformatfliesen\b", "gross format fliesen"),
        (r"\bBewehrung\b", "be wehrung"),
        (r"\bRasenkantensteine\b", "rasen kanten steine"),
        (r"\bHeizkörper\b", "heiz körper"),
        (r"\bHT-Rohre\b", "ht rohre"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\buntergrund\b", "unter grund"),
        (r"\bwerkzeug\b", "werk zeug"),
        (r"\bschotter\b", "schot ter"),
        (r"\bverfugt\b", "ver fugt"),
        (r"\bverspachtelt\b", "ver spachtelt"),
        (r"\bkanal\b", "ka nal"),
        (r"\bplanum\b", "pla num"),
        (r"\bfeierabend\b", "feier abend"),
        (r"\bheizungsplan\b", "heizungs plan"),
        (r"\brollrasen\b", "roll rasen"),
        (r"\bstoßfugen\b", "stoss fugen"),
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
        ("Quadratmeter", "quadrat"),
        ("laufende Meter", "lauf meter"),
        ("durchgeführt", "durch gemacht"),
        ("Problem:", "problem is"),
        ("Offen:", "offen is"),
        ("montiert", "montiert"),
        ("gesprochen", "gred"),
        ("Kubikmeter", "kubik"),
    ):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bwir haben\b", "mia ham", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKunde\b", "Kund", out, flags=re.IGNORECASE)
    return out


def _mega_runon(text: str) -> str:
    core = re.sub(r"[.!?]+\s*", " und also ", text)
    return (
        f"Ja also vom Schichtende her {core} und genau und dann war Feierabend "
        f"und wir sind zufrieden nach Hause und morgen geht's weiter mit dem Rest."
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
                    name=f"{base.trade}_{idx:03d}_{tag}",
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
        projectId="p-wave10",
        projectName="Pilot-Welle 10",
        customerName="Testkunde",
        date="2026-06-29",
        employeeNames=["Max", "Goran", "Ahmet", "Stefan", "Murat"],
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
        print("VIRTUAL-SPEECH-PILOT-WAVE10-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-PILOT-WAVE10-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
