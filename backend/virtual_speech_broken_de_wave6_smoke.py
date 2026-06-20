"""Welle 6: Gebrochenes Deutsch / Nicht-Muttersprachler + Whisper + Kontext.

Schwerpunkt:
- Wortstellung Verb-vor-Objekt ("ich hab gemacht 30 quadrat Pflaster").
- Generische Verben (gemacht/gearbeitet/machen/macht/fertig) statt Fachverb.
- Verkuerzte Einheiten ("30 quadrat", "20 meter").
- Banale Live-Baustellensaetze + formelle/normale Saetze.
- problems / openItems / customerTalk per Rohtext, korrekt gefiltert.

Rein additiv: nichts Bestehendes wird angefasst.
"""

from __future__ import annotations

import os
import re
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_broken_de_wave6_")))
_SMOKE_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class BaseScenario:
    trade: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...] = ()
    forbid_activities: tuple[str, ...] = ()


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


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ============ GaLaBau ============
        # broken (Verb-vor-Objekt, generisches Verb, verkuerzte Einheit)
        BaseScenario("GaLaBau", "Heute ich hab gemacht 30 quadrat Pflaster.",
                     ("30 m² Pflaster verlegt",)),
        BaseScenario("GaLaBau", "heute ich machen Hecke schneiden und Unkraut weg machen.",
                     ("Hecke geschnitten", "Unkraut entfernt")),
        BaseScenario("GaLaBau", "ich hab gelegt Rollrasen und dann Fläche bewässert.",
                     ("Rasen verlegt", "Fläche bewässert")),
        BaseScenario("GaLaBau", "heute ich hab gearbeitet 15 meter Palisaden gesetzt.",
                     ("Palisaden gesetzt",)),
        BaseScenario("GaLaBau", "heute auf baustell ich hab gemacht 8 quadrat Gartenmauer.",
                     ("8 m² Gartenmauer gebaut",)),
        # formell / normal
        BaseScenario("GaLaBau",
                     "Heute haben wir 45 Quadratmeter Pflaster verlegt und 20 laufende Meter Rasenkantensteine gesetzt.",
                     ("45 m² Pflaster verlegt", "Rasenkantensteine gesetzt")),
        BaseScenario("GaLaBau",
                     "Wir haben die Hecke geschnitten, den Rasen gemäht und anschließend Rindenmulch eingedeckt.",
                     ("Hecke geschnitten", "Rasen gemäht", "Rindenmulch eingedeckt")),

        # ============ Sanierung / Stuck (Putz) ============
        BaseScenario("Sanierung", "heute auf baustell ich hab gearbeitet 30 quadrat oberputz.",
                     ("Oberputz aufgetragen",), expect_materials=("Oberputz",)),
        BaseScenario("Sanierung", "heute ich hab gemacht 40 quadrat unterputz und 40 quadrat oberputz.",
                     ("Unterputz aufgetragen", "Oberputz aufgetragen")),
        BaseScenario("Sanierung", "ich hab gemacht Schimmel weg und dann Sanierputz drauf.",
                     ("Schimmel beseitigt", "Sanierputz aufgebracht")),
        BaseScenario("Stuck", "heute ich machen innenputz und sockelputz.",
                     ("Innenputz aufgetragen", "Sockelputz aufgetragen")),
        # formell
        BaseScenario("Stuck",
                     "Heute haben wir Grundputz aufgetragen und im Außenbereich Reibputz verarbeitet.",
                     ("Grundputz aufgetragen", "Reibputz aufgetragen")),
        BaseScenario("Sanierung",
                     "Wir haben den Altputz entfernt, den Schimmel beseitigt und Sanierputz aufgebracht.",
                     ("Altputz entfernt", "Schimmel beseitigt", "Sanierputz aufgebracht")),

        # ============ SHK ============
        BaseScenario("SHK", "heute ich hab gemacht WC und Waschbecken montiert.",
                     ("WC montiert", "Waschbecken montiert")),
        BaseScenario("SHK", "ich hab gemacht Heizkörper und dann Druckprüfung gemacht.",
                     ("Heizkörper montiert", "Druckprüfung durchgeführt")),
        BaseScenario("SHK", "heute ich hab gearbeitet 20 meter kg rohr dn 110 verlegt.",
                     ("20 lfm KG-Rohre DN 110 verlegt",)),
        BaseScenario("SHK", "ich machen Dusche und Armaturen fertig.",
                     ("Dusche montiert", "Armaturen montiert")),
        # formell
        BaseScenario("SHK",
                     "Heute haben wir die Wasserleitungen verlegt, die Heizkörper montiert und eine Druckprüfung durchgeführt.",
                     ("Wasserleitungen verlegt", "Heizkörper montiert", "Druckprüfung durchgeführt")),
        BaseScenario("SHK",
                     "Wir haben die Fußbodenheizung verlegt und den hydraulischen Abgleich durchgeführt.",
                     ("Fußbodenheizung verlegt", "Hydraulischer Abgleich durchgeführt")),

        # ============ Fliesen ============
        BaseScenario("Fliesen", "heute auf baustell ich hab gearbeitet 25 quadrat Fliesen.",
                     ("25 m² Fliesen verlegt",)),
        BaseScenario("Fliesen", "ich hab gemacht Fliesen verfugt und Silikon gezogen.",
                     ("Fliesen verfugt", "Silikonfugen silikoniert")),
        BaseScenario("Fliesen", "heute ich machen 60 quadrat Großformat Fliesen.",
                     ("60 m² Großformatfliesen verlegt",)),
        BaseScenario("Fliesen", "ich hab gemacht Abdichtung und Bodenablauf eingebaut.",
                     ("Abdichtung hergestellt", "Bodenablauf eingebaut")),
        # formell
        BaseScenario("Fliesen",
                     "Heute haben wir Nivelliermasse aufgetragen, 35 Quadratmeter Fliesen verlegt und anschließend verfugt.",
                     ("Nivelliermasse aufgetragen", "35 m² Fliesen verlegt", "Fliesen verfugt")),

        # ============ Tiefbau ============
        BaseScenario("Tiefbau", "heute ich graben gemacht 15 meter und dann graben wieder verfüllt.",
                     ("Graben ausgehoben", "Graben verfüllt")),
        BaseScenario("Tiefbau", "ich hab gemacht Asphalt auf Straße fertig.",
                     ("Asphalt eingebaut",)),
        BaseScenario("Tiefbau", "heute ich hab gemacht Hausanschluss und Leitungstrasse.",
                     ("Hausanschluss hergestellt", "Leitungstrasse hergestellt")),
        # formell
        BaseScenario("Tiefbau",
                     "Heute haben wir den Graben ausgehoben, 30 laufende Meter KG-Rohre DN 160 verlegt und den Graben wieder verfüllt.",
                     ("Graben ausgehoben", "30 lfm KG-Rohre DN 160 verlegt", "Graben verfüllt")),
        BaseScenario("Tiefbau",
                     "Wir haben die Drainage eingebaut, Filtervlies verlegt und den Untergrund verdichtet.",
                     ("Drainage/Entwässerung eingebaut", "Geotextil verlegt", "Untergrund verdichtet")),

        # ============ Trockenbau ============
        BaseScenario("Trockenbau", "heute ich hab gemacht Ständerwerk und Dämmung eingebaut.",
                     ("Ständerwerk montiert", "Dämmung eingebaut")),
        BaseScenario("Trockenbau", "ich machen Decke abgehängt und Gipskarton montiert.",
                     ("Decke abgehängt", "Gipskartonplatten montiert")),
        # formell
        BaseScenario("Trockenbau",
                     "Heute haben wir das Ständerwerk montiert, die Dämmung eingebaut und die Gipskartonplatten beplankt.",
                     ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert")),
        BaseScenario("Trockenbau",
                     "Wir haben die Decke abgehängt und die Fugen verspachtelt.",
                     ("Decke abgehängt", "Fugen verspachtelt")),

        # ============ Vertiefung: weitere banale gebrochene Faelle ============
        BaseScenario("GaLaBau", "heute ich machen Rasen mähen 100 quadrat.",
                     ("100 m² Rasen gemäht",)),
        BaseScenario("GaLaBau", "ich hab gemacht Beet und Pflanzen gesetzt.",
                     ("Pflanzen gesetzt",)),
        BaseScenario("GaLaBau", "heute ich hab gemacht 20 quadrat Rollrasen verlegt.",
                     ("20 m² Rasen verlegt",)),
        BaseScenario("Fliesen", "ich machen 20 quadrat Naturstein.",
                     ("20 m² Naturstein verlegt",)),
        BaseScenario("Fliesen", "heute ich hab gemacht Nivelliermasse.",
                     ("Nivelliermasse aufgetragen",)),
        BaseScenario("SHK", "heute ich hab gemacht KG Bögen und KG Abzweig.",
                     ("KG-Bögen eingebaut", "KG-Abzweig eingebaut")),
        BaseScenario("SHK", "ich hab gemacht Fußbodenheizung verlegt.",
                     ("Fußbodenheizung verlegt",)),
        BaseScenario("Tiefbau", "heute ich machen Verbau gesetzt und Untergrund verdichtet.",
                     ("Verbau gesetzt", "Untergrund verdichtet")),
        BaseScenario("Trockenbau", "ich hab gemacht Akustikdecke eingebaut und Revisionsklappe montiert.",
                     ("Akustikdecke eingebaut", "Revisionsklappe eingebaut")),
        BaseScenario("Hochbau", "heute ich hab gemacht Fundament erstellt und Filigrandecke montiert.",
                     ("Fundament erstellt", "Filigrandecke montiert")),
        BaseScenario("Stuck", "ich hab gemacht WDVS und Armierung.",
                     ("WDVS ausgeführt", "Armierung ausgeführt")),

        # ============ Hochbau ============
        BaseScenario("Hochbau", "heute ich hab gemacht 5 kubik Beton.",
                     ("5 m³ Beton eingebracht",)),
        BaseScenario("Hochbau", "ich hab gemacht Schalung und Bewehrung eingebaut.",
                     ("Schalung erstellt", "Bewehrung eingebaut")),
        BaseScenario("Hochbau", "heute ich machen 12 quadrat Mauerwerk Kalksandstein.",
                     ("Mauerwerk erstellt",)),
        # formell
        BaseScenario("Hochbau",
                     "Heute haben wir die Schalung erstellt, die Bewehrung eingebaut und 6 Kubikmeter Beton eingebracht.",
                     ("Schalung erstellt", "Bewehrung eingebaut", "6 m³ Beton eingebracht")),
    ]


