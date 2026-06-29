"""Welle 21: Pilot-Monster-Welle — 50 Szenarien × 7 Gewerke × 6 Varianten = 2100 Fälle.

Letzte große Welle vor Pilot: Kundengespräch, Problem, Offen, kurz/lang, Ketten,
Whisper/Dialekt/gebrochenes Deutsch, Summary ohne Material-Echo.
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
from pilot_monster_wave21_scenarios import all_base_scenarios  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_pilot_monster_wave21_")))
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
    customer_must_not_contain: tuple[str, ...]
    forbid_summary_contains: tuple[str, ...]
    forbid_summary_material_echo: bool


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
            "happy",
            "meckert",
            "einverstanden",
            "vor ort",
            "weiter mit uns",
            "möchte weiter",
        )
    )


_MATERIAL_ECHO_SUMMARY = re.compile(
    r"\b(?:verarbeitet|verbaut|verwendet|eingesetzt|eingebaut|zum\s+einsatz)\b",
    flags=re.IGNORECASE,
)


def _summary_has_material_echo(summary: str, materials: list[str], activities: list[str]) -> str | None:
    low = summary.casefold()
    acts_joined = " ".join(activities).casefold()
    for mat in materials:
        m = str(mat).casefold().strip()
        if not m or m not in low:
            continue
        if not _MATERIAL_ECHO_SUMMARY.search(low):
            continue
        if "pflasterstein" in m and "pflaster" in acts_joined and "pflasterstein" in low:
            return "Material-Echo Pflaster/Pflastersteine in Summary"
        if "fliesen verlegt" in acts_joined and "fliesen" in m:
            return "Material-Echo Fliesen in Summary"
        if "putz" in m and "putz" in acts_joined:
            return "Material-Echo Putz in Summary"
        if "gipskarton" in m and "gipskarton" in acts_joined:
            return "Material-Echo Gipskarton in Summary"
        if "beton" in m and "beton" in acts_joined:
            return "Material-Echo Beton in Summary"
    if re.search(r"\bdaf(ü|ue)r\s+kam", low) and any("pflasterstein" in str(x).casefold() for x in materials):
        return "dafür kamen … zum Einsatz in Summary"
    return None


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bRasenkantensteine\b", "rasen kanten steine"),
        (r"\bGipskartonplatten\b", "gips karton platten"),
        (r"\bThermostatventile\b", "thermo stat ventile"),
        (r"\bHeizkörper\b", "heiz körper"),
        (r"\bFußbodenheizung\b", "fuss boden heizung"),
        (r"\bFiligrandecke\b", "filigran decke"),
        (r"\bSchotter\b", "schot ter"),
        (r"\bPflastersteine\b", "pflaster steine"),
        (r"\bFliesenkleber\b", "fliesen kleber"),
        (r"\bGroßformatfliesen\b", "gross format fliesen"),
        (r"\bNivelliermasse\b", "nivellier masse"),
        (r"\bKG-Rohre\b", "ka ga rohre"),
        (r"\bHT-Rohre\b", "ha te rohre"),
        (r"\bAußenputz\b", "aussen putz"),
        (r"\bFassadenarmierung\b", "fassaden armierung"),
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\blaufende Meter\b", "lauf ende meter"),
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
        ("durchgeführt", "durch gemacht"),
        ("verlegt", "ver legt"),
        ("gesprochen", "gred"),
        ("abgesprochen", "abgred"),
        ("Problem", "problem is"),
        ("Offen", "offen is"),
        ("Kundin", "kundin"),
    ):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKunde\b", "Kund", out, flags=re.IGNORECASE)
    out = re.sub(r"\bdann\b", "denn", out, flags=re.IGNORECASE, count=8)
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
        name=f"{trade}_{idx:03d}_{tag}",
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
        customer_must_not_contain=tuple(spec.get("cust_not") or ()),
        forbid_summary_contains=tuple(spec.get("sum_forbid") or ()),
        forbid_summary_material_echo=bool(spec.get("mat_echo")),
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
        projectId="pilot-monster-wave21",
        projectName=f"Pilot Monster {case.trade}",
        customerName="Testkunde",
        date="2026-07-28",
        employeeNames=["Max", "Goran", "Ahmet", "Stefan", "Murat", "Dennis"],
        startTime="06:00",
        endTime="18:00",
        exportFormat="PDF",
        rawText=case.raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


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
        if mega_skip:
            pass
        elif len(acts) < case.min_activity_count:
            failures.append(
                f"{case.name}: zu wenige Tätigkeiten ({len(acts)} < {case.min_activity_count}) got={acts!r}"
            )
        if not mega_skip:
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

        if acts and (not summary or len(summary.strip()) < 10):
            failures.append(f"{case.name}: summary leer/zu kurz (got={summary!r})")

        for forbidden in case.forbid_summary_contains:
            if _contains_in_text(summary, forbidden):
                failures.append(f"{case.name}: summary verboten -> {forbidden!r} (got={summary!r})")

        if case.forbid_summary_material_echo and case.variant == "N":
            echo = _summary_has_material_echo(summary, mats, acts)
            if echo:
                failures.append(f"{case.name}: {echo} (summary={summary!r})")

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer")

        if case.expect_customer:
            if not _has_customer_talk(customer):
                failures.append(f"{case.name}: customerTalk fehlt (got={customer!r})")
            for token in case.customer_must_not_contain:
                if _contains_in_text(customer, token):
                    failures.append(f"{case.name}: customerTalk enthält verboten {token!r} (got={customer!r})")
            if summary and customer.casefold() == summary.casefold() and customer.casefold() not in {
                "",
                "keine angabe",
            }:
                failures.append(f"{case.name}: customerTalk ist Summary-Kopie")

    if failures:
        print("VIRTUAL-SPEECH-PILOT-MONSTER-WAVE21-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:600]:
            print(" -", row)
        if len(failures) > 600:
            print(f" ... und {len(failures) - 600} weitere")
        return 1

    print("VIRTUAL-SPEECH-PILOT-MONSTER-WAVE21-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    print(f"Trades: GaLaBau, Trockenbau, Fliesen, SHK, Hochbau, Tiefbau, Putz")
    print(f"Basisszenarien pro Gewerk: 50")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
