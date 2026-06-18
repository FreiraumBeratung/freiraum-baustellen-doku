"""Welle 3: Lange, aufeinanderfolgende Aufgabenketten pro Gewerk.

Fokus:
- lange Satzketten statt Einzeiler
- mehrere Tätigkeiten + Materialien in einem Diktat
- Materialvorschläge müssen auch im langen Kontext funktionieren
- customerTalk / problems / openItems im Mischtext
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_virtual_longchain_wave3_")))
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
    summary_contains: tuple[str, ...] = ()


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
    summary_contains: tuple[str, ...]


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def _base_scenarios() -> list[BaseScenario]:
    return [
        # GaLaBau long chains
        BaseScenario(
            trade="GaLaBau",
            raw=(
                "Heute haben wir 50 Quadratmeter Pflaster verlegt, danach 5 Quadratmeter Gartenmauer gebaut, "
                "anschließend 20 laufende Meter Rasenkantensteine gesetzt, dann noch 15 laufende Meter Palisaden montiert "
                "und zum Schluss die Fläche mit Rindenmulch gemulcht."
            ),
            expect_activities=(
                "50 m² Pflaster verlegt",
                "5 m² Gartenmauer gebaut",
                "20 lfm Rasenkantensteine gesetzt",
                "15 lfm Palisaden gesetzt",
                "Rindenmulch eingedeckt",
            ),
            expect_materials=("Pflastersteine", "Rasenkantensteine", "Palisaden", "Rindenmulch"),
            summary_contains=("Pflaster", "Gartenmauer"),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw=(
                "Wir haben erst 30 Quadratmeter Keramikterrasse mit Keramikplatten 2 Zentimeter dick verlegt, "
                "dann Geotextil eingebaut, danach den Rasen vertikutiert und gedüngt sowie im Anschluss die Fläche bewässert."
            ),
            expect_activities=(
                "30 m² Keramikterrasse verlegt",
                "Geotextil verlegt",
                "Rasen vertikutiert",
                "Rasen gedüngt",
                "Fläche bewässert",
            ),
            expect_materials=("Keramikplatten", "Geotextil", "Dünger"),
            expect_suggestions=("Stelzlager benutzt?",),
            forbid_suggestions=("Einkornmörtel benutzt?", "Drainagemörtel benutzt?"),
            summary_contains=("Keramikterrasse", "Rasen"),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw=(
                "Heute Winterdienst durchgeführt, Schnee geräumt, Streugut gestreut, "
                "danach noch 12 Quadratmeter WPC Terrasse gebaut und zwei Pflanzkübel mit Erde befüllt."
            ),
            expect_activities=(
                "Winterdienst durchgeführt",
                "12 m² Holz-/WPC-Terrasse gebaut",
                "Pflanzkübel mit Erde befüllt",
            ),
            expect_materials=("Streugut", "WPC-Dielen", "Pflanzkübel"),
            summary_contains=("Winterdienst", "WPC"),
        ),
        BaseScenario(
            trade="GaLaBau",
            raw=(
                "Heute wir haben 40 qm Pflaster gemacht dann 2 kubik schotter rein gemacht und danach die hecke zurückgeschnitten "
                "und unkraut weg gemacht und am ende mulch reingemacht."
            ),
            expect_activities=(
                "40 m² Pflaster verlegt",
                "2 m³ Schotter eingebaut",
                "Hecke geschnitten",
                "Unkraut entfernt",
                "Fläche mit Mulch eingedeckt",
            ),
            expect_materials=("Pflastersteine", "Schotter", "Mulch"),
        ),
        # SHK long chains including KG/HT
        BaseScenario(
            trade="SHK",
            raw=(
                "Heute haben wir 25 laufende Meter DN 160 KG Rohre verlegt, zwei KG-Bögen gesetzt, einen KG-Abzweig eingebaut, "
                "danach 14 laufende Meter HT DN 50 verlegt, HT-Manschette montiert und anschließend Druckprüfung durchgeführt."
            ),
            expect_activities=(
                "25 lfm KG-Rohre DN 160 verlegt",
                "KG-Bögen eingebaut",
                "KG-Abzweig eingebaut",
                "14 lfm HT-Rohre DN 50 verlegt",
                "HT-Manschette montiert",
                "Druckprüfung durchgeführt",
            ),
            expect_materials=("KG-Rohre DN 160", "HT-Rohre DN 50", "HT-Manschette DN 50", "Prüfset"),
            summary_contains=("KG-Rohre", "HT-Rohre"),
        ),
        BaseScenario(
            trade="SHK",
            raw=(
                "Wir haben Wasserleitungen verlegt, Heizkörper montiert, dann WC gesetzt, Waschbecken montiert, "
                "Dusche angeschlossen, Armaturen montiert und zum Schluss hydraulischer Abgleich durchgeführt."
            ),
            expect_activities=(
                "Wasserleitungen verlegt",
                "Heizkörper montiert",
                "WC montiert",
                "Waschbecken montiert",
                "Dusche montiert",
                "Armaturen montiert",
                "Hydraulischer Abgleich durchgeführt",
            ),
            expect_materials=("Rohrleitungen", "Heizkörper", "WC", "Waschbecken", "Dusche", "Armaturen"),
        ),
        BaseScenario(
            trade="SHK",
            raw=(
                "Heute Fußbodenheizung verlegt, Heizkreisverteiler angeschlossen, danach Wärmepumpe installiert "
                "und im Anschluss Heizungsanschlüsse montiert."
            ),
            expect_activities=(
                "Fußbodenheizung verlegt",
                "Wärmepumpe installiert",
                "Heizungsanschlüsse montiert",
            ),
            expect_suggestions=("Randdämmstreifen benutzt?", "Tackersystem benutzt?"),
        ),
        BaseScenario(
            trade="SHK",
            raw=(
                "heute rohre gelegt heizung angeschlossen wasser angeschlossen dann druckprobe gemacht und abgleich gemacht"
            ),
            expect_activities=(
                "Wasserleitungen verlegt",
                "Heizungsanschlüsse montiert",
                "Druckprüfung durchgeführt",
                "Hydraulischer Abgleich durchgeführt",
            ),
        ),
        # Fliesen long chains
        BaseScenario(
            trade="Fliesen",
            raw=(
                "Heute haben wir im Badezimmer 80 Quadratmeter Großformatfliesen verlegt, davor Nivelliermasse aufgetragen, "
                "danach Fliesenkleber verarbeitet, anschließend verfugt und die Silikonfugen abgeschlossen."
            ),
            expect_activities=(
                "80 m² Großformatfliesen verlegt",
                "Nivelliermasse aufgetragen",
                "Fliesenkleber aufgetragen",
                "Fliesen verfugt",
                "Silikonfugen silikoniert",
            ),
            expect_materials=("Fliesen", "Nivelliermasse", "Fliesenkleber", "Fugenmörtel", "Silikon"),
            summary_contains=("80 m²", "Fliesen"),
        ),
        BaseScenario(
            trade="Fliesen",
            raw=(
                "Heute Duschrinne eingebaut, Bodenablauf montiert, Abdichtung hergestellt, 24 Quadratmeter Naturstein verlegt "
                "und danach die Fugen verfugt."
            ),
            expect_activities=(
                "Bodenablauf eingebaut",
                "Abdichtung hergestellt",
                "24 m² Naturstein verlegt",
                "Fliesen verfugt",
            ),
            expect_materials=("Bodenablauf", "Abdichtung", "Naturstein"),
        ),
        BaseScenario(
            trade="Fliesen",
            raw=(
                "Heute 35 Quadratmeter Fliesen gelegt, Kleber gezogen, Grundierung benutzt, Fugenmörtel eingebracht "
                "und zum Schluss Silikon gezogen."
            ),
            expect_activities=(
                "35 m² Fliesen verlegt",
                "Fliesenkleber aufgetragen",
                "Grundierung aufgetragen",
                "Fliesen verfugt",
                "Silikonfugen silikoniert",
            ),
            expect_materials=("Fliesen", "Fliesenkleber", "Grundierung", "Fugenmörtel", "Silikon"),
        ),
        BaseScenario(
            trade="Fliesen",
            raw=(
                "heute fliesen gemacht dann ausgleichsmasse gezogen und bodenablauf gesetzt dann verfugt"
            ),
            expect_activities=("Fliesen verlegt", "Nivelliermasse aufgetragen", "Bodenablauf eingebaut", "Fliesen verfugt"),
        ),
        # Tiefbau long chains
        BaseScenario(
            trade="Tiefbau",
            raw=(
                "Heute mit dem Bagger Graben ausgehoben, 30 laufende Meter DN 160 KG Rohr verlegt, "
                "drei KG-Bögen und zwei KG-Abzweige eingebaut, Graben verfüllt und Untergrund verdichtet."
            ),
            expect_activities=(
                "Graben ausgehoben",
                "30 lfm KG-Rohre DN 160 verlegt",
                "KG-Bögen eingebaut",
                "KG-Abzweig eingebaut",
                "Graben verfüllt",
                "Untergrund verdichtet",
            ),
            expect_materials=("KG-Rohre DN 160", "KG-Bögen DN 160", "KG-Abzweige DN 160"),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw=(
                "Heute Leitungstrasse hergestellt, Verbau gesetzt, Hausanschluss gemacht, "
                "danach Drainage eingebaut, Filtervlies verlegt und Asphalt eingebaut."
            ),
            expect_activities=(
                "Leitungstrasse hergestellt",
                "Verbau gesetzt",
                "Hausanschluss hergestellt",
                "Drainage/Entwässerung eingebaut",
                "Geotextil verlegt",
                "Asphalt eingebaut",
            ),
            expect_materials=("Hausanschluss", "Geotextil", "Asphalt"),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw=(
                "Heute Kanal angeschlossen, Schacht gesetzt, anschließend 18 laufende Meter Hunderter KG Rohr verlegt "
                "und dann die Baugrube verdichtet."
            ),
            expect_activities=("Kanal-/Schachtarbeiten durchgeführt", "18 lfm KG-Rohre DN 110 verlegt", "Untergrund verdichtet"),
            expect_materials=("KG-Rohre DN 110",),
        ),
        BaseScenario(
            trade="Tiefbau",
            raw=(
                "heute graben gezogen dann kg rohre gelegt dann grube verfüllt und boden verdichtet"
            ),
            expect_activities=("Graben ausgehoben", "KG-Rohre verlegt", "Graben verfüllt", "Untergrund verdichtet"),
        ),
        # Trockenbau long chains
        BaseScenario(
            trade="Trockenbau",
            raw=(
                "Heute Ständerwerk mit CW/UW-Profilen montiert, Steinwolle Dämmung eingebaut, "
                "Gipskartonplatten montiert, Decke abgehängt und die Fugen mit Fugenspachtel verspachtelt."
            ),
            expect_activities=(
                "Ständerwerk montiert",
                "Dämmung eingebaut",
                "Gipskartonplatten montiert",
                "Decke abgehängt",
                "Fugen verspachtelt",
            ),
            expect_materials=("Steinwolle", "Gipskartonplatten", "Fugenspachtel"),
        ),
        BaseScenario(
            trade="Trockenbau",
            raw=(
                "Heute Brandschutzwand hergestellt, Akustikdecke eingebaut und zum Schluss Revisionsklappe montiert."
            ),
            expect_activities=("Brandschutzwand hergestellt", "Akustikdecke eingebaut", "Revisionsklappe eingebaut"),
        ),
        BaseScenario(
            trade="Trockenbau",
            raw=(
                "Heute Rigips dran gemacht, Wand zugemacht, dann zugespachtelt und Decke abgehangen."
            ),
            expect_activities=("Gipskartonplatten montiert", "Trockenbauwand geschlossen", "Spachtelarbeiten durchgeführt", "Decke abgehängt"),
        ),
        BaseScenario(
            trade="Trockenbau",
            raw=(
                "heute trockenbauwand gestellt dann fugen mit fugenspachtel zugemacht dann dämmung eingebracht"
            ),
            expect_activities=("Trockenbauwand geschlossen", "Fugen verspachtelt", "Dämmung eingebaut"),
        ),
        # Hochbau long chains
        BaseScenario(
            trade="Hochbau",
            raw=(
                "Heute Schalung erstellt, Bewehrung eingebaut, Fundament erstellt, danach 6 Kubikmeter Beton eingebracht "
                "und zum Schluss Filigrandecke montiert."
            ),
            expect_activities=("Schalung erstellt", "Bewehrung eingebaut", "Fundament erstellt", "6 m³ Beton eingebracht", "Filigrandecke montiert"),
            expect_materials=("Schalung", "Bewehrungsstahl", "Beton"),
        ),
        BaseScenario(
            trade="Hochbau",
            raw=(
                "Heute 25 Quadratmeter 17 5 aporoton gemauert, anschließend 15er Kalksandstein verarbeitet "
                "und Mauermörtel eingebracht."
            ),
            expect_activities=("25 m² Mauerwerk erstellt",),
            expect_materials=("17,5er Poroton", "15er KS", "Mauermörtel"),
        ),
        BaseScenario(
            trade="Hochbau",
            raw=(
                "Heute 15 m² 11 5 a porit hochgezogen, Baukleber benutzt und danach Bewährung verarbeitet."
            ),
            expect_activities=("15 m² Mauerwerk erstellt", "Bewehrung eingebaut"),
            expect_materials=("11,5er Porit", "Baukleber", "Bewehrungsstahl"),
        ),
        BaseScenario(
            trade="Hochbau",
            raw=(
                "heute mauer gebaut schalung gestellt dann beton gemacht und bewehrung verbaut"
            ),
            expect_activities=("Mauerwerk erstellt", "Schalung erstellt", "Beton eingebracht", "Bewehrung eingebaut"),
        ),
        # Sanierung/Stuck long chains
        BaseScenario(
            trade="Sanierung",
            raw=(
                "Heute Altputz entfernt, Schimmel beseitigt, Sanierputz aufgebracht, "
                "danach Unterputz nachgearbeitet und Oberputz aufgetragen."
            ),
            expect_activities=("Altputz entfernt", "Schimmel beseitigt", "Sanierputz aufgebracht", "Unterputz aufgetragen", "Oberputz aufgetragen"),
            expect_materials=("Sanierputz", "Unterputz", "Oberputz"),
        ),
        BaseScenario(
            trade="Stuck",
            raw=(
                "Heute Innenputz aufgetragen, WDVS ausgeführt, Armierungsgewebe eingebettet, "
                "danach Sockelputz gemacht, Reibputz gemacht und Kratzputz gemacht."
            ),
            expect_activities=("Innenputz aufgetragen", "WDVS ausgeführt", "Armierung ausgeführt", "Sockelputz aufgetragen", "Reibputz aufgetragen", "Kratzputz aufgetragen"),
            expect_materials=("Innenputz", "Armierungsgewebe", "Sockelputz", "Reibputz", "Kratzputz"),
        ),
        BaseScenario(
            trade="Sanierung",
            raw=(
                "Heute den alten Putz runtergemacht, Haftgrund benutzt, dann Außenputz verarbeitet und Stuckleisten montiert."
            ),
            expect_activities=("Altputz entfernt", "Außenputz aufgetragen", "Stuckarbeiten durchgeführt"),
        ),
        BaseScenario(
            trade="Sanierung",
            raw=(
                "heute schimmel entfernt putz runter dann sanierputz drauf gemacht und oberputz verarbeitet"
            ),
            expect_activities=("Schimmel beseitigt", "Altputz entfernt", "Sanierputz aufgebracht", "Oberputz aufgetragen"),
        ),
    ]


def _build_cases() -> list[Case]:
    bases = _base_scenarios()
    cases: list[Case] = []
    for idx, base in enumerate(bases, start=1):
        # A: original long chain
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
                summary_contains=base.summary_contains,
            )
        )
        # B: gleicher Inhalt mit gebrochenem Einstieg
        broken = f"heute wir machen so: {base.raw.lower()} dann alles fertig."
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
                summary_contains=base.summary_contains,
            )
        )
        # C: mit customer/problem/open in gleicher langen Kette
        contextual = (
            f"{base.raw} Danach mit dem Kunden gesprochen, Kundin war zufrieden. "
            "Problem: Untergrund war uneben und Material fehlt. "
            "Offen bleibt, dass wir morgen nachbestellen und den Rest klären müssen."
        )
        cases.append(
            Case(
                name=f"{base.trade}_{idx:03d}_C",
                raw=contextual,
                expect_activities=base.expect_activities,
                expect_materials=base.expect_materials,
                expect_suggestions=base.expect_suggestions,
                forbid_activities=base.forbid_activities,
                forbid_suggestions=base.forbid_suggestions,
                expect_problem=True,
                expect_open=True,
                expect_customer=True,
                summary_contains=base.summary_contains,
            )
        )

    return cases


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    cases = _build_cases()
    failures: list[str] = []

    for case in cases:
        body = StructureReportBody(
            projectId="p-wave3-long",
            projectName="Long Chain Matrix",
            customerName="Testkunde",
            date="2026-06-18",
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
        summary = str(structured.get("summary") or "")

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
        for needle in case.summary_contains:
            if needle.casefold() not in summary.casefold():
                failures.append(f"{case.name}: summary fehlt -> {needle} (summary={summary!r})")

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer trotz Problem-Text")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer trotz Offen-Text")
        if case.expect_customer and ("kund" not in customer.casefold()):
            failures.append(f"{case.name}: customerTalk leer trotz Kunden-Text (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-LONGCHAIN-WAVE3-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:260]:
            print(" -", row)
        if len(failures) > 260:
            print(f" ... weitere {len(failures) - 260} Fehler gekürzt")
        return 1

    print("VIRTUAL-SPEECH-LONGCHAIN-WAVE3-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

