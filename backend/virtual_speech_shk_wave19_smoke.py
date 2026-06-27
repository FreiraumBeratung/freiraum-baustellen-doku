"""Welle 19: SHK-only — Herz-Nieren-Test für das komplette Gewerk.

Nur SHK (Sanitär, Heizung, Klima): kurz/lang, Umgangssprache, ASR/Whisper, Dialekt,
gebrochenes Deutsch, Kundengespräch, Problem, Offen. Rein additiv.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_shk_wave19_")))
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
    _kg_forbid = ("Wasserleitungen verlegt",)
    return [
        # ── Komplett-Tagesbericht ──
        BaseScenario(
            (
                "Morgens 20 laufende Meter KG-Rohre DN 160 verlegt HT-Rohre DN 50 verlegt "
                "drei Heizkörper montiert WC gesetzt Waschbecken montiert Druckprüfung durchgeführt "
                "Bauleitung kurz da Problem ein KG-Bogen fehlte Offen Bogen morgen nachlegen "
                "nach dem Kundengespräch Feierabend."
            ),
            (
                "KG-Rohre",
                "HT-Rohre",
                "Heizkörper montiert",
                "WC montiert",
                "Waschbecken montiert",
                "Druckprüfung durchgeführt",
            ),
            expect_materials=("KG-Rohre",),
            forbid_activities=_kg_forbid,
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Wasserleitungen verlegt Fußbodenheizung verlegt hydraulischen Abgleich durchgeführt.",
            (
                "Wasserleitungen verlegt",
                "Fußbodenheizung verlegt",
                "Hydraulischer Abgleich durchgeführt",
            ),
        ),
        BaseScenario(
            (
                "WC montiert Waschbecken montiert Dusche montiert Armaturen montiert "
                "und Druckprüfung gemacht."
            ),
            (
                "WC montiert",
                "Waschbecken montiert",
                "Dusche montiert",
                "Armaturen montiert",
                "Druckprüfung durchgeführt",
            ),
        ),
        BaseScenario(
            "30 laufende Meter KG-Rohre DN 110 verlegt drei Heizkörper montiert Druckprüfung durchgeführt.",
            ("KG-Rohre DN 110", "Heizkörper montiert", "Druckprüfung durchgeführt"),
            expect_materials=("KG-Rohre",),
            forbid_activities=_kg_forbid,
        ),
        BaseScenario(
            (
                "25 laufende Meter KG-Rohre DN 160 verlegt zwei KG-Bögen gesetzt einen KG-Abzweig eingebaut "
                "14 laufende Meter HT-Rohre DN 50 verlegt HT-Manschette montiert."
            ),
            (
                "KG-Rohre DN 160",
                "KG-Bögen",
                "KG-Abzweig",
                "HT-Rohre DN 50",
                "HT-Manschette",
            ),
            expect_materials=("KG-Rohre", "HT-Rohre"),
            forbid_activities=_kg_forbid,
        ),
        BaseScenario(
            "KG-Rohre verlegt zwei KG-Bögen eingebaut einen KG-Abzweig eingebaut.",
            ("KG-Rohre", "KG-Bögen", "KG-Abzweig"),
            forbid_activities=_kg_forbid,
        ),
        # ── Kurzberichte ──
        BaseScenario("Heizkörper montiert fertig.", ("Heizkörper montiert",), min_activity_count=1),
        BaseScenario("WC montiert.", ("WC montiert",), min_activity_count=1),
        BaseScenario("Wasserleitungen verlegt.", ("Wasserleitungen verlegt",), min_activity_count=1),
        BaseScenario(
            (
                "Fußbodenheizung verlegt Heizkreisverteiler angeschlossen "
                "Wärmepumpe installiert Heizungsanschlüsse montiert."
            ),
            (
                "Fußbodenheizung verlegt",
                "Heizungsanschlüsse montiert",
                "Wärmepumpe installiert",
            ),
        ),
        BaseScenario("15 Meter KG verlegt fertig.", ("KG-Rohre",), forbid_activities=_kg_forbid, min_activity_count=1),
        BaseScenario(
            "14 laufende Meter HT-Rohre DN 50 verlegt.",
            ("HT-Rohre",),
            min_activity_count=1,
        ),
        # ── Gebrochenes Deutsch ──
        BaseScenario(
            (
                "heute rohre gelegt heizung angeschlossen wasser angeschlossen "
                "dann druckprobe gemacht und abgleich gemacht"
            ),
            (
                "Wasserleitungen verlegt",
                "Heizungsanschlüsse montiert",
                "Druckprüfung durchgeführt",
                "Hydraulischer Abgleich durchgeführt",
            ),
        ),
        BaseScenario(
            "ich hab gemacht KG Bögen und KG Abzweig.",
            ("KG-Bögen eingebaut", "KG-Abzweig eingebaut"),
        ),
        BaseScenario(
            "heute ich hab 20 laufende meter kg rohre verlegt.",
            ("KG-Rohre",),
            forbid_activities=_kg_forbid,
            min_activity_count=1,
        ),
        BaseScenario(
            "heute ich hab gemacht wasserleitungen und fussbodenheizung verlegt.",
            ("Wasserleitungen verlegt", "Fußbodenheizung verlegt"),
        ),
        # ── Großprojekt / Hotel ──
        BaseScenario(
            (
                "An der Hotel-Baustelle 35 laufende Meter KG-Rohre DN 110 verlegt "
                "vier Heizkörper montiert WC gesetzt Waschbecken montiert Druckprüfung durchgeführt "
                "Bauherr zufrieden Problem Lieferung spät Offen Rest Sanitär nächste Woche."
            ),
            (
                "KG-Rohre DN 110",
                "Heizkörper montiert",
                "WC montiert",
                "Waschbecken montiert",
                "Druckprüfung durchgeführt",
            ),
            expect_materials=("KG-Rohre",),
            forbid_activities=_kg_forbid,
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        # ── Ketten / formell ──
        BaseScenario(
            (
                "Heute haben wir Wasserleitungen verlegt drei Heizkörper montiert "
                "WC gesetzt Waschbecken montiert und die Druckprüfung durchgeführt."
            ),
            (
                "Wasserleitungen verlegt",
                "Heizkörper montiert",
                "WC montiert",
                "Waschbecken montiert",
                "Druckprüfung durchgeführt",
            ),
        ),
        BaseScenario(
            "Heizkreisverteiler angeschlossen Fußbodenheizung verlegt hydraulischen Abgleich durchgeführt.",
            (
                "Heizungsanschlüsse montiert",
                "Fußbodenheizung verlegt",
                "Hydraulischer Abgleich durchgeführt",
            ),
        ),
        BaseScenario(
            "HT-Rohre verlegt HT-Bögen eingebaut HT-Abzweig eingebaut.",
            ("HT-Rohre", "HT-Bögen", "HT-Abzweig"),
        ),
        BaseScenario(
            "Dusche montiert Armaturen montiert Druckprüfung durchgeführt.",
            ("Dusche montiert", "Armaturen montiert", "Druckprüfung durchgeführt"),
        ),
        BaseScenario("Druckprüfung durchgeführt fertig.", ("Druckprüfung durchgeführt",), min_activity_count=1),
        BaseScenario(
            "Hydraulischen Abgleich durchgeführt.",
            ("Hydraulischer Abgleich durchgeführt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Heizungsanschlüsse montiert fertig.",
            ("Heizungsanschlüsse montiert",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Wärmepumpe installiert Heizungsanschlüsse montiert.",
            ("Wärmepumpe installiert", "Heizungsanschlüsse montiert"),
        ),
        BaseScenario(
            "KG-Rohre DN 125 verlegt HT-Rohre verlegt Druckprüfung durchgeführt.",
            ("KG-Rohre", "HT-Rohre", "Druckprüfung durchgeführt"),
            forbid_activities=_kg_forbid,
        ),
        BaseScenario(
            "WC gesetzt Waschbecken montiert.",
            ("WC montiert", "Waschbecken montiert"),
        ),
        BaseScenario(
            "Problem undichtes Rohr Druckprüfung verschoben Kundengespräch gehabt Offen morgen nacharbeiten.",
            (),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            min_activity_count=0,
        ),
        BaseScenario(
            "Kundengespräch gehabt Heizungsplan besprochen Problem Material fehlt Offen Rest nächste Woche.",
            (),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            min_activity_count=0,
        ),
        BaseScenario(
            "Rohre gelegt Wasser angeschlossen Heizung angeschlossen.",
            ("Wasserleitungen verlegt", "Heizungsanschlüsse montiert"),
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
        (r"\bHT-Rohre\b", "ht rohre"),
        (r"\bHT-Bögen\b", "ht bögen"),
        (r"\bHT-Abzweig\b", "ht abzweig"),
        (r"\bHT-Manschette\b", "ht manschette"),
        (r"\blaufende Meter\b", "lauf ende meter"),
        (r"\bDruckprüfung\b", "druck prüfung"),
        (r"\bFußbodenheizung\b", "fuss boden heizung"),
        (r"\bHeizkörper\b", "heiz körper"),
        (r"\bWasserleitungen\b", "wasser leitungen"),
        (r"\bHeizungsanschlüsse\b", "heizungs anschlüsse"),
        (r"\bHeizungsanschluesse\b", "heizungs anschluesse"),
        (r"\bWärmepumpe\b", "wärme pumpe"),
        (r"\bWaermepumpe\b", "waerme pumpe"),
        (r"\bWaschbecken\b", "wasch becken"),
        (r"\bHeizkreisverteiler\b", "heiz kreis verteiler"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bverlegt\b", "ver legt"),
        (r"\bmontiert\b", "mon tiert"),
        (r"\beingebaut\b", "ein gebaut"),
        (r"\bangeschlossen\b", "an geschlossen"),
        (r"\binstalliert\b", "in stalliert"),
        (r"\bdurchgeführt\b", "durch ge führt"),
        (r"\bdruckprüfung\b", "druckprufung"),
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
        ("Druckprüfung", "Druckprobe"),
        ("druckprüfung", "druckprobe"),
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
                    name=f"SHK_{idx:03d}_{tag}",
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
        projectId="shk-wave19",
        projectName="SHK Welle 19",
        customerName="Testkunde",
        date="2026-07-26",
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
        print("VIRTUAL-SPEECH-SHK-WAVE19-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-SHK-WAVE19-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
