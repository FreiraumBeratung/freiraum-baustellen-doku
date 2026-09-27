"""Smoke: getippte Feldnotizen (Uli-Stil) — Sprache und Stichpunkte unberührt."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

os.environ["OPENAI_API_KEY"] = ""
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

from smoke_isolation import isolate_smoke_data

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_typed_notes_")))

from app.services.note_translator import expand_notes_if_guarded, looks_like_notes  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from app.services.typed_field_notes import looks_like_typed_field_note, rescue_typed_field_notes  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402

_STORE = TenantStore(str(uuid.uuid4()))

ULI_CASES: list[tuple[str, tuple[str, ...]]] = [
    (
        "Zusatzaufwand zum LVV: Fahrt zum Lager / Baustelle. Lieferu 2 Bögen Fabekun HSS DN315",
        ("fahrt", "fabekun", "bögen", "bogen", "lager"),
    ),
    (
        "Zusatzaufwand zum LV: Stahlplatten zur Überfahrt des offenen Rohrgraben zur Baustelle transportiert und ausgelegt.",
        ("stahlplatten", "überfahrt", "ueberfahrt", "ausgelegt", "transportiert"),
    ),
    (
        "Schmutzwasserschacht per Handschachtung freigelegt",
        ("schmutzwasser", "handschacht", "freigelegt"),
    ),
    (
        "Oberboden angedeckt und eingesät.",
        ("oberboden", "angedeckt", "eingesät", "eingesaet"),
    ),
]

EXTRA_CASES: list[tuple[str, tuple[str, ...]]] = [
    ("Bordstein auf 12 m gesetzt", ("bordstein", "gesetzt")),
    ("Kanaldeckel angehoben und gereinigt", ("kanaldeckel", "angehoben", "gereinigt")),
    ("Rohrgraben offen gehalten, Absperrung gestellt", ("rohrgraben", "absperrung", "gestellt")),
    ("Sandfang geleert", ("sandfang", "geleert")),
    ("Hydrant freigelegt", ("hydrant", "freigelegt")),
    ("Straßenkappe gesucht und angefahren", ("straßenkappe", "strassenkappe", "gesucht", "angefahren")),
    ("Schieberkappe freigestemmt", ("schieberkappe", "freigestemmt")),
    ("Betonplatte geschnitten", ("betonplatte", "geschnitten")),
    ("Asphalt aufgeschnitten, 3 m", ("asphalt", "aufgeschnitten")),
    ("Kiestragschicht eingebaut", ("kiestragschicht", "eingebaut")),
    ("Vlies ausgelegt im Graben", ("vlies", "ausgelegt")),
    ("Drainagerohr verlegt DN100", ("drainage", "verlegt")),
    ("Kontrollschacht gesetzt", ("kontrollschacht", "gesetzt")),
    ("Hausanschluss vorbereitet", ("hausanschluss", "vorbereitet")),
    ("Trasse abgesteckt", ("trasse", "abgesteckt")),
    ("Schnurgerüst gestellt", ("schnurgerüst", "schnurgeruest", "gestellt")),
    ("Mutterboden seitlich gelagert", ("mutterboden", "gelagert")),
    ("Berme gezogen", ("berme", "gezogen")),
    ("Wasserhaltung aufgebaut", ("wasserhaltung", "aufgebaut")),
    ("Pumpe gesetzt und Schlauch verlegt", ("pumpe", "schlauch", "gesetzt", "verlegt")),
    ("Schalung für Fundamente gestellt", ("schalung", "gestellt")),
    ("Bewehrung eingebunden", ("bewehrung", "eingebunden")),
    ("Beton angeliefert und eingebracht", ("beton", "angeliefert", "eingebracht")),
    ("Rasenfläche gefräst", ("rasen", "gefräst", "gefraest")),
    ("Unebenheiten planiert", ("unebenheiten", "planiert")),
    ("Zaunfeld demontiert", ("zaunfeld", "demontiert")),
    ("Bauzaun umgesetzt", ("bauzaun", "umgesetzt")),
    ("Container Stellplatz vorbereitet", ("container", "stellplatz", "vorbereitet")),
    ("Aushub zur Deponie gefahren", ("aushub", "deponie", "gefahren")),
    ("Splittdeckung nachgezogen", ("splittdeckung", "nachgezogen")),
    ("Pflasterreihe nachgerichtet", ("pflaster", "nachgerichtet")),
    ("Fugen sand eingefegt", ("fugen", "eingefegt", "sand")),
    ("Laterne 4, Kabelzug gemacht", ("laterne", "kabelzug", "gemacht")),
    ("Zusatzaufwand: Wartezeit wegen Fremdfirma", ("wartezeit", "fremdfirma", "zusatzaufwand")),
    ("Zusatzaufwand zum LV: Material vom Hof geholt", ("material", "hof", "geholt")),
    ("Regenrinne gereinigt und gespült", ("regenrinne", "gereinigt", "gespült", "gespuelt")),
    ("Revisionsschacht geöffnet", ("revisionsschacht", "geöffnet", "geoeffnet")),
    ("Dichtungsmanschette gesetzt", ("dichtungsmanschette", "gesetzt")),
    ("Pressung vorbereitet", ("pressung", "vorbereitet")),
    ("Schutzrohr eingezogen", ("schutzrohr", "eingezogen")),
    ("Fläche abgesperrt und beschildert", ("fläche", "flaeche", "abgesperrt", "beschildert")),
    ("Schachtabdeckung getauscht", ("schachtabdeckung", "getauscht")),
    ("Bankett abgeschoben", ("bankett", "abgeschoben")),
    ("Leitungsauskunft eingeholt", ("leitungsauskunft", "eingeholt")),
    ("Sohle im Graben nachprofiliert", ("sohle", "nachprofiliert", "graben")),
]

SPEECH = "Heute haben wir fünfzig Quadratmeter Pflaster verlegt und danach die Hecke geschnitten."
NOTE_LIST = "2qm Pflaster\n1 Std. Handschachtung\n5 Meter Kabel"


def _structure(raw: str) -> dict:
    body = StructureReportBody(
        projectId="p-typed",
        projectName="Kundenbaustelle",
        customerName="Testkunde",
        date="2026-09-24",
        employeeNames=["Uli"],
        startTime="07:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    return api_structure_report(body, store=_STORE).get("structured") or {}


def _blob(structured: dict) -> str:
    acts = " ".join(str(x) for x in (structured.get("activities") or []))
    return f"{acts} {structured.get('summary') or ''}".casefold()


def _expect_work(raw: str, tokens: tuple[str, ...], failures: list[str], *, require_token: bool) -> None:
    s = _structure(raw)
    acts = [str(x).strip() for x in (s.get("activities") or []) if str(x).strip()]
    summary = str(s.get("summary") or "").strip()
    talk = str(s.get("customerTalk") or "").strip()
    if not acts:
        failures.append(f"keine Tätigkeit: {raw!r}")
        return
    if not summary or summary == "Keine Angabe":
        failures.append(f"Zusammenfassung leer: {raw!r} -> {summary!r}")
    if talk and talk != "Keine Angabe":
        failures.append(f"Kundengespräch erfunden: {raw!r} -> {talk!r}")
    if str(s.get("rawText") or "").strip() != raw.strip():
        failures.append(f"Rohtext verändert: {raw!r}")
    if require_token and not any(tok in _blob(s) for tok in tokens):
        failures.append(f"Token fehlt {tokens} in {raw!r} -> acts={acts} sum={summary!r}")


def main() -> int:
    failures: list[str] = []

    if looks_like_notes(SPEECH):
        failures.append("Sprache darf nicht wie Stichpunkte wirken")
    if expand_notes_if_guarded(SPEECH) != SPEECH:
        failures.append("Sprache darf vom Notiz-Übersetzer nicht verändert werden")
    if looks_like_typed_field_note(SPEECH):
        failures.append("Sprache darf nicht als getippte Feldnotiz gelten")
    if rescue_typed_field_notes(SPEECH, ["Pflaster verlegt"]):
        failures.append("Rettung darf bestehende Tätigkeiten nicht ersetzen")
    if looks_like_typed_field_note("Morgen Schacht freilegen"):
        failures.append("Zukunft darf nicht gerettet werden")
    if looks_like_typed_field_note("test"):
        failures.append("Rauschen darf nicht als Feldnotiz gelten")
    if rescue_typed_field_notes("", []):
        failures.append("Leerer Rohtext darf nichts liefern")

    for raw, tokens in ULI_CASES:
        _expect_work(raw, tokens, failures, require_token=True)
    for raw, tokens in EXTRA_CASES:
        _expect_work(raw, tokens, failures, require_token=False)

    speech = _structure(SPEECH)
    speech_acts = _blob(speech)
    if "pflaster" not in speech_acts or "hecke" not in speech_acts:
        failures.append(f"Sprache kaputt: {speech.get('activities')}")
    if str(speech.get("summary") or "") == "Keine Angabe":
        failures.append("Sprache: Zusammenfassung leer")

    notes = _structure(NOTE_LIST)
    notes_acts = _blob(notes)
    if "pflaster" not in notes_acts or "handschacht" not in notes_acts:
        failures.append(f"Stichpunkte kaputt: {notes.get('activities')}")

    future = _structure("Morgen machen wir den Schacht auf.")
    future_sum = str(future.get("summary") or "")
    future_acts = " ".join(str(x) for x in (future.get("activities") or [])).casefold()
    if "schacht" in future_acts and "morgen" in str(future.get("rawText") or "").casefold():
        if future_sum != "Keine Angabe" and future_acts:
            # Filter darf Zukunft leeren; Rettung darf sie nicht wiederbeleben.
            if looks_like_typed_field_note("Morgen machen wir den Schacht auf."):
                failures.append("Zukunft wurde als Feldnotiz gewertet")

    if failures:
        print("TYPED-FIELD-NOTES-SMOKE: FEHLER")
        for item in failures:
            print(" -", item)
        return 1
    print("TYPED-FIELD-NOTES-SMOKE: OK")
    print(f"Fälle: {len(ULI_CASES)} Uli + {len(EXTRA_CASES)} Extra")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
