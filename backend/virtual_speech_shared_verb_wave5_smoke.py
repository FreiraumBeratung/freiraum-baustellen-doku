"""Welle 5: Aufzaehlungen mit geteiltem Verb + ASR-Varianten ueber alle Gewerke.

Schwerpunkt (vom realen Pilot-Fund abgeleitet):
- "A und B <verb>" / "A und B und C <verb>" -> ALLE Glieder muessen als
  Taetigkeit erscheinen (nicht nur das letzte).
- Whisper-Trennungen von Komposita ("unter putz" -> Unterputz) und
  typische Verhoerer (Hecke->Ecke, Geotextil->Geotextiel, Schimmel->Schimel).
- Materialfilter, Materialvorschlaege, problems/openItems/customerTalk.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_shared_verb_wave5_")))
_SMOKE_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class BaseScenario:
    trade: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...] = ()
    expect_suggestions: tuple[str, ...] = ()
    forbid_activities: tuple[str, ...] = ()


@dataclass(frozen=True)
class Case:
    name: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...]
    expect_suggestions: tuple[str, ...]
    forbid_activities: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ---------------- Sanierung / Stuck (Putz-Schwerpunkt) ----------------
        BaseScenario(
            "Sanierung",
            "Heute 50 Quadratmeter Unterputz und 50 Quadratmeter Oberputz aufgebracht.",
            ("Unterputz aufgetragen", "Oberputz aufgetragen"),
            expect_materials=("Unterputz", "Oberputz"),
        ),
        BaseScenario(
            "Sanierung",
            "Heute Grundputz und Unterputz und Oberputz aufgetragen.",
            ("Grundputz aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen"),
        ),
        BaseScenario(
            "Sanierung",
            "Heute Altputz entfernt und Schimmel beseitigt und Sanierputz aufgebracht.",
            ("Altputz entfernt", "Schimmel beseitigt", "Sanierputz aufgebracht"),
        ),
        BaseScenario(
            "Stuck",
            "Heute Sockelputz und Reibputz und Kratzputz aufgetragen.",
            ("Sockelputz aufgetragen", "Reibputz aufgetragen", "Kratzputz aufgetragen"),
        ),
        BaseScenario(
            "Stuck",
            "Heute Innenputz und Außenputz aufgetragen.",
            ("Innenputz aufgetragen", "Außenputz aufgetragen"),
        ),
        BaseScenario(
            "Sanierung",
            "Heute Unterputz aufgetragen und Oberputz aufgetragen und danach Altputz im Nebenraum entfernt.",
            ("Unterputz aufgetragen", "Oberputz aufgetragen", "Altputz entfernt"),
        ),
        BaseScenario(
            "Stuck",
            "Heute WDVS ausgeführt und Armierungsgewebe eingebettet und Sockelputz aufgetragen.",
            ("WDVS ausgeführt", "Armierung ausgeführt", "Sockelputz aufgetragen"),
        ),
        BaseScenario(
            "Sanierung",
            "Heute 30 Quadratmeter Grundputz und 30 Quadratmeter Oberputz aufgebracht.",
            ("Grundputz aufgetragen", "Oberputz aufgetragen"),
        ),
        # ---------------- GaLaBau ----------------
        BaseScenario(
            "GaLaBau",
            "Heute 50 Quadratmeter Pflaster verlegt und 30 Quadratmeter Gartenmauer gebaut und 10 Meter Hecke geschnitten.",
            ("50 m² Pflaster verlegt", "30 m² Gartenmauer gebaut", "Hecke geschnitten"),
            expect_materials=("Pflastersteine",),
        ),
        BaseScenario(
            "GaLaBau",
            "Heute Hecke geschnitten und Unkraut entfernt und Rindenmulch eingedeckt.",
            ("Hecke geschnitten", "Unkraut entfernt", "Rindenmulch eingedeckt"),
        ),
        BaseScenario(
            "GaLaBau",
            "Heute 20 laufende Meter Rasenkantensteine und 15 laufende Meter Palisaden gesetzt.",
            ("Rasenkantensteine gesetzt", "Palisaden gesetzt"),
        ),
        BaseScenario(
            "GaLaBau",
            "Heute Rasen vertikutiert und gedüngt und Fläche bewässert.",
            ("Rasen vertikutiert", "Rasen gedüngt", "Fläche bewässert"),
        ),
        BaseScenario(
            "GaLaBau",
            "Heute 30 Quadratmeter Keramikterrasse verlegt und Geotextil verlegt und Rasen gedüngt.",
            ("30 m² Keramikterrasse verlegt", "Geotextil verlegt", "Rasen gedüngt"),
            expect_materials=("Keramikplatten", "Geotextil", "Dünger"),
            expect_suggestions=("Stelzlager benutzt?",),
        ),
        BaseScenario(
            "GaLaBau",
            "Heute 40 Quadratmeter Pflaster verlegt und 2 Kubikmeter Schotter eingebaut und Unkraut entfernt.",
            ("40 m² Pflaster verlegt", "2 m³ Schotter eingebaut", "Unkraut entfernt"),
        ),
        BaseScenario(
            "GaLaBau",
            "Heute Winterdienst durchgeführt und Streugut gestreut und Hecke geschnitten.",
            ("Winterdienst durchgeführt", "Hecke geschnitten"),
        ),
        # ---------------- SHK ----------------
        BaseScenario(
            "SHK",
            "Heute WC und Waschbecken und Dusche montiert.",
            ("WC montiert", "Waschbecken montiert", "Dusche montiert"),
        ),
        BaseScenario(
            "SHK",
            "Heute 25 laufende Meter KG Rohre DN 160 verlegt und KG-Bögen und KG-Abzweig eingebaut.",
            ("25 lfm KG-Rohre DN 160 verlegt", "KG-Bögen eingebaut", "KG-Abzweig eingebaut"),
        ),
        BaseScenario(
            "SHK",
            "Heute Wasserleitungen verlegt und Heizkörper montiert und Druckprüfung durchgeführt.",
            ("Wasserleitungen verlegt", "Heizkörper montiert", "Druckprüfung durchgeführt"),
        ),
        BaseScenario(
            "SHK",
            "Heute Fußbodenheizung verlegt und Wärmepumpe installiert und hydraulischer Abgleich durchgeführt.",
            ("Fußbodenheizung verlegt", "Wärmepumpe installiert", "Hydraulischer Abgleich durchgeführt"),
        ),
        BaseScenario(
            "SHK",
            "Heute Waschbecken und Armaturen montiert.",
            ("Waschbecken montiert", "Armaturen montiert"),
        ),
        BaseScenario(
            "SHK",
            "Heute 14 laufende Meter HT Rohre DN 50 verlegt und HT-Manschette montiert und Druckprüfung durchgeführt.",
            ("14 lfm HT-Rohre DN 50 verlegt", "HT-Manschette montiert", "Druckprüfung durchgeführt"),
        ),
        # ---------------- Fliesen ----------------
        BaseScenario(
            "Fliesen",
            "Heute 80 Quadratmeter Großformatfliesen verlegt und Nivelliermasse aufgetragen und verfugt.",
            ("80 m² Großformatfliesen verlegt", "Nivelliermasse aufgetragen", "Fliesen verfugt"),
        ),
        BaseScenario(
            "Fliesen",
            "Heute Grundierung und Fliesenkleber aufgetragen und Fliesen verlegt.",
            ("Grundierung aufgetragen", "Fliesenkleber aufgetragen", "Fliesen verlegt"),
        ),
        BaseScenario(
            "Fliesen",
            "Heute Bodenablauf eingebaut und Abdichtung hergestellt und 24 Quadratmeter Naturstein verlegt.",
            ("Bodenablauf eingebaut", "Abdichtung hergestellt", "24 m² Naturstein verlegt"),
        ),
        BaseScenario(
            "Fliesen",
            "Heute 35 Quadratmeter Fliesen verlegt und verfugt und Silikonfugen gezogen.",
            ("35 m² Fliesen verlegt", "Fliesen verfugt", "Silikonfugen silikoniert"),
        ),
        # ---------------- Tiefbau ----------------
        BaseScenario(
            "Tiefbau",
            "Heute Graben ausgehoben und 30 laufende Meter KG Rohre DN 160 verlegt und Graben verfüllt.",
            ("Graben ausgehoben", "30 lfm KG-Rohre DN 160 verlegt", "Graben verfüllt"),
        ),
        BaseScenario(
            "Tiefbau",
            "Heute Leitungstrasse hergestellt und Verbau gesetzt und Hausanschluss hergestellt.",
            ("Leitungstrasse hergestellt", "Verbau gesetzt", "Hausanschluss hergestellt"),
        ),
        BaseScenario(
            "Tiefbau",
            "Heute Drainage eingebaut und Filtervlies verlegt und Asphalt eingebaut.",
            ("Drainage/Entwässerung eingebaut", "Geotextil verlegt", "Asphalt eingebaut"),
        ),
        BaseScenario(
            "Tiefbau",
            "Heute Graben ausgehoben und verfüllt und Untergrund verdichtet.",
            ("Graben ausgehoben", "Graben verfüllt", "Untergrund verdichtet"),
        ),
        # ---------------- Trockenbau ----------------
        BaseScenario(
            "Trockenbau",
            "Heute Ständerwerk montiert und Dämmung eingebaut und Gipskartonplatten montiert.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert"),
        ),
        BaseScenario(
            "Trockenbau",
            "Heute Decke abgehängt und Fugen verspachtelt.",
            ("Decke abgehängt", "Fugen verspachtelt"),
        ),
        BaseScenario(
            "Trockenbau",
            "Heute Brandschutzwand hergestellt und Akustikdecke eingebaut und Revisionsklappe montiert.",
            ("Brandschutzwand hergestellt", "Akustikdecke eingebaut", "Revisionsklappe eingebaut"),
        ),
        # ---------------- Hochbau ----------------
        BaseScenario(
            "Hochbau",
            "Heute Schalung erstellt und Bewehrung eingebaut und 6 Kubikmeter Beton eingebracht.",
            ("Schalung erstellt", "Bewehrung eingebaut", "6 m³ Beton eingebracht"),
        ),
        BaseScenario(
            "Hochbau",
            "Heute 15 Quadratmeter 17 5 Poroton und 10 Quadratmeter Kalksandstein gemauert.",
            ("Mauerwerk erstellt",),
        ),
        BaseScenario(
            "Hochbau",
            "Heute Fundament erstellt und Filigrandecke montiert.",
            ("Fundament erstellt", "Filigrandecke montiert"),
        ),
        # ---------------- Subjekt-Propagation ("A <verb> und <verb>") ----------------
        BaseScenario(
            "Tiefbau",
            "Heute Baugrube ausgehoben und verdichtet.",
            ("Graben ausgehoben", "Untergrund verdichtet"),
        ),
        BaseScenario(
            "Tiefbau",
            "Heute Graben ausgehoben und verfüllt.",
            ("Graben ausgehoben", "Graben verfüllt"),
        ),
        BaseScenario(
            "Fliesen",
            "Heute Fliesen verlegt und verfugt und silikoniert.",
            ("Fliesen verlegt", "Fliesen verfugt", "Silikonfugen silikoniert"),
        ),
        # ---------------- Banale Einzelfaelle (gut/halb-gut) ----------------
        BaseScenario(
            "GaLaBau",
            "Heute 60 Quadratmeter Pflaster verlegt.",
            ("60 m² Pflaster verlegt",),
        ),
        BaseScenario(
            "GaLaBau",
            "Heute Rollrasen verlegt und Fläche bewässert.",
            ("Rasen verlegt", "Fläche bewässert"),
        ),
        BaseScenario(
            "GaLaBau",
            "Heute Hecke geschnitten und Rasen gemäht.",
            ("Hecke geschnitten", "Rasen gemäht"),
        ),
        BaseScenario(
            "GaLaBau",
            "Heute 12 laufende Meter Palisaden gesetzt und 8 Quadratmeter Gartenmauer gebaut.",
            ("Palisaden gesetzt", "8 m² Gartenmauer gebaut"),
        ),
        BaseScenario(
            "SHK",
            "Heute WC montiert und Silikonfugen gezogen.",
            ("WC montiert", "Silikonfugen silikoniert"),
        ),
        BaseScenario(
            "SHK",
            "Heute 20 laufende Meter HT Rohre DN 50 verlegt.",
            ("20 lfm HT-Rohre DN 50 verlegt",),
        ),
        BaseScenario(
            "SHK",
            "Heute Heizkörper montiert und Wasserleitungen verlegt.",
            ("Heizkörper montiert", "Wasserleitungen verlegt"),
        ),
        BaseScenario(
            "Fliesen",
            "Heute 50 Quadratmeter Fliesen verlegt.",
            ("50 m² Fliesen verlegt",),
        ),
        BaseScenario(
            "Fliesen",
            "Heute Abdichtung hergestellt und Fliesen verlegt und verfugt.",
            ("Abdichtung hergestellt", "Fliesen verlegt", "Fliesen verfugt"),
        ),
        BaseScenario(
            "Trockenbau",
            "Heute Ständerwerk montiert und Gipskartonplatten montiert und Decke abgehängt.",
            ("Ständerwerk montiert", "Gipskartonplatten montiert", "Decke abgehängt"),
        ),
        BaseScenario(
            "Trockenbau",
            "Heute Trockenbaufugen verspachtelt und geschliffen.",
            ("Fugen verspachtelt",),
        ),
        BaseScenario(
            "Hochbau",
            "Heute 8 Kubikmeter Beton eingebracht.",
            ("8 m³ Beton eingebracht",),
        ),
        BaseScenario(
            "Hochbau",
            "Heute Schalung erstellt und Bewehrung eingebaut.",
            ("Schalung erstellt", "Bewehrung eingebaut"),
        ),
        BaseScenario(
            "Sanierung",
            "Heute Schimmel beseitigt und Sanierputz aufgebracht.",
            ("Schimmel beseitigt", "Sanierputz aufgebracht"),
        ),
        BaseScenario(
            "Stuck",
            "Heute Innenputz aufgetragen und Sockelputz aufgetragen und Reibputz aufgetragen.",
            ("Innenputz aufgetragen", "Sockelputz aufgetragen", "Reibputz aufgetragen"),
        ),
    ]


def _asr_noise(text: str) -> str:
    out = text
    pairs = (
        (r"\bUnterputz\b", "unter putz"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bGrundputz\b", "grund putz"),
        (r"\bInnenputz\b", "innen putz"),
        (r"\bAußenputz\b", "außen putz"),
        (r"\bSockelputz\b", "sockel putz"),
        (r"\bSanierputz\b", "sanier putz"),
        (r"\bHecke\b", "Ecke"),
        (r"\bGeotextil\b", "Geotextiel"),
        (r"\bSchimmel\b", "Schimel"),
        (r"\bDruckprüfung\b", "Druckprufung"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    out = out.lower().replace(".", "")
    return f"also heute ham wa so gemacht {out}"


def _build_cases() -> list[Case]:
    bases = _base_scenarios()
    cases: list[Case] = []
    idx = 1
    # A: normal, B: ASR-Noise, C: + Kontext (problem/open/customer)
    for variant in ("A", "B", "C"):
        for base in bases:
            if variant == "A":
                raw = base.raw
                ep = eo = ec = False
            elif variant == "B":
                raw = _asr_noise(base.raw)
                ep = eo = ec = False
            else:
                raw = (
                    f"{base.raw} Mit dem Kunden gesprochen, Kunde war zufrieden. "
                    "Problem: Material war knapp und Untergrund uneben. "
                    "Offen: morgen Rest nachbestellen und fertigstellen."
                )
                ep = eo = ec = True
            cases.append(
                Case(
                    name=f"{base.trade}_{idx:03d}_{variant}",
                    raw=raw,
                    expect_activities=base.expect_activities,
                    expect_materials=base.expect_materials,
                    expect_suggestions=base.expect_suggestions,
                    forbid_activities=base.forbid_activities,
                    expect_problem=ep,
                    expect_open=eo,
                    expect_customer=ec,
                )
            )
            idx += 1
    return cases


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    cases = _build_cases()
    failures: list[str] = []

    for case in cases:
        body = StructureReportBody(
            projectId="p-wave5",
            projectName="Shared Verb Matrix",
            customerName="Testkunde",
            date="2026-06-20",
            employeeNames=["Max", "Ali", "Murat"],
            startTime="07:00",
            endTime="17:00",
            exportFormat="PDF",
            rawText=case.raw,
        )
        out = api_structure_report(body, store=_SMOKE_STORE)
        structured = out.get("structured") or {}
        acts = [str(x) for x in (structured.get("activities") or [])]
        mats = [str(x) for x in (structured.get("materials") or [])]
        suggs = [str(x) for x in (structured.get("materialSuggestions") or [])]
        probs = [str(x) for x in (structured.get("problems") or [])]
        opens = [str(x) for x in (structured.get("openItems") or [])]
        customer = str(structured.get("customerTalk") or "")

        for expected in case.expect_activities:
            if not _contains_any(acts, expected):
                failures.append(f"{case.name}: activity fehlt -> {expected} (got={acts!r})")
        for expected in case.expect_materials:
            if not _contains_any(mats, expected):
                failures.append(f"{case.name}: material fehlt -> {expected} (got={mats!r})")
        for expected in case.expect_suggestions:
            if not _contains_any(suggs, expected):
                failures.append(f"{case.name}: suggestion fehlt -> {expected} (got={suggs!r})")
        for forbidden in case.forbid_activities:
            if _contains_any(acts, forbidden):
                failures.append(f"{case.name}: activity verboten -> {forbidden} (got={acts!r})")
        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer trotz Problem-Text")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer trotz Offen-Text")
        if case.expect_customer and ("kund" not in customer.casefold()):
            failures.append(f"{case.name}: customerTalk leer trotz Kunden-Text (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-SHARED-VERB-WAVE5-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:340]:
            print(" -", row)
        if len(failures) > 340:
            print(f" ... weitere {len(failures) - 340} Fehler gekuerzt")
        return 1

    print("VIRTUAL-SPEECH-SHARED-VERB-WAVE5-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
