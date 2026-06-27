"""Welle 11: Neue Sätze — Kurz, lang, Ketten, ASR, Kunde/Problem/Offen.

Komplett neue Formulierungen gegenüber Welle 6–10.
Alle Gewerke gleichwertig. Rein additiv.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_pilot_wave11_")))
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
            "rücksprache",
            "ruecksprache",
        )
    )


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ═══ PUTZ / STUCK ═══
        BaseScenario(
            "Putz",
            (
                "Morgens Erstbesichtigung mit dem Bauherrn dann alten Putz runter Wand angeschliffen "
                "Grundierung drauf Unterputz zweimal aufgezogen während wir gewartet haben "
                "mit der Kundin telefoniert sie will andere Farbe Problem Feuchtigkeit im Mauerwerk "
                "Offen Restecke Küche morgen Oberputz glatt gezogen und fertig für heute."
            ),
            ("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario("Putz", "Sanierputz aufgebracht Kratzputz verarbeitet Außenputz aufgetragen.", ("Sanierputz aufgebracht", "Kratzputz aufgetragen", "Außenputz aufgetragen")),
        BaseScenario("Putz", "12 Quadratmeter Sockelputz gemacht.", ("Sockelputz aufgetragen",), min_activity_count=1),
        BaseScenario(
            "Stuck",
            "Fassadenarmierung eingebettet WDVS gedämmt Reibputz geschliffen Kunde informiert Problem Kleber knapp Offen Sockelleiste.",
            ("Fassadenarmierung ausgeführt", "WDVS ausgeführt", "Reibputz aufgetragen"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),

        # ═══ TIEFBAU ═══
        BaseScenario(
            "Tiefbau",
            (
                "Erdaushub gemacht 18 laufende Meter KG-Rohre DN 125 verlegt Splittschicht eingebaut "
                "Graben verfüllt Planum verdichtet Hausanschluss vorbereitet "
                "Auftraggeber war da Problem Leitungsplan fehlt noch Offen morgen Schacht setzen."
            ),
            ("Graben ausgehoben", "KG-Rohre", "Splitt eingebaut", "Graben verfüllt", "Untergrund verdichtet"),
            expect_materials=("KG-Rohre",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Tiefbau",
            "Baugrube ausgehoben Kanal angeschlossen Entwässerung eingebaut Leitungstrasse angelegt.",
            ("Graben ausgehoben", "Kanal-/Schachtarbeiten durchgeführt", "Drainage/Entwässerung eingebaut", "Leitungstrasse hergestellt"),
        ),
        BaseScenario("Tiefbau", "Sand eingebaut verdichtet fertig.", ("Sand eingebaut", "Untergrund verdichtet")),
        BaseScenario("Tiefbau", "15 Meter KG-Rohre verlegt.", ("KG-Rohre",), min_activity_count=1),

        # ═══ GaLaBau ═══
        BaseScenario(
            "GaLaBau",
            (
                "Terrasse neu 35 Quadratmeter Keramikplatten verlegt Splitt 16/32 eingebaut "
                "Stelzlager gesetzt Sichtschutz montiert Unkraut im Beet entfernt "
                "Bauherrin sehr happy Problem Pflastersteine falsche Farbe Offen Umtausch nächste Woche."
            ),
            ("Keramikterrasse verlegt", "Splitt", "Stelzlager", "Unkraut entfernt"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "GaLaBau",
            "Gartenmauer hochgezogen Zaun gesetzt Rollrasen ausgelegt Rasen gedüngt Winterdienst Streugut verteilt.",
            ("Gartenmauer gebaut", "Zaun", "Rasen verlegt", "Rasen gedüngt", "Winterdienst"),
        ),
        BaseScenario(
            "GaLaBau",
            "Palisaden eingesetzt Geotextil unter Pflaster verlegt Randsteine gesetzt.",
            ("Palisaden gesetzt", "Geotextil verlegt", "Randsteine gesetzt"),
        ),
        BaseScenario("GaLaBau", "80 Quadratmeter Rollrasen verlegt fertig.", ("Rasen verlegt",), min_activity_count=1),
        BaseScenario("GaLaBau", "Ecke zurückgeschnitten.", ("Hecke geschnitten",), min_activity_count=1),

        # ═══ SHK ═══
        BaseScenario(
            "SHK",
            (
                "Abwasser HT-Rohre 12 laufende Meter verlegt Wasserleitungen angeschlossen "
                "Dusche montiert Armaturen gesetzt Druckprüfung abgeschlossen "
                "Rücksprache mit Kunde Problem Manschette undicht Offen morgen tauschen."
            ),
            ("HT-Rohre verlegt", "Wasserleitungen verlegt", "Dusche montiert", "Armaturen montiert", "Druckprüfung durchgeführt"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "SHK",
            "Fußbodenheizung installiert Rücklaufverschraubung montiert Lüftung eingebaut.",
            ("Fußbodenheizung verlegt", "Rücklaufverschraubung montiert", "Lüftungs-/Klimatechnik installiert"),
        ),
        BaseScenario("SHK", "Waschbecken montiert fertig.", ("Waschbecken montiert",), min_activity_count=1),
        BaseScenario("SHK", "Dusche eingebaut.", ("Dusche montiert",), min_activity_count=1),

        # ═══ FLIESEN ═══
        BaseScenario(
            "Fliesen",
            (
                "Bad komplett Wandfliesen 22 Quadratmeter verlegt Bodenfliesen verfugt "
                "Abdichtung im Duschbereich Nivelliermasse gezogen Silikonfugen nachgezogen "
                "Kunde vor Ort Problem Wand schief viel Ausgleich Offen Rest Silikon Donnerstag."
            ),
            ("Fliesen verlegt", "Fliesen verfugt", "Abdichtung hergestellt", "Nivelliermasse aufgetragen"),
            expect_materials=("Fliesen",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Fliesen",
            "Fliesenkleber aufgezogen Naturstein verlegt Bodenablauf eingebaut Duschrinne gesetzt.",
            ("Fliesenkleber aufgetragen", "Naturstein verlegt", "Bodenablauf eingebaut"),
        ),
        BaseScenario("Fliesen", "18 Quadratmeter Wandfliesen geklebt fertig.", ("Fliesen verlegt",), min_activity_count=1),

        # ═══ TROCKENBAU ═══
        BaseScenario(
            "Trockenbau",
            (
                "CW-Profil und UW-Profil montiert Dämmmatte eingesetzt zwei Lagen Gipskarton verschraubt "
                "Fugenspachtel gezogen Akustikdecke abgehängt Brandschutzplatten beplankt "
                "Bauleitung abgesprochen Problem Lieferverzug Offen Revisionsöffnung Freitag."
            ),
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Fugen verspachtelt", "Decke abgehängt"),
            expect_materials=("Gipskartonplatten",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario("Trockenbau", "Rigipswand geschlossen Decke montiert.", ("Trockenbauwand geschlossen", "Decke abgehängt")),
        BaseScenario("Trockenbau", "Trockenbauwand fertiggestellt.", ("Trockenbauwand geschlossen",), min_activity_count=1),

        # ═══ HOCHBAU ═══
        BaseScenario(
            "Hochbau",
            (
                "Fundamentplatte geschalt 15er Poroton gemauert Bewehrungsstahl gebunden "
                "7 Kubikmeter Beton gegossen Schalung abgebaut "
                "Bauherr informiert Problem Frost nachts Offen Nachbehandlung Wäscheplane."
            ),
            ("Schalung erstellt", "Mauerwerk erstellt", "Bewehrung eingebaut", "Beton eingebracht"),
            expect_materials=("Beton",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Hochbau",
            "Erdarbeiten durchgeführt Schalung gestellt Betondecke gegossen.",
            ("Erdarbeiten durchgeführt", "Schalung erstellt", "Beton eingebracht"),
        ),
        BaseScenario("Hochbau", "Poroton 17,5er gemauert.", ("Mauerwerk erstellt",), min_activity_count=1),
    ]


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bUnterputz\b", "unter putz"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bSanierputz\b", "sanier putz"),
        (r"\bSockelputz\b", "sockel putz"),
        (r"\bHecke\b", "Ecke"),
        (r"\bGeotextil\b", "geo textil"),
        (r"\bDruckprüfung\b", "druck prüfung"),
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\blaufende Meter\b", "lauf ende meter"),
        (r"\bKG-Rohre\b", "ka ga rohre"),
        (r"\bFußbodenheizung\b", "fuss boden heizung"),
        (r"\bGipskarton\b", "gips karton"),
        (r"\bNivelliermasse\b", "nivellier masse"),
        (r"\bBewehrungsstahl\b", "be wehrungs stahl"),
        (r"\bRasenkantensteine\b", "rasen kanten steine"),
        (r"\bStelzlager\b", "stelz lager"),
        (r"\bWinterdienst\b", "winter dienst"),
        (r"\bHT-Rohre\b", "ht rohre"),
        (r"\bAbdichtung\b", "ab dichtung"),
        (r"\bFassadenarmierung\b", "fassaden armierung"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\buntergrund\b", "unter grund"),
        (r"\bschotter\b", "schot ter"),
        (r"\bverfugt\b", "ver fugt"),
        (r"\bverspachtelt\b", "ver spachtelt"),
        (r"\bkanal\b", "ka nal"),
        (r"\bplanum\b", "pla num"),
        (r"\bporoton\b", "poro ton"),
        (r"\bentwässerung\b", "ent wässerung"),
        (r"\brollrasen\b", "roll rasen"),
        (r"\bsilikonfugen\b", "silikon fugen"),
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
        ("abgeschlossen", "zu gemacht"),
        ("Problem:", "problem is"),
        ("Offen:", "offen is"),
        ("gesprochen", "gred"),
        ("Kubikmeter", "kubik"),
        ("informiert", "informiert"),
        ("montiert", "montiert"),
    ):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bwir haben\b", "mia ham", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKunde\b", "Kund", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgenau\b", "eba", out, flags=re.IGNORECASE)
    return out


def _mega_runon(text: str) -> str:
    core = re.sub(r"[.!?]+\s*", " und also ", text)
    return (
        f"Kurz gesagt vom Tag {core} und ja und dann Feierabend "
        f"und morgen machen wir den Rest fertig wenn das Material da ist."
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
        projectId="p-wave11",
        projectName="Pilot-Welle 11",
        customerName="Testkunde",
        date="2026-06-30",
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
        print("VIRTUAL-SPEECH-PILOT-WAVE11-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-PILOT-WAVE11-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
