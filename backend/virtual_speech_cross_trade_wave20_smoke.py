"""Welle 20: Cross-Gewerke — Kundengespräch, Problem, Offen, Summary-Qualität.

Alle Gewerke: kurz/lang, mit/ohne Punkt, Ketten, Whisper/Dialekt/gebrochenes Deutsch.
Schwerpunkt: Kundengespräch isoliert, Probleme/Offene sauber, Summary ohne Material-Echo.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_cross_wave20_")))
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
    customer_must_not_contain: tuple[str, ...] = field(default_factory=tuple)
    forbid_summary_contains: tuple[str, ...] = field(default_factory=tuple)
    forbid_summary_material_echo: bool = False


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
    customer_must_not_contain: tuple[str, ...]
    forbid_summary_contains: tuple[str, ...]
    forbid_summary_material_echo: bool


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def _contains_in_text(haystack: str, needle: str) -> bool:
    return needle.casefold() in haystack.casefold()


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


_MATERIAL_ECHO_SUMMARY = re.compile(
    r"\b(?:verarbeitet|verbaut|verwendet|eingesetzt|eingebaut|zum\s+einsatz)\b",
    flags=re.IGNORECASE,
)


def _summary_has_material_echo(summary: str, materials: list[str], activities: list[str]) -> str | None:
    """Erkennt Summary-Sätze, die nur Material aus der Liste wiederholen."""
    low = summary.casefold()
    acts_joined = " ".join(activities).casefold()
    for mat in materials:
        m = str(mat).casefold().strip()
        if not m or m not in low:
            continue
        if not _MATERIAL_ECHO_SUMMARY.search(low):
            continue
        # Pflaster verlegt + Pflastersteine in Summary = Echo
        if "pflasterstein" in m and "pflaster" in acts_joined and "pflasterstein" in low:
            return f"Material-Echo Pflaster/Pflastersteine in Summary"
        if m in acts_joined and m in low and _MATERIAL_ECHO_SUMMARY.search(low):
            # z.B. "Fliesen verarbeitet" wenn schon "Fliesen verlegt"
            if "fliesen verlegt" in acts_joined and "fliesen" in m:
                return f"Material-Echo Fliesen in Summary"
            if "putz" in m and "putz" in acts_joined:
                return f"Material-Echo Putz in Summary"
    if re.search(r"\bdaf(ü|ue)r\s+kam", low) and any("pflasterstein" in str(x).casefold() for x in materials):
        return "dafür kamen … zum Einsatz in Summary"
    return None


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ── GaLaBau: Kunde + Problem + Offen + Material-Echo ──
        BaseScenario(
            (
                "50 Quadratmeter Pflaster verlegt und Pflastersteine verarbeitet "
                "zwei Kubikmeter Schotter eingebaut Problem Lieferung kam spät "
                "Offen letzte Reihe morgen Mit der Kundin gesprochen sie war sehr zufrieden."
            ),
            ("50 m² Pflaster verlegt", "Schotter eingebaut"),
            expect_materials=("Pflastersteine", "Schotter"),
            forbid_activities=("Pflastersteine verarbeitet",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            customer_must_not_contain=("50", "qm", "m²", "pflaster verlegt", "schotter"),
            forbid_summary_contains=("Pflastersteine verarbeitet", "zum Einsatz"),
            forbid_summary_material_echo=True,
        ),
        BaseScenario(
            (
                "Heute haben wir 50 qm² pflaster gelegt. Anschließend haben wir uns mit der Kundin "
                "unterhalten und die Kundin war sehr zufrieden."
            ),
            ("50 m² Pflaster verlegt",),
            expect_materials=("Pflastersteine",),
            expect_customer=True,
            customer_must_not_contain=("50", "pflaster gelegt", "qm"),
        ),
        BaseScenario(
            (
                "heute 30 quadrat pflaster gelegt und schotter reingemacht und kundin zufrieden "
                "problem regen offen rest montag"
            ),
            ("30 m² Pflaster verlegt", "Schotter eingebaut"),
            expect_materials=("Pflastersteine", "Schotter"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            customer_must_not_contain=("30", "quadrat", "schotter"),
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
            "15 Quadratmeter Naturstein verlegt und Fugen verfugt.",
            ("Naturstein verlegt", "Fliesen verfugt"),
            min_activity_count=1,
        ),
        # ── Fliesen ──
        BaseScenario(
            (
                "Im Bad 25 Quadratmeter Fliesen verlegt Silikonfugen gemacht "
                "Problem Wasserdruck zu niedrig Offen Armatur morgen "
                "mit dem Kunden gesprochen er war zufrieden."
            ),
            ("25 m² Fliesen verlegt", "Silikonfugen"),
            expect_materials=("Fliesen",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            customer_must_not_contain=("25", "fliesen verlegt", "bad"),
        ),
        BaseScenario(
            "40 Quadratmeter Fliesen verlegt Fliesenkleber verwendet.",
            ("40 m² Fliesen verlegt", "Fliesenkleber"),
            expect_materials=("Fliesen", "Fliesenkleber"),
            forbid_summary_contains=("Fliesen verarbeitet",),
        ),
        BaseScenario(
            "35 qm Fliesen gelegt Fliesen verarbeitet.",
            ("35 m² Fliesen verlegt",),
            expect_materials=("Fliesen",),
            forbid_activities=("Fliesen verarbeitet",),
            forbid_summary_material_echo=True,
        ),
        BaseScenario(
            "WC montiert Waschbecken montiert.",
            ("WC montiert", "Waschbecken montiert"),
            min_activity_count=1,
        ),
        # ── Putz & Stuck ──
        BaseScenario(
            (
                "120 Quadratmeter Außenputz aufgetragen Grundierung aufgetragen "
                "Problem Gerüst zu spät Offen Sockel nächste Woche "
                "Bauherr kurz informiert alles abgestimmt."
            ),
            ("Außenputz aufgetragen", "Grundierung aufgetragen"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            customer_must_not_contain=("120", "putz", "qm", "m²"),
        ),
        BaseScenario(
            "80 qm Putz aufgetragen Putz verarbeitet.",
            ("Putz aufgebracht",),
            expect_materials=("Putz",),
            forbid_summary_contains=("Putz verarbeitet",),
            forbid_summary_material_echo=True,
        ),
        BaseScenario(
            "WDVS gedämmt Fassadenarmierung ausgeführt.",
            ("WDVS ausgeführt", "Fassadenarmierung"),
            min_activity_count=1,
        ),
        BaseScenario(
            "Stuck geschlagen Gesims hergestellt Problem Form Offen Rest Freitag.",
            ("Stuckarbeiten",),
            expect_problem=True,
            expect_open=True,
            min_activity_count=1,
        ),
        # ── Trockenbau ──
        BaseScenario(
            (
                "Gipskartonplatten montiert Decke abgehängt Problem Lieferung Offen letzte Wand "
                "mit der Bauleitung Rücksprache gehalten."
            ),
            ("Gipskartonplatten montiert", "Decke abgehängt"),
            expect_materials=("Gipskartonplatten",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            customer_must_not_contain=("gipskarton", "decke"),
        ),
        BaseScenario(
            "Trockenbauwand geschlossen Ständerwerk montiert.",
            ("Trockenbauwand geschlossen", "Ständerwerk montiert"),
            min_activity_count=1,
        ),
        BaseScenario(
            "Brandschutzwand hergestellt Akustikdecke eingebaut.",
            ("Brandschutzwand hergestellt", "Akustikdecke eingebaut"),
            min_activity_count=1,
        ),
        BaseScenario(
            "heute ich hab gipskarton gemacht und decke abhaengen problem schrauben offen morgen",
            ("Gipskartonplatten montiert",),
            expect_problem=True,
            expect_open=True,
            min_activity_count=1,
        ),
        # ── SHK ──
        BaseScenario(
            (
                "40 laufende Meter KG-Rohre verlegt HT-Manschette montiert "
                "Problem Anschluss undicht Offen Druckprüfung morgen "
                "Kunde informiert war einverstanden."
            ),
            ("KG-Rohre verlegt", "HT-Manschette montiert"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            customer_must_not_contain=("kg", "rohr", "meter", "manschette"),
        ),
        BaseScenario(
            (
                "Heizkörper montiert Thermostatventile eingebaut "
                "Problem Umlauf Offen hydraulischer Abgleich "
                "mit dem Kunden gesprochen zufrieden."
            ),
            ("Heizkörper montiert",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            customer_must_not_contain=("heizkörper", "thermostat"),
        ),
        BaseScenario(
            "Dusche montiert Armaturen montiert Kundin sehr zufrieden.",
            ("Dusche montiert", "Armaturen montiert"),
            expect_customer=True,
            customer_must_not_contain=("dusche", "armatur"),
        ),
        BaseScenario(
            "Druckprüfung durchgeführt.",
            ("Druckprüfung durchgeführt",),
            min_activity_count=1,
        ),
        # ── Hochbau ──
        BaseScenario(
            (
                "Fundament betoniert Schalung erstellt Problem Wetter Offen Bewehrung Montag "
                "Bauleitung informiert."
            ),
            ("Fundament erstellt", "Schalung erstellt"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            customer_must_not_contain=("fundament", "beton", "schalung"),
        ),
        BaseScenario(
            "Mauerwerk erstellt Bewehrung eingebaut.",
            ("Mauerwerk erstellt", "Bewehrung eingebaut"),
            min_activity_count=1,
        ),
        BaseScenario(
            "Filigrandecke montiert Fußbodenheizung verlegt.",
            ("Filigrandecke montiert", "Fußbodenheizung verlegt"),
            min_activity_count=1,
        ),
        BaseScenario(
            "heute beton gegossen problem regen offen rest morgen kunde gred war ok",
            ("Beton eingebracht",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            min_activity_count=1,
        ),
        # ── Tiefbau ──
        BaseScenario(
            (
                "Graben ausgehoben Kanalrohre verlegt Problem Leitung Offen Verfüllung morgen "
                "Auftraggeber kurz gesprochen."
            ),
            ("Graben ausgehoben",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            customer_must_not_contain=("graben", "kanal", "meter"),
        ),
        BaseScenario(
            "Asphalt eingebaut Untergrund verdichtet Problem Maschine Offen letzte Bahn.",
            ("Asphalt eingebaut", "Untergrund verdichtet"),
            expect_problem=True,
            expect_open=True,
            min_activity_count=1,
        ),
        BaseScenario(
            "Verbau gesetzt Spundwand eingebaut.",
            ("Verbau gesetzt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Hausanschluss hergestellt Problem Wasserdruck Offen Anmeldung Kunde zufrieden.",
            ("Hausanschluss hergestellt",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            min_activity_count=1,
        ),
        # ── Wild-Ketten / Kurz / Nur Kunde ──
        BaseScenario(
            (
                "Morgens 20 qm Pflaster gelegt dann 15 qm Fliesen im Bad verlegt "
                "dann Putz im Flur aufgetragen Problem Zeitdruck Offen alles nächste Woche "
                "Kundin mega zufrieden."
            ),
            ("20 m² Pflaster verlegt",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            min_activity_count=1,
            customer_must_not_contain=("fliesen", "putz"),
        ),
        BaseScenario(
            "Mit dem Kunden gesprochen er war sehr zufrieden und möchte weiter mit uns arbeiten.",
            (),
            expect_customer=True,
            min_activity_count=0,
            customer_must_not_contain=("m²", "qm"),
        ),
        BaseScenario(
            "Heute 40 Quadratmeter Pflaster verlegt und Feierabend.",
            ("40 m² Pflaster verlegt",),
            expect_materials=("Pflastersteine",),
            min_activity_count=1,
        ),
    ]


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bRasenkantensteine\b", "rasen kanten steine"),
        (r"\bGipskartonplatten\b", "gips karton platten"),
        (r"\bThermostatventile\b", "thermo stat ventile"),
        (r"\bHeizkörper\b", "heiz körper"),
        (r"\bFußbodenheizung\b", "fuss boden heizung"),
        (r"\bFiligrandecke\b", "filigran decke"),
        (r"\bSchotter\b", "schot ter"),
        (r"\bPflastersteine\b", "pflaster steine"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bverlegt\b", "ver legt"),
        (r"\bgesprochen\b", "ge sprochen"),
        (r"\bzufrieden\b", "zu frieden"),
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
        ("Problem", "problem is"),
        ("Offen", "offen is"),
        ("Kundin", "kundin"),
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
                    name=f"Cross_{idx:03d}_{tag}",
                    raw=raw,
                    expect_activities=base.expect_activities,
                    expect_materials=base.expect_materials,
                    forbid_activities=base.forbid_activities,
                    expect_problem=base.expect_problem,
                    expect_open=base.expect_open,
                    expect_customer=base.expect_customer,
                    min_activity_count=min_count,
                    customer_must_not_contain=base.customer_must_not_contain,
                    forbid_summary_contains=base.forbid_summary_contains,
                    forbid_summary_material_echo=base.forbid_summary_material_echo,
                )
            )
            idx += 1
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="cross-wave20",
        projectName="Cross-Gewerke Welle 20",
        customerName="Testkunde",
        date="2026-07-27",
        employeeNames=["Max", "Goran", "Ahmet", "Stefan", "Murat", "Dennis"],
        startTime="06:00",
        endTime="18:00",
        exportFormat="PDF",
        rawText=case.raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["FREIRAUM_AI_STRUCTURING"] = ""
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

        for forbidden in case.forbid_summary_contains:
            if _contains_in_text(summary, forbidden):
                failures.append(f"{case.name}: summary verboten -> {forbidden!r} (got={summary!r})")

        if case.forbid_summary_material_echo:
            echo = _summary_has_material_echo(summary, mats, acts)
            if echo:
                failures.append(f"{case.name}: {echo} (summary={summary!r})")

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer")

        if case.expect_customer:
            if not _has_customer_talk(customer):
                failures.append(f"{case.name}: customerTalk fehlt (got={customer!r})")
            for token in case.customer_must_not_contain:
                if _contains_in_text(customer, token):
                    failures.append(f"{case.name}: customerTalk enthält verboten {token!r} (got={customer!r})")
            if summary and customer.casefold() == summary.casefold() and customer.casefold() not in {
                "",
                "keine angabe",
            }:
                failures.append(f"{case.name}: customerTalk ist Summary-Kopie")

    if failures:
        print("VIRTUAL-SPEECH-CROSS-TRADE-WAVE20-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-CROSS-TRADE-WAVE20-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
