"""Screenshot 1 Gartenboys: Tiefbordsteine (Whisper 'tief vor Steine'), Schotter, Pflaster.

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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_gb_ss1_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402

_STORE = TenantStore(str(uuid.uuid4()))

RAW = (
    "Wir haben tief vor Steine gesetzt und wir haben Schotter verteilt "
    "zusätzlich haben wir noch eine kleine Pflasterfläche angelegt"
)
RAW_TONNEN = (
    "Wir haben tief vor Steine gesetzt und wir haben 5 Tonnen Schotter verteilt "
    "zusätzlich haben wir noch eine kleine Pflasterfläche angelegt"
)
RAW_VARIANTS = (
    RAW,
    "Wir haben Tiefvorstein gesetzt und Schotter verteilt zusätzlich haben wir noch eine kleine Pflasterfläche angelegt",
    "Wir haben tief vor Stein gesetzt und Schotter verteilt zusätzlich eine kleine Pflasterfläche erstellt",
)


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"FAIL: {msg}")


def _run(raw: str) -> dict:
    body = StructureReportBody(
        projectId="gb-ss1",
        projectName="Schmitz Außenanlage",
        customerName="Kunde Schmitz",
        date="2026-09-03",
        employeeNames=["Max"],
        startTime="07:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    return api_structure_report(body, store=_STORE).get("structured") or {}


def _hay(items: list) -> str:
    return " | ".join(str(x).casefold() for x in items)


def _check_core(raw: str, structured: dict, *, expect_tonnen: bool) -> None:
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

    _expect(
        "randstein" in act_h or "rasenkantenstein" in act_h,
        f"Tätigkeit Randsteine fehlt ({raw!r} got={acts!r})",
    )
    _expect("schotter" in act_h, f"Tätigkeit Schotter fehlt ({raw!r} got={acts!r})")
    _expect("pflaster" in act_h, f"Tätigkeit Pflaster fehlt ({raw!r} got={acts!r})")
    _expect("20" not in act_h, f"keine erfundenen 20 m ({acts!r})")

    _expect("schotter" in mat_h, f"Material Schotter fehlt ({mats!r})")
    _expect(
        "randstein" in mat_h or "rasenkantenstein" in mat_h,
        f"Material Randsteine fehlt ({mats!r})",
    )
    _expect("pflasterstein" in mat_h, f"Material Pflastersteine fehlt ({mats!r})")
    if expect_tonnen:
        _expect(
            any("5" in m and "t" in m.casefold() and "schotter" in m.casefold() for m in mats),
            f"Schotter 5 t fehlt ({mats!r})",
        )
    else:
        _expect("2 t" not in mat_h and "2t" not in mat_h.replace(" ", ""), f"keine erfundenen 2 t ({mats!r})")

    _expect("beton benutzt" in sug_h, f"Nachfrage Beton benutzt? fehlt ({suggs!r})")
    _expect(len(summary.strip()) >= 20, f"Zusammenfassung zu kurz ({summary!r})")
    _expect("schmitz" in sum_h or "baustelle" in sum_h, f"Zusammenfassung ohne Baustelle ({summary!r})")
    _expect("pflaster" in sum_h, f"Zusammenfassung ohne Pflaster ({summary!r})")
    _expect("schotter" in sum_h, f"Zusammenfassung ohne Schotter ({summary!r})")
    _expect(
        "randstein" in sum_h or "rasenkanten" in sum_h or "tiefbord" in sum_h,
        f"Zusammenfassung ohne Steine ({summary!r})",
    )
    _expect(not hours, f"keine erfundenen Maschinenstunden ({hours!r})")
    _expect(not probs, f"keine erfundenen Probleme ({probs!r})")


def main() -> int:
    for raw in RAW_VARIANTS:
        _check_core(raw, _run(raw), expect_tonnen=False)
    _check_core(RAW_TONNEN, _run(RAW_TONNEN), expect_tonnen=True)
    print("GARTENBOYS-SCREENSHOT1-SMOKE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
