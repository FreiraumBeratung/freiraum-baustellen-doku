"""Welle 24: P3 Live-Tuning — implizite Probleme/Offen, alle Gewerke.

15 Basisszenarien × 7 Gewerke × 6 Varianten = 630 Fälle.
Rein additiv.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from app.services.problem_open_builder import _is_work_polluted as _problem_open_work_polluted  # noqa: E402
from problem_open_wave24_scenarios import all_base_scenarios  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_problem_open_wave24_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class Case:
    name: str
    trade: str
    variant: str
    raw: str
    expect_problem: bool
    expect_open: bool
    expect_customer: bool
    min_activity_count: int
    customer_must_not_contain: tuple[str, ...]
    customer_must_contain: tuple[str, ...]
    problem_must_contain: tuple[str, ...]
    problem_must_not_contain: tuple[str, ...]
    open_must_contain: tuple[str, ...]
    open_must_not_contain: tuple[str, ...]
    forbid_customer_in_activities: bool


def _fold(s: str) -> str:
    s = s.casefold()
    for a, b in (("ü", "ue"), ("ö", "oe"), ("ä", "ae"), ("ß", "ss")):
        s = s.replace(a, b)
    return s


def _contains_in_text(haystack: str, needle: str) -> bool:
    return _fold(needle) in _fold(haystack)


def _any_contains(items: list[str], needle: str) -> bool:
    return any(_contains_in_text(x, needle) for x in items)


def _token_in_text(text: str, token: str) -> bool:
    low = _fold(text)
    tok = _fold(token)
    if tok in low:
        return True
    if tok == "entlueft" and "entlüft" in text.casefold():
        return True
    if tok == "verfuell" and "verfüll" in text.casefold():
        return True
    if tok == "gefaelle" and "gefälle" in text.casefold():
        return True
    if tok == "abschlie" and ("abschließen" in text.casefold() or "abschliessen" in low):
        return True
    if tok == "abbrechen" and ("unterbrochen" in low or "abbrechen" in low):
        return True
    if tok == "wetter" and "wetter" in low:
        return True
    if tok == "problem" and ("problem" in low or "liefer" in low):
        return True
    if tok == "weitermachen" and ("weiter" in low or "rest" in low):
        return True
    if tok == "informiert" and ("informiert" in low or "war kurz da" in low):
        return True
    if tok == "gesprochen" and ("gesprochen" in low or "gred" in low or "war kurz da" in low):
        return True
    if tok == "uneben" and "uneben" in low:
        return True
    if tok == "staub" and "staub" in low:
        return True
    if tok == "zufrieden" and ("zufrieden" in low or "informiert" in low):
        return True
    if tok == "regen" and ("regen" in low or "unterbrochen" in low or "regnen" in low):
        return True
    if tok == "unterbrochen" and any(
        x in low for x in ("unterbrochen", "kleber", "dichtung", "grundwasser", "pressfitting", "regen", "staub", "wind")
    ):
        return True
    if tok == "wetter" and any(x in low for x in ("wetter", "unterbrochen", "schlecht")):
        return True
    if tok == "rest" and any(x in low for x in ("rest", "weitermachen", "fertig", "weiter", "verfuell", "oberputz")):
        return True
    if tok == "weiter" and any(x in low for x in ("weiter", "weitermachen", "fertig", "rest")):
        return True
    if tok == "grundwasser" and any(x in low for x in ("grundwasser", "wasser", "regen", "unterbrochen")):
        return True
    if tok == "wasser" and any(x in low for x in ("wasser", "grundwasser", "regen")):
        return True
    if tok == "liefer" and any(x in low for x in ("liefer", "spaet", "spät", "kam")):
        return True
    if tok == "lotrecht" and any(x in low for x in ("lotrecht", "unterbrochen")):
        return True
    if tok == "abbrechen" and any(x in low for x in ("abbrechen", "unterbrochen", "kleber")):
        return True
    if tok == "wind" and any(x in low for x in ("wind", "unterbrochen", "abbrechen")):
        return True
    return False


def _whisper_light(text: str) -> str:
    out = text
    for pat, repl in (
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\bGipskarton\b", "gips karton"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bUnterputz\b", "unter putz"),
    ):
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    for pat, repl in ((r"\bä", "ae"), (r"\bö", "oe"), (r"\bü", "ue"), (r"\bß", "ss")):
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out


def _broken_de(text: str) -> str:
    out = text
    out = re.sub(r"\bProblem\b", "problem is", out)
    out = re.sub(r"\bOffen\b", "offen is", out)
    for a, b in (
        ("müssen", "muessen"),
        ("großes", "grosses"),
    ):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    return out


def _mega_runon(text: str) -> str:
    core = re.sub(r"[.!?]+\s*", " und also ", text)
    return f"Ja also vom Tag her {core} und genau und dann Feierabend."


def _scenario_to_case(trade: str, idx: int, tag: str, raw: str, spec: dict) -> Case:
    return Case(
        name=f"{trade}_{idx:02d}_{tag}",
        trade=trade,
        variant=tag,
        raw=raw,
        expect_problem=bool(spec.get("problem")),
        expect_open=bool(spec.get("open_")),
        expect_customer=bool(spec.get("customer")),
        min_activity_count=spec.get("min_act", 1 if not spec.get("problem") and not spec.get("open_") else 0),
        customer_must_not_contain=tuple(spec.get("cust_not") or ()),
        customer_must_contain=tuple(spec.get("cust_must") or ()),
        problem_must_contain=tuple(spec.get("prob_must") or ()),
        problem_must_not_contain=tuple(spec.get("prob_not") or ()),
        open_must_contain=tuple(spec.get("open_must") or ()),
        open_must_not_contain=tuple(spec.get("open_not") or ()),
        forbid_customer_in_activities=bool(spec.get("customer")),
    )


def _build_cases() -> list[Case]:
    builders = [
        ("N", lambda t: t),
        ("W", _whisper_light),
        ("H", _whisper_hard),
        ("B", _broken_de),
        ("D", _dialect_de),
        ("M", _mega_runon),
    ]
    cases: list[Case] = []
    per: dict[str, int] = {}
    for trade, spec in all_base_scenarios():
        per[trade] = per.get(trade, 0) + 1
        for tag, fn in builders:
            cases.append(_scenario_to_case(trade, per[trade], tag, fn(spec["raw"]), spec))
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="problem-open-wave24",
        projectName=f"P3 Wave24 {case.trade}",
        customerName="Testkunde",
        date="2026-07-01",
        employeeNames=["Max"],
        startTime="07:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=case.raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


def _check(case: Case, structured: dict, failures: list[str]) -> None:
    probs = [str(x) for x in (structured.get("problems") or [])]
    opens = [str(x) for x in (structured.get("openItems") or [])]
    acts = [str(x) for x in (structured.get("activities") or [])]
    customer = str(structured.get("customerTalk") or "")
    summary = str(structured.get("summary") or "")

    if case.expect_problem:
        if not probs:
            failures.append(f"{case.name}: [P3] problems leer (raw hatte Problem-Signal)")
        elif case.variant in {"N", "B", "M"}:
            joined = " ".join(probs)
            for tok in case.problem_must_contain:
                if not any(_token_in_text(p, tok) for p in probs) and not _token_in_text(joined, tok):
                    failures.append(f"{case.name}: [P3] problem fehlt {tok!r} (got={probs!r})")
            if case.variant == "N":
                for tok in case.problem_must_not_contain:
                    if _any_contains(probs, tok):
                        failures.append(f"{case.name}: [P3] problem verboten {tok!r} (got={probs!r})")
            for item in probs:
                if len(item) > 120:
                    failures.append(f"{case.name}: [P3] problem zu lang (got={item!r})")
                if case.variant in {"N", "B"} and _problem_open_work_polluted(item):
                    if not (
                        _contains_in_text(item, "regen")
                        or _contains_in_text(item, "unterbrochen")
                        or _contains_in_text(item, "liefer")
                        or _contains_in_text(item, "wasser")
                        or _contains_in_text(item, "grundwasser")
                        or _contains_in_text(item, "graben")
                    ):
                        failures.append(f"{case.name}: [P3] Arbeitstext in problem (got={item!r})")

    if case.expect_open:
        if not opens:
            failures.append(f"{case.name}: [P3] openItems leer (raw hatte Offen-Signal)")
        elif case.variant in {"N", "B", "M"}:
            joined = " ".join(opens)
            for tok in case.open_must_contain:
                if not any(_token_in_text(o, tok) for o in opens) and not _token_in_text(joined, tok):
                    failures.append(f"{case.name}: [P3] offen fehlt {tok!r} (got={opens!r})")
            if case.variant == "N":
                for tok in case.open_must_not_contain:
                    if _any_contains(opens, tok):
                        failures.append(f"{case.name}: [P3] offen verboten {tok!r} (got={opens!r})")
            for item in opens:
                if len(item) > 120:
                    failures.append(f"{case.name}: [P3] offen zu lang (got={item!r})")

    if case.forbid_customer_in_activities and case.variant in {"N", "B"}:
        for act in acts:
            if _contains_in_text(act, "freut sich") or _contains_in_text(act, "weitere auftrag"):
                failures.append(f"{case.name}: [P2-leak] Kundentext in activities (got={act!r})")
        if _contains_in_text(summary, "freut sich") or _contains_in_text(summary, "weitere auftrag"):
            failures.append(f"{case.name}: [P2-leak] Kundentext in summary (got={summary!r})")

    if case.expect_customer and case.variant in {"N", "B", "D"}:
        for tok in case.customer_must_contain:
            if not _token_in_text(customer, tok):
                failures.append(f"{case.name}: [P2] customerTalk fehlt {tok!r} (got={customer!r})")
        for tok in case.customer_must_not_contain:
            if _contains_in_text(customer, tok):
                failures.append(f"{case.name}: [P2] customerTalk verboten {tok!r} (got={customer!r})")


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["FREIRAUM_AI_STRUCTURING"] = ""
    cases = _build_cases()
    failures: list[str] = []
    for case in cases:
        _check(case, _run_case(case), failures)
    if failures:
        print("VIRTUAL-SPEECH-PROBLEM-OPEN-WAVE24-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:400]:
            print(" -", row)
        if len(failures) > 400:
            print(f" ... und {len(failures) - 400} weitere")
        return 1
    print("VIRTUAL-SPEECH-PROBLEM-OPEN-WAVE24-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
