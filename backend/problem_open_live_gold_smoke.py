"""Gold-Smoke: Live-Hetzner-Tests — P3 implizit + Kundentext-Leak-Schutz.

Permanent verankerte Rohtexte aus Nutzer-Live-Tests (Juni 2026).
Rein additiv.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_problem_open_live_gold_")))
_STORE = TenantStore(str(uuid.uuid4()))

LIVE_CASES = (
    {
        "name": "live_rain_open",
        "raw": (
            "heute haben wir 50 Quadratmeter Pflaster gelegt und 5 m² Gartenmauer gebaut "
            "leider mussten wir die Arbeiten abbrechen weil es geregnet hat "
            "morgen müssen wir noch fünf weitere Quadratmeter legen"
        ),
        "expect_problem": True,
        "expect_open": True,
        "prob_tokens": ("regen", "unterbrochen"),
        "open_tokens": ("morgen", "offen"),
        "cust_empty": True,
    },
    {
        "name": "live_rain_only",
        "raw": (
            "heute haben wir 50 Quadratmeter Pflaster gelegt wir mussten die Arbeiten "
            "leider abbrechen weil es angefangen hat zu regnen"
        ),
        "expect_problem": True,
        "expect_open": False,
        "prob_tokens": ("regen", "unterbrochen"),
        "open_tokens": (),
        "cust_empty": True,
    },
    {
        "name": "live_uneben_customer",
        "raw": (
            "heute haben wir 50 Quadratmeter Pflaster gelegt leider war der Untergrund "
            "sehr uneben was zu Problemen geführt hat die Kundin war trotzdem zufrieden "
            "mit unserer Arbeit und freut sich auf weitere Auftraege"
        ),
        "expect_problem": True,
        "expect_open": False,
        "prob_tokens": ("uneben",),
        "open_tokens": (),
        "cust_tokens": ("zufrieden", "freut"),
        "cust_empty": False,
        "no_leak": True,
    },
    {
        "name": "live_morgen_hecke",
        "raw": (
            "heute haben wir 50 Quadratmeter Pflaster gelegt "
            "morgen müssen wir noch 20 m Hecke schneiden"
        ),
        "expect_problem": False,
        "expect_open": True,
        "prob_tokens": (),
        "open_tokens": ("morgen", "hecke", "offen"),
        "cust_empty": True,
    },
    {
        "name": "live_putz_oberputz",
        "raw": (
            "heute haben wir grundiert und den Unterputz aufgetragen "
            "morgen müssen wir auf der Baustelle mit Oberputz abschliessen"
        ),
        "expect_problem": False,
        "expect_open": True,
        "prob_tokens": (),
        "open_tokens": ("morgen", "oberputz", "offen"),
        "cust_empty": True,
    },
    {
        "name": "live_rain_plan",
        "raw": (
            "Heute haben wir 50 m² Pflaster verlegt wir mussten die Arbeiten leider abbrechen "
            "weil es angefangen hat zu regnen dementsprechend werden wir morgen dort weitermachen"
        ),
        "expect_problem": True,
        "expect_open": True,
        "prob_tokens": ("regen", "unterbrochen"),
        "open_tokens": ("morgen", "weitermachen", "offen"),
        "prob_not": ("weitermachen", "dementsprechend"),
        "cust_empty": True,
    },
)


def _fold(s: str) -> str:
    s = s.casefold()
    for a, b in (("ü", "ue"), ("ö", "oe"), ("ä", "ae"), ("ß", "ss")):
        s = s.replace(a, b)
    return s


def _has(text: str, token: str) -> bool:
    return _fold(token) in _fold(text)


def _fail(msg: str, failures: list[str]) -> None:
    failures.append(msg)


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["FREIRAUM_AI_STRUCTURING"] = ""
    failures: list[str] = []

    for case in LIVE_CASES:
        body = StructureReportBody(
            projectId="problem-open-live-gold",
            projectName="Live Gold",
            customerName="Test",
            date="2026-07-01",
            employeeNames=["Max"],
            startTime="07:00",
            endTime="16:00",
            exportFormat="PDF",
            rawText=case["raw"],
        )
        s = (api_structure_report(body, store=_STORE).get("structured") or {})
        probs = [str(x) for x in (s.get("problems") or [])]
        opens = [str(x) for x in (s.get("openItems") or [])]
        acts = [str(x) for x in (s.get("activities") or [])]
        customer = str(s.get("customerTalk") or "")
        summary = str(s.get("summary") or "")
        joined_p = " ".join(probs)
        joined_o = " ".join(opens)

        if case["expect_problem"] and not probs:
            _fail(f"{case['name']}: problems leer", failures)
        if case["expect_open"] and not opens:
            _fail(f"{case['name']}: openItems leer", failures)
        for tok in case.get("prob_tokens") or ():
            if case["expect_problem"] and not (
                _has(joined_p, tok)
                or any(_has(p, tok) for p in probs)
                or (tok == "regen" and _has(joined_p, "regnen"))
                or (tok == "unterbrochen" and _has(joined_p, "regnen"))
            ):
                _fail(f"{case['name']}: problem fehlt {tok!r} (got={probs!r})", failures)
        for tok in case.get("open_tokens") or ():
            if case["expect_open"] and not (_has(joined_o, tok) or any(_has(o, tok) for o in opens)):
                _fail(f"{case['name']}: offen fehlt {tok!r} (got={opens!r})", failures)
        for tok in case.get("prob_not") or ():
            if probs and (_has(joined_p, tok)):
                _fail(f"{case['name']}: problem verboten {tok!r} (got={probs!r})", failures)
        for item in probs + opens:
            if len(item) > 120:
                _fail(f"{case['name']}: Eintrag zu lang (got={item!r})", failures)

        if case.get("cust_empty"):
            if customer and customer.strip() and customer != "Keine Angabe":
                _fail(f"{case['name']}: customerTalk sollte leer sein (got={customer!r})", failures)

        if not case.get("cust_empty"):
            for tok in case.get("cust_tokens") or ():
                if not _has(customer, tok):
                    _fail(f"{case['name']}: customerTalk fehlt {tok!r} (got={customer!r})", failures)

        if case.get("no_leak"):
            for act in acts:
                if _has(act, "freut sich") or _has(act, "auftrag"):
                    _fail(f"{case['name']}: leak in activity {act!r}", failures)
            if _has(summary, "freut sich") or _has(summary, "auftrag"):
                _fail(f"{case['name']}: leak in summary {summary!r}", failures)

    if failures:
        print("PROBLEM-OPEN-LIVE-GOLD-SMOKE: FEHLER")
        for row in failures:
            print(" -", row)
        return 1
    print("PROBLEM-OPEN-LIVE-GOLD-SMOKE: OK")
    print(f"Cases: {len(LIVE_CASES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
