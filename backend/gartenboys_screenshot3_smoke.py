"""Screenshot 3 Gartenboys: Jacuzzi-Stellfläche, Splitt 2/5, Drittelverband, Frau Nockemann.

Rohtext 1:1 aus dem Screenshot. Isoliertes Temp-Verzeichnis. OPENAI aus.
Getippte Maschinenstunden/Tätigkeiten bleiben unangetastet — die Engine erfindet sie
aus „abgerüttelt“ nicht, darf sie aber auch nicht verbieten.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ["OPENAI_API_KEY"] = ""
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_gb_ss3_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402

_STORE = TenantStore(str(uuid.uuid4()))

RAW = (
    "heute war ich ganz alleine auf der Baustelle. Kamil Urlaub weil er Geburtstag hat. "
    "dominik ist mal wieder krank. ich habe heute die Jacuzzi Stellfläche abgerüttelt, "
    "nach dem Abrütteln habe ich noch einige Stellen nachgeschottert und nochmals verdichtet. "
    "danach habe ich 2,5 Körnung Splitt eingebaut den Split abgezogen danach habe ich die "
    "Pflasterfläche zugelegt komplett und alleine halbverband wurde ein drittelverband da sonst "
    "der Zuschnitt an einer Seite 3 cm verlaufen wäre dies ist mit Frau nockemann besprochen worden"
)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _run(raw: str) -> dict:
    body = StructureReportBody(
        projectId="gb-ss3",
        projectName="Handwerkstraße",
        customerName="Frau Nockemann",
        date="2026-09-16",
        employeeNames=["Max"],
        startTime="07:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    return api_structure_report(body, store=_STORE).get("structured") or {}


def _hay(items: list) -> str:
    return " | ".join(str(x).casefold() for x in items)


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
    talk_h = talk.casefold()
    prob_h = _hay(probs)

    _expect("abgerüttelt" in act_h or "abgeruettelt" in act_h, f"Tätigkeit abgerüttelt fehlt ({acts!r})")
    _expect("jacuzzi" in act_h or "stellfläche" in act_h or "stellflaeche" in act_h, f"Jacuzzi-Stellfläche fehlt ({acts!r})")
    _expect("nachgeschottert" in act_h, f"Tätigkeit nachgeschottert fehlt ({acts!r})")
    _expect("splitt" in act_h, f"Tätigkeit Splitt fehlt ({acts!r})")
    _expect("2/5" in act_h or "2 / 5" in act_h, f"Splitt 2/5 fehlt in Tätigkeiten ({acts!r})")
    _expect("abgezogen" in act_h, f"Splitt abgezogen fehlt ({acts!r})")
    _expect("pflaster" in act_h, f"Tätigkeit Pflaster fehlt ({acts!r})")
    _expect("drittelverband" in act_h, f"Drittelverband fehlt ({acts!r})")
    _expect("zugelegt" in act_h or "verlegt" in act_h, f"Pflaster verlegt/zugelegt fehlt ({acts!r})")
    _expect("urlaub" not in act_h, f"Urlaub ist keine Tätigkeit ({acts!r})")
    _expect("geburtstag" not in act_h, f"Geburtstag ist keine Tätigkeit ({acts!r})")
    _expect("krank" not in act_h, f"Krankheit ist keine Tätigkeit ({acts!r})")
    _expect("schubkarre" not in act_h, f"keine erfundenen Schubkarren ({acts!r})")
    _expect("lieferschein" not in act_h, f"kein erfundener Lieferschein ({acts!r})")
    _expect("1 tonne" not in act_h and "1 t" not in act_h, f"keine erfundene 1 t ({acts!r})")

    _expect("schotter" in mat_h, f"Material Schotter fehlt ({mats!r})")
    _expect("splitt" in mat_h, f"Material Splitt fehlt ({mats!r})")
    _expect("2/5" in mat_h or "2 / 5" in mat_h, f"Material Splitt 2/5 fehlt ({mats!r})")
    _expect("pflaster" in mat_h, f"Material Pflaster fehlt ({mats!r})")
    _expect("0/45" not in mat_h and "0 45" not in mat_h, f"keine erfundene Schotter 0/45 ({mats!r})")
    _expect("schubkarre" not in mat_h, f"keine Schubkarren im Material ({mats!r})")
    _expect("1 t" not in mat_h and "1 tonne" not in mat_h, f"keine 1 t im Material ({mats!r})")

    _expect(not hours, f"keine erfundenen Rüttelstunden aus abgerüttelt ({hours!r})")
    _expect("rüttelplattenstunden" not in sug_h and "ruettelplattenstunden" not in sug_h, f"keine Stunden-Nachfrage nur wegen abgerüttelt ({suggs!r})")

    _expect(any("zuschnitt" in p.casefold() or "3" in p for p in probs), f"Problem Zuschnitt 3 cm fehlt ({probs!r})")
    _expect("4 cm" not in prob_h, f"keine erfundenen 4 cm ({probs!r})")
    _expect("nicht einverstanden" not in prob_h, f"kein erfundenes Nicht-Einverstanden ({probs!r})")
    _expect("1.3" not in prob_h and "1,3 verband" not in prob_h, f"kein 1,3 Verband ({probs!r})")

    _expect(
        not opens or all(x.strip().casefold() in {"", "keine angabe"} for x in opens),
        f"keine offenen Punkte erfinden ({opens!r})",
    )

    _expect("nockemann" in talk_h, f"Kundengespräch Frau Nockemann fehlt ({talk!r})")
    _expect("besprochen" in talk_h, f"Kundengespräch ohne besprochen ({talk!r})")
    _expect("drittelverband" in talk_h, f"Kundengespräch ohne Drittelverband ({talk!r})")
    _expect("keine angabe" not in talk_h, f"Kundengespräch darf nicht leer bleiben ({talk!r})")

    _expect(len(summary.strip()) >= 20, f"Zusammenfassung zu kurz ({summary!r})")
    _expect("16.09" in summary or "16. september" in sum_h, f"Datum fehlt in Zusammenfassung ({summary!r})")
    _expect("pflaster" in sum_h or "drittelverband" in sum_h, f"Zusammenfassung ohne Pflaster ({summary!r})")
    _expect("splitt" in sum_h or "schotter" in sum_h or "abgerüttelt" in sum_h or "jacuzzi" in sum_h, f"Zusammenfassung ohne Arbeit ({summary!r})")
    _expect(
        "allein" in sum_h or "allein" in act_h,
        f"allein fehlt in Zusammenfassung/Tätigkeiten ({summary!r} acts={acts!r})",
    )
    _expect("kamil" not in sum_h and "geburtstag" not in sum_h, f"kein Personal-Klatsch in der Zusammenfassung ({summary!r})")
    _expect("fortschritt der baumaßnahme" not in sum_h and "fortschritt der baumassnahme" not in sum_h, f"kein Füllsatz ({summary!r})")

    hours_ok = _run("Heute 1 Stunde Rüttelplatte auf der Fläche.")
    typed_hours = [str(x) for x in (hours_ok.get("machineHours") or [])]
    _expect(
        any("1" in h and "rüttel" in h.casefold() or "ruettel" in h.casefold() or "rüttelplatte" in h.casefold() for h in typed_hours)
        or any("1" in h for h in typed_hours),
        f"gesprochene Rüttelstunden müssen bleiben ({typed_hours!r})",
    )

    print("GARTENBOYS-SCREENSHOT3-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
