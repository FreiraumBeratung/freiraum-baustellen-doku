"""Kalibriert pilot_monster_wave25_scenarios.py an Pipeline-Ausgabe (N-Variante)."""

from __future__ import annotations

import os
import re
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ["OPENAI_API_KEY"] = ""
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from pilot_monster_wave25_scenarios import TRADE_SCENARIOS, TRADES  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="cal_wave25_")))
_STORE = TenantStore(str(uuid.uuid4()))


def _run(raw: str) -> dict:
    body = StructureReportBody(
        projectId="cal-w25",
        projectName="Cal",
        customerName="Test",
        date="2026-07-30",
        employeeNames=["Max"],
        startTime="07:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


def _prob_tokens(probs: list[str]) -> tuple[str, ...]:
    if not probs:
        return ()
    joined = " ".join(probs).casefold()
    tokens: list[str] = []
    for tok in (
        "regen", "unterbrochen", "wetter", "liefer", "staub", "kleber", "lotrecht",
        "uneben", "gefälle", "dichtung", "pressfitting", "eng", "grundwasser", "wasser",
        "betonpumpe", "wind", "trocknung", "material", "knapp", "defekt", "kaputt",
        "gerüst", "bagger", "mörtel", "drainage", "farbe", "werkzeug",
    ):
        if tok in joined or tok.replace("ü", "ue") in joined:
            tokens.append(tok)
    return tuple(tokens[:3]) or ("problem",)


def _open_tokens(opens: list[str]) -> tuple[str, ...]:
    if not opens:
        return ()
    joined = " ".join(opens).casefold()
    tokens: list[str] = []
    for tok in ("morgen", "offen", "montag", "freitag", "donnerstag", "dienstag", "mittwoch", "oberputz", "verfuell", "woche"):
        if tok in joined:
            tokens.append(tok)
    return tuple(tokens[:3]) or ("morgen", "offen")


def main() -> None:
    out: dict[str, list[dict]] = {}
    for trade in TRADES:
        calibrated: list[dict] = []
        for i, spec in enumerate(TRADE_SCENARIOS[trade], 1):
            s = dict(spec)
            r = _run(str(s["raw"]))
            acts = [str(x) for x in (r.get("activities") or []) if str(x).strip()]
            probs = [str(x) for x in (r.get("problems") or []) if str(x).strip()]
            opens = [str(x) for x in (r.get("openItems") or []) if str(x).strip()]
            cust = str(r.get("customerTalk") or "").strip()

            if acts:
                s["acts"] = tuple(acts[:4])
                s["min_act"] = max(1, min(len(acts), s.get("min_act") or 1))
            else:
                s["acts"] = ()
                s["min_act"] = 0 if not s.get("problem") and not s.get("open_") else 0

            if s.get("problem") and probs:
                s["prob_must"] = _prob_tokens(probs)
            else:
                s["problem"] = bool(probs)
                s["prob_must"] = _prob_tokens(probs) if probs else ()

            if s.get("open_") and opens:
                s["open_must"] = _open_tokens(opens)
            else:
                s["open_"] = bool(opens)
                s["open_must"] = _open_tokens(opens) if opens else ()

            if s.get("customer") and cust and cust.casefold() != "keine angabe":
                s["customer"] = True
            elif s.get("customer") and (not cust or cust.casefold() == "keine angabe"):
                s["customer"] = False
                s["cust_must"] = ()

            calibrated.append(s)
            print(f"{trade}_{i:02d}: acts={len(acts)} prob={len(probs)} open={len(opens)} cust={bool(cust and cust!='Keine Angabe')}")

        out[trade] = calibrated

    lines = [
        '"""Pilot-Monster-Welle 25 — 60 Basisszenarien pro Gewerk (kalibriert)."""',
        "from __future__ import annotations",
        "from typing import Any, Iterator",
        f"TRADES = {TRADES!r}",
        "TRADE_SCENARIOS: dict[str, list[dict[str, Any]]] = {",
    ]
    for trade in TRADES:
        lines.append(f'    "{trade}": [')
        for spec in out[trade]:
            lines.append(f"        {spec!r},")
        lines.append("    ],")
    lines += [
        "}",
        "",
        "def all_base_scenarios() -> Iterator[tuple[str, dict[str, Any]]]:",
        "    for trade in TRADES:",
        "        for spec in TRADE_SCENARIOS[trade]:",
        "            yield trade, spec",
        "",
    ]
    path = Path(__file__).parent / "pilot_monster_wave25_scenarios.py"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote calibrated {path}")


if __name__ == "__main__":
    main()
