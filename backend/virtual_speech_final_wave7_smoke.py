"""Welle 7 (finaler Sprach-Engine-Lauf vor Pilot).

Ziele:
- Alle aktiven Gewerke mit Aneinanderreihungen von Taetigkeiten testen.
- Je Gewerk: normales Deutsch, gebrochenes Deutsch, Whisper-Noise, Kontext.
- Zusaetzlich die ZUSAMMENFASSUNG im Blick: muss vorhanden und belastbar sein,
  wenn Taetigkeiten erkannt wurden (deterministische Basis; in Produktion macht
  Hebel 1 daraus natuerlicheren Text).

Rein additiv. Nichts Bestehendes wird angefasst.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_final_wave7_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class BaseScenario:
    trade: str
    raw: str
    expect_activities: tuple[str, ...]
    forbid_activities: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Case:
    name: str
    raw: str
    expect_activities: tuple[str, ...]
    forbid_activities: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ===================== GaLaBau =====================
        BaseScenario("GaLaBau",
                     "Heute haben wir 60 Quadratmeter Pflaster verlegt, 25 laufende Meter Rasenkantensteine gesetzt, die Hecke geschnitten und zum Schluss Rindenmulch eingedeckt.",
                     ("60 m² Pflaster verlegt", "Rasenkantensteine gesetzt", "Hecke geschnitten", "Rindenmulch eingedeckt")),
        BaseScenario("GaLaBau",
                     "Wir haben den Rasen gemäht, vertikutiert und anschließend gedüngt sowie die Fläche bewässert.",
                     ("Rasen gemäht", "Rasen vertikutiert", "Rasen gedüngt", "Fläche bewässert")),
        BaseScenario("GaLaBau",
                     "heute ich machen 50 quadrat Pflaster und Hecke schneiden und Unkraut weg machen.",
                     ("50 m² Pflaster verlegt", "Hecke geschnitten", "Unkraut entfernt")),
        BaseScenario("GaLaBau",
                     "heute ich hab gemacht 15 meter Palisaden gesetzt und 30 quadrat Rollrasen verlegt.",
                     ("15 lfm Palisaden gesetzt", "30 m² Rasen verlegt")),
        BaseScenario("GaLaBau",
                     "30 Quadratmeter Keramikterrasse verlegt, Geotextil verlegt und Splitt 2/5 mm eingebaut.",
                     ("30 m² Keramikterrasse verlegt", "Geotextil verlegt", "Splitt 2/5 mm eingebaut")),

        # ===================== Sanierung / Stuck =====================
        BaseScenario("Sanierung",
                     "Heute den Altputz entfernt, den Schimmel beseitigt, Unterputz aufgetragen und Oberputz aufgetragen.",
                     ("Altputz entfernt", "Schimmel beseitigt", "Unterputz aufgetragen", "Oberputz aufgetragen")),
        BaseScenario("Sanierung",
                     "heute ich hab gemacht 40 quadrat unterputz und 40 quadrat oberputz.",
                     ("Unterputz aufgetragen", "Oberputz aufgetragen")),
        BaseScenario("Stuck",
                     "Wir haben Grundputz aufgetragen, im Innenbereich Innenputz aufgebracht und außen Sockelputz verarbeitet.",
                     ("Grundputz aufgetragen", "Innenputz aufgetragen", "Sockelputz aufgetragen")),
        BaseScenario("Stuck",
                     "ich machen WDVS und Armierung und Reibputz.",
                     ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen")),

        # ===================== SHK =====================
        BaseScenario("SHK",
                     "Wir haben 30 laufende Meter KG-Rohre DN 110 verlegt, drei Heizkörper montiert, das WC gesetzt und eine Druckprüfung durchgeführt.",
                     ("30 lfm KG-Rohre DN 110 verlegt", "Heizkörper montiert", "WC montiert", "Druckprüfung durchgeführt")),
        BaseScenario("SHK",
                     "Heute die Wasserleitungen verlegt, die Fußbodenheizung verlegt und den hydraulischen Abgleich durchgeführt.",
                     ("Wasserleitungen verlegt", "Fußbodenheizung verlegt", "Hydraulischer Abgleich durchgeführt")),
        BaseScenario("SHK",
                     "ich hab gemacht WC und Waschbecken montiert und dann Druckprüfung gemacht.",
                     ("WC montiert", "Waschbecken montiert", "Druckprüfung durchgeführt")),
        BaseScenario("SHK",
                     "heute ich machen Dusche und Armaturen fertig und Heizkörper montiert.",
                     ("Dusche montiert", "Armaturen montiert", "Heizkörper montiert")),

        # ===================== Fliesen =====================
        BaseScenario("Fliesen",
                     "Heute Nivelliermasse aufgetragen, danach 40 Quadratmeter Fliesen verlegt, anschließend verfugt und die Silikonfugen gezogen.",
                     ("Nivelliermasse aufgetragen", "40 m² Fliesen verlegt", "Fliesen verfugt", "Silikonfugen silikoniert")),
        BaseScenario("Fliesen",
                     "Abdichtung hergestellt, Bodenablauf eingebaut und 25 Quadratmeter Großformatfliesen verlegt.",
                     ("Abdichtung hergestellt", "Bodenablauf eingebaut", "25 m² Großformatfliesen verlegt")),
        BaseScenario("Fliesen",
                     "heute auf baustell ich hab gearbeitet 30 quadrat Fliesen und dann verfugt.",
                     ("30 m² Fliesen verlegt", "Fliesen verfugt")),

        # ===================== Tiefbau =====================
        BaseScenario("Tiefbau",
                     "Graben ausgehoben, 30 laufende Meter KG-Rohre DN 160 verlegt, Graben verfüllt und Untergrund verdichtet.",
                     ("Graben ausgehoben", "30 lfm KG-Rohre DN 160 verlegt", "Graben verfüllt", "Untergrund verdichtet")),
        BaseScenario("Tiefbau",
                     "Heute Hausanschluss hergestellt, Leitungstrasse hergestellt und Drainage eingebaut.",
                     ("Hausanschluss hergestellt", "Leitungstrasse hergestellt", "Drainage/Entwässerung eingebaut")),
        BaseScenario("Tiefbau",
                     "heute ich graben gemacht 15 meter und dann graben wieder verfüllt und Asphalt fertig.",
                     ("Graben ausgehoben", "Graben verfüllt", "Asphalt eingebaut")),

        # ===================== Trockenbau =====================
        BaseScenario("Trockenbau",
                     "Ständerwerk montiert, Dämmung eingebaut, Gipskartonplatten beplankt und die Fugen verspachtelt.",
                     ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Fugen verspachtelt")),
        BaseScenario("Trockenbau",
                     "Heute die Decke abgehängt und die Trockenbauwand geschlossen.",
                     ("Decke abgehängt", "Trockenbauwand geschlossen")),
        BaseScenario("Trockenbau",
                     "ich hab gemacht Ständerwerk und Dämmung eingebaut und Gipskarton montiert.",
                     ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert")),

        # ===================== Hochbau =====================
        BaseScenario("Hochbau",
                     "Schalung erstellt, Bewehrung eingebaut und 8 Kubikmeter Beton eingebracht.",
                     ("Schalung erstellt", "Bewehrung eingebaut", "8 m³ Beton eingebracht")),
        BaseScenario("Hochbau",
                     "Heute 12 Quadratmeter Mauerwerk aus Kalksandstein erstellt und Fundament erstellt.",
                     ("Mauerwerk erstellt", "Fundament erstellt")),
        BaseScenario("Hochbau",
                     "ich machen 6 kubik Beton und Schalung.",
                     ("6 m³ Beton eingebracht", "Schalung erstellt")),
    ]


def _whisper_noise(text: str) -> str:
    out = text
    pairs = (
        (r"\bUnterputz\b", "unter putz"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bHecke\b", "Ecke"),
        (r"\bGeotextil\b", "Geotextiel"),
        (r"\bDruckprüfung\b", "Druckprufung"),
        (r"\bQuadratmeter\b", "quadrat"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    # Realistische Whisper-Simulation: Verhoerer + Kleinschreibung. Satzzeichen
    # bleiben erhalten (Whisper setzt i.d.R. Satz-/Teilsatzgrenzen).
    return out.lower()


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
                    f"{base.raw} Der Kunde war vor Ort und sehr zufrieden. "
                    "Problem: die Lieferung kam zu spät und es hat zwischendurch geregnet. "
                    "Offen: morgen müssen wir den Rest fertig machen und noch aufräumen."
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
                    forbid_activities=base.forbid_activities,
                    expect_problem=ep,
                    expect_open=eo,
                    expect_customer=ec,
                )
            )
            idx += 1
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="p-wave7",
        projectName="Finaler Lauf",
        customerName="Testkunde",
        date="2026-06-20",
        employeeNames=["Max", "Goran", "Ahmet"],
        startTime="07:00",
        endTime="17:00",
        exportFormat="PDF",
        rawText=case.raw,
    )
    out = api_structure_report(body, store=_STORE)
    return out.get("structured") or {}


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    cases = _build_cases()
    failures: list[str] = []

    for case in cases:
        structured = _run_case(case)
        acts = [str(x) for x in (structured.get("activities") or [])]
        probs = [str(x) for x in (structured.get("problems") or [])]
        opens = [str(x) for x in (structured.get("openItems") or [])]
        customer = str(structured.get("customerTalk") or "")
        summary = str(structured.get("summary") or "")

        for expected in case.expect_activities:
            if not _contains_any(acts, expected):
                failures.append(f"{case.name}: activity fehlt -> {expected} (got={acts!r})")
        for forbidden in case.forbid_activities:
            if _contains_any(acts, forbidden):
                failures.append(f"{case.name}: activity verboten -> {forbidden} (got={acts!r})")

        # Zusammenfassung: muss belastbar sein, sobald Taetigkeiten erkannt wurden.
        if acts:
            if not summary or summary.strip() == "Keine Angabe" or len(summary.strip()) < 15:
                failures.append(f"{case.name}: Zusammenfassung leer/zu kurz (got={summary!r})")

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer trotz Problem-Text")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer trotz Offen-Text")
        if case.expect_customer and ("kund" not in customer.casefold()):
            failures.append(f"{case.name}: customerTalk leer trotz Kunden-Text (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-FINAL-WAVE7-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:400]:
            print(" -", row)
        return 1

    print("VIRTUAL-SPEECH-FINAL-WAVE7-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
