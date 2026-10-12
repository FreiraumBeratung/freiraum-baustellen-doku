"""Screenshot 7 Gartenboys: Pflaster-Sanierung Hüttner, Holzleisten, Ilex, Entsorgung.

Rohtext 1:1 aus dem Screenshot. Isoliertes Temp-Verzeichnis. OPENAI aus.
Getippte Materialien (Schotter 1 Schubkarre, Splitt 1,5 Schubkarren, Pflaster,
Pflastersteine) bleiben Overlay — die Engine erfindet die 1,5 nicht.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import uuid
from pathlib import Path

os.environ["OPENAI_API_KEY"] = ""
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_gb_ss7_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402

_STORE = TenantStore(str(uuid.uuid4()))

RAW = (
    "Pflasterfläche aufgenommen im abgesackten Bereich "
    "Pflaster gestapelt seitlich. Schotter ca eine Schubkarre eingearbeitet verdichtet "
    "mittels Handstampfer der Bruchgefahr der großen scheibenfrontbestand Splitt aufgetragen "
    "ca eine Schubkarre voll diesen höhengerecht abgezogen darauf dass vorhandene Pflaster "
    "nach Muster neu verlegt auf Höhe mittels Kantholz und Gummihammer zurecht geschlagen "
    "auf Höhe einkehrmaterial eingearbeitet ein Sack alte Holzleisten von der Gartenhütte "
    "demontiert neue Holzleisten zurechtgeschnitten und montiert alten Ilex Stamm mit der "
    "Kettensäge bodennah abgeschnitten Stamm entsorgt Bauschutt aus dem Garten entsorgt "
    "ca eine Schubkarre voll drei plastikstegplatten mit entsorgt"
)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _run(raw: str) -> dict:
    body = StructureReportBody(
        projectId="gb-ss7",
        projectName="Hüttner",
        customerName="Kunde",
        date="2026-09-29",
        employeeNames=["Max"],
        startTime="08:00",
        endTime="16:30",
        exportFormat="PDF",
        rawText=raw,
    )
    return api_structure_report(body, store=_STORE).get("structured") or {}


def _hay(items: list) -> str:
    return " | ".join(str(x).casefold() for x in items)


def _no_hut_demolished(acts: list[str]) -> bool:
    for act in acts:
        low = str(act).casefold()
        if "gartenhütte" in low or "gartenhuette" in low:
            if "holzleiste" not in low:
                return False
    return True


def main() -> int:
    structured = _run(RAW)
    acts = [str(x) for x in (structured.get("activities") or [])]
    mats = [str(x) for x in (structured.get("materials") or [])]
    suggs = [str(x) for x in (structured.get("materialSuggestions") or [])]
    summary = str(structured.get("summary") or "")
    hours = [str(x) for x in (structured.get("machineHours") or [])]
    probs = [str(x) for x in (structured.get("problems") or [])]
    opens = [str(x) for x in (structured.get("openItems") or [])]
    talk = str(structured.get("customerTalk") or "")
    act_h = _hay(acts)
    mat_h = _hay(mats)
    sug_h = _hay(suggs)
    sum_h = summary.casefold()

    _expect("aufgenommen" in act_h, f"Pflasterfläche aufgenommen fehlt ({acts!r})")
    _expect("abgesackt" in act_h, f"abgesackter Bereich fehlt ({acts!r})")
    _expect("gestapelt" in act_h, f"Pflaster gestapelt fehlt ({acts!r})")
    _expect("schotter" in act_h, f"Schotter fehlt ({acts!r})")
    _expect("handstampfer" in act_h or "verdichtet" in act_h, f"Verdichten/Handstampfer fehlt ({acts!r})")
    _expect("splitt" in act_h, f"Splitt fehlt ({acts!r})")
    _expect("abgezogen" in act_h or "höhengerecht" in act_h or "hoehengerecht" in act_h, f"Splitt abgezogen fehlt ({acts!r})")
    _expect("nach muster" in act_h, f"Pflaster nach Muster fehlt ({acts!r})")
    _expect("kantholz" in act_h or "gummihammer" in act_h, f"Kantholz/Gummihammer fehlt ({acts!r})")
    _expect("einkehrmaterial" in act_h, f"Einkehrmaterial fehlt ({acts!r})")
    _expect("holzleiste" in act_h, f"Holzleisten fehlen ({acts!r})")
    _expect("demontiert" in act_h, f"Holzleisten demontiert fehlt ({acts!r})")
    _expect("zurechtgeschnitten" in act_h or "montiert" in act_h, f"neue Holzleisten fehlen ({acts!r})")
    _expect(_no_hut_demolished(acts), f"Gartenhütte darf nicht als Ganzes demontiert sein ({acts!r})")
    _expect("ilex" in act_h, f"Ilex-Stamm fehlt ({acts!r})")
    _expect("kettensäge" in act_h or "kettensaege" in act_h, f"Kettensäge fehlt ({acts!r})")
    _expect("bauschutt" in act_h, f"Bauschutt fehlt ({acts!r})")
    _expect("stegplatten" in act_h, f"Plastikstegplatten fehlen ({acts!r})")
    _expect("scheibenfront" not in act_h, f"Whisper-Matsch darf nicht zur Tätigkeit werden ({acts!r})")
    _expect("bruchgefahr" not in act_h, f"kein erfundenes Bruchgefahr-Problem als Tätigkeit ({acts!r})")

    _expect("schotter" in mat_h, f"Material Schotter fehlt ({mats!r})")
    _expect("splitt" in mat_h, f"Material Splitt fehlt ({mats!r})")
    _expect(not any("1,5" in m or "1.5" in m for m in mats), f"keine erfundenen 1,5 Schubkarren ({mats!r})")
    _expect("beton" not in mat_h, f"kein erfundener Beton ({mats!r})")

    _expect("fugensand" not in sug_h, f"kein Fugensand-Vorschlag wenn Einkehrmaterial gesprochen ({suggs!r})")

    _expect(not hours, f"keine erfundenen Maschinenstunden ({hours!r})")
    _expect(not probs, f"keine erfundenen Probleme aus Whisper-Matsch ({probs!r})")
    _expect(
        not opens or all(x.strip().casefold() in {"", "keine angabe"} for x in opens),
        f"keine offenen Punkte ({opens!r})",
    )
    _expect(talk.strip().casefold() in {"", "keine angabe"}, f"kein Kundengespräch erfinden ({talk!r})")

    _expect(len(summary.strip()) >= 40, f"Zusammenfassung zu kurz ({summary!r})")
    _expect("29.09" in summary or "29. september" in sum_h, f"Datum fehlt ({summary!r})")
    _expect("aufgenommen" in sum_h, f"Zusammenfassung ohne Aufnehmen ({summary!r})")
    _expect("gestapelt" in sum_h, f"Zusammenfassung ohne Stapeln ({summary!r})")
    _expect("holzleiste" in sum_h, f"Zusammenfassung ohne Holzleisten ({summary!r})")
    _expect("zurechtgeschnitten" in sum_h or "neue holzleisten" in sum_h, f"Zusammenfassung ohne neue Holzleisten ({summary!r})")
    _expect("ilex" in sum_h, f"Zusammenfassung ohne Ilex ({summary!r})")
    _expect("bauschutt" in sum_h or "stegplatten" in sum_h, f"Zusammenfassung ohne Entsorgung ({summary!r})")
    hut_wrong = bool(re.search(r"gartenh(?:ü|ue)tte demontiert", sum_h)) and "holzleiste" not in sum_h
    _expect(not hut_wrong, f"Zusammenfassung darf die Hütte nicht abreißen ({summary!r})")

    hut = _run("Alte Holzleisten von der Gartenhütte demontiert.")
    hut_h = _hay([str(x) for x in (hut.get("activities") or [])])
    _expect("holzleiste" in hut_h, f"Holzleisten-Variante fehlt ({hut.get('activities')!r})")
    _expect(_no_hut_demolished([str(x) for x in (hut.get("activities") or [])]), f"Hütte nicht als Ganzes ({hut.get('activities')!r})")

    ilex = _run("Alten Ilex Stamm mit der Kettensäge bodennah abgeschnitten und entsorgt.")
    ilex_h = _hay([str(x) for x in (ilex.get("activities") or [])])
    _expect("ilex" in ilex_h, f"Ilex-Variante fehlt ({ilex.get('activities')!r})")

    steg = _run("Bauschutt entsorgt und drei plastikstegplatten mit entsorgt.")
    steg_h = _hay([str(x) for x in (steg.get("activities") or [])])
    _expect("bauschutt" in steg_h, f"Bauschutt-Variante fehlt ({steg.get('activities')!r})")
    _expect("stegplatten" in steg_h, f"Stegplatten-Variante fehlt ({steg.get('activities')!r})")

    angelegt = _run("Wir haben eine kleine Pflasterfläche angelegt.")
    angelegt_h = _hay([str(x) for x in (angelegt.get("activities") or [])])
    _expect("aufgenommen" not in angelegt_h, f"angelegt nicht als aufgenommen ({angelegt.get('activities')!r})")

    tief = _run("Wir haben tief vor Steine gesetzt.")
    tief_h = _hay([str(x) for x in (tief.get("activities") or [])])
    _expect(
        "randstein" in tief_h or "rasenkantenstein" in tief_h,
        f"Tiefbord-Regression ({tief.get('activities')!r})",
    )

    lstein = _run("Heute 3 l steine gesetzt.")
    l_h = _hay([str(x) for x in (lstein.get("activities") or [])])
    _expect("l-stein" in l_h or "l stein" in l_h, f"L-Steine-Regression ({lstein.get('activities')!r})")

    print("GARTENBOYS-SCREENSHOT7-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
