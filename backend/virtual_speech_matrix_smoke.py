"""Große virtuelle Sprachtest-Matrix über alle aktiven Gewerke.

Ziel:
- viele Raw-Text-Fälle (inkl. gebrochenem Deutsch)
- Activities/Materials/MaterialSuggestions prüfen
- customerTalk / problems / openItems prüfen
- additive Regression-Sicherung für den gesamten Parser-Flow
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_virtual_matrix_")))
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


def _build_matrix_cases() -> list[Case]:
    bases: list[BaseScenario] = [
        # GaLaBau (8 x 3 = 24)
        BaseScenario(
            trade="GaLaBau",
            raw="Heute 50 Quadratmeter Pflaster verlegt und drei Kubikmeter Schotter eingebaut.",
            expect_activities=("50 m² Pflaster verlegt", "3 m³ Schotter eingebaut"),
            expect_materials=("Pflastersteine", "Schotter"),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute 20 laufende Meter Palisaden gesetzt.",
            expect_activities=("20 lfm Palisaden gesetzt",),
            expect_materials=("Palisaden",),
            expect_suggestions=("Splitt benutzt?", "Beton benutzt?"),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute 35 Quadratmeter Fläche mit Rindenmulch gemulcht.",
            expect_activities=("35 m² Rindenmulch eingedeckt",),
            expect_materials=("Rindenmulch",),
            forbid_activities=("Pflegearbeiten durchgeführt",),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute Terrasse mit Keramikplatten 2 Zentimeter dick verlegt, 30 Quadratmeter.",
            expect_activities=("30 m² Keramikterrasse verlegt",),
            expect_materials=("Keramikplatten",),
            expect_suggestions=("Stelzlager benutzt?",),
            forbid_suggestions=("Einkornmörtel benutzt?", "Drainagemörtel benutzt?"),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute Terrasse mit Keramikplatte 3 cm dick verlegt, 18 qm.",
            expect_activities=("18 m² Keramikterrasse verlegt",),
            expect_materials=("Keramikplatten",),
            expect_suggestions=("Einkornmörtel benutzt?", "Drainagemörtel benutzt?"),
            forbid_suggestions=("Stelzlager benutzt?",),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute Rasen vertikutiert, danach Rasen gedüngt und die Fläche bewässert.",
            expect_activities=("Rasen vertikutiert", "Rasen gedüngt", "Fläche bewässert"),
            expect_materials=("Dünger",),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute Winterdienst gemacht, Schnee geräumt und Streugut gestreut.",
            expect_activities=("Winterdienst durchgeführt",),
            expect_materials=("Streugut",),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw="Heute 24 Quadratmeter WPC Terrasse gebaut.",
            expect_activities=("24 m² Holz-/WPC-Terrasse gebaut",),
            expect_materials=("WPC-Dielen",),
            expect_suggestions=("Unterkonstruktion benutzt?",),
        ),
        # SHK (7 x 3 = 21)
        BaseScenario(
            trade="SHK",
            raw="Heute Wasserleitungen verlegt und Heizkörper montiert.",
            expect_activities=("Wasserleitungen verlegt", "Heizkörper montiert"),
            expect_materials=("Rohrleitungen", "Heizkörper"),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute WC gesetzt, Waschbecken montiert, Dusche angeschlossen und Armaturen montiert.",
            expect_activities=("WC montiert", "Waschbecken montiert", "Dusche montiert", "Armaturen montiert"),
            expect_materials=("WC", "Waschbecken", "Dusche", "Armaturen"),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute Druckprobe gemacht und hydraulischer Abgleich durchgeführt.",
            expect_activities=("Druckprüfung durchgeführt", "Hydraulischer Abgleich durchgeführt"),
            expect_materials=("Prüfset",),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute 12 laufende Meter HT DN 50 verlegt, zwei Bögen gesetzt und einen Abzweig eingebaut.",
            expect_activities=("12 lfm HT-Rohre DN 50 verlegt", "HT-Bögen eingebaut", "HT-Abzweig eingebaut"),
            expect_materials=("HT-Rohre DN 50", "HT-Bögen DN 50", "HT-Abzweige DN 50"),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute Wärmepumpe installiert und Heizungsanschlüsse montiert.",
            expect_activities=("Wärmepumpe installiert", "Heizungsanschlüsse montiert"),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute Fußbodenheizung verlegt und den Verteiler montiert.",
            expect_activities=("Fußbodenheizung verlegt",),
            expect_suggestions=("Randdämmstreifen benutzt?", "Tackersystem benutzt?"),
            forbid_suggestions=("FBH-Verteiler benutzt?",),
        ),
        BaseScenario(
            trade="SHK",
            raw="Heute Lüftungsanlage montiert.",
            expect_activities=("Lüftungs-/Klimatechnik installiert",),
        ),
        # Fliesen (7 x 3 = 21)
        BaseScenario(
            trade="Fliesen",
            raw="Heute 40 Quadratmeter Fliesen verlegt, Fliesenkleber aufgetragen und anschließend verfugt.",
            expect_activities=("40 m² Fliesen verlegt", "Fliesenkleber aufgetragen", "Fliesen verfugt"),
            expect_materials=("Fliesen", "Fliesenkleber", "Fugenmörtel"),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute 30 Quadratmeter Großformatfliesen verlegt und Ausgleichsmasse gezogen.",
            expect_activities=("30 m² Großformatfliesen verlegt", "Nivelliermasse aufgetragen"),
            expect_materials=("Fliesen", "Nivelliermasse"),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute Bodenablauf gesetzt und danach 12 qm Naturstein verlegt.",
            expect_activities=("Bodenablauf eingebaut", "12 m² Naturstein verlegt"),
            expect_materials=("Bodenablauf", "Naturstein"),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute im Badezimmer 22 Quadratmeter Fliesen verlegt und mit Silikon abgeschlossen.",
            expect_activities=("22 m² Fliesen verlegt", "Silikonfugen silikoniert"),
            expect_materials=("Fliesen", "Silikon"),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute Grundierung aufgetragen, Abdichtung hergestellt und Fliesen gelegt.",
            expect_activities=("Grundierung aufgetragen", "Abdichtung hergestellt", "Fliesen verlegt"),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute Fliesen repariert und zwei Stück ausgetauscht.",
            expect_activities=("Fliesen repariert",),
        ),
        BaseScenario(
            trade="Fliesen",
            raw="Heute Duschrinne eingebaut und die Fugen verfugt.",
            expect_activities=("Bodenablauf eingebaut", "Fliesen verfugt"),
            expect_materials=("Bodenablauf",),
        ),
        # Tiefbau (7 x 3 = 21)
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Graben ausgehoben, 20 lfm DN 160 KG Rohr verlegt, Graben verfüllt und Untergrund verdichtet.",
            expect_activities=("Graben ausgehoben", "20 lfm KG-Rohre DN 160 verlegt", "Graben verfüllt", "Untergrund verdichtet"),
            expect_materials=("KG-Rohre DN 160",),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Hausanschluss gemacht und Asphalt eingebaut.",
            expect_activities=("Hausanschluss hergestellt", "Asphalt eingebaut"),
            expect_materials=("Hausanschluss", "Asphalt"),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Leitungstrasse hergestellt und anschließend Verbau gesetzt.",
            expect_activities=("Leitungstrasse hergestellt", "Verbau gesetzt"),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Kanal angeschlossen und Schacht gesetzt.",
            expect_activities=("Kanal-/Schachtarbeiten durchgeführt",),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute 18 laufende Meter Hunderter KG Rohr verlegt.",
            expect_activities=("18 lfm KG-Rohre DN 110 verlegt",),
            expect_materials=("KG-Rohre DN 110",),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute 15 laufende Meter 150er KG Rohr verlegt.",
            expect_activities=("15 lfm KG-Rohre DN 160 verlegt",),
            expect_materials=("KG-Rohre DN 160",),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw="Heute Drainage eingebaut und Filtervlies verlegt.",
            expect_activities=("Drainage/Entwässerung eingebaut", "Geotextil verlegt"),
            expect_materials=("Geotextil",),
        ),
        # Trockenbau (6 x 3 = 18)
        BaseScenario(
            trade="Trockenbau",
            raw="Heute Ständerwerk montiert und Steinwolle Dämmung eingebaut.",
            expect_activities=("Ständerwerk montiert", "Dämmung eingebaut"),
            expect_materials=("Steinwolle",),
        ),
        BaseScenario(
            trade="Trockenbau",
            raw="Heute Gipskartonplatten montiert, Decke abgehängt und Fugen verspachtelt.",
            expect_activities=("Gipskartonplatten montiert", "Decke abgehängt", "Fugen verspachtelt"),
            expect_materials=("Gipskartonplatten", "Fugenspachtel"),
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
            raw="Heute Revisionsklappe eingebaut.",
            expect_activities=("Revisionsklappe eingebaut",),
        ),
        BaseScenario(
            trade="Trockenbau",
            raw="Heute Rigips dran gemacht und zugespachtelt.",
            expect_activities=("Gipskartonplatten montiert", "Spachtelarbeiten durchgeführt"),
        ),
        # Hochbau (6 x 3 = 18)
        BaseScenario(
            trade="Hochbau",
            raw="Heute Schalung erstellt, Bewehrung eingebaut und 4 Kubikmeter Beton eingebracht.",
            expect_activities=("Schalung erstellt", "Bewehrung eingebaut", "4 m³ Beton eingebracht"),
            expect_materials=("Schalung", "Bewehrungsstahl", "Beton"),
        ),
        BaseScenario(
            trade="Hochbau",
            raw="Heute Fundament erstellt und Filigrandecke montiert.",
            expect_activities=("Fundament erstellt", "Filigrandecke montiert"),
        ),
        BaseScenario(
            trade="Hochbau",
            raw="Heute 20 m² 17 5 aporoton gemauert.",
            expect_activities=("20 m² Mauerwerk erstellt",),
            expect_materials=("17,5er Poroton",),
        ),
        BaseScenario(
            trade="Hochbau",
            raw="Heute 15 m² 11 5 a porit hochgezogen und Baukleber verarbeitet.",
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
            raw="Heute Bewehrungsstahl eingebaut und Schalung gestellt.",
            expect_activities=("Bewehrung eingebaut", "Schalung erstellt"),
        ),
        # Sanierung/Putz/Stuck (8 x 3 = 24)
        BaseScenario(
            trade="Sanierung",
            raw="Heute Altputz entfernt, Schimmel beseitigt und Sanierputz aufgebracht.",
            expect_activities=("Altputz entfernt", "Schimmel beseitigt", "Sanierputz aufgebracht"),
            expect_materials=("Sanierputz",),
        ),
        BaseScenario(
            trade="Sanierung",
            raw="Heute Oberputz aufgetragen und Unterputz nachgearbeitet.",
            expect_activities=("Oberputz aufgetragen", "Unterputz aufgetragen"),
            expect_materials=("Oberputz", "Unterputz"),
        ),
        BaseScenario(
            trade="Sanierung",
            raw="Heute Sockelputz gemacht, Reibputz gemacht und Kratzputz gemacht.",
            expect_activities=("Sockelputz aufgetragen", "Reibputz aufgetragen", "Kratzputz aufgetragen"),
            expect_materials=("Sockelputz", "Reibputz", "Kratzputz"),
        ),
        BaseScenario(
            trade="Stuck",
            raw="Heute Innenputz aufgetragen, WDVS ausgeführt und Armierungsgewebe eingebettet.",
            expect_activities=("Innenputz aufgetragen", "WDVS ausgeführt", "Armierung ausgeführt"),
            expect_materials=("Innenputz", "Armierungsgewebe"),
        ),
        BaseScenario(
            trade="Stuck",
            raw="Heute Fassadenarmierung ausgeführt und Außenputz aufgetragen.",
            expect_activities=("Fassadenarmierung ausgeführt", "Außenputz aufgetragen"),
        ),
        BaseScenario(
            trade="Stuck",
            raw="Heute Stuckleisten montiert.",
            expect_activities=("Stuckarbeiten durchgeführt",),
        ),
        BaseScenario(
            trade="Sanierung",
            raw="Heute Grundputz aufgetragen und danach Innenputz verarbeitet.",
            expect_activities=("Grundputz aufgetragen", "Innenputz aufgetragen"),
            expect_materials=("Grundputz", "Innenputz"),
        ),
        BaseScenario(
            trade="Sanierung",
            raw="Heute Schimmel entfernt und Oberputz verarbeitet.",
            expect_activities=("Schimmel beseitigt", "Oberputz aufgetragen"),
            expect_suggestions=("Schimmelentferner benutzt?",),
        ),
    ]

    cases: list[Case] = []
    for idx, base in enumerate(bases, start=1):
        # Variante A: normal
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

        # Variante B: leicht gebrochenes Deutsch
        broken = f"heute wir haben {base.raw.lower()} dann gemacht."
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

        # Variante C: mit Kunde + Problem + offen
        enriched = (
            f"{base.raw} Mit dem Kunden gesprochen, er war zufrieden. "
            "Problem: Untergrund war sehr uneben und Material fehlt. "
            "Muss noch morgen nachbestellen."
        )
        cases.append(
            Case(
                name=f"{base.trade}_{idx:03d}_C",
                raw=enriched,
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

    return cases


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    failures: list[str] = []
    cases = _build_matrix_cases()

    for case in cases:
        body = StructureReportBody(
            projectId="p-virtual-matrix",
            projectName="Virtuelle Matrix",
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
        for forbidden in case.forbid_activities:
            if _contains_any(acts, forbidden):
                failures.append(f"{case.name}: activity verboten -> {forbidden} (got={acts!r})")
        for expected in case.expect_materials:
            if not _contains_any(mats, expected):
                failures.append(f"{case.name}: material fehlt -> {expected} (got={mats!r})")
        for expected in case.expect_suggestions:
            if not _contains_any(suggs, expected):
                failures.append(f"{case.name}: suggestion fehlt -> {expected} (got={suggs!r})")
        for forbidden in case.forbid_suggestions:
            if _contains_any(suggs, forbidden):
                failures.append(f"{case.name}: suggestion verboten -> {forbidden} (got={suggs!r})")

        if case.expect_problem and not problems:
            failures.append(f"{case.name}: problems leer trotz Problem-Text")
        if case.expect_open and not open_items:
            failures.append(f"{case.name}: openItems leer trotz Offen-Text")
        if case.expect_customer and ("kunde" not in customer.casefold() and "kund" not in customer.casefold()):
            failures.append(f"{case.name}: customerTalk fehlt trotz Kunden-Text (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-MATRIX-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:220]:
            print(" -", row)
        if len(failures) > 220:
            print(f" ... weitere {len(failures) - 220} Fehler gekürzt")
        return 1

    print("VIRTUAL-SPEECH-MATRIX-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

