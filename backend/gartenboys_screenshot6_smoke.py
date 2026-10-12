"""Screenshot 6 Gartenboys: Spritzschutz-Kantensteine, Podest, L-Steine.

Rohtext 1:1 aus dem Screenshot. Isoliertes Temp-Verzeichnis. OPENAI aus.
Getippter Beton 0,5 m³ bleibt Overlay — die Engine erfindet ihn nicht,
bietet Beton aber als Vorschlag an. Tiefbord→Randsteine und lfm bleiben.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_gb_ss6_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402

_STORE = TenantStore(str(uuid.uuid4()))

RAW = (
    "Heute Spritschutz kannte Steine gesetzt, sowie Podest für Wassertonne. "
    "Zudem 3 l steine gesetzt."
)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _run(raw: str) -> dict:
    body = StructureReportBody(
        projectId="gb-ss6",
        projectName="Garten",
        customerName="Kunde",
        date="2026-09-19",
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

    _expect("spritzschutz" in act_h, f"Spritzschutz-Kantensteine fehlen ({acts!r})")
    _expect("kantenstein" in act_h, f"Kantensteine fehlen ({acts!r})")
    _expect("gesetzt" in act_h, f"gesetzt fehlt ({acts!r})")
    _expect("podest" in act_h, f"Podest fehlt ({acts!r})")
    _expect("wassertonne" in act_h, f"Wassertonne fehlt ({acts!r})")
    _expect("l-stein" in act_h or "l stein" in act_h, f"L-Steine fehlen ({acts!r})")
    _expect("3" in act_h, f"3 L-Steine Menge fehlt ({acts!r})")
    _expect("lfm" not in act_h, f"3 l nicht als lfm lesen ({acts!r})")
    _expect("randstein" not in act_h, f"Spritzschutz nicht zu Randsteinen ({acts!r})")
    _expect("tiefbord" not in act_h, f"kein Tiefbord aus diesem Rohtext ({acts!r})")
    _expect("kannte" not in act_h, f"Whisper 'kannte' darf nicht stehen bleiben ({acts!r})")
    _expect("spritschutz" not in act_h, f"Whisper Spritschutz muss repariert sein ({acts!r})")

    _expect("kantenstein" in mat_h, f"Material Kantensteine fehlt ({mats!r})")
    _expect("l-stein" in mat_h or "l stein" in mat_h, f"Material L-Steine fehlt ({mats!r})")
    _expect("beton" not in mat_h, f"Beton nicht automatisch ins Material ({mats!r})")
    _expect(
        not any("0,5" in m or "0.5" in m for m in mats),
        f"keine erfundenen 0,5 m³ ({mats!r})",
    )
    _expect("rasenkantenstein" not in mat_h, f"nicht zu Rasenkantensteinen kippen ({mats!r})")

    _expect("beton" in sug_h, f"Vorschlag Beton fehlt ({suggs!r})")
    _expect(
        not any("0,5" in s or "0.5" in s for s in suggs),
        f"Vorschlag Beton ohne Menge ({suggs!r})",
    )

    _expect(not hours, f"keine erfundenen Maschinenstunden ({hours!r})")
    _expect(not probs, f"keine erfundenen Probleme ({probs!r})")
    _expect(
        not opens or all(x.strip().casefold() in {"", "keine angabe"} for x in opens),
        f"keine offenen Punkte ({opens!r})",
    )
    _expect(talk.strip().casefold() in {"", "keine angabe"}, f"kein Kundengespräch erfinden ({talk!r})")

    _expect(len(summary.strip()) >= 20, f"Zusammenfassung zu kurz ({summary!r})")
    _expect("19.09" in summary or "19. september" in sum_h, f"Datum fehlt ({summary!r})")
    _expect("spritzschutz" in sum_h or "kantenstein" in sum_h, f"Zusammenfassung ohne Kantensteine ({summary!r})")
    _expect("podest" in sum_h or "wassertonne" in sum_h, f"Zusammenfassung ohne Podest ({summary!r})")
    _expect("l-stein" in sum_h or "l stein" in sum_h, f"Zusammenfassung ohne L-Steine ({summary!r})")
    _expect("zudem" not in sum_h, f"kein Rohtext-Dump in der Zusammenfassung ({summary!r})")

    tief = _run("Wir haben tief vor Steine gesetzt.")
    tief_h = _hay([str(x) for x in (tief.get("activities") or [])])
    _expect(
        "randstein" in tief_h or "rasenkantenstein" in tief_h,
        f"Tiefbord-Regression ({tief.get('activities')!r})",
    )
    _expect("l-stein" not in tief_h, f"Tiefbord nicht zu L-Steinen ({tief.get('activities')!r})")

    lfm = _run("Heute 3 lfm Randsteine gesetzt.")
    lfm_h = _hay([str(x) for x in (lfm.get("activities") or [])])
    _expect("lfm" in lfm_h and "randstein" in lfm_h, f"lfm-Regression ({lfm.get('activities')!r})")
    _expect("l-stein" not in lfm_h, f"3 lfm nicht zu L-Steinen ({lfm.get('activities')!r})")

    spoken = _run("Heute Randsteine gesetzt und 0,5 m³ Beton verarbeitet.")
    spoken_mat = _hay([str(x) for x in (spoken.get("materials") or [])])
    _expect("beton" in spoken_mat, f"gesprochener Beton muss Material bleiben ({spoken.get('materials')!r})")

    for variant in (
        "Heute 3 l stein gesetzt.",
        "Heute 3 lstein gesetzt.",
        "Heute 3 lsteine gesetzt.",
        "Heute 3 l-steine gesetzt.",
    ):
        vs = _run(variant)
        v_act = _hay([str(x) for x in (vs.get("activities") or [])])
        v_mat = _hay([str(x) for x in (vs.get("materials") or [])])
        v_sum = str(vs.get("summary") or "").casefold()
        _expect(
            "l-stein" in v_act or "l stein" in v_act or "lstein" in v_act,
            f"Whisper-Variante Tätigkeit fehlt ({variant!r} → {vs.get('activities')!r})",
        )
        _expect(
            "l-stein" in v_mat or "l stein" in v_mat or "lstein" in v_mat,
            f"Whisper-Variante Material fehlt ({variant!r} → {vs.get('materials')!r})",
        )
        _expect(
            "l-stein" in v_sum or "l stein" in v_sum or "lstein" in v_sum,
            f"Whisper-Variante Zusammenfassung fehlt ({variant!r} → {vs.get('summary')!r})",
        )
        _expect("lfm" not in v_act, f"Variante nicht als lfm ({variant!r} → {vs.get('activities')!r})")

    print("GARTENBOYS-SCREENSHOT6-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
