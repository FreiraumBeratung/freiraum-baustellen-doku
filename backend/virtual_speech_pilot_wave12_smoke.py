"""Welle 12: Fokus schwächere Gewerke — Trockenbau, Fliesen, Stuck, Tiefbau, Hochbau.

Umgangssprache, ASR/Whisper, kurz/lang, Ketten, Kunde/Problem/Offen.
Ziel: Niveau GaLaBau/Putz (8,5) für alle Gewerke. Rein additiv.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_pilot_wave12_")))
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
        # ═══ TROCKENBAU (Schwerpunkt) ═══
        BaseScenario(
            "Trockenbau",
            (
                "Morgens erst die Ständerwerksprofile an die Wand festgeschraubt dann die Dämmmatte "
                "reingepackt danach die GK Platten bzw Gipskartonplatten dran montiert "
                "Fugen gespachtelt und die Decke abgehängt Bauleitung war da Problem Lieferung "
                "kam spät Offen Revisionsklappe morgen noch."
            ),
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Fugen verspachtelt", "Decke abgehängt"),
            expect_materials=("Gipskartonplatten",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Trockenbau",
            (
                "CW Profile und UW Profile an die Decke und Wand geschraubt Mineralwolle eingesetzt "
                "zwei Lagen Rigips verschraubt Fugenspachtel drüber gezogen Akustikdecke runtergehängt "
                "Brandschutzplatten beplankt Trockenbauwand zu gemacht."
            ),
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Fugen verspachtelt", "Decke abgehängt", "Trockenbauwand geschlossen"),
        ),
        BaseScenario(
            "Trockenbau",
            "Ständerwerk angebaut Dämmung reingemacht Rigipsplatten festgeschraubt Decke montiert.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Decke abgehängt"),
        ),
        BaseScenario(
            "Trockenbau",
            "Profile montiert Gipskarton beplankt Fugen verspachtelt Brandschutz beplankt.",
            ("Ständerwerk montiert", "Gipskartonplatten montiert", "Fugen verspachtelt"),
        ),
        BaseScenario("Trockenbau", "GK Platten montiert fertig.", ("Gipskartonplatten montiert",), min_activity_count=1),
        BaseScenario("Trockenbau", "Rigips dran gemacht.", ("Gipskartonplatten montiert",), min_activity_count=1),
        BaseScenario("Trockenbau", "Decke abgehangen Fugen gespachtelt.", ("Decke abgehängt", "Fugen verspachtelt")),
        BaseScenario(
            "Trockenbau",
            "Schnellbauschrauben reingedreht UW CW Profile gesetzt Dämmung eingebaut und Wand geschlossen.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Trockenbauwand geschlossen"),
        ),

        # ═══ FLIESEN ═══
        BaseScenario(
            "Fliesen",
            (
                "Im Bad erst Wandfliesen drauf geklebt dann Bodenfliesen verlegt und verfugt "
                "Abdichtung im Duschbereich gemacht Nivelliermasse gezogen Silikonfugen nachgezogen "
                "Kunde meckert wegen Farbe Problem Wand schief Offen Rest Silikon Donnerstag."
            ),
            ("Fliesen verlegt", "Fliesen verfugt", "Abdichtung hergestellt", "Nivelliermasse aufgetragen"),
            expect_materials=("Fliesen",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Fliesen",
            "Fliesenkleber aufgezogen Großformatfliesen verlegt Bodenablauf eingebaut Duschrinne gesetzt.",
            ("Fliesenkleber aufgetragen", "Großformatfliesen verlegt", "Bodenablauf eingebaut"),
        ),
        BaseScenario(
            "Fliesen",
            "Wandfliesen geklebt Bodenfliesen verfugt Flexkleber gezogen Naturstein verlegt.",
            ("Fliesen verlegt", "Fliesen verfugt", "Fliesenkleber aufgetragen", "Naturstein verlegt"),
        ),
        BaseScenario("Fliesen", "30 Quadratmeter Fliesen gelegt fertig.", ("Fliesen verlegt",), min_activity_count=1),
        BaseScenario("Fliesen", "Bad fliesen fertig gemacht.", ("Fliesen verlegt",), min_activity_count=1),

        # ═══ STUCK ═══
        BaseScenario(
            "Stuck",
            (
                "WDVS Platten angeklebt Armierungsgewebe eingebettet Reibputz drauf gemacht "
                "Sockelleiste stucken Kunde informiert Problem Kleber knapp Offen Rest morgen."
            ),
            ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Stuck",
            "Fassade gedämmt Gewebe reingemacht Außenputz aufgetragen Gesims stuckiert.",
            ("WDVS ausgeführt", "Fassadenarmierung ausgeführt", "Außenputz aufgetragen"),
        ),
        BaseScenario("Stuck", "Stuckarbeiten gemacht.", ("Stuckarbeiten durchgeführt",), min_activity_count=1),

        # ═══ TIEFBAU ═══
        BaseScenario(
            "Tiefbau",
            (
                "Erdaushub gemacht 22 laufende Meter KG Rohre DN 125 verlegt Splittschicht reingepackt "
                "Graben verfüllt Planum verdichtet Hausanschluss vorbereitet "
                "Auftraggeber da Problem Plan fehlt Offen Schacht setzen."
            ),
            ("Graben ausgehoben", "KG-Rohre", "Splitt eingebaut", "Graben verfüllt", "Untergrund verdichtet"),
            expect_materials=("KG-Rohre",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Tiefbau",
            "Baugrube ausgehoben Kanal angeschlossen Drainage verlegt Leitungstrasse angelegt.",
            ("Graben ausgehoben", "Kanal-/Schachtarbeiten durchgeführt", "Drainage/Entwässerung eingebaut", "Leitungstrasse hergestellt"),
        ),
        BaseScenario("Tiefbau", "Sand reingepackt und verdichtet.", ("Sand eingebaut", "Untergrund verdichtet")),
        BaseScenario("Tiefbau", "15 Meter KG verlegt fertig.", ("KG-Rohre",), min_activity_count=1),

        # ═══ HOCHBAU ═══
        BaseScenario(
            "Hochbau",
            (
                "Fundamentplatte geschalt 15er Poroton hochgemauert Bewehrungsstahl gebunden "
                "8 Kubikmeter Beton gegossen Schalung abgebaut "
                "Bauherr zufrieden Problem Frost nachts Offen Nachbehandlung Plane."
            ),
            ("Schalung erstellt", "Mauerwerk erstellt", "Bewehrung eingebaut", "Beton eingebracht"),
            expect_materials=("Beton",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Hochbau",
            "Erdarbeiten gemacht Schalung gestellt Betondecke gegossen Fundament erstellt.",
            ("Erdarbeiten durchgeführt", "Schalung erstellt", "Beton eingebracht", "Fundament erstellt"),
        ),
        BaseScenario("Hochbau", "11,5er Poroton gemauert.", ("Mauerwerk erstellt",), min_activity_count=1),
        BaseScenario("Hochbau", "5 Kubik Beton gegossen fertig.", ("Beton eingebracht",), min_activity_count=1),

        # ═══ Leicht: starke Gewerke (Regression) ═══
        BaseScenario("GaLaBau", "60 Quadratmeter Pflaster gelegt Hecke geschnitten fertig.", ("Pflaster verlegt", "Hecke geschnitten")),
        BaseScenario("Putz", "Unterputz aufgetragen Oberputz gemacht.", ("Unterputz aufgetragen", "Oberputz aufgetragen")),
        BaseScenario("SHK", "Heizkörper montiert WC gesetzt.", ("Heizkörper montiert", "WC montiert")),
    ]


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bStänderwerk\b", "staender werk"),
        (r"\bStänderwerksprofile\b", "staender werks profile"),
        (r"\bGipskartonplatten\b", "gips karton platten"),
        (r"\bGK Platten\b", "gk platten"),
        (r"\bGK-Platten\b", "gk platten"),
        (r"\bRigips\b", "ri gips"),
        (r"\bFugenspachtel\b", "fugen spachtel"),
        (r"\bMineralwolle\b", "mineral wolle"),
        (r"\bFliesenkleber\b", "fliesen kleber"),
        (r"\bGroßformatfliesen\b", "gross format fliesen"),
        (r"\bNivelliermasse\b", "nivellier masse"),
        (r"\bAbdichtung\b", "ab dichtung"),
        (r"\bKG-Rohre\b", "ka ga rohre"),
        (r"\bKG Rohre\b", "ka ga rohre"),
        (r"\bBewehrungsstahl\b", "be wehrungs stahl"),
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\blaufende Meter\b", "lauf ende meter"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bprofile\b", "pro file"),
        (r"\bverschraubt\b", "ver schraubt"),
        (r"\bverspachtelt\b", "ver spachtelt"),
        (r"\bverfugt\b", "ver fugt"),
        (r"\babgehängt\b", "abge haengt"),
        (r"\bgeschraubt\b", "ge schraubt"),
        (r"\bkanal\b", "ka nal"),
        (r"\bplanum\b", "pla num"),
        (r"\bporoton\b", "poro ton"),
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
        ("montiert", "montiert"),
        ("geschraubt", "fest gemacht"),
        ("gespachtelt", "zu gemacht"),
        ("verlegt", "gelegt"),
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
    out = re.sub(r"\bdann\b", "denn", out, flags=re.IGNORECASE, count=4)
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
        projectId="p-wave12",
        projectName="Pilot-Welle 12",
        customerName="Testkunde",
        date="2026-07-01",
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
        print("VIRTUAL-SPEECH-PILOT-WAVE12-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-PILOT-WAVE12-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
