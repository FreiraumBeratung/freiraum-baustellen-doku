"""Welle 21: Putz & Stuck — 300 Basisszenarien × 6 = 1800 Smoke-Fälle.

Breite Abdeckung Stuck+Putz, Ketten, POB, gebrochenes DE, Vorschläge/Material.
Rein additiv zu Welle 20.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.problem_open_builder import _is_work_polluted as _problem_open_work_polluted  # noqa: E402
from app.services.summary_material_guard import summary_has_material_echo  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from putz_stuck_wave21_scenarios import all_base_scenarios  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_putz_stuck_wave21_")))
_STORE = TenantStore(str(uuid.uuid4()))

_LAYER_MAT_NAMES = (
    "oberputz",
    "unterputz",
    "grundputz",
    "innenputz",
    "außenputz",
    "aussenputz",
    "sockelputz",
    "kratzputz",
    "reibputz",
    "sanierputz",
    "altputz",
)


@dataclass(frozen=True)
class Case:
    name: str
    variant: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...]
    expect_machine_hours: tuple[str, ...]
    expect_suggestions: tuple[str, ...]
    forbid_activities: tuple[str, ...]
    forbid_suggestions: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool
    min_activity_count: int
    prob_must: tuple[str, ...]
    prob_not: tuple[str, ...]
    open_must: tuple[str, ...]
    open_not: tuple[str, ...]
    cust_must: tuple[str, ...]
    cust_not: tuple[str, ...]
    mat_echo: bool
    sum_qty: tuple[str, ...]
    forbid_layer_mats: bool


def _contains_any(haystack: list[str], needle: str, *, variant: str = "N") -> bool:
    n = needle.casefold()
    if any(n in str(item).casefold() for item in haystack):
        return True
    if "armierungsmörtel" in n or "armierungsmoertel" in n:
        return any(
            "armierungs" in str(item).casefold()
            and ("mörtel" in str(item).casefold() or "moertel" in str(item).casefold())
            for item in haystack
        )
    if variant in {"W", "H"}:
        tokens = [t for t in re.split(r"[\s\-/]+", n) if len(t) > 3]
        if tokens:
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
            "weiterempfehl",
            "rücksprache",
            "ruecksprache",
            "kundengespräch",
            "kundengespraech",
            "unterhalten",
            "einverstanden",
            "termin",
        )
    )


def _is_generic_layer_material(mat: str) -> bool:
    low = str(mat).casefold().strip()
    low = re.sub(r"^\d+(?:[.,]\d+)?\s*(?:m²|m2|qm²|qm2|quadratmeter)\s+", "", low)
    low = re.sub(r"\s+aufgetragen\s*$", "", low)
    if low in _LAYER_MAT_NAMES:
        return True
    for layer in _LAYER_MAT_NAMES:
        if low == layer or low.startswith(layer + " "):
            return True
    return False


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bWDVS\b", "wdvs"),
        (r"\bUnterputz\b", "unter putz"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bAltputz\b", "alt putz"),
        (r"\bGrundputz\b", "grund putz"),
        (r"\bInnenputz\b", "innen putz"),
        (r"\bAußenputz\b", "außen putz"),
        (r"\bAussenputz\b", "aussen putz"),
        (r"\bSanierputz\b", "sanier putz"),
        (r"\bSockelputz\b", "sockel putz"),
        (r"\bReibputz\b", "reib putz"),
        (r"\bKratzputz\b", "kratz putz"),
        (r"\bArmierungsgewebe\b", "armierungs gewebe"),
        (r"\bArmierungsmörtel\b", "armierungs moertel"),
        (r"\bGrundierung\b", "grundierung"),
        (r"\bSchimmel\b", "schim mel"),
        (r"\bGipsputz\b", "gipsputz"),
        (r"\bKalkputz\b", "kalkputz"),
        (r"\bFeinputz\b", "feinputz"),
        (r"\bSilikatputz\b", "silikatputz"),
        (r"\bSilikonharzputz\b", "silikonharzputz"),
        (r"\bKalkzementputz\b", "kalkzementputz"),
        (r"\bLehmputz\b", "lehmputz"),
        (r"\bTellerdübel\b", "tellerdübel"),
        (r"\bGlättkelle\b", "glätt kelle"),
        (r"\bFilzbrett\b", "filz brett"),
        (r"\bZahntraufel\b", "zahn traufel"),
        (r"\bPutzmaschine\b", "putzmaschine"),
        (r"\bKartätsche\b", "kartätsche"),
        (r"\bHaftbrücke\b", "haft brücke"),
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\bqm²\b", "qm"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\baufgetragen\b", "auf getragen"),
        (r"\baufgebracht\b", "auf gebracht"),
        (r"\bgeschliffen\b", "ge schliffen"),
        (r"\bgedübelt\b", "ge dübelt"),
        (r"\beingebettet\b", "ein gebettet"),
        (r"\bglätten\b", "glä tten"),
        (r"\bfilziert\b", "fil ziert"),
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
        ("Problem:", "problem is"),
        ("Offen:", "offen is"),
        ("gesprochen", "gred"),
        ("aufgetragen", "auf getragen"),
        ("eingebettet", "ein gebettet"),
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
    return f"Ja also vom Tag her {core} und Feierabend."


def _build_cases() -> list[Case]:
    builders: list[tuple[str, Callable[[str], str]]] = [
        ("N", lambda t: t),
        ("W", _whisper_light),
        ("H", _whisper_hard),
        ("B", _broken_de),
        ("D", _dialect_de),
        ("M", _mega_runon),
    ]
    cases: list[Case] = []
    idx = 1
    for spec in all_base_scenarios():
        acts = tuple(spec.get("acts") or ())
        min_count = spec["min_act"] if spec.get("min_act") is not None else len(acts)
        for tag, fn in builders:
            cases.append(
                Case(
                    name=f"PutzStuck21_{idx:03d}_{tag}",
                    variant=tag,
                    raw=fn(spec["raw"]),
                    expect_activities=acts,
                    expect_materials=tuple(spec.get("mats") or ()),
                    expect_machine_hours=tuple(spec.get("mach") or ()),
                    expect_suggestions=tuple(spec.get("sugs") or ()),
                    forbid_activities=tuple(spec.get("forbid_acts") or ()),
                    forbid_suggestions=tuple(spec.get("forbid_sugs") or ()),
                    expect_problem=bool(spec.get("problem")),
                    expect_open=bool(spec.get("open_")),
                    expect_customer=bool(spec.get("customer")),
                    min_activity_count=min_count,
                    prob_must=tuple(spec.get("prob_must") or ()),
                    prob_not=tuple(spec.get("prob_not") or ()),
                    open_must=tuple(spec.get("open_must") or ()),
                    open_not=tuple(spec.get("open_not") or ()),
                    cust_must=tuple(spec.get("cust_must") or ()),
                    cust_not=tuple(spec.get("cust_not") or ()),
                    mat_echo=bool(spec.get("mat_echo")),
                    sum_qty=tuple(spec.get("sum_qty") or ()),
                    forbid_layer_mats=bool(spec.get("forbid_layer_mats")),
                )
            )
            idx += 1
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="ps-wave21",
        projectName="Putz Stuck Welle 21",
        customerName="Testkunde",
        date="2026-07-11",
        employeeNames=["Max", "Goran", "Ahmet", "Stefan", "Murat", "Dennis"],
        startTime="06:00",
        endTime="17:30",
        exportFormat="PDF",
        rawText=case.raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


def _suggestion_satisfied(suggestions: list[str], expected: str) -> bool:
    if _contains_any(suggestions, expected):
        return True
    low = expected.casefold()
    if "dübel benutzt" in low or "duebel benutzt" in low:
        return any("dübel benutzt" in str(s).casefold() or "duebel benutzt" in str(s).casefold() for s in suggestions)
    return False


def _check_pob(case: Case, probs: list[str], opens: list[str], failures: list[str]) -> None:
    if case.expect_problem:
        if not probs:
            failures.append(f"{case.name}: problems leer")
        elif case.variant in {"N", "B", "M"}:
            joined = " ".join(probs)
            for token in case.prob_must:
                if not _any_contains_in_list(probs, token) and not _contains_in_text(joined, token):
                    failures.append(f"{case.name}: problem fehlt {token!r} (got={probs!r})")
            if case.variant == "N":
                for token in case.prob_not:
                    if _any_contains_in_list(probs, token):
                        failures.append(f"{case.name}: problem verboten {token!r} (got={probs!r})")
            for item in probs:
                if _problem_open_work_polluted(item):
                    failures.append(f"{case.name}: Arbeitstext in problem (got={item!r})")

    if case.expect_open:
        if not opens:
            failures.append(f"{case.name}: openItems leer")
        elif case.variant in {"N", "B", "M"}:
            joined = " ".join(opens)
            for token in case.open_must:
                if not _any_contains_in_list(opens, token) and not _contains_in_text(joined, token):
                    failures.append(f"{case.name}: offen fehlt {token!r} (got={opens!r})")
            if case.variant == "N":
                for token in case.open_not:
                    if _any_contains_in_list(opens, token):
                        failures.append(f"{case.name}: offen verboten {token!r} (got={opens!r})")
            for item in opens:
                if _problem_open_work_polluted(item):
                    failures.append(f"{case.name}: Arbeitstext in openItems (got={item!r})")


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
    cases = _build_cases()
    failures: list[str] = []

    for case in cases:
        structured = _run_case(case)
        acts = [str(x) for x in (structured.get("activities") or [])]
        mats = [str(x) for x in (structured.get("materials") or [])]
        sugs = [str(x) for x in (structured.get("materialSuggestions") or [])]
        machine_hours = [str(x) for x in (structured.get("machineHours") or [])]
        probs = [str(x) for x in (structured.get("problems") or [])]
        opens = [str(x) for x in (structured.get("openItems") or [])]
        customer = str(structured.get("customerTalk") or "")
        summary = str(structured.get("summary") or "")

        if len(acts) < case.min_activity_count:
            skip_min = (
                (case.variant in {"W", "H"} and not acts)
                or (case.variant == "M" and len(acts) >= max(1, case.min_activity_count - 2))
            )
            if not skip_min:
                failures.append(
                    f"{case.name}: zu wenige Tätigkeiten ({len(acts)} < {case.min_activity_count}) got={acts!r}"
                )
        if case.min_activity_count > 0:
            if case.variant in {"W", "H", "B", "M"}:
                if case.variant in {"W", "H"} and not acts:
                    pass
                else:
                    matched = sum(
                        1 for expected in case.expect_activities
                        if _contains_any(acts, expected, variant=case.variant)
                    )
                    if matched < case.min_activity_count:
                        failures.append(
                            f"{case.name}: zu wenige passende Tätigkeiten ({matched} < {case.min_activity_count}) "
                            f"expect={case.expect_activities!r} got={acts!r}"
                        )
            else:
                for expected in case.expect_activities:
                    if not _contains_any(acts, expected, variant=case.variant):
                        failures.append(f"{case.name}: activity fehlt -> {expected} (got={acts!r})")
            for expected in case.expect_materials:
                if not _contains_any(mats, expected, variant=case.variant):
                    failures.append(f"{case.name}: material fehlt -> {expected} (got={mats!r})")
        for expected in case.expect_machine_hours:
            if not _contains_any(machine_hours, expected, variant=case.variant):
                failures.append(f"{case.name}: maschinenstunden fehlen -> {expected} (got={machine_hours!r})")

        if case.variant in {"N", "B"}:
            for expected in case.expect_suggestions:
                if not _suggestion_satisfied(sugs, expected):
                    failures.append(f"{case.name}: suggestion fehlt -> {expected} (got={sugs!r})")
            for forbidden in case.forbid_suggestions:
                if _contains_any(sugs, forbidden):
                    failures.append(f"{case.name}: suggestion verboten -> {forbidden} (got={sugs!r})")

        for forbidden in case.forbid_activities:
            if _contains_any(acts, forbidden, variant=case.variant):
                failures.append(f"{case.name}: activity verboten -> {forbidden}")

        if acts and case.min_activity_count > 0 and (not summary or len(summary.strip()) < 8):
            failures.append(f"{case.name}: summary leer/zu kurz (got={summary!r})")

        if case.sum_qty and case.variant in {"N", "B", "M"}:
            for token in case.sum_qty:
                if not _contains_in_text(summary, token):
                    failures.append(f"{case.name}: summary Menge fehlt {token!r} (got={summary!r})")

        if case.forbid_layer_mats and case.variant in {"N", "B"}:
            bad = [m for m in mats if _is_generic_layer_material(m)]
            if bad:
                failures.append(f"{case.name}: Putzschicht-Dublette in Materialien {bad!r} (got={mats!r})")

        if case.mat_echo and case.variant == "N" and mats and summary_has_material_echo(summary, mats, acts):
            failures.append(f"{case.name}: Material-Echo in summary (got={summary!r})")

        _check_pob(case, probs, opens, failures)

        if case.expect_customer and case.variant in {"N", "B", "M"}:
            if not _has_customer_talk(customer):
                failures.append(f"{case.name}: customerTalk fehlt (got={customer!r})")
            else:
                for token in case.cust_must:
                    if not _contains_in_text(customer, token):
                        failures.append(f"{case.name}: kunde fehlt {token!r} (got={customer!r})")
                if case.variant == "N":
                    for token in case.cust_not:
                        if _contains_in_text(customer, token):
                            failures.append(f"{case.name}: kunde verboten {token!r} (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-PUTZ-STUCK-WAVE21-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print(f"VIRTUAL-SPEECH-PUTZ-STUCK-WAVE21-SMOKE: OK ({len(cases)}/{len(cases)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
