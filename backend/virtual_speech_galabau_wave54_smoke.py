"""Welle 54: GaLaBau-Schutznetz — 100 Basen × 5 = 500 Fälle.

Gartenalltag, Whisper-Patzer, Vorschläge (Beton), keine erfundenen Stunden.
Rein additiv — bestehende Wellen und Screenshots unangetastet.
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

os.environ["OPENAI_API_KEY"] = ""
os.environ["FREIRAUM_AI_STRUCTURING"] = ""

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from smoke_isolation import isolate_smoke_data  # noqa: E402

isolate_smoke_data(Path(tempfile.mkdtemp(prefix="freiraum_galabau_wave54_")))

from app.services.tenant_storage import TenantStore  # noqa: E402
from galabau_wave54_scenarios import all_base_scenarios  # noqa: E402
from main import StructureReportBody, api_structure_report  # noqa: E402

_STORE = TenantStore(str(uuid.uuid4()))


@dataclass(frozen=True)
class Case:
    name: str
    variant: str
    raw: str
    act_tokens: tuple[str, ...]
    mat_tokens: tuple[str, ...]
    sugs: tuple[str, ...]
    forbid_acts: tuple[str, ...]
    forbid_mats: tuple[str, ...]
    forbid_sugs: tuple[str, ...]
    forbid_hours: bool
    mach: tuple[str, ...]
    mach_sug: tuple[str, ...]
    expect_problem: bool
    expect_open: bool
    expect_customer: bool
    min_act: int


def _hay(items: list[str]) -> str:
    return " | ".join(str(x).casefold() for x in items)


def _has_tok(haystack: str, token: str) -> bool:
    t = token.casefold()
    h = haystack.casefold()
    if t == "l-stein":
        return "l-stein" in h or "l stein" in h or "lstein" in h
    if t == "rasenkantenstein":
        return "rasenkantenstein" in h or "randstein" in h
    if t == "kantenstein":
        return "kantenstein" in h or "randstein" in h or "rasenkantenstein" in h
    if t == "gemäht":
        return "gemäht" in h or "gemaht" in h or "gemaeht" in h
    if t == "gedüngt":
        return "gedüngt" in h or "geduengt" in h or "gedungt" in h
    if t == "vertikutiert":
        return "vertikutiert" in h or "vertikuti" in h
    if t == "keramik":
        return "keramik" in h
    if t == "geotextil":
        return "geotextil" in h or "vlies" in h
    if t in {"fahrradständer", "fahrradstaender"}:
        return "fahrradständer" in h or "fahrradstaender" in h or "fahrradstander" in h
    if t == "grünschnitt":
        return "grünschnitt" in h or "gruenschnitt" in h or "grunschnitt" in h
    if t == "rüttel":
        return "rüttel" in h or "ruettel" in h or "ruttel" in h or "abgerüttelt" in h or "abgeruettelt" in h
    if t == "wassertonne":
        return "wassertonne" in h or "regentonne" in h
    if t == "regentonne":
        return "regentonne" in h or "wassertonne" in h
    if t == "tropf":
        return "tropf" in h or "bewässer" in h or "bewaesser" in h
    if t in {"mähkante", "maehkante"}:
        return "mähkante" in h or "maehkante" in h or "corten" in h
    if t == "rasengitter":
        return "rasengitter" in h
    if t == "stelzlager":
        return "stelzlager" in h or "keramik" in h
    if t == "gully":
        return "gully" in h or "hofablauf" in h or "ablauf" in h
    if t == "hofablauf":
        return "hofablauf" in h or "gully" in h or "ablauf" in h
    if t == "pflaster":
        return "pflaster" in h or "verbundstein" in h
    if t == "aushub":
        return "aushub" in h or "graben" in h
    if t == "geogitter":
        return "geogitter" in h
    if t == "pflanzen":
        return "pflanz" in h or "hortensien" in h or "thuja" in h
    if t == "planum":
        return "planum" in h
    if t == "dumper":
        return "dumper" in h
    if t == "bewässer":
        return "bewässer" in h or "bewaesser" in h or "tropf" in h
    return t in h


def _hut_demolished_without_leisten(acts: list[str]) -> bool:
    for act in acts:
        low = str(act or "").casefold()
        if ("gartenhütte demontiert" in low or "gartenhuette demontiert" in low) and "holzleiste" not in low:
            return True
    return False


def _has_customer(text: str) -> bool:
    low = text.casefold()
    return any(
        x in low
        for x in (
            "kund",
            "bauherr",
            "gesprochen",
            "gred",
            "zufrieden",
            "informiert",
            "abgestimmt",
            "bestätigt",
            "bestaetigt",
            "meckert",
        )
    )


def _whisper_light(text: str) -> str:
    out = text
    pairs = (
        (r"\bRasenkantensteine\b", "rasen kanten steine"),
        (r"\bSpritzschutz\b", "spritz schutz"),
        (r"\bKantensteine\b", "kanten steine"),
        (r"\bGeotextil\b", "geo textil"),
        (r"\bEinkehrmaterial\b", "einkehr material"),
        (r"\bHolzleisten\b", "holz leisten"),
        (r"\bGartenhütte\b", "garten hütte"),
        (r"\bIlex\b", "ilex"),
        (r"\bBauschutt\b", "bau schutt"),
        (r"\bHandstampfer\b", "hand stampfer"),
        (r"\bKettensäge\b", "ketten saege"),
        (r"\bKantholz\b", "kant holz"),
        (r"\bGummihammer\b", "gummi hammer"),
        (r"\bPalisaden\b", "palisaden"),
        (r"\bSchotter\b", "schot ter"),
        (r"\bQuadratmeter\b", "quadrat meter"),
        (r"\blaufende Meter\b", "lauf ende meter"),
        (r"\bGabionen\b", "gabio nen"),
        (r"\bHochbeet\b", "hoch beet"),
        (r"\bMutterboden\b", "mutter boden"),
        (r"\bOberboden\b", "ober boden"),
        (r"\bGrünschnitt\b", "grün schnitt"),
        (r"\bDoppelstabmattenzaun\b", "doppel stab matten zaun"),
        (r"\bTropfbewässerung\b", "tropf bewaesserung"),
        (r"\bTrockenmauer\b", "trocken mauer"),
        (r"\bFindlinge\b", "find linge"),
        (r"\bTeichfolie\b", "teich folie"),
        (r"\bUnkrautvlies\b", "unkraut vlies"),
        (r"\bWurzelstock\b", "wurzel stock"),
        (r"\bSandkasten\b", "sand kasten"),
        (r"\bGartentor\b", "garten tor"),
        (r"\bHofablauf\b", "hof ablauf"),
        (r"\bWaschbetonplatten\b", "wasch beton platten"),
        (r"\bGranitpflaster\b", "granit pflaster"),
        (r"\bFrostschutz\b", "frost schutz"),
        (r"\bNoppenbahn\b", "noppen bahn"),
        (r"\bFahrradständer\b", "fahrrad staender"),
        (r"\bRüttelplatte\b", "ruettel platte"),
        (r"\bMinibagger\b", "mini bagger"),
        (r"\bTiefbordsteine\b", "tief bord steine"),
        (r"\bFugensand\b", "fugen sand"),
        (r"\bEdelsplitt\b", "edel splitt"),
        (r"\bRegentonne\b", "regen tonne"),
        (r"\bLiguster\b", "liguster"),
        (r"\bKirschlorbeer\b", "kirsch lorbeer"),
        (r"\bRasengittersteine\b", "rasen gitter steine"),
        (r"\bSitzmauer\b", "sitz mauer"),
        (r"\bSickerschacht\b", "sicker schacht"),
        (r"\bVersenkregner\b", "versenk regner"),
        (r"\bMähkante\b", "maeh kante"),
        (r"\bFormschnitt\b", "form schnitt"),
        (r"\bFeuerstelle\b", "feuer stelle"),
        (r"\bZaunpfosten\b", "zaun pfosten"),
        (r"\bStelzlager\b", "stelz lager"),
        (r"\bGartenhaus\b", "garten haus"),
        (r"\bÖkopflaster\b", "oeko pflaster"),
        (r"\bBetonsteinpflaster\b", "beton stein pflaster"),
        (r"\bBlockstufen\b", "block stufen"),
        (r"\bCortenstahl\b", "corten stahl"),
        (r"\bDrainagesplitt\b", "drainage splitt"),
        (r"\bVerbundsteine\b", "verbund steine"),
        (r"\bZisterne\b", "zisterne"),
        (r"\bHortensien\b", "hortensien"),
        (r"\bThujahecke\b", "thuja hecke"),
        (r"\bHolzsichtschutzzaun\b", "holz sichtschutz zaun"),
        (r"\bGeogitter\b", "geo gitter"),
        (r"\bQuellstein\b", "quell stein"),
        (r"\bSchwimmteich\b", "schwimm teich"),
        (r"\bFiltervlies\b", "filter vlies"),
        (r"\bSpielrasen\b", "spiel rasen"),
        (r"\bWPC-Zaunfelder\b", "wpc zaun felder"),
    )
    for pat, repl in pairs:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out.lower()


def _whisper_hard(text: str) -> str:
    out = _whisper_light(text)
    extra = (
        (r"\bverlegt\b", "ver legt"),
        (r"\bgesetzt\b", "ge setzt"),
        (r"\bgeschnitten\b", "ge schnitten"),
        (r"\bverdichtet\b", "ver dichtet"),
        (r"\beingearbeitet\b", "ein gearbeitet"),
        (r"\bentsorgt\b", "ent sorgt"),
        (r"\bdemontiert\b", "de montiert"),
        (r"\bangelegt\b", "an gelegt"),
        (r"\bgefüllt\b", "ge fuellt"),
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
        ("gesprochen", "gred"),
        ("Problem", "problem is"),
        ("Offen", "offen is"),
    ):
        out = out.replace(a, b)
    return out


def _dialect_de(text: str) -> str:
    out = text
    out = re.sub(r"\bhaben wir\b", "hamma", out, flags=re.IGNORECASE)
    out = re.sub(r"\bgesprochen\b", "gred", out, flags=re.IGNORECASE)
    return out


def _build_cases() -> list[Case]:
    builders: list[tuple[str, Callable[[str], str]]] = [
        ("N", lambda t: t),
        ("W", _whisper_light),
        ("H", _whisper_hard),
        ("B", _broken_de),
        ("D", _dialect_de),
    ]
    cases: list[Case] = []
    idx = 1
    for spec in all_base_scenarios():
        acts = tuple(spec.get("acts") or ())
        min_act = int(spec.get("min_act") if spec.get("min_act") is not None else max(1, len(acts)))
        for tag, fn in builders:
            cases.append(
                Case(
                    name=f"GaLaBau54_{idx:03d}_{tag}",
                    variant=tag,
                    raw=fn(str(spec["raw"])),
                    act_tokens=acts,
                    mat_tokens=tuple(spec.get("mats") or ()),
                    sugs=tuple(spec.get("sugs") or ()),
                    forbid_acts=tuple(spec.get("forbid_acts") or ()),
                    forbid_mats=tuple(spec.get("forbid_mats") or ()),
                    forbid_sugs=tuple(spec.get("forbid_sugs") or ()),
                    forbid_hours=bool(spec.get("forbid_hours")),
                    mach=tuple(spec.get("mach") or ()),
                    mach_sug=tuple(spec.get("mach_sug") or ()),
                    expect_problem=bool(spec.get("problem")),
                    expect_open=bool(spec.get("open_")),
                    expect_customer=bool(spec.get("customer")),
                    min_act=min_act,
                )
            )
            idx += 1
    return cases


def _run(raw: str) -> dict:
    body = StructureReportBody(
        projectId="gb-wave54",
        projectName="Gartenanlage",
        customerName="Kunde",
        date="2026-10-14",
        employeeNames=["Max"],
        startTime="07:00",
        endTime="16:00",
        exportFormat="PDF",
        rawText=raw,
    )
    return api_structure_report(body, store=_STORE).get("structured") or {}


def main() -> int:
    cases = _build_cases()
    if len(cases) != 500:
        print(f"VIRTUAL-SPEECH-GALABAU-WAVE54-SMOKE: FEHLER case-count {len(cases)} != 500")
        return 1
    failures: list[str] = []

    for case in cases:
        structured = _run(case.raw)
        acts = [str(x) for x in (structured.get("activities") or [])]
        mats = [str(x) for x in (structured.get("materials") or [])]
        sugs = [str(x) for x in (structured.get("materialSuggestions") or [])]
        hours = [str(x) for x in (structured.get("machineHours") or [])]
        mach_sugs = [str(x) for x in (structured.get("machineSuggestions") or [])]
        probs = [str(x) for x in (structured.get("problems") or [])]
        opens = [str(x) for x in (structured.get("openItems") or [])]
        talk = str(structured.get("customerTalk") or "")
        summary = str(structured.get("summary") or "")
        act_h = _hay(acts)
        mat_h = _hay(mats)
        sug_h = _hay(sugs)

        strict = case.variant in {"N", "B"}

        if strict and case.min_act > 0 and len(acts) < case.min_act:
            failures.append(f"{case.name}: zu wenige Tätigkeiten ({len(acts)} < {case.min_act}) got={acts!r}")

        if strict:
            for tok in case.act_tokens:
                if not _has_tok(act_h, tok):
                    failures.append(f"{case.name}: activity-token fehlt -> {tok} (got={acts!r})")
            for tok in case.mat_tokens:
                if not _has_tok(mat_h, tok):
                    failures.append(f"{case.name}: material-token fehlt -> {tok} (got={mats!r})")
            for tok in case.sugs:
                if not _has_tok(sug_h, tok):
                    failures.append(f"{case.name}: vorschlag fehlt -> {tok} (got={sugs!r})")
            for tok in case.forbid_sugs:
                if _has_tok(sug_h, tok):
                    failures.append(f"{case.name}: vorschlag verboten -> {tok} (got={sugs!r})")
            for tok in case.mach_sug:
                if not _has_tok(_hay(mach_sugs), tok):
                    failures.append(f"{case.name}: maschinen-vorschlag fehlt -> {tok} (got={mach_sugs!r})")

        for tok in case.forbid_acts:
            if tok.casefold() in {"gartenhütte demontiert", "gartenhuette demontiert"}:
                if _hut_demolished_without_leisten(acts):
                    failures.append(f"{case.name}: activity verboten -> {tok} (got={acts!r})")
                continue
            if _has_tok(act_h, tok):
                failures.append(f"{case.name}: activity verboten -> {tok} (got={acts!r})")
        if strict:
            for tok in case.forbid_mats:
                if _has_tok(mat_h, tok):
                    failures.append(f"{case.name}: material verboten -> {tok} (got={mats!r})")

        for expected in case.mach:
            if not _has_tok(_hay(hours), expected):
                failures.append(f"{case.name}: maschinenstunden fehlen -> {expected} (got={hours!r})")
        if case.forbid_hours and hours:
            failures.append(f"{case.name}: keine Stunden erfinden ({hours!r})")

        if acts and case.min_act > 0 and len(summary.strip()) < 12:
            failures.append(f"{case.name}: summary zu kurz (got={summary!r})")

        if strict and case.expect_problem and not probs:
            failures.append(f"{case.name}: problems leer")
        if strict and case.expect_open and not opens:
            failures.append(f"{case.name}: openItems leer")
        if strict and case.expect_customer and not _has_customer(talk):
            failures.append(f"{case.name}: customerTalk fehlt (got={talk!r})")

    if failures:
        print("VIRTUAL-SPEECH-GALABAU-WAVE54-SMOKE: FEHLER")
        print(f"Total cases: {len(cases)}  failures: {len(failures)}")
        for row in failures[:140]:
            print(" -", row)
        if len(failures) > 140:
            print(f" ... und {len(failures) - 140} weitere")
        return 1

    print(f"VIRTUAL-SPEECH-GALABAU-WAVE54-SMOKE: OK ({len(cases)}/{len(cases)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
