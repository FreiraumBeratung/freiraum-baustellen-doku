"""Welle 22: Cross-Validierung P1 (Summary) + P2 (Kundengespräch) + P3 (Problem/Offen).

Frische Szenarien (nicht Welle 20/21), alle 7 Gewerke, 6 Varianten.
10 Basisszenarien × 7 Gewerke × 6 = 420 Fälle.
Rein additiv — keine bestehenden Smoke-Dateien ändern.
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
from app.services.summary_material_guard import (  # noqa: E402
    detect_material_echo_in_summary,
    summary_has_material_echo,
)
from app.services.problem_open_builder import _is_work_polluted as _problem_open_work_polluted  # noqa: E402
from priority_p123_wave22_scenarios import all_base_scenarios  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_priority_p123_wave22_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class Case:
    name: str
    trade: str
    variant: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...]
    forbid_activities: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool
    min_activity_count: int
    forbid_summary_contains: tuple[str, ...]
    forbid_summary_material_echo: bool
    customer_must_not_contain: tuple[str, ...]
    customer_must_contain: tuple[str, ...]
    problem_must_contain: tuple[str, ...]
    problem_must_not_contain: tuple[str, ...]
    open_must_contain: tuple[str, ...]
    open_must_not_contain: tuple[str, ...]


def _contains_any(haystack: list[str], needle: str, *, variant: str = "N") -> bool:
    n = needle.casefold()
    if any(n in str(item).casefold() for item in haystack):
        return True
    if variant == "N":
        return False
    tokens = [t for t in re.split(r"[\s\-/]+", n) if len(t) > 3]
    if not tokens:
        return False
    for item in haystack:
        low = str(item).casefold()
        hits = sum(1 for t in tokens if t in low)
        if hits >= max(1, len(tokens) - 1):
            return True
    return False


def _contains_in_text(haystack: str, needle: str) -> bool:
    return needle.casefold() in haystack.casefold()


def _any_contains_in_list(items: list[str], needle: str) -> bool:
    return any(_contains_in_text(x, needle) for x in items)


def _has_customer_talk(text: str) -> bool:
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
            "einverstanden",
            "rücksprache",
            "ruecksprache",
            "happy",
            "unterhalten",
            "kundengespräch",
            "kundengespraech",
            "besprochen",
            "geklärt",
            "geklaert",
        )
    )


def _token_in_text(text: str, token: str) -> bool:
    low = text.casefold()
    tok = token.casefold()
    if tok in low:
        return True
    if tok == "gesprochen" and "gred" in low:
        return True
    if tok == "einverstanden" and "einverstandn" in low:
        return True
    if tok == "abgestimmt" and "abgred" in low:
        return True
    if tok == "kunden" and "kund" in low:
        return True
    return False


def _customer_has_communication_context(text: str) -> bool:
    low = text.casefold()
    return any(
        token in low
        for token in (
            "gesprochen",
            "gred",
            "unterhalten",
            "informiert",
            "abgestimmt",
            "abgesprochen",
            "rücksprache",
            "ruecksprache",
            "kundengespräch",
            "kundengespraech",
            "besprochen",
            "geklärt",
            "geklaert",
            "einverstanden",
        )
    )


def _raw_expects_communication(raw: str) -> bool:
    low = raw.casefold()
    return any(
        token in low
        for token in (
            "gesprochen",
            "gred",
            "unterhalten",
            "informiert",
            "abgestimmt",
            "abgesprochen",
            "rücksprache",
            "ruecksprache",
            "kundengespräch",
            "kundengespraech",
            "besprochen",
            "geklärt",
            "geklaert",
        )
    )


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bGipskartonplatten\b", "gips karton platten"),
        (r"\bThermostatventile\b", "thermo stat ventile"),
        (r"\bHeizkörper\b", "heiz körper"),
        (r"\bFußbodenheizung\b", "fuss boden heizung"),
        (r"\bFiligrandecke\b", "filigran decke"),
        (r"\bPflastersteine\b", "pflaster steine"),
        (r"\bFliesenkleber\b", "fliesen kleber"),
        (r"\bGroßformatfliesen\b", "gross format fliesen"),
        (r"\bTerrassenplatten\b", "terrassen platten"),
        (r"\bRollrasen\b", "roll rasen"),
        (r"\bAußenputz\b", "aussen putz"),
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\bKG-Rohr\b", "ka ga rohr"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bverlegt\b", "ver legt"),
        (r"\bgesprochen\b", "ge sprochen"),
        (r"\bzufrieden\b", "zu frieden"),
        (r"\baufgetragen\b", "auf getragen"),
        (r"\bä", "ae"),
        (r"\bö", "oe"),
        (r"\bü", "ue"),
        (r"\bß", "ss"),
    )
    for pat, repl in extra:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out


def _broken_de(text: str) -> str:
    out = text
    for a, b in (
        ("haben wir", "hamma"),
        ("Heute", "heute"),
        ("verlegt", "ver legt"),
        ("gesprochen", "gred"),
        ("abgesprochen", "abgred"),
        ("Problem", "problem is"),
        ("Offen", "offen is"),
        ("Kundin", "kundin"),
        ("einverstanden", "einverstandn"),
    ):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKunde\b", "Kund", out, flags=re.IGNORECASE)
    return out


def _mega_runon(text: str) -> str:
    core = re.sub(r"[.!?]+\s*", " und also ", text)
    return (
        f"Ja also vom Tag her {core} und genau und dann Feierabend "
        f"und morgen machen wir den Rest wenn Material da ist."
    )


def _scenario_to_case(trade: str, idx: int, tag: str, raw: str, spec: dict) -> Case:
    acts = tuple(spec.get("acts") or ())
    min_count = spec["min_act"] if spec.get("min_act") is not None else len(acts)
    return Case(
        name=f"{trade}_{idx:02d}_{tag}",
        trade=trade,
        variant=tag,
        raw=raw,
        expect_activities=acts,
        expect_materials=tuple(spec.get("mats") or ()),
        forbid_activities=tuple(spec.get("forbid_acts") or ()),
        expect_problem=bool(spec.get("problem")),
        expect_open=bool(spec.get("open_")),
        expect_customer=bool(spec.get("customer")),
        min_activity_count=min_count,
        forbid_summary_contains=tuple(spec.get("sum_forbid") or ()),
        forbid_summary_material_echo=bool(spec.get("mat_echo")),
        customer_must_not_contain=tuple(spec.get("cust_not") or ()),
        customer_must_contain=tuple(spec.get("cust_must") or ()),
        problem_must_contain=tuple(spec.get("prob_must") or ()),
        problem_must_not_contain=tuple(spec.get("prob_not") or ()),
        open_must_contain=tuple(spec.get("open_must") or ()),
        open_must_not_contain=tuple(spec.get("open_not") or ()),
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
    per_trade_idx: dict[str, int] = {}
    for trade, spec in all_base_scenarios():
        per_trade_idx[trade] = per_trade_idx.get(trade, 0) + 1
        idx = per_trade_idx[trade]
        for tag, builder in builders:
            cases.append(_scenario_to_case(trade, idx, tag, builder(spec["raw"]), spec))
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="priority-p123-wave22",
        projectName=f"P123 Cross {case.trade}",
        customerName="Testkunde",
        date="2026-07-29",
        employeeNames=["Max", "Goran", "Ahmet"],
        startTime="06:00",
        endTime="18:00",
        exportFormat="PDF",
        rawText=case.raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


def _check_p1(case: Case, summary: str, mats: list[str], acts: list[str], failures: list[str]) -> None:
    if not summary or len(summary.strip()) < 8:
        if acts:
            failures.append(f"{case.name}: [P1] summary leer/zu kurz (got={summary!r})")
        return
    for forbidden in case.forbid_summary_contains:
        if _contains_in_text(summary, forbidden):
            failures.append(f"{case.name}: [P1] summary verboten {forbidden!r} (got={summary!r})")
    if case.forbid_summary_material_echo and case.variant in {"N", "W", "B"} and mats:
        if summary_has_material_echo(summary, mats, acts):
            echo = detect_material_echo_in_summary(summary, mats, acts) or "Material-Echo"
            failures.append(f"{case.name}: [P1] {echo} (summary={summary!r})")
        for needle in ("zum einsatz", "dafür kamen", "dafuer kamen", "hierbei kamen"):
            if _contains_in_text(summary, needle):
                failures.append(f"{case.name}: [P1] summary enthält {needle!r} (got={summary!r})")


def _check_p2(case: Case, customer: str, summary: str, failures: list[str]) -> None:
    if not case.expect_customer:
        return
    if not customer or customer.casefold() == "keine angabe":
        failures.append(f"{case.name}: [P2] customerTalk leer (got={customer!r})")
        return
    if not _has_customer_talk(customer):
        failures.append(f"{case.name}: [P2] customerTalk ohne Kundeninhalt (got={customer!r})")
    for token in case.customer_must_not_contain:
        if _contains_in_text(customer, token):
            failures.append(f"{case.name}: [P2] customerTalk verboten {token!r} (got={customer!r})")
    if case.variant in {"N", "B", "D"}:
        for token in case.customer_must_contain:
            if not _token_in_text(customer, token):
                failures.append(
                    f"{case.name}: [P2] customerTalk fehlt {token!r} (got={customer!r})"
                )
    if case.variant in {"N", "B"} and _raw_expects_communication(case.raw):
        if not _customer_has_communication_context(customer):
            failures.append(
                f"{case.name}: [P2] Gesprächskontext fehlt (got={customer!r})"
            )
    if summary and customer.casefold() == summary.casefold():
        failures.append(f"{case.name}: [P2] customerTalk ist Summary-Kopie")


def _check_p3(
    case: Case,
    probs: list[str],
    opens: list[str],
    failures: list[str],
) -> None:
    if case.expect_problem:
        if not probs:
            failures.append(f"{case.name}: [P3] problems leer")
        else:
            joined = " ".join(probs)
            if case.variant in {"N", "B", "M"}:
                for token in case.problem_must_contain:
                    if not _any_contains_in_list(probs, token) and not _contains_in_text(joined, token):
                        failures.append(
                            f"{case.name}: [P3] problem fehlt {token!r} (got={probs!r})"
                        )
            if case.variant == "N":
                for token in case.problem_must_not_contain:
                    if _any_contains_in_list(probs, token):
                        failures.append(
                            f"{case.name}: [P3] problem verboten {token!r} (got={probs!r})"
                        )
            if case.variant in {"N", "B", "M"}:
                for item in probs:
                    if _problem_open_work_polluted(item):
                        failures.append(
                            f"{case.name}: [P3] Arbeitstext in problem (got={item!r})"
                        )

    if case.expect_open:
        if not opens:
            failures.append(f"{case.name}: [P3] openItems leer")
        else:
            joined = " ".join(opens)
            if case.variant in {"N", "B", "M"}:
                for token in case.open_must_contain:
                    if not _any_contains_in_list(opens, token) and not _contains_in_text(joined, token):
                        failures.append(
                            f"{case.name}: [P3] offen fehlt {token!r} (got={opens!r})"
                        )
            if case.variant == "N":
                for token in case.open_must_not_contain:
                    if _any_contains_in_list(opens, token):
                        failures.append(
                            f"{case.name}: [P3] offen verboten {token!r} (got={opens!r})"
                        )
            if case.variant in {"N", "B", "M"}:
                for item in opens:
                    if _problem_open_work_polluted(item):
                        failures.append(
                            f"{case.name}: [P3] Arbeitstext in openItems (got={item!r})"
                        )


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["FREIRAUM_AI_STRUCTURING"] = ""
    cases = _build_cases()
    failures: list[str] = []

    for case in cases:
        structured = _run_case(case)
        acts = [str(x) for x in (structured.get("activities") or [])]
        mats = [str(x) for x in (structured.get("materials") or [])]
        probs = [str(x) for x in (structured.get("problems") or [])]
        opens = [str(x) for x in (structured.get("openItems") or [])]
        customer = str(structured.get("customerTalk") or "")
        summary = str(structured.get("summary") or "")

        if case.variant == "N":
            for forbidden in case.forbid_activities:
                if _contains_any(acts, forbidden, variant=case.variant):
                    failures.append(f"{case.name}: [P1] activity verboten -> {forbidden}")

        _check_p1(case, summary, mats, acts, failures)
        _check_p2(case, customer, summary, failures)
        _check_p3(case, probs, opens, failures)

    if failures:
        print("VIRTUAL-SPEECH-PRIORITY-P123-WAVE22-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:800]:
            print(" -", row)
        if len(failures) > 800:
            print(f" ... und {len(failures) - 800} weitere")
        return 1

    print("VIRTUAL-SPEECH-PRIORITY-P123-WAVE22-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    print("Trades: GaLaBau, Trockenbau, Fliesen, SHK, Hochbau, Tiefbau, Putz")
    print("Basisszenarien pro Gewerk: 10 (P1/P2/P3 Cross-Validierung)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
