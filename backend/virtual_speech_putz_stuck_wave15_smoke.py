"""Welle 15: Putz & Stuck — Herz-Nieren-Test für beide verwandten Gewerke.

Putz und Stuck gemeinsam: kurz/lang, Umgangssprache, ASR/Whisper, Dialekt,
gebrochenes Deutsch, Kundengespräch, Problem, Offen. Rein additiv.
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
from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_putz_stuck_wave15_")))
_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class BaseScenario:
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...] = field(default_factory=tuple)
    forbid_activities: tuple[str, ...] = field(default_factory=tuple)
    expect_problem: bool = False
    expect_open: bool = False
    expect_customer: bool = False
    min_activity_count: int | None = None


@dataclass(frozen=True)
class Case:
    name: str
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...]
    forbid_activities: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool
    min_activity_count: int


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


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ── Putz: Komplett-Tagesberichte ──
        BaseScenario(
            (
                "Also heute früh erst den alten Putz abgetragen dann die Wand geschliffen "
                "danach grundiert Unterputz aufgetragen während der Unterputz trocknete "
                "Bauleitung kurz da Problem Feuchte im Mauerwerk Offen Rest Decke morgen "
                "nach dem Kundengespräch Oberputz aufgetragen und Feierabend."
            ),
            (
                "Altputz entfernt",
                "Wand geschliffen",
                "Grundierung aufgetragen",
                "Unterputz aufgetragen",
                "Oberputz aufgetragen",
            ),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            (
                "Altputz entfernt Schimmel beseitigt Sanierputz aufgebracht "
                "Unterputz nachgearbeitet und Oberputz aufgetragen."
            ),
            (
                "Altputz entfernt",
                "Schimmel beseitigt",
                "Sanierputz aufgebracht",
                "Unterputz aufgetragen",
                "Oberputz aufgetragen",
            ),
            expect_materials=("Sanierputz",),
        ),
        BaseScenario(
            (
                "Im Neubau Treppenhaus Grundputz aufgetragen Innenputz verarbeitet "
                "Sockelputz gemacht Kunde informiert Problem Gerüst spät "
                "Offen Oberputz nächste Woche."
            ),
            (
                "Grundputz aufgetragen",
                "Innenputz aufgetragen",
                "Sockelputz aufgetragen",
            ),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        # ── Putz: Kurz / Umgangssprache ──
        BaseScenario(
            "40 Quadratmeter Unterputz aufgetragen fertig.",
            ("Unterputz aufgetragen",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Oberputz gemacht fertig.",
            ("Oberputz aufgetragen",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Altputz runter und Wand geschliffen.",
            ("Altputz entfernt", "Wand geschliffen"),
        ),
        BaseScenario(
            "Wand grundiert und geschliffen.",
            ("Wand geschliffen", "Grundierung aufgetragen"),
        ),
        BaseScenario(
            "Schimmel weg gemacht Sanierputz drauf.",
            ("Schimmel beseitigt", "Sanierputz aufgebracht"),
        ),
        BaseScenario(
            "Grundputz aufgetragen Innenputz aufgebracht Sockelputz verarbeitet Reibputz aufgetragen.",
            (
                "Grundputz aufgetragen",
                "Innenputz aufgetragen",
                "Sockelputz aufgetragen",
                "Reibputz aufgetragen",
            ),
        ),
        BaseScenario(
            "Unterputz aufgetragen und Oberputz gemacht.",
            ("Unterputz aufgetragen", "Oberputz aufgetragen"),
        ),
        BaseScenario(
            "Außenputz an der Fassade aufgebracht.",
            ("Außenputz aufgetragen",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Kratzputz aufgetragen Reibputz nachgearbeitet.",
            ("Kratzputz aufgetragen", "Reibputz aufgetragen"),
        ),
        # ── Stuck: WDVS / Fassade ──
        BaseScenario(
            (
                "WDVS Platten angeklebt Armierungsgewebe eingebettet Reibputz drauf gemacht "
                "Sockelleiste stuckiert Kunde informiert Problem Kleber knapp Offen Rest morgen."
            ),
            ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen"),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            "Fassade gedämmt Gewebe reingemacht Außenputz aufgetragen Gesims stuckiert.",
            ("WDVS ausgeführt", "Fassadenarmierung ausgeführt", "Außenputz aufgetragen"),
        ),
        BaseScenario(
            "WDVS montiert Armierung eingebaut Reibputz aufgetragen.",
            ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen"),
        ),
        BaseScenario(
            "Stuckarbeiten gemacht.",
            ("Stuckarbeiten durchgeführt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Armierungsgewebe eingebettet fertig.",
            ("Armierung ausgeführt",),
            min_activity_count=1,
        ),
        # ── Gebrochenes Deutsch / Slang ──
        BaseScenario(
            "heute ich hab gemacht Unterputz und Oberputz.",
            ("Unterputz aufgetragen", "Oberputz aufgetragen"),
        ),
        BaseScenario(
            "heute auf baustell ich hab gearbeitet 45 quadrat Unterputz.",
            ("Unterputz aufgetragen",),
            min_activity_count=1,
        ),
        BaseScenario(
            "hamma Altputz runter und neu verputzt.",
            ("Altputz entfernt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "ich hab gemacht Schimmel weg und Sanierputz drauf.",
            ("Schimmel beseitigt", "Sanierputz aufgebracht"),
        ),
        BaseScenario(
            "ich machen WDVS und Armierung reingemacht.",
            ("WDVS ausgeführt", "Armierung ausgeführt"),
        ),
        # ── Großprojekt / Hotel ──
        BaseScenario(
            (
                "An der Hotel-Fassade WDVS komplett montiert Armierungsgewebe eingebettet "
                "Reibputz aufgetragen Außenputz strukturiert Bauherr zufrieden "
                "Problem Wind nachts Offen letzte Etage Montag."
            ),
            (
                "WDVS ausgeführt",
                "Armierung ausgeführt",
                "Reibputz aufgetragen",
                "Außenputz aufgetragen",
            ),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        # ── Ketten / formell ──
        BaseScenario(
            (
                "Heute haben wir den alten Putz abgetragen die Wand geschliffen "
                "die Wand danach grundiert den Unterputz aufgetragen und den Oberputz aufgetragen."
            ),
            (
                "Altputz entfernt",
                "Wand geschliffen",
                "Grundierung aufgetragen",
                "Unterputz aufgetragen",
                "Oberputz aufgetragen",
            ),
        ),
        BaseScenario(
            "Innenputz im Flur aufgetragen Decke gespachtelt.",
            ("Innenputz aufgetragen",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Putz abgetragen Wand geschliffen Grundierung drauf Unterputz gezogen.",
            (
                "Altputz entfernt",
                "Wand geschliffen",
                "Grundierung aufgetragen",
                "Unterputz aufgetragen",
            ),
        ),
        BaseScenario(
            "50 Quadratmeter Oberputz verarbeitet fertig.",
            ("Oberputz aufgetragen",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Sanierputz aufgebracht und getrocknet.",
            ("Sanierputz aufgebracht",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Sockelleiste stuckiert Gesims angebracht.",
            ("Stuckarbeiten durchgeführt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Kundengespräch gehabt Putzmuster gewählt Problem Feuchte im Keller Offen Rest nächste Woche.",
            (),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
            min_activity_count=0,
        ),
    ]


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
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
        (r"\bArmierung\b", "armierung"),
        (r"\bWDVS\b", "wdvs"),
        (r"\bGrundierung\b", "grundierung"),
        (r"\bSchimmel\b", "schim mel"),
        (r"\bFassade\b", "fas sade"),
        (r"\bGesims\b", "ge sims"),
        (r"\bStuckleiste\b", "stuck leiste"),
        (r"\bStuckarbeiten\b", "stuck arbeiten"),
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
        (r"\bangeschliffen\b", "an ge schliffen"),
        (r"\beingebettet\b", "ein gebettet"),
        (r"\bangeklebt\b", "an geklebt"),
        (r"\bgedämmt\b", "ge daemmt"),
        (r"\bgedämmt\b", "ge daemmt"),
        (r"\bstuckiert\b", "stuck iert"),
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
        ("aufgetragen", "auf getragen"),
        ("aufgebracht", "auf gebracht"),
        ("geschliffen", "ge schliffen"),
        ("abgetragen", "ab getragen"),
        ("eingebettet", "ein gebettet"),
        ("gesprochen", "gred"),
        ("Problem:", "problem is"),
        ("Offen:", "offen is"),
    ):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    out = re.sub(r"\bKunde\b", "Kund", out, flags=re.IGNORECASE)
    out = re.sub(r"\bdann\b", "denn", out, flags=re.IGNORECASE, count=6)
    return out


def _mega_runon(text: str) -> str:
    core = re.sub(r"[.!?]+\s*", " und also ", text)
    return (
        f"Ja also vom Tag her {core} und genau und dann Feierabend "
        f"und morgen machen wir den Rest wenn Material da ist."
    )


def _build_cases() -> list[Case]:
    bases = _base_scenarios()
    cases: list[Case] = []
    idx = 1
    builders = [
        ("N", lambda t: t),
        ("W", _whisper_light),
        ("H", _whisper_hard),
        ("B", _broken_de),
        ("D", _dialect_de),
        ("M", _mega_runon),
    ]
    for tag, builder in builders:
        for base in bases:
            raw = builder(base.raw)
            min_count = base.min_activity_count if base.min_activity_count is not None else len(base.expect_activities)
            cases.append(
                Case(
                    name=f"PutzStuck_{idx:03d}_{tag}",
                    raw=raw,
                    expect_activities=base.expect_activities,
                    expect_materials=base.expect_materials,
                    forbid_activities=base.forbid_activities,
                    expect_problem=base.expect_problem,
                    expect_open=base.expect_open,
                    expect_customer=base.expect_customer,
                    min_activity_count=min_count,
                )
            )
            idx += 1
    return cases


def _run_case(case: Case) -> dict:
    body = StructureReportBody(
        projectId="ps-wave15",
        projectName="Putz Stuck Welle 15",
        customerName="Testkunde",
        date="2026-07-25",
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
        print("VIRTUAL-SPEECH-PUTZ-STUCK-WAVE15-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-PUTZ-STUCK-WAVE15-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
