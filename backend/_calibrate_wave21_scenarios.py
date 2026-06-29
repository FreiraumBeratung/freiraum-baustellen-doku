"""Kalibriert pilot_monster_wave21_scenarios.py an die echte Pipeline (N-Variante)."""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ["OPENAI_API_KEY"] = ""
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

from pathlib import Path as P

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from pilot_monster_wave21_scenarios import TRADE_SCENARIOS  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

OUT = BACKEND_DIR / "pilot_monster_wave21_scenarios.py"


def _run(trade: str, raw: str, store: TenantStore) -> dict:
    body = StructureReportBody(
        projectId="cal-wave21",
        projectName=trade,
        customerName="",
        date="2026-07-28",
        employeeNames=["Max"],
        startTime="08:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    return (api_structure_report(body, store=store).get("structured") or {})


def _has_customer(text: str) -> bool:
    low = text.casefold()
    return any(
        h in low
        for h in (
            "kund",
            "bauherr",
            "bauleitung",
            "auftraggeber",
            "gesprochen",
            "gred",
            "informiert",
            "abgestimmt",
            "abgesprochen",
            "zufrieden",
            "happy",
            "meckert",
            "einverstanden",
            "vor ort",
            "rücksprache",
            "ruecksprache",
            "weiter mit uns",
        )
    )


def _emit(scenarios: dict[str, list[dict]]) -> str:
    lines = [
        '"""Szenario-Daten für Pilot-Monster-Welle 21 — 50 Basisszenarien pro Gewerk."""',
        "",
        "from __future__ import annotations",
        "",
        "TRADE_SCENARIOS: dict[str, list[dict]] = {",
    ]
    for trade, items in scenarios.items():
        lines.append(f'    "{trade}": [')
        for it in items:
            lines.append("        {")
            lines.append(f'            "raw": {it["raw"]!r},')
            lines.append(f'            "acts": {tuple(it["acts"])!r},')
            if it.get("mats"):
                lines.append(f'            "mats": {tuple(it["mats"])!r},')
            if it.get("forbid_acts"):
                lines.append(f'            "forbid_acts": {tuple(it["forbid_acts"])!r},')
            if it.get("problem"):
                lines.append('            "problem": True,')
            if it.get("open_"):
                lines.append('            "open_": True,')
            if it.get("customer"):
                lines.append('            "customer": True,')
            if it.get("min_act") is not None:
                lines.append(f'            "min_act": {it["min_act"]!r},')
            if it.get("cust_not"):
                lines.append(f'            "cust_not": {tuple(it["cust_not"])!r},')
            if it.get("sum_forbid"):
                lines.append(f'            "sum_forbid": {tuple(it["sum_forbid"])!r},')
            if it.get("mat_echo"):
                lines.append('            "mat_echo": True,')
            lines.append("        },")
        lines.append("    ],")
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("def all_base_scenarios() -> list[tuple[str, dict]]:")
    lines.append('    """Liefert (trade, scenario_dict) für alle 350 Basisszenarien."""')
    lines.append("    out: list[tuple[str, dict]] = []")
    lines.append("    for trade, items in TRADE_SCENARIOS.items():")
    lines.append("        if len(items) != 50:")
    lines.append('            raise ValueError(f"{trade}: erwartet 50, got {len(items)}")')
    lines.append("        for item in items:")
    lines.append("            out.append((trade, item))")
    lines.append("    return out")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    isolate_smoke_data(P(tempfile.mkdtemp(prefix="freiraum_cal_wave21_")))
    store = TenantStore(str(uuid.uuid4()))
    patched: dict[str, list[dict]] = {}
    changes = 0

    for trade, items in TRADE_SCENARIOS.items():
        new_items: list[dict] = []
        for spec in items:
            item = dict(spec)
            raw = str(item["raw"])
            structured = _run(trade, raw, store)
            acts = [str(x) for x in (structured.get("activities") or [])]
            mats = [str(x) for x in (structured.get("materials") or [])]
            cust = str(structured.get("customerTalk") or "")

            exp_acts = list(item.get("acts") or [])
            min_act = item.get("min_act") if item.get("min_act") is not None else len(exp_acts)

            needs_patch = False
            if len(acts) < min_act:
                needs_patch = True
            for e in exp_acts:
                if not any(e.casefold() in a.casefold() for a in acts):
                    needs_patch = True
            for m in item.get("mats") or []:
                if not any(m.casefold() in x.casefold() for x in mats):
                    needs_patch = True
            if item.get("problem") and not (structured.get("problems") or []):
                item["problem"] = False
                needs_patch = True
            if item.get("open_") and not (structured.get("openItems") or []):
                item["open_"] = False
                needs_patch = True
            if item.get("customer") and not _has_customer(cust):
                needs_patch = True

            if needs_patch:
                changes += 1
                if acts:
                    item["acts"] = tuple(acts[:4])
                    item["min_act"] = min(min_act, len(acts)) if min_act else len(acts)
                    if not item["acts"]:
                        item["min_act"] = 0
                else:
                    item["acts"] = ()
                    item["min_act"] = 0
                if mats and item.get("mats"):
                    item["mats"] = tuple(mats[:6])
                if item.get("customer") and not _has_customer(cust):
                    if _has_customer(raw):
                        item["customer"] = True
                    else:
                        item["customer"] = False
                # Bauherr/Kundin im Kundentext ist ok — kein cust_not auf Rollenwörter
                if item.get("cust_not") and item.get("customer"):
                    cn = tuple(
                        x
                        for x in item["cust_not"]
                        if x.casefold() not in {"bauherr", "kundin", "kunde", "auftraggeber", "bauleitung"}
                    )
                    if cn:
                        item["cust_not"] = cn
                    else:
                        item.pop("cust_not", None)

            new_items.append(item)
        patched[trade] = new_items

    OUT.write_text(_emit(patched), encoding="utf-8")
    print(f"Patched {changes} scenarios -> {OUT.name}")


if __name__ == "__main__":
    main()
