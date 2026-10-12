"""Screenshot 5 Gartenboys: Edeka Rollerständer, Schilder, Fahrradständer.

Rohtext 1:1 aus dem Screenshot. Isoliertes Temp-Verzeichnis. OPENAI aus.
Getippte Maschinenstunden bleiben unangetastet — die Engine erfindet sie
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_gb_ss5_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402

_STORE = TenantStore(str(uuid.uuid4()))

RAW = (
    "Und zwar habe ich heute beim Edeka Essen Markt mit den vorhandenen Fundamenten "
    "von den Jungs habe ich die die den Rollerständer montiert aber musste vorher auch "
    "den Rollerständer zusammenbauen das wusste ich vorher nicht dann hab ich noch zwei "
    "Schilder angebracht hab dann noch vor dem Bäcker die Fahrradständer auch noch "
    "befestigt und genau das war alles"
)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _run(raw: str) -> dict:
    body = StructureReportBody(
        projectId="gb-ss5",
        projectName="Edeka Essen Markt",
        customerName="Edeka",
        date="2026-09-18",
        employeeNames=["Max"],
        startTime="08:00",
        endTime="12:15",
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
    prob_h = _hay(probs)

    _expect("rollerständer" in act_h or "rollerstaender" in act_h, f"Rollerständer fehlt ({acts!r})")
    _expect("zusammengebaut" in act_h, f"zusammengebaut fehlt ({acts!r})")
    _expect("montiert" in act_h, f"montiert fehlt ({acts!r})")
    _expect("fundament" in act_h, f"vorhandene Fundamente fehlen ({acts!r})")
    _expect("edeka" in act_h, f"Ort Edeka fehlt in der Tätigkeit ({acts!r})")
    _expect("schild" in act_h, f"Schilder fehlen ({acts!r})")
    _expect("angebracht" in act_h, f"angebracht fehlt ({acts!r})")
    _expect("2" in act_h or "zwei" in act_h, f"zwei Schilder fehlen ({acts!r})")
    _expect("fahrradständer" in act_h or "fahrradstaender" in act_h, f"Fahrradständer fehlt ({acts!r})")
    _expect("befestigt" in act_h, f"befestigt fehlt ({acts!r})")
    _expect("bäcker" in act_h or "baecker" in act_h, f"vor dem Bäcker fehlt ({acts!r})")
    _expect("jungs" not in act_h, f"'die Jungs' darf nicht in Tätigkeiten ({acts!r})")
    _expect("ständerwerk" not in act_h and "staenderwerk" not in act_h, f"kein Ständerwerk ({acts!r})")
    _expect("zaun gesetzt" not in act_h, f"Fahrradständer nicht zu Zaun ({acts!r})")
    _expect("fundament erstellt" not in act_h, f"keine Fundamente als heutige Leistung ({acts!r})")
    _expect("garagenwand" not in act_h, f"kein Altbestand Garagenwand ({acts!r})")

    _expect(
        not mats or all(str(m).strip().casefold() in {"", "keine angabe"} for m in mats),
        f"kein Material erfinden ({mats!r})",
    )
    _expect("fundament" not in mat_h, f"Fundamente sind kein Tagesmaterial ({mats!r})")
    _expect("beton" not in mat_h, f"kein erfundener Beton ({mats!r})")
    _expect("schotter" not in mat_h, f"kein erfundener Schotter ({mats!r})")

    _expect(not hours, f"keine erfundenen Maschinenstunden ({hours!r})")
    _expect("zusammengebaut" in prob_h or "vorher" in prob_h, f"Problem Zusammenbau fehlt ({probs!r})")
    _expect("jungs" not in prob_h, f"'die Jungs' nicht ins Problem ({probs!r})")
    _expect(
        not opens or all(x.strip().casefold() in {"", "keine angabe"} for x in opens),
        f"keine offenen Punkte ({opens!r})",
    )
    _expect(talk.strip().casefold() in {"", "keine angabe"}, f"kein Kundengespräch erfinden ({talk!r})")

    _expect(len(summary.strip()) >= 20, f"Zusammenfassung zu kurz ({summary!r})")
    _expect("18.09" in summary or "18. september" in sum_h, f"Datum fehlt ({summary!r})")
    _expect("rollerständer" in sum_h or "rollerstaender" in sum_h or "montiert" in sum_h, f"Zusammenfassung ohne Rollerständer ({summary!r})")
    _expect("jungs" not in sum_h, f"'die Jungs' nicht in der Zusammenfassung ({summary!r})")
    _expect("bagger" not in sum_h and "radlader" not in sum_h, f"keine Maschinen in der Zusammenfassung ({summary!r})")

    tb = _run("Heute Ständerwerk montiert.")
    tb_h = _hay([str(x) for x in (tb.get("activities") or [])])
    _expect("ständerwerk" in tb_h or "staenderwerk" in tb_h, f"Ständerwerk-Regression ({tb.get('activities')!r})")

    fund = _run("Heute das Fundament betoniert.")
    fund_h = _hay([str(x) for x in (fund.get("activities") or [])])
    _expect(
        "fundament" in fund_h and ("beton" in fund_h or "erstellt" in fund_h or "eingebracht" in fund_h),
        f"Fundament-Regression ({fund.get('activities')!r})",
    )

    zaun = _run("Heute den Zaun gesetzt.")
    zaun_h = _hay([str(x) for x in (zaun.get("activities") or [])])
    _expect("zaun" in zaun_h, f"Zaun-Regression ({zaun.get('activities')!r})")

    bagger = _run("Heute 2 Stunden Bagger und 1 Stunde Radlader.")
    bag_hours = [str(x) for x in (bagger.get("machineHours") or [])]
    bag_h = _hay(bag_hours)
    _expect(
        any("2" in h for h in bag_hours) and ("bagger" in bag_h),
        f"gesprochene Baggerstunden müssen bleiben ({bag_hours!r})",
    )

    print("GARTENBOYS-SCREENSHOT5-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
