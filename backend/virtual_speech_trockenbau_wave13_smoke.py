"""Welle 13: Trockenbau-only — Herz-Nieren-Test für das komplette Gewerk.

Nur Trockenbau: kurz/lang, Umgangssprache, ASR/Whisper, Dialekt, gebrochenes Deutsch,
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

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_trockenbau_wave13_")))
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
        )
    )


def _base_scenarios() -> list[BaseScenario]:
    return [
        # ── Komplett-Tagesbericht mit Kunde/Problem/Offen ──
        BaseScenario(
            (
                "Morgens erst die Ständerwerksprofile an die Wand festgeschraubt dann die Dämmmatte "
                "reingepackt danach die GK Platten bzw Gipskartonplatten dran montiert "
                "Fugen gespachtelt und die Decke abgehängt Bauleitung war da Problem Lieferung "
                "kam spät Offen Revisionsklappe morgen noch."
            ),
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Fugen verspachtelt", "Decke abgehängt"),
            expect_materials=("Gipskartonplatten",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        BaseScenario(
            (
                "CW Profile und UW Profile an die Decke und Wand geschraubt Mineralwolle eingesetzt "
                "zwei Lagen Rigips verschraubt Fugenspachtel drüber gezogen Akustikdecke runtergehängt "
                "Brandschutzplatten beplankt Trockenbauwand zu gemacht."
            ),
            (
                "Ständerwerk montiert",
                "Dämmung eingebaut",
                "Gipskartonplatten montiert",
                "Fugen verspachtelt",
                "Decke abgehängt",
                "Trockenbauwand geschlossen",
            ),
        ),
        BaseScenario(
            (
                "Im Bürotrakt Ständerwerk montiert Steinwolle Dämmung eingebaut Gipskartonplatten "
                "beplankt Decke abgehängt mit CD Profilen und Abhängern Fugen verspachtelt "
                "Revisionsklappe eingebaut Kunde informiert Problem Schrauben knapp "
                "Offen Brandschutzplatten Rest liefern Donnerstag."
            ),
            (
                "Ständerwerk montiert",
                "Dämmung eingebaut",
                "Gipskartonplatten montiert",
                "Decke abgehängt",
                "Fugen verspachtelt",
                "Revisionsklappe eingebaut",
            ),
            expect_materials=("Gipskartonplatten",),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        # ── Umgangssprache / Kurz ──
        BaseScenario(
            "Ständerwerk angebaut Dämmung reingemacht Rigipsplatten festgeschraubt Decke montiert.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Decke abgehängt"),
        ),
        BaseScenario(
            "Profile montiert Gipskarton beplankt Fugen verspachtelt Brandschutz beplankt.",
            ("Ständerwerk montiert", "Gipskartonplatten montiert", "Fugen verspachtelt"),
        ),
        BaseScenario("GK Platten montiert fertig.", ("Gipskartonplatten montiert",), min_activity_count=1),
        BaseScenario("Rigips dran gemacht.", ("Gipskartonplatten montiert",), min_activity_count=1),
        BaseScenario("Decke abgehangen Fugen gespachtelt.", ("Decke abgehängt", "Fugen verspachtelt")),
        BaseScenario(
            "Schnellbauschrauben reingedreht UW CW Profile gesetzt Dämmung eingebaut und Wand geschlossen.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Trockenbauwand geschlossen"),
        ),
        BaseScenario("Knaufplatten verschraubt fertig.", ("Gipskartonplatten montiert",), min_activity_count=1),
        BaseScenario("Wand zugemacht.", ("Trockenbauwand geschlossen",), min_activity_count=1),
        # ── Einzelaktivitäten ──
        BaseScenario("Heute Akustikdecke eingebaut.", ("Akustikdecke eingebaut",), min_activity_count=1),
        BaseScenario("Revisionsklappe montiert fertig.", ("Revisionsklappe eingebaut",), min_activity_count=1),
        BaseScenario("Brandschutzwand hergestellt.", ("Brandschutzwand hergestellt",), min_activity_count=1),
        BaseScenario(
            "Heute die Decke abgehängt und die Trockenbauwand geschlossen.",
            ("Decke abgehängt", "Trockenbauwand geschlossen"),
        ),
        # ── Ketten / formell ──
        BaseScenario(
            "Ständerwerk montiert Dämmung eingebaut Gipskartonplatten beplankt Fugen verspachtelt Decke abgehängt.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Fugen verspachtelt", "Decke abgehängt"),
        ),
        BaseScenario(
            "Heute haben wir das Ständerwerk montiert die Dämmung eingebaut und die Gipskartonplatten beplankt.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert"),
        ),
        BaseScenario(
            "Ständerwerk mit CW und UW Profilen montiert Steinwolle eingebaut Gipskartonplatten montiert Decke abgehängt Fugen verspachtelt.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Decke abgehängt", "Fugen verspachtelt"),
        ),
        BaseScenario(
            "Brandschutzwand hergestellt Akustikdecke eingebaut Revisionsklappe montiert.",
            ("Brandschutzwand hergestellt", "Akustikdecke eingebaut", "Revisionsklappe eingebaut"),
        ),
        # ── Gebrochenes Deutsch / Baustellen-Slang ──
        BaseScenario(
            "heute ich hab gemacht Ständerwerk und Dämmung eingebaut.",
            ("Ständerwerk montiert", "Dämmung eingebaut"),
        ),
        BaseScenario(
            "ich machen Decke abgehängt und Gipskarton montiert.",
            ("Decke abgehängt", "Gipskartonplatten montiert"),
        ),
        BaseScenario(
            "ich hab gemacht Ständerwerk und Dämmung eingebaut und Gipskarton montiert.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert"),
        ),
        BaseScenario(
            "ich hab gemacht Akustikdecke eingebaut und Revisionsklappe montiert.",
            ("Akustikdecke eingebaut", "Revisionsklappe eingebaut"),
        ),
        BaseScenario(
            "hamma die Profile festgemacht Mineralwolle reingepackt und Rigips drauf geschraubt.",
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert"),
        ),
        # ── Spachtel / Schleifen ──
        BaseScenario(
            "Fugenspachtel aufgetragen Fugen verspachtelt und geschliffen.",
            ("Fugen verspachtelt",),
            min_activity_count=1,
        ),
        BaseScenario(
            "Heute Trockenbauwand geschlossen Fugen verspachtelt Spachtelarbeiten durchgeführt.",
            ("Trockenbauwand geschlossen", "Fugen verspachtelt"),
        ),
        # ── Hotel / Großprojekt ──
        BaseScenario(
            (
                "Im Hotel Flur zwanzig Meter Ständerwerk gesetzt Dämmung eingebaut beidseitig Rigips "
                "montiert Decke abgehängt Fugen verspachtelt Brandschutz F30 erfüllt "
                "Bauherr war zufrieden Problem Lärm von unten Offen letzte Revisionsklappe Montag."
            ),
            (
                "Ständerwerk montiert",
                "Dämmung eingebaut",
                "Gipskartonplatten montiert",
                "Decke abgehängt",
                "Fugen verspachtelt",
            ),
            expect_problem=True,
            expect_open=True,
            expect_customer=True,
        ),
        # ── Doppelständerwand ──
        BaseScenario(
            (
                "Doppelständerwand aufgebaut beide Seiten beplankt Mineralwolle zweifach eingebaut "
                "Schallschutz F90 Trockenbauwand geschlossen."
            ),
            ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert", "Trockenbauwand geschlossen"),
        ),
        # ── Nur Decke / Reparatur ──
        BaseScenario(
            "Abhangdecke runtergehängt alte Platten raus neue GK Platten rein Fugen nachgespachtelt.",
            ("Decke abgehängt", "Gipskartonplatten montiert", "Fugen verspachtelt"),
        ),
        BaseScenario(
            "Kundengespräch gehabt Rigipsplatten nachbestellt Problem Feuchte im Altbau Offen Rest nächste Woche.",
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
        (r"\bStänderwerk\b", "staender werk"),
        (r"\bStänderwerksprofile\b", "staender werks profile"),
        (r"\bGipskartonplatten\b", "gips karton platten"),
        (r"\bGipskarton\b", "gips karton"),
        (r"\bGK Platten\b", "gk platten"),
        (r"\bGK-Platten\b", "gk platten"),
        (r"\bRigips\b", "ri gips"),
        (r"\bRigipsplatten\b", "ri gips platten"),
        (r"\bFugenspachtel\b", "fugen spachtel"),
        (r"\bMineralwolle\b", "mineral wolle"),
        (r"\bSteinwolle\b", "stein wolle"),
        (r"\bAkustikdecke\b", "akustik decke"),
        (r"\bBrandschutzwand\b", "brand schutz wand"),
        (r"\bBrandschutzplatten\b", "brand schutz platten"),
        (r"\bRevisionsklappe\b", "revision sklappe"),
        (r"\bSchnellbauschrauben\b", "schnell bau schrauben"),
        (r"\bTrockenbauwand\b", "trocken bau wand"),
        (r"\bAbhänger\b", "ab haenger"),
        (r"\bCD-Profile\b", "cd pro file"),
        (r"\bCW Profile\b", "cw pro file"),
        (r"\bUW Profile\b", "uw pro file"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bprofile\b", "pro file"),
        (r"\bverschraubt\b", "ver schraubt"),
        (r"\bverspachtelt\b", "ver spachtelt"),
        (r"\babgehängt\b", "abge haengt"),
        (r"\bgeschraubt\b", "ge schraubt"),
        (r"\bgeschlossen\b", "ge schlossen"),
        (r"\bbeplankt\b", "be plankt"),
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
        ("geschraubt", "fest gemacht"),
        ("festgeschraubt", "fest gemacht"),
        ("gespachtelt", "zu gemacht"),
        ("verspachtelt", "zu gemacht"),
        ("montiert", "montiert"),
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
                    name=f"Trockenbau_{idx:03d}_{tag}",
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
        projectId="tb-wave13",
        projectName="Trockenbau Welle 13",
        customerName="Testkunde",
        date="2026-07-15",
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
        print("VIRTUAL-SPEECH-TROCKENBAU-WAVE13-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}")
        for row in failures[:500]:
            print(" -", row)
        if len(failures) > 500:
            print(f" ... und {len(failures) - 500} weitere")
        return 1

    print("VIRTUAL-SPEECH-TROCKENBAU-WAVE13-SMOKE: OK")
    print(f"Total cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
