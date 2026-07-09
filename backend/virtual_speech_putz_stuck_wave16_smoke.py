"""Welle 16: Putz & Stuck — JSON Engine-Welle A (WDVS kleben/dübeln, Glätten/Filzen).

30 Basisszenarien × 6 Varianten = 180 Smoke-Fälle. Rein additiv.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from main import StructureReportBody, api_structure_report  # noqa: E402
from app.services.tenant_storage import TenantStore  # noqa: E402
from putz_stuck_wave16_scenarios import all_base_scenarios  # noqa: E402
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_putz_stuck_wave16_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class Case:
    name: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...] = field(default_factory=tuple)
    forbid_activities: tuple[str, ...] = field(default_factory=tuple)
    expect_problem: bool = False
    expect_open: bool = False
    expect_customer: bool = False
    min_activity_count: int = 0


def _contains_any(haystack: list[str], needle: str) -> bool:
    n = needle.casefold()
    return any(n in str(item).casefold() for item in haystack)


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
        )
    )


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bWDVS\b", "wdvs"),
        (r"\bDämmung\b", "dämmung"),
        (r"\bDämmplatten\b", "dämmplatten"),
        (r"\bTellerdübel\b", "teller dübel"),
        (r"\bArmierungsgewebe\b", "armierungs gewebe"),
        (r"\bKlebe- und Armierungsmörtel\b", "klebe und armierungsmörtel"),
        (r"\bFeinputz\b", "feinputz"),
        (r"\bGipsputz\b", "gipsputz"),
        (r"\bSilikatputz\b", "silikatputz"),
        (r"\bFilzbrett\b", "filz brett"),
        (r"\bGlättkelle\b", "glätt kelle"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bgedübelt\b", "ge dübelt"),
        (r"\bgeklebt\b", "ge klebt"),
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
        ("Heute", "heute"),
        ("Problem:", "problem is"),
        ("Offen:", "offen is"),
        ("gedübelt", "gedübelt"),
        ("aufgetragen", "auf getragen"),
        ("eingebettet", "ein gebettet"),
        ("gesprochen", "gred"),
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
    idx = 1
    for spec in all_base_scenarios():
        acts = tuple(spec.get("acts") or ())
        min_count = spec["min_act"] if spec.get("min_act") is not None else len(acts)
        for tag, fn in builders:
            cases.append(
                Case(
                    name=f"PutzStuck16_{idx:03d}_{tag}",
                    raw=fn(spec["raw"]),
                    expect_activities=acts,
                    expect_materials=tuple(spec.get("mats") or ()),
                    forbid_activities=tuple(spec.get("forbid_acts") or ()),
                    expect_problem=bool(spec.get("problem")),
                    expect_open=bool(spec.get("open_")),
                    expect_customer=bool(spec.get("customer")),
                    min_activity_count=min_count,
                )
            )
            idx += 1
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="ps-wave16",
        projectName="Putz Stuck Welle 16",
        customerName="Testkunde",
        date="2026-07-09",
        employeeNames=["Max", "Goran", "Ahmet", "Stefan", "Murat", "Dennis"],
        startTime="06:00",
        endTime="18:00",
        exportFormat="PDF",
        rawText=case.raw,
    )
    return (api_structure_report(body, store=_STORE).get("structured") or {})


def main() -> int:
    os.environ["OPENAI_API_KEY"] = ""
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

        if len(acts) < case.min_activity_count:
            failures.append(
                f"{case.name}: zu wenige Tätigkeiten ({len(acts)} < {case.min_activity_count}) got={acts!r}"
            )
        for expected in case.expect_activities:
            if not _contains_any(acts, expected):
                failures.append(f"{case.name}: activity fehlt -> {expected} (got={acts!r})")
        for expected in case.expect_materials:
            if not _contains_any(mats, expected):
                failures.append(f"{case.name}: material fehlt -> {expected} (got={mats!r})")
        for forbidden in case.forbid_activities:
            if _contains_any(acts, forbidden):
                failures.append(f"{case.name}: activity verboten -> {forbidden}")

        if acts and (not summary or len(summary.strip()) < 10):
            failures.append(f"{case.name}: summary leer/zu kurz (got={summary!r})")

        if case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer")
        if case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer")
        if case.expect_customer and not _has_customer_talk(customer):
            failures.append(f"{case.name}: customerTalk fehlt (got={customer!r})")

    if failures:
        print("VIRTUAL-SPEECH-PUTZ-STUCK-WAVE16-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print(f"VIRTUAL-SPEECH-PUTZ-STUCK-WAVE16-SMOKE: OK ({len(cases)}/{len(cases)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
