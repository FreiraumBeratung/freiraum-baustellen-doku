"""Screenshot 4 Gartenboys: Garagenwand, Jacuzzi-Schnitt, Dichtschlämme, Dämmplatte.

Rohtext 1:1 aus dem Screenshot. Isoliertes Temp-Verzeichnis. OPENAI aus.
Getippte Bagger-/Radladerstunden bleiben unangetastet — die Engine erfindet sie
nicht aus diesem Rohtext, darf gesprochene Stunden aber nicht verbieten.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_gb_ss4_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402

_STORE = TenantStore(str(uuid.uuid4()))

RAW = (
    "heute haben wir die Garage Wand von ca 7 laufende Meter freigelegt auf ca 50 cm Tiefe "
    "zudem haben wir die Jacuzzi Stellfläche eingeschnitten schnittwaren ca 9,50 m "
    "zudem haben wir die Ecke an der Hauswand mit Dichtschlämme behandelt und mit mit Dämmplatte verkleidet"
)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _run(raw: str) -> dict:
    body = StructureReportBody(
        projectId="gb-ss4",
        projectName="Handwerkstraße",
        customerName="Kunde",
        date="2026-09-17",
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
    summary = str(structured.get("summary") or "")
    hours = [str(x) for x in (structured.get("machineHours") or [])]
    probs = [str(x) for x in (structured.get("problems") or [])]
    opens = [str(x) for x in (structured.get("openItems") or [])]
    talk = str(structured.get("customerTalk") or "")
    act_h = _hay(acts)
    mat_h = _hay(mats)
    sum_h = summary.casefold()

    _expect("garagenwand" in act_h or "garage" in act_h, f"Tätigkeit Garagenwand fehlt ({acts!r})")
    _expect("freigelegt" in act_h, f"freigelegt fehlt ({acts!r})")
    _expect("7" in act_h, f"7 lfm fehlt ({acts!r})")
    _expect("50" in act_h, f"50 cm Tiefe fehlt ({acts!r})")
    _expect("jacuzzi" in act_h or "stellfläche" in act_h or "stellflaeche" in act_h, f"Jacuzzi-Stellfläche fehlt ({acts!r})")
    _expect("eingeschnitten" in act_h, f"eingeschnitten fehlt ({acts!r})")
    _expect("9,50" in act_h or "9.50" in act_h, f"Schnittware 9,50 m fehlt ({acts!r})")
    _expect("dichtschl" in act_h, f"Dichtschlämme-Tätigkeit fehlt ({acts!r})")
    _expect("behandelt" in act_h, f"Dichtschlämme behandelt fehlt ({acts!r})")
    _expect("dämmplatte" in act_h or "daemmplatte" in act_h, f"Dämmplatte-Tätigkeit fehlt ({acts!r})")
    _expect("verkleidet" in act_h, f"verkleidet fehlt ({acts!r})")
    _expect("gestellt" not in act_h, f"Dämmplatte nicht auf gestellt mappen ({acts!r})")
    _expect("platten eingeschnitten" not in act_h, f"Jacuzzi-Schnitt nicht zu Platten ({acts!r})")
    _expect("bagger" not in act_h, f"kein Bagger aus Rohtext ({acts!r})")
    _expect("radlader" not in act_h, f"kein Radlader aus Rohtext ({acts!r})")

    _expect("dichtschl" in mat_h, f"Material Dichtschlämme fehlt ({mats!r})")
    _expect("dämmplatte" in mat_h or "daemmplatte" in mat_h, f"Material Dämmplatten fehlt ({mats!r})")
    _expect(
        not any("9,50" in m or "9.50" in m for m in mats),
        f"9,50 m ist Schnittware, kein Material ({mats!r})",
    )
    _expect(
        not any("7" in m and "dicht" in m.casefold() for m in mats),
        f"7 lfm nicht an Dichtschlämme hängen ({mats!r})",
    )
    _expect("schotter" not in mat_h, f"kein erfundener Schotter ({mats!r})")
    _expect("beton" not in mat_h, f"kein erfundener Beton ({mats!r})")

    _expect(not hours, f"keine erfundenen Maschinenstunden ({hours!r})")
    _expect(not probs, f"keine erfundenen Probleme ({probs!r})")
    _expect(
        not opens or all(x.strip().casefold() in {"", "keine angabe"} for x in opens),
        f"keine offenen Punkte ({opens!r})",
    )
    _expect(talk.strip().casefold() in {"", "keine angabe"}, f"kein Kundengespräch erfinden ({talk!r})")

    _expect(len(summary.strip()) >= 20, f"Zusammenfassung zu kurz ({summary!r})")
    _expect("17.09" in summary or "17. september" in sum_h, f"Datum fehlt ({summary!r})")
    _expect("freigelegt" in sum_h, f"Zusammenfassung ohne Freilegen ({summary!r})")
    _expect("jacuzzi" in sum_h or "eingeschnitten" in sum_h, f"Zusammenfassung ohne Jacuzzi-Schnitt ({summary!r})")
    _expect("dichtschl" in sum_h or "dämm" in sum_h or "daemm" in sum_h, f"Zusammenfassung ohne Abdichtung ({summary!r})")
    _expect("bagger" not in sum_h and "radlader" not in sum_h, f"keine Maschinen in der Zusammenfassung ({summary!r})")

    wall = _run("Heute die Hauswand freigelegt.")
    wall_h = _hay([str(x) for x in (wall.get("activities") or [])])
    _expect("hauswand" in wall_h and "freigelegt" in wall_h, f"Hauswand-Regression ({wall.get('activities')!r})")

    bagger = _run("Heute 2 Stunden Bagger und 1 Stunde Radlader.")
    bag_hours = [str(x) for x in (bagger.get("machineHours") or [])]
    bag_h = _hay(bag_hours)
    _expect(
        any("2" in h for h in bag_hours) and ("bagger" in bag_h),
        f"gesprochene Baggerstunden müssen bleiben ({bag_hours!r})",
    )

    print("GARTENBOYS-SCREENSHOT4-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
