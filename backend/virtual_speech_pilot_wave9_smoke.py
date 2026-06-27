"""Welle 9: Pilot-Vorbereitung — maximale Sprach-Vielfalt pro Gewerk.

Fokus:
- Lange Ketten + sehr lange Run-on-Sätze + kurze Einzeiler
- ASR/Whisper-Patzer, Worttrennungen, Dialekt-Färbungen
- Kundengespräch / Probleme / Offene Punkte im Mischtext
- Alle Gewerke gleichwertig abdecken

Rein additiv. Bei Fehlern patchen → erneut testen → weiter.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_pilot_wave9_")))
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
    summary_contains: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Case:
    name: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...]
    forbid_activities: tuple[str, ...]
    summary_contains: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool
    min_activity_count: int


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def _summary_needles(activities: tuple[str, ...]) -> tuple[str, ...]:
    out: list[str] = []
    for act in activities:
        low = act.casefold()
        for key, label in (
            ("kg-rohr", "KG"),
            ("unterputz", "Unterputz"),
            ("oberputz", "Oberputz"),
            ("altputz", "Altputz"),
            ("geschiffen", "geschiffen"),
            ("grundierung", "Grund"),
            ("ausgeschachtet", "ausgeschacht"),
            ("verdichtet", "verdicht"),
            ("pflaster", "Pflaster"),
            ("fliesen", "Fliesen"),
            ("heizkörper", "Heizkörper"),
            ("heizkoerper", "Heizkörper"),
            ("gipskarton", "Gipskarton"),
            ("schalung", "Schalung"),
            ("bewehrung", "Bewehrung"),
            ("hecke", "Hecke"),
            ("rasen", "Rasen"),
            ("drainage", "Drainage"),
            ("wdvs", "WDVS"),
        ):
            if key in low:
                out.append(label)
                break
        else:
            m = re.search(r"[a-zäöüß]{5,}", low)
            if m:
                out.append(m.group(0)[:8])
    return tuple(dict.fromkeys(out))


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ── Putz / Stuck ──────────────────────────────────────────────
        BaseScenario(
            "Putz",
            (
                "Heute haben wir den alten Putz abgetragen die Wand geschliffen danach grundiert "
                "dann haben wir den Unterputz aufgetragen. In der Zeit wo der Unterputz getrocknet ist "
                "haben wir uns mit der Kundin unterhalten die Kundin ist sehr zufrieden mit unserer Arbeit "
                "die wird uns auf jeden Fall weiterempfehlen. Problem der Untergrund war uneben es ist viel "
                "Material draufgegangen. Offen morgen noch Rest nacharbeiten. Nach dem Gespräch haben wir "
                "den Oberputz aufgetragen und dann waren wir fertig."
            ),
            ("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Putz",
            "Altputz runter Schimmel beseitigt Unterputz aufgetragen Oberputz aufgetragen.",
            ("Altputz entfernt", "Schimmel beseitigt", "Unterputz aufgetragen", "Oberputz aufgetragen"),
        ),
        BaseScenario(
            "Stuck",
            (
                "WDVS gedämmt Armierung aufgebracht Reibputz aufgetragen. Mit dem Kunden gesprochen, "
                "Kunde wünscht gleiche Putzstruktur am Nachbarhaus. Problem: Folie war knapp. "
                "Offen: Rest Armierung morgen fertig machen."
            ),
            ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario("Putz", "Sockelputz aufgetragen.", ("Sockelputz aufgetragen",)),

        # ── Tiefbau ───────────────────────────────────────────────────
        BaseScenario(
            "Tiefbau",
            (
                "Den Boden ausgeschachtet 30 laufende Meter KG-Rohre DN 110 verlegt Sand eingebaut "
                "und den Untergrund verdichtet. Problem: es hat zwischendurch geregnet der Graben "
                "war nass. Mit dem Bauherrn gesprochen er will morgen die Abnahme. "
                "Offen: Rest Schotter nachliefern."
            ),
            ("Boden ausgeschachtet", "KG-Rohre", "Sand eingebaut", "Untergrund verdichtet"),
            expect_materials=("KG-Rohre",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Tiefbau",
            "Graben ausgehoben Drainage eingebaut Hausanschluss hergestellt Leitungstrasse hergestellt.",
            ("Graben ausgehoben", "Drainage/Entwässerung eingebaut", "Hausanschluss hergestellt", "Leitungstrasse hergestellt"),
        ),
        BaseScenario(
            "Tiefbau",
            "Frostschutz eingebaut Planum verdichtet.",
            ("Frostschutz eingebaut", "Untergrund verdichtet"),
        ),
        BaseScenario("Tiefbau", "15 Meter Graben ausgehoben.", ("Graben ausgehoben",)),

        # ── GaLaBau ───────────────────────────────────────────────────
        BaseScenario(
            "GaLaBau",
            (
                "60 Quadratmeter Pflaster verlegt 25 laufende Meter Rasenkantensteine gesetzt "
                "die Hecke geschnitten und Rindenmulch eingedeckt. Kundin war da und sehr zufrieden. "
                "Problem: Lieferung Pflastersteine kam zu spät. Offen: zwei Paletten Nachschub bestellen."
            ),
            ("Pflaster verlegt", "Rasenkantensteine gesetzt", "Hecke geschnitten", "Rindenmulch eingedeckt"),
            expect_materials=("Pflastersteine",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "GaLaBau",
            (
                "Rasen gemäht Rasen vertikutiert Rasen gedüngt Fläche bewässert "
                "und 15 laufende Meter Palisaden gesetzt."
            ),
            ("Rasen gemäht", "Rasen vertikutiert", "Rasen gedüngt", "Fläche bewässert", "Palisaden gesetzt"),
        ),
        BaseScenario(
            "GaLaBau",
            "Keramikterrasse verlegt Geotextil verlegt Splitt eingebaut.",
            ("Keramikterrasse verlegt", "Geotextil verlegt", "Splitt eingebaut"),
        ),
        BaseScenario("GaLaBau", "Unkraut entfernt.", ("Unkraut entfernt",)),

        # ── SHK ───────────────────────────────────────────────────────
        BaseScenario(
            "SHK",
            (
                "25 laufende Meter KG-Rohre DN 160 verlegt drei Heizkörper montiert WC gesetzt "
                "und Druckprüfung durchgeführt. Kunde informiert über Heizungsplan. "
                "Problem: ein Bogen fehlte auf der Baustelle. Offen: Bogen morgen nachlegen."
            ),
            ("KG-Rohre", "Heizkörper montiert", "WC montiert", "Druckprüfung durchgeführt"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "SHK",
            "Wasserleitungen verlegt Fußbodenheizung verlegt hydraulischen Abgleich durchgeführt.",
            ("Wasserleitungen verlegt", "Fußbodenheizung verlegt", "Hydraulischer Abgleich durchgeführt"),
        ),
        BaseScenario(
            "SHK",
            "Waschbecken montiert Dusche montiert Armaturen montiert.",
            ("Waschbecken montiert", "Dusche montiert", "Armaturen montiert"),
        ),
        BaseScenario("SHK", "Heizkörper montiert.", ("Heizkörper montiert",)),

        # ── Fliesen ───────────────────────────────────────────────────
        BaseScenario(
            "Fliesen",
            (
                "Wand grundiert Nivelliermasse aufgetragen 35 Quadratmeter Fliesen verlegt "
                "verfugt und Silikonfugen gezogen. Kundin hat Farbe bestätigt. "
                "Problem: Untergrund war uneben viel Ausgleichsmasse nötig. "
                "Offen: Restsilikon morgen nachziehen."
            ),
            ("Grundierung aufgetragen", "Nivelliermasse aufgetragen", "Fliesen verlegt", "Fliesen verfugt", "Silikonfugen silikoniert"),
            expect_materials=("Fliesen",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Fliesen",
            "Abdichtung hergestellt Bodenablauf eingebaut Großformatfliesen verlegt.",
            ("Abdichtung hergestellt", "Bodenablauf eingebaut", "Großformatfliesen verlegt"),
        ),
        BaseScenario("Fliesen", "Fliesenkleber aufgetragen Fliesen verlegt.", ("Fliesenkleber aufgetragen", "Fliesen verlegt")),

        # ── Trockenbau ────────────────────────────────────────────────
        BaseScenario(
            "Trockenbau",
            (
                "Ständerwerk montiert Dämmung eingebaut Gipskartonplatten beplankt Fugen verspachtelt. "
                "Mit Bauleitung abgestimmt. Problem: Lieferung Rigips kam erst mittags. "
                "Offen: Revisionsklappe morgen setzen."
            ),
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Fugen verspachtelt"),
            expect_materials=("Gipskartonplatten",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Trockenbau",
            "Decke abgehängt Trockenbauwand geschlossen.",
            ("Decke abgehängt", "Trockenbauwand geschlossen"),
        ),
        BaseScenario("Trockenbau", "Gipskarton montiert.", ("Gipskartonplatten montiert",)),

        # ── Hochbau ───────────────────────────────────────────────────
        BaseScenario(
            "Hochbau",
            (
                "Schalung erstellt Bewehrung eingebaut 8 Kubikmeter Beton eingebracht. "
                "Bauherr war vor Ort sehr zufrieden. Problem: Regen zwischendurch Schalung "
                "musste abgedeckt werden. Offen: Schalung Freitag abbauen."
            ),
            ("Schalung erstellt", "Bewehrung eingebaut", "Beton eingebracht"),
            expect_materials=("Beton",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Hochbau",
            "Fundament erstellt Mauerwerk gemauert Betondecke gegossen.",
            ("Fundament erstellt", "Mauerwerk erstellt"),
        ),
        BaseScenario("Hochbau", "Bewehrung eingebaut.", ("Bewehrung eingebaut",)),
    ]


def _whisper_asr(text: str) -> str:
    out = text
    pairs = (
        (r"\bUnterputz\b", "unter putz"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bAltputz\b", "alt putz"),
        (r"\bGrundputz\b", "grund putz"),
        (r"\bHecke\b", "Ecke"),
        (r"\bGeotextil\b", "Geo textil"),
        (r"\bDruckprüfung\b", "Druck prüfung"),
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\blaufende Meter\b", "lauf ende meter"),
        (r"\bKG-Rohre\b", "ka ga rohre"),
        (r"\bFußbodenheizung\b", "fuss boden heizung"),
        (r"\bGipskartonplatten\b", "gips karton platten"),
        (r"\bNivelliermasse\b", "nivellier masse"),
        (r"\bRasenkantensteine\b", "rasen kanten steine"),
        (r"\bausgeschachtet\b", "aus geschachtet"),
        (r"\bverschachtet\b", "ver schachtet"),
        (r"\bSilikonfugen\b", "silikon fugen"),
        (r"\bGroßformatfliesen\b", "gross format fliesen"),
        (r"\bBewehrung\b", "be wehrung"),
        (r"\bHydraulischer\b", "hydraulischer"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _broken_de(text: str) -> str:
    out = text
    repl = (
        ("haben wir", "hamma"),
        ("Heute", "heute"),
        ("und dann", "dann"),
        ("Quadratmeter", "quadrat"),
        ("laufende Meter", "lauf meter"),
        ("durchgeführt", "durch gemacht"),
        ("montiert", "montiert"),
        ("gesprochen", "gred"),
        ("Problem:", "problem is"),
        ("Offen:", "offen is"),
    )
    for a, b in repl:
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    """Leichte Dialekt-Färbung (Süddeutsch / Ruhr / Ost) — typisch für Baustellen."""
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bwir haben\b", "mia ham", out, flags=re.IGNORECASE)
    out = re.sub(r"\bdas\b", "des", out, flags=re.IGNORECASE, count=3)
    out = re.sub(r"\bgenau\b", "eba", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKunde\b", "Kund", out, flags=re.IGNORECASE)
    return out


def _long_runon(text: str) -> str:
    """Sehr langer Run-on-Satz ohne klare Satzgrenzen."""
    core = re.sub(r"\.\s+", " und also ", text)
    return (
        f"Also kurz und knapp vom Schichtende {core} und ja so war der Tag "
        f"eigentlich und Feierabend war dann so gegen halb sechs."
    )


def _build_cases() -> list[Case]:
    bases = _base_scenarios()
    cases: list[Case] = []
    idx = 1
    builders: list[tuple[str, callable]] = [
        ("N", lambda t: t),
        ("W", _whisper_asr),
        ("B", _broken_de),
        ("D", _dialect_de),
        ("L", _long_runon),
    ]
    for tag, builder in builders:
        for base in bases:
            raw = builder(base.raw)
            summary = base.summary_contains or _summary_needles(base.expect_activities)
            cases.append(
                Case(
                    name=f"{base.trade}_{idx:03d}_{tag}",
                    raw=raw,
                    expect_activities=base.expect_activities,
                    expect_materials=base.expect_materials,
                    forbid_activities=base.forbid_activities,
                    summary_contains=summary,
                    expect_problem=base.expect_problem,
                    expect_open=base.expect_open,
                    expect_customer=base.expect_customer,
                    min_activity_count=len(base.expect_activities),
                )
            )
            idx += 1
    return cases


def _has_customer_talk(text: str) -> bool:
    low = text.casefold()
    hints = (
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
    )
    return any(h in low for h in hints)


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="p-wave9",
        projectName="Pilot-Welle 9",
        customerName="Testkunde",
        date="2026-06-28",
        employeeNames=["Max", "Goran", "Ahmet", "Stefan"],
        startTime="06:30",
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

        if acts:
            if not summary or len(summary.strip()) < 12:
                failures.append(f"{case.name}: summary leer/zu kurz")
            if case.summary_contains and len(case.expect_activities) >= 3:
                hits = sum(1 for n in case.summary_contains if n.casefold() in summary.casefold())
                needed = max(2, (len(case.summary_contains) + 1) // 2)
                if hits < needed:
                    failures.append(
                        f"{case.name}: summary dünn ({hits}/{needed}) need={case.summary_contains!r}"
                    )

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer")
        if case.expect_customer and not _has_customer_talk(customer):
            failures.append(f"{case.name}: customerTalk fehlt (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-PILOT-WAVE9-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:600]:
            print(" -", row)
        if len(failures) > 600:
            print(f" ... und {len(failures) - 600} weitere")
        return 1

    print("VIRTUAL-SPEECH-PILOT-WAVE9-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
