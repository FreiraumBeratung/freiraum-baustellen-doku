"""Welle 2: 200 neue virtuelle Sprachtest-Fälle.

Aufbau:
- 50 Basis-Szenarien über alle aktiven Gewerke
- je 4 Varianten (normal, gebrochen, mit customer/problem/open, umgangssprachlich)
- insgesamt 200 Fälle
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_virtual_matrix_wave2_")))
_SMOKE_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class BaseScenario:
    trade: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...] = ()
    expect_suggestions: tuple[str, ...] = ()
    forbid_activities: tuple[str, ...] = ()
    forbid_suggestions: tuple[str, ...] = ()


@dataclass(frozen=True)
class Case:
    name: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...]
    expect_suggestions: tuple[str, ...]
    forbid_activities: tuple[str, ...]
    forbid_suggestions: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def _build_base_scenarios() -> list[BaseScenario]:
    return [
        # GaLaBau (10)
        BaseScenario(
            trade="GaLaBau",
            raw="Heute 60 Quadratmeter Pflaster verlegt und vier Kubikmeter Schotter eingebaut.",
            expect_activities=("60 m² Pflaster verlegt", "4 m³ Schotter eingebaut"),
            expect_materials=("Pflastersteine", "Schotter"),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute 15 laufende Meter Palisaden montiert.",
            expect_activities=("15 lfm Palisaden gesetzt",),
            expect_materials=("Palisaden",),
            expect_suggestions=("Splitt benutzt?", "Beton benutzt?"),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute Beetfläche mit Mulch bestreut.",
            expect_activities=("Fläche mit Mulch eingedeckt",),
            expect_materials=("Mulch",),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute 22 Quadratmeter mit Rindenmulch gemulcht.",
            expect_activities=("22 m² Rindenmulch eingedeckt",),
            expect_materials=("Rindenmulch",),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute Terrasse mit Keramikplatten zwei Zentimeter dick verlegt.",
            expect_activities=("Keramikterrasse verlegt",),
            expect_materials=("Keramikplatten",),
            expect_suggestions=("Stelzlager benutzt?",),
            forbid_suggestions=("Einkornmörtel benutzt?", "Drainagemörtel benutzt?"),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute Terrasse mit Keramikplatte 3 cm dick gelegt.",
            expect_activities=("Keramikterrasse verlegt",),
            expect_materials=("Keramikplatten",),
            expect_suggestions=("Einkornmörtel benutzt?", "Drainagemörtel benutzt?"),
            forbid_suggestions=("Stelzlager benutzt?",),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute Rasen vertikutiert und danach gedüngt.",
            expect_activities=("Rasen vertikutiert", "Rasen gedüngt"),
            expect_materials=("Dünger",),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute die Fläche bewässert und Unkraut entfernt.",
            expect_activities=("Fläche bewässert", "Unkraut entfernt"),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute Winterdienst durchgeführt, Schnee geräumt und Salz gestreut.",
            expect_activities=("Winterdienst durchgeführt",),
            expect_materials=("Streugut",),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute 18 Quadratmeter WPC Terrasse hergestellt und Trennvlies verlegt.",
            expect_activities=("18 m² Holz-/WPC-Terrasse gebaut", "Geotextil verlegt"),
            expect_materials=("WPC-Dielen", "Geotextil"),
        ),
        # SHK (9)
        BaseScenario(
            trade="SHK",
            raw="Heute Wasserleitungen verlegt und Heizkörper montiert.",
            expect_activities=("Wasserleitungen verlegt", "Heizkörper montiert"),
            expect_materials=("Rohrleitungen", "Heizkörper"),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute WC eingebaut und Waschbecken montiert.",
            expect_activities=("WC montiert", "Waschbecken montiert"),
            expect_materials=("WC", "Waschbecken"),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute Dusche montiert und Armaturen angeschlossen.",
            expect_activities=("Dusche montiert", "Armaturen montiert"),
            expect_materials=("Dusche", "Armaturen"),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute Druckprüfung durchgeführt.",
            expect_activities=("Druckprüfung durchgeführt",),
            expect_materials=("Prüfset",),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute hydraulischer Abgleich gemacht.",
            expect_activities=("Hydraulischer Abgleich durchgeführt",),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute 14 lfm HT DN 50 verlegt und Manschette montiert.",
            expect_activities=("14 lfm HT-Rohre DN 50 verlegt", "HT-Manschette montiert"),
            expect_materials=("HT-Rohre DN 50", "HT-Manschette DN 50"),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute 12 lfm KG DN 160 verlegt und KG-Abzweig eingebaut.",
            expect_activities=("12 lfm KG-Rohre DN 160 verlegt", "KG-Abzweig eingebaut"),
            expect_materials=("KG-Rohre DN 160",),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute Fußbodenheizung verlegt.",
            expect_activities=("Fußbodenheizung verlegt",),
            expect_suggestions=("Randdämmstreifen benutzt?", "Tackersystem benutzt?"),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute Wohnraumlüftung installiert.",
            expect_activities=("Lüftungs-/Klimatechnik installiert",),
        ),
        # Fliesen (8)
        BaseScenario(
            trade="Fliesen",
            raw="Heute 28 Quadratmeter Fliesen verlegt, Kleber gezogen und verfugt.",
            expect_activities=("28 m² Fliesen verlegt", "Fliesenkleber aufgetragen", "Fliesen verfugt"),
            expect_materials=("Fliesen", "Fliesenkleber", "Fugenmörtel"),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute 32 Quadratmeter Großformatfliesen verlegt.",
            expect_activities=("32 m² Großformatfliesen verlegt",),
            expect_materials=("Fliesen",),
            expect_suggestions=("Nivelliersystem benutzt?",),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute Nivelliermasse aufgetragen.",
            expect_activities=("Nivelliermasse aufgetragen",),
            expect_materials=("Nivelliermasse",),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute Duschrinne eingebaut und Fliesen verfugt.",
            expect_activities=("Bodenablauf eingebaut", "Fliesen verfugt"),
            expect_materials=("Bodenablauf",),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute 16 Quadratmeter Natursteinplatte verlegt.",
            expect_activities=("16 m² Naturstein verlegt",),
            expect_materials=("Naturstein",),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute Abdichtung hergestellt und danach Fliesen gelegt.",
            expect_activities=("Abdichtung hergestellt", "Fliesen verlegt"),
            expect_materials=("Abdichtung", "Fliesen"),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute Bodenablauf gesetzt.",
            expect_activities=("Bodenablauf eingebaut",),
            expect_suggestions=("Ablaufset benutzt?",),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute Fliesen repariert und beschädigte Platte ausgetauscht.",
            expect_activities=("Fliesen repariert",),
        ),
        # Tiefbau (7)
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Graben ausgehoben, 24 lfm DN 160 KG Rohr verlegt, Graben verfüllt und Untergrund verdichtet.",
            expect_activities=("Graben ausgehoben", "24 lfm KG-Rohre DN 160 verlegt", "Graben verfüllt", "Untergrund verdichtet"),
            expect_materials=("KG-Rohre DN 160",),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Leitungstrasse angelegt und Verbau gesetzt.",
            expect_activities=("Leitungstrasse hergestellt", "Verbau gesetzt"),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Hausanschluss hergestellt.",
            expect_activities=("Hausanschluss hergestellt",),
            expect_materials=("Hausanschluss",),
            expect_suggestions=("Dichteinsatz benutzt?",),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Asphalt eingebracht.",
            expect_activities=("Asphalt eingebaut",),
            expect_materials=("Asphalt",),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Drainage eingebaut und Filtervlies verlegt.",
            expect_activities=("Drainage/Entwässerung eingebaut", "Geotextil verlegt"),
            expect_materials=("Geotextil",),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Kanal angeschlossen und Schacht gesetzt.",
            expect_activities=("Kanal-/Schachtarbeiten durchgeführt",),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute 10 laufende Meter Hunderter KG Rohr verlegt.",
            expect_activities=("10 lfm KG-Rohre DN 110 verlegt",),
            expect_materials=("KG-Rohre DN 110",),
        ),
        # Trockenbau (6)
        BaseScenario(
            trade="Trockenbau",
            raw="Heute Ständerwerk montiert und Steinwolle eingebaut.",
            expect_activities=("Ständerwerk montiert", "Dämmung eingebaut"),
            expect_materials=("Steinwolle",),
        ),
        BaseScenario(
            trade="Trockenbau",
            raw="Heute Gipskartonplatten montiert und Decke abgehängt.",
            expect_activities=("Gipskartonplatten montiert", "Decke abgehängt"),
            expect_materials=("Gipskartonplatten",),
        ),
        BaseScenario(
            trade="Trockenbau",
            raw="Heute die Trockenbaufugen mit Fugenspachtel verspachtelt.",
            expect_activities=("Fugen verspachtelt",),
            expect_materials=("Fugenspachtel",),
        ),
        BaseScenario(
            trade="Trockenbau",
            raw="Heute Akustikdecke eingebaut.",
            expect_activities=("Akustikdecke eingebaut",),
        ),
        BaseScenario(
            trade="Trockenbau",
            raw="Heute Brandschutzwand hergestellt.",
            expect_activities=("Brandschutzwand hergestellt",),
        ),
        BaseScenario(
            trade="Trockenbau",
            raw="Heute Revisionsklappe montiert.",
            expect_activities=("Revisionsklappe eingebaut",),
        ),
        # Hochbau (6)
        BaseScenario(
            trade="Hochbau",
            raw="Heute 20 m² Mauerwerk mit Poroton erstellt.",
            expect_activities=("20 m² Mauerwerk erstellt",),
        ),
        BaseScenario(
            trade="Hochbau",
            raw="Heute Schalung erstellt, Bewehrung eingebaut und 5 Kubikmeter Beton eingebracht.",
            expect_activities=("Schalung erstellt", "Bewehrung eingebaut", "5 m³ Beton eingebracht"),
            expect_materials=("Schalung", "Bewehrungsstahl", "Beton"),
        ),
        BaseScenario(
            trade="Hochbau",
            raw="Heute Fundament erstellt und Filigrandecke montiert.",
            expect_activities=("Fundament erstellt", "Filigrandecke montiert"),
        ),
        BaseScenario(
            trade="Hochbau",
            raw="Heute 15 m² 11 5 a porit hochgezogen und Baukleber verwendet.",
            expect_activities=("15 m² Mauerwerk erstellt",),
            expect_materials=("11,5er Porit", "Baukleber"),
        ),
        BaseScenario(
            trade="Hochbau",
            raw="Heute 24er KS Stein gesetzt und Mauermörtel verarbeitet.",
            expect_activities=("Mauerwerk erstellt",),
            expect_materials=("24er KS", "Mauermörtel"),
        ),
        BaseScenario(
            trade="Hochbau",
            raw="Heute Erdarbeiten durchgeführt und Baugrube ausgehoben.",
            expect_activities=("Erdarbeiten durchgeführt", "Graben ausgehoben"),
        ),
        # Sanierung / Stuck (4)
        BaseScenario(
            trade="Sanierung",
            raw="Heute Altputz entfernt, Schimmel beseitigt und Sanierputz aufgebracht.",
            expect_activities=("Altputz entfernt", "Schimmel beseitigt", "Sanierputz aufgebracht"),
            expect_materials=("Sanierputz",),
            expect_suggestions=("Schimmelentferner benutzt?",),
        ),
        BaseScenario(
            trade="Sanierung",
            raw="Heute Oberputz aufgetragen und Unterputz nachgearbeitet.",
            expect_activities=("Oberputz aufgetragen", "Unterputz aufgetragen"),
            expect_materials=("Oberputz", "Unterputz"),
        ),
        BaseScenario(
            trade="Stuck",
            raw="Heute Innenputz aufgetragen, WDVS ausgeführt und Armierungsgewebe eingebettet.",
            expect_activities=("Innenputz aufgetragen", "WDVS ausgeführt", "Armierung ausgeführt"),
            expect_materials=("Innenputz", "Armierungsgewebe"),
        ),
        BaseScenario(
            trade="Stuck",
            raw="Heute Sockelputz gemacht, Reibputz gemacht und Kratzputz gemacht.",
            expect_activities=("Sockelputz aufgetragen", "Reibputz aufgetragen", "Kratzputz aufgetragen"),
            expect_materials=("Sockelputz", "Reibputz", "Kratzputz"),
        ),
    ]


def _build_cases() -> list[Case]:
    bases = _build_base_scenarios()
    cases: list[Case] = []

    for idx, base in enumerate(bases, start=1):
        # A: normal
        cases.append(
            Case(
                name=f"{base.trade}_{idx:03d}_A",
                raw=base.raw,
                expect_activities=base.expect_activities,
                expect_materials=base.expect_materials,
                expect_suggestions=base.expect_suggestions,
                forbid_activities=base.forbid_activities,
                forbid_suggestions=base.forbid_suggestions,
                expect_problem=False,
                expect_open=False,
                expect_customer=False,
            )
        )

        # B: gebrochenes Deutsch
        broken = f"heute wir haben {base.raw.lower()} dann machen fertig."
        cases.append(
            Case(
                name=f"{base.trade}_{idx:03d}_B",
                raw=broken,
                expect_activities=base.expect_activities,
                expect_materials=base.expect_materials,
                expect_suggestions=base.expect_suggestions,
                forbid_activities=base.forbid_activities,
                forbid_suggestions=base.forbid_suggestions,
                expect_problem=False,
                expect_open=False,
                expect_customer=False,
            )
        )

        # C: mit Kundengespräch + Problem + offen
        with_context = (
            f"{base.raw} Mit dem Kunden gesprochen, Kundin war zufrieden. "
            "Problem: Untergrund war sehr uneben und Material fehlt aktuell. "
            "Muss noch morgen nachbestellen und klären."
        )
        cases.append(
            Case(
                name=f"{base.trade}_{idx:03d}_C",
                raw=with_context,
                expect_activities=base.expect_activities,
                expect_materials=base.expect_materials,
                expect_suggestions=base.expect_suggestions,
                forbid_activities=base.forbid_activities,
                forbid_suggestions=base.forbid_suggestions,
                expect_problem=True,
                expect_open=True,
                expect_customer=True,
            )
        )

        # D: umgangssprachliche Kette
        colloquial = (
            f"{base.raw} danach noch kurz geprüft und sauber gemacht"
        )
        cases.append(
            Case(
                name=f"{base.trade}_{idx:03d}_D",
                raw=colloquial,
                expect_activities=base.expect_activities,
                expect_materials=base.expect_materials,
                expect_suggestions=base.expect_suggestions,
                forbid_activities=base.forbid_activities,
                forbid_suggestions=base.forbid_suggestions,
                expect_problem=False,
                expect_open=False,
                expect_customer=False,
            )
        )

    return cases


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    cases = _build_cases()
    failures: list[str] = []

    for case in cases:
        body = StructureReportBody(
            projectId="p-wave2",
            projectName="Virtuelle Matrix Welle 2",
            customerName="Testkunde",
            date="2026-06-18",
            employeeNames=["Max", "Ali"],
            startTime="07:30",
            endTime="16:30",
            exportFormat="PDF",
            rawText=case.raw,
        )
        out = api_structure_report(body, store=_SMOKE_STORE)
        structured = out.get("structured") or {}
        acts = [str(x) for x in (structured.get("activities") or [])]
        mats = [str(x) for x in (structured.get("materials") or [])]
        suggs = [str(x) for x in (structured.get("materialSuggestions") or [])]
        problems = [str(x) for x in (structured.get("problems") or [])]
        open_items = [str(x) for x in (structured.get("openItems") or [])]
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
        for forbidden in case.forbid_suggestions:
            if _contains_any(suggs, forbidden):
                failures.append(f"{case.name}: suggestion verboten -> {forbidden} (got={suggs!r})")

        if case.expect_problem and not problems:
            failures.append(f"{case.name}: problems leer trotz Problem-Text")
        if case.expect_open and not open_items:
            failures.append(f"{case.name}: openItems leer trotz Offen-Text")
        if case.expect_customer and ("kund" not in customer.casefold()):
            failures.append(f"{case.name}: customerTalk leer trotz Kunden-Text (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-MATRIX-WAVE2-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:260]:
            print(" -", row)
        if len(failures) > 260:
            print(f" ... weitere {len(failures) - 260} Fehler gekürzt")
        return 1

    print("VIRTUAL-SPEECH-MATRIX-WAVE2-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

