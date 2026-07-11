"""P3 Gold-Smoke: Probleme/Offen — Isolation, deterministische Sätze, optional KI-Polish.

Prüft Guards offline und die volle Pipeline mit/ohne OPENAI_API_KEY.
Rein additiv — keine bestehenden Wellen ändern.
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
from app.services.problem_open_builder import (  # noqa: E402
    extract_open_items_from_text,
    extract_problems_from_text,
    refine_open_items_list,
    refine_problems_list,
)
from app.services.problem_open_guard import (  # noqa: E402
    open_item_polish_is_safe,
    problem_item_polish_is_safe,
)
from services.ai_report_service import polish_problem_open_with_ai  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_problem_open_gold_")))
_STORE = TenantStore(str(uuid.uuid4()))
_SAVED_KEY = os.environ.get("OPENAI_API_KEY", "")


def _fail(msg: str, failures: list[str]) -> None:
    failures.append(msg)


def _has_work_pollution(text: str) -> bool:
    low = text.casefold()
    return any(
        token in low
        for token in (
            "pflaster verlegt",
            "quadratmeter",
            " m²",
            " m2",
            "schotter eingebaut",
            "qm ",
            "50 ",
            "30 ",
        )
    )


def _guard_unit_tests(failures: list[str]) -> None:
    raw = (
        "50 qm pflaster gelegt problem lieferung kam spaet "
        "offen letzte reihe morgen kundin zufrieden"
    )
    probs = extract_problems_from_text(raw)
    opens = extract_open_items_from_text(raw)
    if not probs:
        _fail("Extract: Problem fehlt", failures)
    if not opens:
        _fail("Extract: Offen fehlt", failures)
    if any(_has_work_pollution(p) for p in probs):
        _fail(f"Extract: Arbeitstext in problems (got={probs!r})", failures)
    if any(_has_work_pollution(o) for o in opens):
        _fail(f"Extract: Arbeitstext in openItems (got={opens!r})", failures)
    if any("kund" in p.casefold() for p in probs + opens):
        _fail("Extract: Kundentext in Problem/Offen", failures)
    if "lieferung" not in probs[0].casefold():
        _fail(f"Extract: Lieferung fehlt im Problem (got={probs!r})", failures)

    det_p = refine_problems_list([raw], raw)
    det_o = refine_open_items_list([raw], raw)
    if problem_item_polish_is_safe(
        "Die Lieferung kam verspätet.",
        det_p[0],
        raw_text=raw,
    ) is not True:
        _fail("Guard: sauberer Problem-Polish sollte akzeptiert werden", failures)
    if problem_item_polish_is_safe(
        "50 m² Pflaster verlegt, Lieferung spät.",
        det_p[0],
        raw_text=raw,
    ) is not False:
        _fail("Guard: Arbeitstext im Problem-Polish muss abgelehnt werden", failures)
    if open_item_polish_is_safe(
        "Die letzte Reihe ist für morgen noch offen.",
        det_o[0],
        raw_text=raw,
    ) is not True:
        _fail("Guard: sauberer Offen-Polish sollte akzeptiert werden", failures)


def _pipeline_offline(failures: list[str]) -> None:
    os.environ["OPENAI_API_KEY"] = ""
    cases = [
        (
            "runon_gala",
            (
                "50 Quadratmeter Pflaster verlegt und Pflastersteine verarbeitet "
                "zwei Kubikmeter Schotter eingebaut Problem Lieferung kam spät "
                "Offen letzte Reihe morgen Mit der Kundin gesprochen sie war sehr zufrieden."
            ),
            ("lieferung",),
            ("reihe", "morgen", "offen"),
            ("pflaster verlegt", "50", "schotter", "kundin"),
        ),
        (
            "runon_short",
            "heute 30 quadrat pflaster gelegt problem regen offen rest montag",
            ("regen",),
            ("montag", "offen"),
            ("pflaster", "30", "quadrat"),
        ),
        (
            "regen_abbruch",
            (
                "Heute haben wir den Untergrund frei gebaggert damit 3,5 m³ Schotter null 32 verdichtet "
                "dann haben wir drei Kubik Split zwei Fünfer eingebaut leider mussten wir die Arbeiten "
                "abrechnen weil es stark angefangen zu regnen dementsprechend verschiebt sich das "
                "Pflastern auf morgen"
            ),
            ("regen",),
            ("pflaster", "morgen", "offen"),
            ("kundin",),
        ),
        (
            "drainage",
            "Kundengespräch gehabt Pflastermuster gewählt Problem Drainage Offen Rest nächste Woche.",
            ("drainage",),
            ("rest", "woche", "offen"),
            ("kundengespräch gehabt",),
        ),
    ]
    for name, raw, must_p, must_o, forbid in cases:
        body = StructureReportBody(
            projectId="p3",
            projectName="Test",
            customerName="K",
            date="2026-06-27",
            employeeNames=["M"],
            startTime="08:00",
            endTime="16:00",
            exportFormat="PDF",
            rawText=raw,
        )
        structured = (api_structure_report(body, store=_STORE).get("structured") or {})
        probs = [str(x) for x in (structured.get("problems") or [])]
        opens = [str(x) for x in (structured.get("openItems") or [])]
        if not probs:
            _fail(f"{name}: problems leer", failures)
        if not opens:
            _fail(f"{name}: openItems leer", failures)
        joined_p = " ".join(probs).casefold()
        joined_o = " ".join(opens).casefold()
        for token in must_p:
            if token.casefold() not in joined_p:
                _fail(f"{name}: Problem fehlt {token!r} (got={probs!r})", failures)
        for token in must_o:
            if token.casefold() not in joined_o:
                _fail(f"{name}: Offen fehlt {token!r} (got={opens!r})", failures)
        for token in forbid:
            if token.casefold() in joined_p or token.casefold() in joined_o:
                _fail(f"{name}: verboten {token!r} in Problem/Offen", failures)
        if any(_has_work_pollution(x) for x in probs + opens):
            _fail(f"{name}: Arbeitstext in Problem/Offen (p={probs!r}, o={opens!r})", failures)


def _pipeline_with_key_if_available(failures: list[str]) -> None:
    key = (_SAVED_KEY or "").strip()
    if not key:
        print("PROBLEM-OPEN-POLISH-GOLD: OPENAI_API_KEY nicht gesetzt — KI-Polish-Skip")
        return

    os.environ["OPENAI_API_KEY"] = key
    raw = (
        "50 qm pflaster gelegt problem lieferung kam spaet "
        "offen letzte reihe morgen kundin zufrieden"
    )
    body = StructureReportBody(
        projectId="p3-ai",
        projectName="Test",
        customerName="K",
        date="2026-06-27",
        employeeNames=["M"],
        startTime="08:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    structured = (api_structure_report(body, store=_STORE).get("structured") or {})
    probs = list(structured.get("problems") or [])
    opens = list(structured.get("openItems") or [])
    if not probs or not opens:
        _fail("KI-Pipeline: Problem/Offen leer", failures)
    if any(_has_work_pollution(x) for x in probs + opens):
        _fail(f"KI-Pipeline: Arbeitstext (p={probs!r}, o={opens!r})", failures)

    det = {
        "problems": refine_problems_list(probs, raw),
        "openItems": refine_open_items_list(opens, raw),
    }
    polished = polish_problem_open_with_ai(det, raw_text=raw)
    if polished:
        all_items = list(polished.get("problems") or []) + list(polished.get("openItems") or [])
        if any(_has_work_pollution(x) for x in all_items):
            _fail(f"polish_problem_open_with_ai: Arbeitstext (got={polished!r})", failures)
        for item in all_items:
            if len(re.split(r"(?<=[.!?])\s+", item.strip())) > 2:
                _fail(f"polish_problem_open_with_ai: zu viele Sätze (got={item!r})", failures)


def main() -> int:
    failures: list[str] = []
    try:
        _guard_unit_tests(failures)
        _pipeline_offline(failures)
        _pipeline_with_key_if_available(failures)
    finally:
        if _SAVED_KEY:
            os.environ["OPENAI_API_KEY"] = _SAVED_KEY
        else:
            os.environ.pop("OPENAI_API_KEY", None)

    if failures:
        print("PROBLEM-OPEN-POLISH-GOLD: FEHLER")
        for f in failures:
            print(" -", f)
        return 1
    print("PROBLEM-OPEN-POLISH-GOLD: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
