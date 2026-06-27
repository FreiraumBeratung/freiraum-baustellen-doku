"""Welle 8: Aneinanderreihungen (Ketten) pro Gewerk — Pilot-Härtung.

Fokus:
- Mehrere aufeinanderfolgende Tätigkeiten in einem Diktat (Ketten)
- Kurze Einzeltätigkeiten als Mischung
- ASR-/Whisper-Patzer und gebrochenes Deutsch
- Zusammenfassung darf keine erkannten Tätigkeiten verschlucken
- Materialien und Vorschläge im Blick

Rein additiv. Bei Fehlern: gezielt patchen, erneut testen.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_chain_wave8_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class BaseScenario:
    trade: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...] = field(default_factory=tuple)
    forbid_activities: tuple[str, ...] = field(default_factory=tuple)
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
  """Kurze Stichwörter, die in der Zusammenfassung vorkommen sollen."""
  out: list[str] = []
  for act in activities:
    low = act.casefold()
    if "kg-rohr" in low:
      out.append("KG-Rohr")
    elif "unterputz" in low:
      out.append("Unterputz")
    elif "oberputz" in low:
      out.append("Oberputz")
    elif "altputz" in low:
      out.append("Altputz")
    elif "geschiffen" in low:
      out.append("geschiffen")
    elif "grundierung" in low or "grundiert" in low:
      out.append("Grundierung")
    elif "ausgeschachtet" in low:
      out.append("ausgeschachtet")
    elif "verdichtet" in low:
      out.append("verdichtet")
    elif "sand" in low:
      out.append("Sand")
    elif "pflaster" in low:
      out.append("Pflaster")
    elif "fliesen" in low:
      out.append("Fliesen")
    elif "heizkörper" in low or "heizkoerper" in low:
      out.append("Heizkörper")
    elif "schalung" in low:
      out.append("Schalung")
    elif "bewehrung" in low:
      out.append("Bewehrung")
    elif "gipskarton" in low:
      out.append("Gipskarton")
    elif "hecke" in low:
      out.append("Hecke")
    elif "drainage" in low or "entwässerung" in low:
      out.append("Drainage")
    else:
      # Fallback: erstes substantivisches Wort mit mind. 5 Zeichen
      m = re.search(r"[A-ZÄÖÜa-zäöüß]{5,}", act)
      if m:
        out.append(m.group(0))
  return tuple(dict.fromkeys(out))


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ===== Tiefbau — Pilot-Kette (User-Beispiel) =====
        BaseScenario(
            "Tiefbau",
            "Den Boden haben wir ausgeschachtet die KG Rohre verlegt Sand reingepackt und dann den Boden verdichtet.",
            ("Boden ausgeschachtet", "KG-Rohre verlegt", "Sand eingebaut", "Untergrund verdichtet"),
            expect_materials=("KG-Rohre",),
        ),
        BaseScenario(
            "Tiefbau",
            "Graben ausgehoben 25 laufende Meter KG-Rohre DN 110 verlegt Schotter eingebaut Graben verfüllt und Planum verdichtet.",
            ("KG-Rohre DN 110 verlegt", "Schotter eingebaut", "Graben ausgehoben", "Graben verfüllt", "Untergrund verdichtet"),
            expect_materials=("KG-Rohre DN 110", "Schotter"),
        ),
        BaseScenario(
            "Tiefbau",
            "Hausanschluss hergestellt Leitungstrasse hergestellt Drainage eingebaut und Schacht gesetzt.",
            ("Hausanschluss hergestellt", "Leitungstrasse hergestellt", "Drainage/Entwässerung eingebaut"),
        ),
        BaseScenario(
            "Tiefbau",
            "heute ich graben gemacht 20 meter kg rohre verlegt sand rein und boden verdichtet.",
            ("KG-Rohre verlegt", "Sand eingebaut", "Untergrund verdichtet"),
        ),
        BaseScenario("Tiefbau", "Frostschutz eingebaut.", ("Frostschutz eingebaut",)),

        # ===== Putz / Stuck — Pilot-Kette =====
        BaseScenario(
            "Putz",
            "Heute haben wir den alten Putz abgetragen die Wand geschliffen die Wand danach grundiert den Unterputz aufgetragen und als der Unterputz fertig geworden ist den Oberputz aufgetragen.",
            ("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen"),
        ),
        BaseScenario(
            "Putz",
            "Altputz entfernt Schimmel beseitigt Unterputz aufgetragen und Oberputz aufgetragen.",
            ("Altputz entfernt", "Schimmel beseitigt", "Unterputz aufgetragen", "Oberputz aufgetragen"),
        ),
        BaseScenario(
            "Stuck",
            "Grundputz aufgetragen Innenputz aufgebracht Sockelputz verarbeitet und Reibputz aufgetragen.",
            ("Grundputz aufgetragen", "Innenputz aufgetragen", "Sockelputz aufgetragen", "Reibputz aufgetragen"),
        ),
        BaseScenario(
            "Stuck",
            "WDVS gedämmt Armierung aufgebracht und Reibputz aufgetragen.",
            ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen"),
        ),
        BaseScenario("Putz", "40 Quadratmeter Unterputz aufgetragen.", ("Unterputz aufgetragen",)),

        # ===== GaLaBau =====
        BaseScenario(
            "GaLaBau",
            "60 Quadratmeter Pflaster verlegt 25 laufende Meter Rasenkantensteine gesetzt Hecke geschnitten und Rindenmulch eingedeckt.",
            ("60 m² Pflaster verlegt", "Rasenkantensteine gesetzt", "Hecke geschnitten", "Rindenmulch eingedeckt"),
            expect_materials=("Pflastersteine", "Rasenkantensteine", "Rindenmulch"),
        ),
        BaseScenario(
            "GaLaBau",
            "Rasen gemäht Rasen vertikutiert Rasen gedüngt und Fläche bewässert.",
            ("Rasen gemäht", "Rasen vertikutiert", "Rasen gedüngt", "Fläche bewässert"),
        ),
        BaseScenario(
            "GaLaBau",
            "30 Quadratmeter Keramikterrasse verlegt Geotextil verlegt und Splitt 2/5 mm eingebaut.",
            ("30 m² Keramikterrasse verlegt", "Geotextil verlegt", "Splitt 2/5 mm eingebaut"),
            expect_materials=("Keramikplatten", "Geotextil", "Splitt"),
        ),
        BaseScenario(
            "GaLaBau",
            "15 laufende Meter Palisaden gesetzt 30 Quadratmeter Rollrasen verlegt und Unkraut entfernt.",
            ("Palisaden gesetzt", "30 m² Rasen verlegt", "Unkraut entfernt"),
        ),
        BaseScenario("GaLaBau", "Hecke zurückgeschnitten.", ("Hecke geschnitten",)),

        # ===== SHK =====
        BaseScenario(
            "SHK",
            "30 laufende Meter KG-Rohre DN 110 verlegt drei Heizkörper montiert WC gesetzt und Druckprüfung durchgeführt.",
            ("KG-Rohre DN 110 verlegt", "Heizkörper montiert", "WC montiert", "Druckprüfung durchgeführt"),
            expect_materials=("KG-Rohre DN 110", "Heizkörper"),
        ),
        BaseScenario(
            "SHK",
            "Wasserleitungen verlegt Fußbodenheizung verlegt und hydraulischen Abgleich durchgeführt.",
            ("Wasserleitungen verlegt", "Fußbodenheizung verlegt", "Hydraulischer Abgleich durchgeführt"),
        ),
        BaseScenario(
            "SHK",
            "WC montiert Waschbecken montiert Dusche montiert Armaturen montiert und Druckprüfung gemacht.",
            ("WC montiert", "Waschbecken montiert", "Dusche montiert", "Armaturen montiert", "Druckprüfung durchgeführt"),
        ),
        BaseScenario("SHK", "Heizkörper montiert.", ("Heizkörper montiert",)),

        # ===== Fliesen =====
        BaseScenario(
            "Fliesen",
            "Wand grundiert Nivelliermasse aufgetragen 40 Quadratmeter Fliesen verlegt und verfugt.",
            ("Grundierung aufgetragen", "Nivelliermasse aufgetragen", "40 m² Fliesen verlegt", "Fliesen verfugt"),
            expect_materials=("Fliesen", "Nivelliermasse"),
        ),
        BaseScenario(
            "Fliesen",
            "Abdichtung hergestellt Bodenablauf eingebaut 25 Quadratmeter Großformatfliesen verlegt und Silikonfugen gezogen.",
            ("Abdichtung hergestellt", "Bodenablauf eingebaut", "25 m² Großformatfliesen verlegt", "Silikonfugen silikoniert"),
        ),
        BaseScenario(
            "Fliesen",
            "Fliesenkleber aufgetragen Fliesen verlegt verfugt und Silikonfugen silikoniert.",
            ("Fliesenkleber aufgetragen", "Fliesen verlegt", "Fliesen verfugt", "Silikonfugen silikoniert"),
        ),
        BaseScenario("Fliesen", "15 Quadratmeter Fliesen verlegt.", ("15 m² Fliesen verlegt",)),

        # ===== Trockenbau =====
        BaseScenario(
            "Trockenbau",
            "Ständerwerk montiert Dämmung eingebaut Gipskartonplatten beplankt und Fugen verspachtelt.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Fugen verspachtelt"),
            expect_materials=("Gipskartonplatten",),
        ),
        BaseScenario(
            "Trockenbau",
            "Decke abgehängt Trockenbauwand geschlossen und Revisionsklappe eingebaut.",
            ("Decke abgehängt", "Trockenbauwand geschlossen"),
        ),
        BaseScenario("Trockenbau", "Gipskarton montiert.", ("Gipskartonplatten montiert",)),

        # ===== Hochbau =====
        BaseScenario(
            "Hochbau",
            "Schalung erstellt Bewehrung eingebaut und 8 Kubikmeter Beton eingebracht.",
            ("Schalung erstellt", "Bewehrung eingebaut", "8 m³ Beton eingebracht"),
            expect_materials=("Beton",),
        ),
        BaseScenario(
            "Hochbau",
            "Fundament erstellt 12 Quadratmeter Mauerwerk gemauert und Betondecke gegossen.",
            ("Fundament erstellt", "Mauerwerk erstellt"),
        ),
        BaseScenario(
            "Hochbau",
            "Bewehrung eingebaut Schalung gestellt und Beton eingebracht.",
            ("Bewehrung eingebaut", "Schalung erstellt", "Beton eingebracht"),
        ),
        BaseScenario("Hochbau", "Schalung erstellt.", ("Schalung erstellt",)),
    ]


def _broken_de(text: str) -> str:
    return (
        text.replace("haben wir", "wir hab")
        .replace("Heute", "heute")
        .replace("und dann", "dann")
        .replace("Quadratmeter", "quadrat")
        .replace("laufende Meter", "lauf meter")
    )


def _whisper_noise(text: str) -> str:
    out = text
    pairs = (
        (r"\bUnterputz\b", "unter putz"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bHecke\b", "Ecke"),
        (r"\bGeotextil\b", "Geotextiel"),
        (r"\bDruckprüfung\b", "Druckprufung"),
        (r"\bQuadratmeter\b", "quadrat"),
        (r"\bGrundierung\b", "grundierung"),
        (r"\bausgeschachtet\b", "aus geschachtet"),
        (r"\bgeschliffen\b", "geschliffen"),
        (r"\bKG-Rohre\b", "kg rohre"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _build_cases() -> list[Case]:
    bases = _base_scenarios()
    cases: list[Case] = []
    idx = 1
    for variant in ("P", "K", "W", "B", "S"):
        for base in bases:
            if variant == "P":
                raw = base.raw
                ep = eo = ec = False
            elif variant == "K":
                raw = (
                    f"{base.raw} Der Kunde war vor Ort. "
                    "Problem: Lieferung kam zu spät und es hat geregnet. "
                    "Offen: morgen Rest fertig machen."
                )
                ep = eo = ec = True
            elif variant == "W":
                raw = _whisper_noise(base.raw)
                ep = eo = ec = False
            elif variant == "B":
                raw = _broken_de(base.raw)
                ep = eo = ec = False
            else:  # S — kurzer Kontext-Prefix
                raw = f"Kurz: {base.raw}"
                ep = eo = ec = False

            summary_needles = base.summary_contains or _summary_needles(base.expect_activities)
            cases.append(
                Case(
                    name=f"{base.trade}_{idx:03d}_{variant}",
                    raw=raw,
                    expect_activities=base.expect_activities,
                    expect_materials=base.expect_materials,
                    forbid_activities=base.forbid_activities,
                    summary_contains=summary_needles,
                    expect_problem=ep,
                    expect_open=eo,
                    expect_customer=ec,
                    min_activity_count=len(base.expect_activities),
                )
            )
            idx += 1
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="p-wave8",
        projectName="Ketten-Lauf",
        customerName="Testkunde",
        date="2026-06-27",
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
                failures.append(f"{case.name}: activity verboten -> {forbidden} (got={acts!r})")

        if acts:
            if not summary or summary.strip() == "Keine Angabe" or len(summary.strip()) < 15:
                failures.append(f"{case.name}: Zusammenfassung leer/zu kurz (got={summary!r})")
            # Mindestens die Hälfte der Summary-Nadeln muss in der Zusammenfassung vorkommen
            if case.summary_contains:
                hits = sum(1 for n in case.summary_contains if n.casefold() in summary.casefold())
                if len(case.summary_contains) <= 1:
                    needed = 1
                else:
                    needed = max(2, (len(case.summary_contains) + 1) // 2)
                if hits < needed:
                    failures.append(
                        f"{case.name}: summary zu dünn ({hits}/{needed} Stichwörter) "
                        f"need={case.summary_contains!r} summary={summary!r}"
                    )

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer trotz Problem-Text")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer trotz Offen-Text")
        if case.expect_customer and ("kund" not in customer.casefold()):
            failures.append(f"{case.name}: customerTalk leer trotz Kunden-Text (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-CHAIN-WAVE8-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-CHAIN-WAVE8-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