def _whisper_noise(text: str) -> str:
    out = text
    pairs = (
        (r"\bUnterputz\b", "unter putz"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bHecke\b", "Ecke"),
        (r"\bGeotextil\b", "Geotextiel"),
        (r"\bDruckprüfung\b", "Druckprufung"),
        (r"\bquadratmeter\b", "quadrat"),
        (r"\bQuadratmeter\b", "quadrat"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out)
    return out.replace(",", "").replace(".", "")


def _build_cases() -> list[Case]:
    bases = _base_scenarios()
    cases: list[Case] = []
    idx = 1
    for variant in ("P", "K", "W"):
        for base in bases:
            if variant == "P":
                raw = base.raw
                ep = eo = ec = False
            elif variant == "K":
                raw = (
                    f"{base.raw} Kunde war da und hat gesagt alles super. "
                    "Problem: Lieferung kam zu spät und Untergrund war nass. "
                    "Offen: morgen müssen wir Rest fertig machen und aufräumen."
                )
                ep = eo = ec = True
            else:
                raw = _whisper_noise(base.raw)
                ep = eo = ec = False
            cases.append(
                Case(
                    name=f"{base.trade}_{idx:03d}_{variant}",
                    raw=raw,
                    expect_activities=base.expect_activities,
                    expect_materials=base.expect_materials,
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
            projectId="p-wave6",
            projectName="Broken DE Matrix",
            customerName="Testkunde",
            date="2026-06-20",
            employeeNames=["Max", "Goran", "Ahmet"],
            startTime="07:00",
            endTime="17:00",
            exportFormat="PDF",
            rawText=case.raw,
        )
        out = api_structure_report(body, store=_SMOKE_STORE)
        structured = out.get("structured") or {}
        acts = [str(x) for x in (structured.get("activities") or [])]
        mats = [str(x) for x in (structured.get("materials") or [])]
        probs = [str(x) for x in (structured.get("problems") or [])]
        opens = [str(x) for x in (structured.get("openItems") or [])]
        customer = str(structured.get("customerTalk") or "")

        for expected in case.expect_activities:
            if not _contains_any(acts, expected):
                failures.append(f"{case.name}: activity fehlt -> {expected} (got={acts!r})")
        for expected in case.expect_materials:
            if not _contains_any(mats, expected):
                failures.append(f"{case.name}: material fehlt -> {expected} (got={mats!r})")
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
        print("VIRTUAL-SPEECH-BROKEN-DE-WAVE6-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:400]:
            print(" -", row)
        if len(failures) > 400:
            print(f" ... weitere {len(failures) - 400} Fehler gekuerzt")
        return 1

    print("VIRTUAL-SPEECH-BROKEN-DE-WAVE6-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
