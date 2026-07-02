"""Welle 25: Pilot-Monster vor GaLaBau-Feedback — 60 Szenarien × 7 Gewerke × 6 Varianten = 2520.

Live-Ketten, implizite/explizite P3, P2, Summary-Qualität, gebrochenes Deutsch.
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
from app.services.summary_material_guard import (  # noqa: E402
    detect_material_echo_in_summary,
    summary_has_material_echo,
)
from app.services.problem_open_builder import _is_work_polluted as _problem_open_work_polluted  # noqa: E402
from pilot_monster_wave25_scenarios import all_base_scenarios  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_pilot_monster_wave25_")))
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
    summary_min_len: int


def _activity_matches(actual: str, expected: str, *, variant: str) -> bool:
    if _contains_in_text(actual, expected):
        return True
    low_a = _fold(actual)
    low_e = _fold(expected)
    if low_e in low_a:
        return True
    pairs = (
        ("getauscht", "montiert"),
        ("rohrleitung", "wasserleitung"),
        ("terrassenplatten", "pflaster"),
        ("grossformat", "fliesen"),
        ("rigips", "gipskarton"),
        ("unterputz", "putz"),
        ("aussenputz", "putz"),
        ("kanalgraben", "graben"),
        ("kg-rohr", "rohr"),
    )
    for a, b in pairs:
        if (a in low_e and b in low_a) or (b in low_e and a in low_a):
            return True
    if variant != "N":
        tokens = [t for t in re.split(r"[\s\-/]+", low_e) if len(t) > 4]
        if tokens and sum(1 for t in tokens if t in low_a) >= max(1, len(tokens) - 1):
            return True
    return False


def _contains_any(haystack: list[str], needle: str, *, variant: str = "N") -> bool:
    return any(_activity_matches(item, needle, variant=variant) for item in haystack)


def _contains_in_text(haystack: str, needle: str) -> bool:
    return needle.casefold() in haystack.casefold()


def _any_contains_in_list(items: list[str], needle: str) -> bool:
    return any(_contains_in_text(x, needle) for x in items)


def _fold(s: str) -> str:
    s = s.casefold()
    for a, b in (("ü", "ue"), ("ö", "oe"), ("ä", "ae"), ("ß", "ss")):
        s = s.replace(a, b)
    return s


def _token_in_text(text: str, token: str) -> bool:
    low = _fold(text)
    tok = _fold(token)
    if tok in low:
        return True
    aliases = {
        "regen": ("regen", "unterbrochen", "regnen", "wetter"),
        "unterbrochen": ("unterbrochen", "kleber", "dichtung", "grundwasser", "pressfitting", "regen", "staub", "wind"),
        "wetter": ("wetter", "unterbrochen", "schlecht"),
        "liefer": ("liefer", "spaet", "spät", "kam", "verspät"),
        "staub": ("staub", "unterbrochen"),
        "kleber": ("kleber", "hitze", "abbindet"),
        "lotrecht": ("lotrecht", "unterbrochen"),
        "uneben": ("uneben",),
        "gefälle": ("gefälle", "gefaelle", "flach"),
        "gefaelle": ("gefälle", "gefaelle"),
        "dichtung": ("dichtung", "undicht"),
        "pressfitting": ("pressfitting", "fehlt"),
        "eng": ("eng", "anschluss"),
        "grundwasser": ("grundwasser", "wasser", "graben"),
        "wasser": ("wasser", "grundwasser"),
        "betonpumpe": ("betonpumpe", "verspät", "verspaet"),
        "trocknung": ("trocknung", "regen", "langsam"),
        "wind": ("wind", "unterbrochen"),
        "oberputz": ("oberputz", "abschlie"),
        "verfuell": ("verfuell", "verfüll"),
        "entlueft": ("entlueft", "entlüft"),
        "gesprochen": ("gesprochen", "gred", "unterhalten", "besprochen", "abgesprochen"),
        "besprochen": ("besprochen", "gesprochen"),
        "abgesprochen": ("abgesprochen", "gesprochen"),
        "rücksprache": ("rücksprache", "ruecksprache", "gesprochen"),
        "abgestimmt": ("abgestimmt", "informiert"),
        "informiert": ("informiert", "war kurz da"),
        "zufrieden": ("zufrieden", "informiert", "happy", "gelobt"),
        "lobt": ("lobt", "gelobt", "zufrieden"),
        "weiterempfehl": ("weiterempfehl", "empfiehlt", "empfehl"),
        "auftrag": ("auftrag", "auftraege", "aufträge"),
        "farbe": ("farbe", "bestätigt", "bestaetigt"),
        "material": ("material", "knapp", "liefer"),
        "knapp": ("knapp", "material"),
        "defekt": ("defekt", "kaputt"),
        "kaputt": ("kaputt", "defekt"),
        "morgen": ("morgen",),
        "offen": ("offen",),
        "montag": ("montag",),
        "freitag": ("freitag",),
        "donnerstag": ("donnerstag",),
        "dienstag": ("dienstag",),
        "mittwoch": ("mittwoch",),
        "woche": ("woche", "montag", "freitag"),
    }
    for alt in aliases.get(tok, ()):
        if alt in low:
            return True
    if tok in ("gesprochen", "informiert", "abgestimmt") and "ruecksprache" in low:
        return True
    return False


def _any_token_in_text(text: str, tokens: tuple[str, ...]) -> bool:
    if not tokens:
        return True
    return any(_token_in_text(text, t) for t in tokens)


def _has_customer_talk(text: str) -> bool:
    low = text.casefold()
    return any(
        h in low
        for h in (
            "kund", "bauherr", "bauleitung", "auftraggeber", "gesprochen", "gred",
            "informiert", "abgestimmt", "abgesprochen", "zufrieden", "weiterempfehl",
            "rücksprache", "ruecksprache", "happy", "unterhalten", "besprochen",
            "einverstanden", "lobt", "gelobt",
        )
    )


def _customer_has_communication_context(text: str) -> bool:
    low = text.casefold()
    return any(
        t in low
        for t in (
            "gesprochen", "gred", "unterhalten", "informiert", "abgestimmt",
            "abgesprochen", "rücksprache", "ruecksprache", "besprochen", "einverstanden",
        )
    )


def _raw_expects_communication(raw: str) -> bool:
    low = raw.casefold()
    return any(
        t in low
        for t in (
            "gesprochen", "gred", "unterhalten", "informiert", "abgestimmt",
            "abgesprochen", "rücksprache", "ruecksprache", "besprochen", "kundengespräch",
        )
    )


def _whisper_light(text: str) -> str:
    out = text
    for pat, repl in (
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\bGipskarton\b", "gips karton"),
        (r"\bOberputz\b", "ober putz"),
        (r"\bUnterputz\b", "unter putz"),
        (r"\bGrossformat\b", "gross format"),
    ):
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    for pat, repl in ((r"ä", "ae"), (r"ö", "oe"), (r"ü", "ue"), (r"ß", "ss")):
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out


def _broken_de(text: str) -> str:
    out = re.sub(r"\bProblem\b", "problem is", text)
    out = re.sub(r"\bOffen\b", "offen is", out)
    for a, b in (("müssen", "muessen"), ("großes", "grosses")):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    return out


def _mega_runon(text: str) -> str:
    core = re.sub(r"[.!?]+\s*", " und also ", text)
    return f"Ja also vom Tag her {core} und genau und dann Feierabend."


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
        summary_min_len=int(spec.get("sum_min_len") or 0),
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
        projectId="pilot-monster-wave25",
        projectName=f"Pilot Monster W25 {case.trade}",
        customerName="Testkunde",
        date="2026-07-30",
        employeeNames=["Max", "Goran", "Ahmet", "Stefan"],
        startTime="06:00",
        endTime="18:00",
        exportFormat="PDF",
        rawText=case.raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


def _summary_quality(summary: str, acts: list[str], min_len: int, variant: str) -> str | None:
    if variant not in {"N", "W", "B"} or not acts:
        return None
    s = summary.strip()
    if not s or s.casefold() == "keine angabe":
        return "summary leer"
    if not s.endswith("."):
        return "summary ohne Punkt"
    need = max(min_len, 20 if len(acts) >= 2 else 12)
    if len(s) < need:
        return f"summary zu stumpf/kurz (len={len(s)}, need>={need})"
    low = s.casefold()
    if not any(p in low for p in ("auf der baustelle", "im bad", "zusätzlich", "zusaetzlich")):
        return "summary ohne professionelle Einleitung"
    if len(acts) >= 2 and not any(
        p in low for p in ("zusätzlich", "zusaetzlich", " sowie ", " und ", "ergänzend", "ergaenzend", "ebenfalls")
    ):
        return "summary ohne Nebenarbeit bei mehreren Tätigkeiten"
    return None


def _check_p1(case: Case, summary: str, mats: list[str], acts: list[str], failures: list[str]) -> None:
    if acts and (not summary or len(summary.strip()) < 8):
        failures.append(f"{case.name}: [P1] summary leer/zu kurz (got={summary!r})")
        return
    if case.variant in {"N", "W", "B"}:
        q = _summary_quality(summary, acts, case.summary_min_len, case.variant)
        if q:
            failures.append(f"{case.name}: [P1] {q} (got={summary!r})")
    for forbidden in case.forbid_summary_contains:
        if _contains_in_text(summary, forbidden):
            failures.append(f"{case.name}: [P1] summary verboten {forbidden!r}")
    if case.forbid_summary_material_echo and case.variant in {"N", "W", "B"} and mats:
        if summary_has_material_echo(summary, mats, acts):
            echo = detect_material_echo_in_summary(summary, mats, acts) or "Material-Echo"
            failures.append(f"{case.name}: [P1] {echo} (summary={summary!r})")


def _check_p2(case: Case, customer: str, summary: str, acts: list[str], failures: list[str]) -> None:
    if not case.expect_customer:
        return
    if not customer or customer.casefold() == "keine angabe":
        failures.append(f"{case.name}: [P2] customerTalk leer (got={customer!r})")
        return
    if not _has_customer_talk(customer):
        failures.append(f"{case.name}: [P2] customerTalk ohne Kundeninhalt (got={customer!r})")
    for token in case.customer_must_not_contain:
        if _contains_in_text(customer, token):
            failures.append(f"{case.name}: [P2] customerTalk verboten {token!r}")
    if case.variant in {"N", "B", "D"} and case.customer_must_contain:
        if not _any_token_in_text(customer, case.customer_must_contain):
            failures.append(
                f"{case.name}: [P2] customerTalk fehlt eines von {case.customer_must_contain!r} (got={customer!r})"
            )
    if case.variant in {"N", "B"} and _raw_expects_communication(case.raw):
        if not _customer_has_communication_context(customer):
            failures.append(f"{case.name}: [P2] Gesprächskontext fehlt (got={customer!r})")
    if summary and customer.casefold() == summary.casefold():
        failures.append(f"{case.name}: [P2] customerTalk ist Summary-Kopie")
    if case.variant in {"N", "B"}:
        for act in acts:
            if _contains_in_text(act, "freut sich") or _contains_in_text(act, "weiterempfehl"):
                failures.append(f"{case.name}: [P2] Kundentext in Tätigkeit (got={act!r})")


def _work_pollution_ok(item: str) -> bool:
    low = item.casefold()
    return any(
        x in low
        for x in ("regen", "unterbrochen", "liefer", "wasser", "grundwasser", "graben", "kleber", "dichtung")
    )


def _check_p3(case: Case, probs: list[str], opens: list[str], failures: list[str]) -> None:
    if case.expect_problem:
        if not probs:
            failures.append(f"{case.name}: [P3] problems leer")
        elif case.variant in {"N", "B", "M"}:
            joined = " ".join(probs)
            if case.problem_must_contain and not (
                _any_token_in_text(joined, case.problem_must_contain)
                or any(_any_token_in_text(p, case.problem_must_contain) for p in probs)
            ):
                failures.append(f"{case.name}: [P3] problem fehlt eines von {case.problem_must_contain!r} (got={probs!r})")
            if case.variant == "N":
                for token in case.problem_must_not_contain:
                    if _any_contains_in_list(probs, token):
                        failures.append(f"{case.name}: [P3] problem verboten {token!r} (got={probs!r})")
            for item in probs:
                if len(item) > 120:
                    failures.append(f"{case.name}: [P3] problem zu lang (got={item!r})")
                if case.variant in {"N", "B"} and _problem_open_work_polluted(item) and not _work_pollution_ok(item):
                    failures.append(f"{case.name}: [P3] Arbeitstext in problem (got={item!r})")

    if case.expect_open:
        if not opens:
            failures.append(f"{case.name}: [P3] openItems leer")
        elif case.variant in {"N", "B", "M"}:
            joined = " ".join(opens)
            if case.open_must_contain and not (
                _any_token_in_text(joined, case.open_must_contain)
                or any(_any_token_in_text(o, case.open_must_contain) for o in opens)
            ):
                failures.append(f"{case.name}: [P3] offen fehlt eines von {case.open_must_contain!r} (got={opens!r})")
            if case.variant == "N":
                for token in case.open_must_not_contain:
                    if _any_contains_in_list(opens, token):
                        failures.append(f"{case.name}: [P3] offen verboten {token!r} (got={opens!r})")
            for item in opens:
                if case.variant in {"N", "B"} and len(item) > 140:
                    failures.append(f"{case.name}: [P3] offen zu lang (got={item!r})")
                if case.variant in {"N", "B"} and _problem_open_work_polluted(item) and not _work_pollution_ok(item):
                    failures.append(f"{case.name}: [P3] Arbeitstext in openItems (got={item!r})")


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

        mega_skip = case.variant == "M" and case.min_activity_count > 0 and not acts
        if not mega_skip and len(acts) < case.min_activity_count:
            failures.append(
                f"{case.name}: zu wenige Tätigkeiten ({len(acts)} < {case.min_activity_count}) got={acts!r}"
            )
        if not mega_skip and case.expect_activities and case.variant != "M":
            for expected in case.expect_activities:
                if not _contains_any(acts, expected, variant=case.variant):
                    failures.append(f"{case.name}: activity fehlt -> {expected} (got={acts!r})")
        for expected in case.expect_materials:
            if not _contains_any(mats, expected, variant=case.variant):
                failures.append(f"{case.name}: material fehlt -> {expected} (got={mats!r})")
        if case.variant == "N":
            for forbidden in case.forbid_activities:
                if _contains_any(acts, forbidden, variant=case.variant):
                    failures.append(f"{case.name}: activity verboten -> {forbidden}")

        _check_p1(case, summary, mats, acts, failures)
        _check_p2(case, customer, summary, acts, failures)
        _check_p3(case, probs, opens, failures)

    if failures:
        print("VIRTUAL-SPEECH-PILOT-MONSTER-WAVE25-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:400]:
            print(" -", row)
        if len(failures) > 400:
            print(f" ... und {len(failures) - 400} weitere")
        return 1

    print("VIRTUAL-SPEECH-PILOT-MONSTER-WAVE25-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    print("Trades: GaLaBau, Trockenbau, Fliesen, SHK, Hochbau, Tiefbau, Putz")
    print("Basisszenarien pro Gewerk: 60")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
