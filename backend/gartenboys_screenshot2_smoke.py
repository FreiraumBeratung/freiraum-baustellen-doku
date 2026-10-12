"""Screenshot 2 Gartenboys: Balkonplatten, Maschinen freigestellt, Gerüstabbau.

Isoliertes Temp-Verzeichnis. OPENAI aus. Bestehende Smokes bleiben unangetastet.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "")
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_gb_ss2_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402

_STORE = TenantStore(str(uuid.uuid4()))

RAW = (
    "heute haben wir den ersten Balkon im ersten Stockwerk linke Seite fertiggestellt "
    "dafür haben wir Platten neu verlegt und zudem 22 Platten ca neu eingeschnitten "
    "den Bagger und Radlader haben wir für heute freigestellt "
    "die Reifen vom Radlader hinten rechts wurde aufgepumpt "
    "zudem haben die Gerüstbauer gegen 12 Uhr angefangen das Gerüst abzubauen"
)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _run(raw: str) -> dict:
    body = StructureReportBody(
        projectId="gb-ss2",
        projectName="Kempel Balkon",
        customerName="Kunde Kempel",
        date="2026-10-10",
        employeeNames=["Robin"],
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
    act_h = _hay(acts)
    mat_h = _hay(mats)
    sug_h = _hay(suggs)
    sum_h = summary.casefold()

    _expect("platten verlegt" in act_h, f"Tätigkeit Platten verlegt fehlt ({acts!r})")
    _expect("fliesen verlegt" not in act_h, f"Platten dürfen nicht zu Fliesen werden ({acts!r})")
    _expect("eingeschnitten" in act_h, f"Tätigkeit Platten eingeschnitten fehlt ({acts!r})")
    _expect("22" in act_h, f"Anzahl 22 Platten fehlt ({acts!r})")
    _expect("balkon" in act_h and "fertiggestellt" in act_h, f"Tätigkeit Balkon fertiggestellt fehlt ({acts!r})")
    _expect("1. og" in act_h or "1.og" in act_h.replace(" ", ""), f"Lage 1. OG fehlt ({acts!r})")
    _expect("links" in act_h, f"Lage links fehlt ({acts!r})")
    _expect("freigestellt" in act_h, f"Tätigkeit Maschinen freigestellt fehlt ({acts!r})")
    _expect("bagger" in act_h and "radlader" in act_h, f"Bagger und Radlader fehlen ({acts!r})")
    _expect("baggerarbeiten" not in act_h, f"keine erfundenen Baggerarbeiten ({acts!r})")
    _expect("radlader eingesetzt" not in act_h, f"kein Radlader eingesetzt aus Freistellung ({acts!r})")
    _expect("radlader verlegt" not in act_h, f"kein Radlader verlegt ({acts!r})")
    _expect("reifen" in act_h and "aufgepumpt" in act_h, f"Tätigkeit Reifen aufgepumpt fehlt ({acts!r})")
    _expect("gerüstabbau" in act_h or "geruestabbau" in act_h, f"Tätigkeit Gerüstabbau fehlt ({acts!r})")
    _expect("12" in act_h, f"Uhrzeit 12 Uhr beim Gerüstabbau fehlt ({acts!r})")

    _expect("platten" in mat_h, f"Material Platten fehlt ({mats!r})")
    _expect("fliesen" not in mat_h, f"kein erfundenes Material Fliesen ({mats!r})")
    _expect("fugenmörtel" not in mat_h and "fugenmoertel" not in mat_h, f"kein Fugenmörtel ({mats!r})")
    _expect("fliesenkleber" not in mat_h, f"kein Fliesenkleber ({mats!r})")
    _expect("perlies" not in mat_h, f"kein erfundenes Perlies ({mats!r})")
    _expect("fugenmaterial" not in mat_h, f"kein erfundenes Fugenmaterial ({mats!r})")

    _expect("fugenmörtel benutzt" not in sug_h, f"keine Fugenmörtel-Nachfrage ({suggs!r})")
    _expect("baggerstunden" not in sug_h, f"keine Baggerstunden-Nachfrage bei Freistellung ({suggs!r})")
    _expect("radladerstunden" not in sug_h, f"keine Radladerstunden-Nachfrage bei Freistellung ({suggs!r})")

    _expect(len(summary.strip()) >= 20, f"Zusammenfassung zu kurz ({summary!r})")
    _expect("platten" in sum_h, f"Zusammenfassung ohne Platten ({summary!r})")
    _expect("fliesen" not in sum_h, f"Zusammenfassung darf keine Fliesen erfinden ({summary!r})")
    _expect(
        "balkon" in sum_h or "eingeschnitten" in sum_h or "freigestellt" in sum_h or "gerüst" in sum_h,
        f"Zusammenfassung ohne Kerninhalt ({summary!r})",
    )
    _expect(not hours, f"keine erfundenen Maschinenstunden ({hours!r})")
    _expect(not probs, f"Gerüstabbau ist kein Problem ({probs!r})")

    tiles = _run("Heute im Bad 18 Quadratmeter Fliesen verlegt.")
    tile_h = _hay([str(x) for x in (tiles.get("activities") or [])])
    _expect("fliesen verlegt" in tile_h, f"Fliesen-Regression ({tiles.get('activities')!r})")
    _expect("platten verlegt" not in tile_h, f"Fliesen dürfen nicht zu Platten werden ({tiles.get('activities')!r})")

    terrace = _run("Heute 35 Quadratmeter Terrassenplatten verlegt.")
    ter_h = _hay([str(x) for x in (terrace.get("activities") or [])])
    _expect("terrassenplatten" in ter_h, f"Terrassenplatten-Regression ({terrace.get('activities')!r})")
    _expect("fliesen verlegt" not in ter_h, f"Terrassenplatten nicht zu Fliesen ({terrace.get('activities')!r})")

    bagger = _run("Heute 3 Stunden mit dem Bagger Aushub gemacht.")
    bag_h = _hay([str(x) for x in (bagger.get("activities") or [])])
    bag_hours = [str(x) for x in (bagger.get("machineHours") or [])]
    _expect(
        "bagger" in bag_h or bag_hours,
        f"echte Baggerarbeit/Stunden dürfen bleiben ({bagger.get('activities')!r} hours={bag_hours!r})",
    )
    _expect(any("3" in h for h in bag_hours) or "3" in bag_h, f"3 Stunden Bagger fehlen ({bag_hours!r} {bagger.get('activities')!r})")

    print("GARTENBOYS-SCREENSHOT2-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
