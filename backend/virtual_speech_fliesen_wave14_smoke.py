"""Welle 14: Fliesen-only — Herz-Nieren-Test für das komplette Gewerk.

Nur Fliesen: kurz/lang, Umgangssprache, ASR/Whisper, Dialekt, gebrochenes Deutsch,
Kundengespräch, Problem, Offen. Rein additiv — keine bestehenden Smoke-Dateien ändern.
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_fliesen_wave14_")))
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
            "meckert",
        )
    )


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ── Komplett-Tagesberichte mit Kunde/Problem/Offen ──
        BaseScenario(
            (
                "Im Bad erst Wandfliesen drauf geklebt dann Bodenfliesen verlegt und verfugt "
                "Abdichtung im Duschbereich gemacht Nivelliermasse gezogen Silikonfugen nachgezogen "
                "Kunde meckert wegen Farbe Problem Wand schief Offen Rest Silikon Donnerstag."
            ),
            (
                "Fliesen verlegt",
                "Fliesen verfugt",
                "Abdichtung hergestellt",
                "Nivelliermasse aufgetragen",
            ),
            expect_materials=("Fliesen",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            (
                "Morgens Wand grundiert Nivelliermasse aufgetragen 40 Quadratmeter Fliesen verlegt "
                "nachmittags verfugt Silikonfugen gezogen Bauleitung war da Problem Kleber knapp "
                "Offen Rest Fliesen Freitag."
            ),
            (
                "Grundierung aufgetragen",
                "Nivelliermasse aufgetragen",
                "Fliesen verlegt",
                "Fliesen verfugt",
            ),
            expect_materials=("Fliesen",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            (
                "Im Neubau Küche und Bad Fliesenkleber aufgezogen 28 Quadratmeter Wandfliesen geklebt "
                "Bodenfliesen verfugt Flexkleber gezogen Kunde informiert Problem Lieferung spät "
                "Offen Sockelfliesen nächste Woche."
            ),
            (
                "Fliesenkleber aufgetragen",
                "Fliesen verlegt",
                "Fliesen verfugt",
            ),
            expect_materials=("Fliesen",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        # ── Umgangssprache / Kurz ──
        BaseScenario(
            "30 Quadratmeter Fliesen gelegt fertig.",
            ("Fliesen verlegt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Bad Fliesen fertig gemacht.",
            ("Fliesen verlegt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Wandfliesen geklebt fertig.",
            ("Fliesen verlegt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Bodenfliesen verfugt Silikon gezogen.",
            ("Fliesen verfugt", "Silikonfugen silikoniert"),
        ),
        BaseScenario(
            "Fliesenkleber drauf gezogen fertig.",
            ("Fliesenkleber aufgetragen",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Abdichtung im Bad gemacht.",
            ("Abdichtung hergestellt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Nivelliermasse aufgetragen und trocken.",
            ("Nivelliermasse aufgetragen",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Grundierung auf die Wand aufgetragen.",
            ("Grundierung aufgetragen",),
            min_activity_count=1,
        ),
        # ── Ketten / formell ──
        BaseScenario(
            "Fliesenkleber aufgezogen Großformatfliesen verlegt Bodenablauf eingebaut Duschrinne gesetzt.",
            (
                "Fliesenkleber aufgetragen",
                "Großformatfliesen verlegt",
                "Bodenablauf eingebaut",
            ),
        ),
        BaseScenario(
            "Wandfliesen geklebt Bodenfliesen verfugt Flexkleber gezogen Naturstein verlegt.",
            (
                "Fliesen verlegt",
                "Fliesen verfugt",
                "Fliesenkleber aufgetragen",
                "Naturstein verlegt",
            ),
        ),
        BaseScenario(
            "Abdichtung hergestellt Fliesenkleber aufgetragen 25 Quadratmeter Großformatfliesen verlegt verfugt.",
            (
                "Abdichtung hergestellt",
                "Fliesenkleber aufgetragen",
                "Großformatfliesen verlegt",
                "Fliesen verfugt",
            ),
        ),
        BaseScenario(
            "Wand grundiert Nivelliermasse aufgetragen 35 Quadratmeter Fliesen verlegt verfugt Silikonfugen silikoniert.",
            (
                "Grundierung aufgetragen",
                "Nivelliermasse aufgetragen",
                "Fliesen verlegt",
                "Fliesen verfugt",
            ),
        ),
        BaseScenario(
            "Dusche komplett Abdichtung hergestellt Wandfliesen verlegt Bodenfliesen verlegt Fugen verfugt.",
            (
                "Abdichtung hergestellt",
                "Fliesen verlegt",
                "Fliesen verfugt",
            ),
        ),
        BaseScenario(
            "Feinsteinzeug verlegt 18 Quadratmeter fertig.",
            ("Fliesen verlegt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Mosaikfliesen gesetzt und verfugt.",
            ("Fliesen verlegt", "Fliesen verfugt"),
        ),
        # ── Gebrochenes Deutsch / Baustellen-Slang ──
        BaseScenario(
            "heute auf baustell ich hab gearbeitet 25 quadrat Fliesen.",
            ("Fliesen verlegt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "ich hab gemacht Fliesen verfugt und Silikon gezogen.",
            ("Fliesen verfugt", "Silikonfugen silikoniert"),
        ),
        BaseScenario(
            "ich hab gemacht Abdichtung und Bodenablauf eingebaut.",
            ("Abdichtung hergestellt", "Bodenablauf eingebaut"),
        ),
        BaseScenario(
            "hamma Flexkleber gezogen und Fliesen drauf geklebt.",
            ("Fliesenkleber aufgetragen", "Fliesen verlegt"),
        ),
        BaseScenario(
            "ich machen 60 quadrat Großformat Fliesen verlegt.",
            ("Großformatfliesen verlegt",),
            min_activity_count=1,
        ),
        # ── Hotel / Großprojekt ──
        BaseScenario(
            (
                "Im Hotel acht Bäder Wandfliesen und Bodenfliesen verlegt Abdichtung im Duschbereich "
                "Nivelliermasse gezogen Silikonfugen nachgezogen Bauherr zufrieden "
                "Problem Wasserstand zu hoch Offen letztes Bad Montag."
            ),
            (
                "Fliesen verlegt",
                "Abdichtung hergestellt",
                "Nivelliermasse aufgetragen",
            ),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        # ── Reparatur / Einzelarbeiten ──
        BaseScenario(
            "Defekte Fliese ausgetauscht und neu verfugt.",
            ("Fliesen repariert", "Fliesen verfugt"),
        ),
        BaseScenario(
            "Einzelne Wandfliese repariert Fuge nachgezogen.",
            ("Fliesen repariert", "Fliesen verfugt"),
        ),
        BaseScenario(
            "Bodenablauf eingebaut und Duschrinne gesetzt Abdichtung drumherum gemacht.",
            ("Bodenablauf eingebaut", "Abdichtung hergestellt"),
        ),
        BaseScenario(
            "Naturstein Terrasse 22 Quadratmeter verlegt Fugen verfugt.",
            ("Naturstein verlegt", "Fliesen verfugt"),
        ),
        BaseScenario(
            "Fliesenkleber aufgetragen Wandfliesen verlegt Deckefliesen angebracht.",
            ("Fliesenkleber aufgetragen", "Fliesen verlegt"),
        ),
        BaseScenario(
            "Kundengespräch gehabt Fliesenmuster gewählt Problem Feuchte im Altbau Offen Rest nächste Woche.",
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
        (r"\bFliesenkleber\b", "fliesen kleber"),
        (r"\bFlexkleber\b", "flex kleber"),
        (r"\bGroßformatfliesen\b", "gross format fliesen"),
        (r"\bGroßformat\b", "gross format"),
        (r"\bNivelliermasse\b", "nivellier masse"),
        (r"\bAbdichtung\b", "ab dichtung"),
        (r"\bSilikonfugen\b", "silikon fugen"),
        (r"\bBodenablauf\b", "boden ablauf"),
        (r"\bDuschrinne\b", "dusch rinne"),
        (r"\bWandfliesen\b", "wand fliesen"),
        (r"\bBodenfliesen\b", "boden fliesen"),
        (r"\bMosaikfliesen\b", "mosaik fliesen"),
        (r"\bFeinsteinzeug\b", "fein steinzeug"),
        (r"\bGrundierung\b", "grundierung"),
        (r"\bFlüssigfolie\b", "fluessig folie"),
        (r"\bFugenmörtel\b", "fugen moertel"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bverlegt\b", "ver legt"),
        (r"\bverfugt\b", "ver fugt"),
        (r"\bgeklebt\b", "ge klebt"),
        (r"\baufgetragen\b", "auf getragen"),
        (r"\baufgezogen\b", "auf gezogen"),
        (r"\bsilikoniert\b", "silikon iert"),
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
        ("verfugt", "ver fugt"),
        ("aufgetragen", "auf getragen"),
        ("aufgezogen", "auf gezogen"),
        ("gesprochen", "gred"),
        ("Problem:", "problem is"),
        ("Offen:", "offen is"),
        ("verlegt", "ver legt"),
        ("geklebt", "ge klebt"),
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
                    name=f"Fliesen_{idx:03d}_{tag}",
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
        projectId="fl-wave14",
        projectName="Fliesen Welle 14",
        customerName="Testkunde",
        date="2026-07-20",
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
        print("VIRTUAL-SPEECH-FLIESEN-WAVE14-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-FLIESEN-WAVE14-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
