"""Generator Pilot Real-Speech Welle 50 — 50 Basisszenarien aus echten Diktat-Mustern."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "pilot_real_speech_wave50_scenarios.py"
TARGET = 50
SITE = "Schmitz Außenanlage"


def s(raw: str, **kw) -> dict:
    d = dict(
        raw=raw,
        acts=(),
        act_tokens=(),
        mats=(),
        mat_tokens=(),
        mach=(),
        mach_sug=(),
        sugs=(),
        forbid_acts=(),
        forbid_mats=(),
        problem=False,
        open_=False,
        customer=False,
        min_act=0,
        prob_must=(),
        prob_not=(),
        open_must=(),
        open_not=(),
        cust_must=(),
        sum_qty=(),
        sum_not=(),
        forbid_future_pflaster=False,
        strict=False,
    )
    d.update(kw)
    return d


def all_base_scenarios() -> list[dict]:
    return [
        # ── Gold: Pilot 1:1 validiert ──
        s(
            (
                "Heute haben wir den Untergrund frei gebaggert dann 5 m³ Schotter null 32 eingebaut "
                "danach drei Kubik Split zwei Fünfer eingebaut und dann 40 m² Pflaster eingebaut"
            ),
            strict=True,
            acts=("Graben ausgehoben", "Baggerarbeiten durchgeführt"),
            mats=("Schotter", "Splitt", "Pflastersteine"),
            mach_sug=("Bagger",),
            sum_qty=("5",),
            min_act=2,
        ),
        s(
            (
                "Heute haben wir den Graben frei gebaggert dann mit 5 m³ Schotter null 32 verdichtet "
                "und danach zwei Kubik Split zwei Fünfer verarbeitet und morgen müssen wir dann "
                "30 m² Pflaster legen"
            ),
            strict=True,
            acts=("Graben ausgehoben", "Baggerarbeiten durchgeführt"),
            mats=("Schotter", "Splitt", "Pflastersteine"),
            open_=True,
            open_must=("morgen", "pflaster", "offen"),
            forbid_acts=("30 m² Pflaster verlegt", "Morgen müssen"),
            forbid_future_pflaster=True,
            sum_not=("pflaster verlegt",),
            mach_sug=("Bagger",),
            min_act=2,
        ),
        s(
            (
                "Heute haben wir den Untergrund frei gebaggert damit 3,5 m³ Schotter null 32 verdichtet "
                "dann haben wir drei Kubik Split zwei Fünfer eingebaut leider mussten wir die Arbeiten "
                "abrechnen weil es stark angefangen zu regnen dementsprechend verschiebt sich das "
                "Pflastern auf morgen"
            ),
            strict=True,
            acts=("Baggerarbeiten durchgeführt",),
            mats=("Schotter", "Splitt"),
            problem=True,
            open_=True,
            prob_must=("regen",),
            open_must=("morgen", "pflaster", "verschoben"),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                "Heute haben wir den Untergrund frei gebaggert dann 5 m³ Schotter null 32 eingebaut "
                "danach drei Kubik Split zwei Fünfer eingebaut"
            ),
            act_tokens=("schotter", "splitt", "graben", "bagger"),
            mat_tokens=("schotter", "splitt"),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                "Graben frei gebaggert mit 3,5 m³ Schotter 0/32 verdichtet zwei Kubik Splitt 2/5 "
                "eingebaut Bagger war den ganzen Tag da."
            ),
            act_tokens=("schotter", "splitt", "bagger"),
            mat_tokens=("schotter", "splitt"),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                "Heute Untergrund frei gebaggert 5 Kubik Schotter null 32 eingebaut "
                "danach 3 Kubik Split zwei Fünfer und 40 Quadratmeter Pflaster eingebaut"
            ),
            act_tokens=("schotter", "splitt", "pflaster", "bagger"),
            mat_tokens=("schotter", "splitt"),
            min_act=1,
        ),
        s(
            "Heute haben wir den Graben ausgehoben dann 5 m³ Schotter eingebaut und Splitt 2/5 mm eingebaut",
            act_tokens=("schotter", "splitt", "graben"),
            mat_tokens=("schotter", "splitt"),
            min_act=1,
        ),
        s(
            "Erdarbeiten heute: Untergrund gebaggert Schotterplanum mit 4 m³ Schotter 0/32 verdichtet Splitt 2/5 eingebaut.",
            act_tokens=("schotter", "splitt", "bagger"),
            mat_tokens=("schotter", "splitt"),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        # ── Morgen / Offen ──
        s(f"morgen müssen wir noch 25 m² Pflaster legen {SITE}", open_=True, open_must=("morgen", "pflaster", "offen"), forbid_future_pflaster=True),
        s(
            f"Heute Schotter eingebaut und Splitt eingebaut dementsprechend verschiebt sich das Pflastern auf morgen {SITE}",
            act_tokens=("schotter", "splitt"),
            mat_tokens=("schotter", "splitt"),
            open_=True,
            open_must=("morgen", "pflaster", "verschoben"),
            forbid_future_pflaster=True,
            min_act=1,
        ),
        s(
            f"Graben gemacht 3 m³ Schotter verdichtet und dann Offen Pflasterarbeiten morgen noch fertig machen",
            act_tokens=("schotter", "pflaster", "graben"),
            mat_tokens=("schotter",),
            open_=True,
            open_must=("morgen", "offen"),
            min_act=1,
        ),
        s(
            f"Heute 2 m³ Splitt eingebaut morgen müssen wir noch 18 m² Pflaster verlegen auf der {SITE}",
            mat_tokens=("splitt",),
            open_=True,
            open_must=("morgen", "pflaster"),
            forbid_acts=("18 m² Pflaster verlegt",),
            forbid_future_pflaster=True,
            min_act=0,
        ),
        s(f"Rest Pflaster morgen legen Schotter und Splitt heute fertig {SITE}", mat_tokens=("schotter", "splitt"), open_=True, open_must=("morgen", "pflaster", "offen")),
        s(
            f"Baggerarbeiten und Graben heute erledigt Schotter eingebaut morgen noch 35 Quadratmeter Pflaster legen",
            act_tokens=("bagger", "schotter", "graben"),
            mat_tokens=("schotter",),
            open_=True,
            open_must=("morgen", "pflaster"),
            forbid_future_pflaster=True,
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            f"Schotterplanum hergestellt Splitt eingebaut Pflaster verschiebt sich auf Montag {SITE}",
            mat_tokens=("splitt",),
            open_=True,
            open_must=("montag", "pflaster", "verschoben"),
            min_act=0,
        ),
        s(
            f"Heute Graben und Schotter 0/32 verdichtet zwei Kubik Splitt eingebaut und morgen Pflaster legen noch offen",
            act_tokens=("schotter", "splitt", "graben"),
            mat_tokens=("schotter", "splitt"),
            open_=True,
            open_must=("morgen", "pflaster", "offen"),
            forbid_future_pflaster=True,
            min_act=1,
        ),
        # ── Problem / Regen ──
        s(
            f"Untergrund gebaggert Schotter verdichtet leider mussten wir abbrechen weil es angefangen zu regnen {SITE}",
            act_tokens=("schotter", "bagger"),
            problem=True,
            prob_must=("regen",),
            min_act=0,
        ),
        s(
            "3 m³ Schotter eingebaut leider mussten wir die Arbeiten abrechnen weil es stark angefangen zu regnen",
            mat_tokens=("schotter",),
            problem=True,
            prob_must=("regen",),
            min_act=0,
        ),
        s(f"Problem Regen heute keine Arbeit mehr Schotter halb eingebaut {SITE}", mat_tokens=("schotter",), problem=True, prob_must=("regen",)),
        s(
            f"Graben ausgehoben Splitt eingebaut mussten wegen Regen stoppen Offen Pflaster morgen",
            act_tokens=("graben", "splitt"),
            mat_tokens=("splitt",),
            problem=True,
            open_=True,
            prob_must=("regen",),
            open_must=("morgen", "pflaster"),
            min_act=1,
        ),
        s(
            f"Heute Schotter und Splitt eingebaut leider Regen Arbeiten unterbrochen Pflastern morgen {SITE}",
            mat_tokens=("schotter", "splitt"),
            problem=True,
            open_=True,
            prob_must=("regen",),
            open_must=("morgen",),
            min_act=0,
        ),
        s(f"leider mussten wir stoppen weil es geregnet hat Erdarbeiten {SITE}", problem=True, prob_must=("regen",)),
        s(
            f"Baggerarbeiten Graben Schotter verdichtet Problem Wetter Offen Rest morgen Pflaster",
            act_tokens=("bagger", "schotter"),
            problem=True,
            open_=True,
            prob_must=("wetter",),
            open_must=("morgen", "pflaster"),
            mach_sug=("Bagger",),
            min_act=0,
        ),
        s(
            "3,5 m³ Schotter null 32 verdichtet drei Kubik Split eingebaut leider mussten wir die Arbeiten abbrechen weil es stark angefangen hat zu regnen",
            mat_tokens=("schotter", "splitt"),
            problem=True,
            prob_must=("regen",),
            min_act=0,
        ),
        # ── Material / Kubik ──
        s(f"5 m³ Schotter 0/32 eingebaut {SITE}", mat_tokens=("schotter",)),
        s(f"drei Kubik Splitt zwei Fünfer eingebaut {SITE}", mat_tokens=("splitt",)),
        s(f"zwei Kubikmeter Schotter null 45 verdichtet {SITE}", mat_tokens=("schotter",)),
        s(f"4 Kubik Split 0/8 eingebaut auf der {SITE}", mat_tokens=("splitt",)),
        s(f"Schotter 0/32 6 m³ eingebaut Splitt 2/5 2 m³ {SITE}", mat_tokens=("schotter", "splitt")),
        s(f"heute 50 Quadratmeter Pflaster gelegt {SITE}", act_tokens=("pflaster",), mat_tokens=("pflaster",), min_act=1),
        s(f"40 m² Pflaster verlegt Fugensand nachgezogen {SITE}", act_tokens=("pflaster",), mat_tokens=("pflaster",), min_act=1),
        s(f"Planum hergestellt 3 m³ Schotter eingebaut 2 m³ Splitt {SITE}", mat_tokens=("schotter", "splitt")),
        # ── Kurz / Misch ──
        s(f"Untergrund frei gebaggert {SITE}", act_tokens=("graben", "bagger"), mach_sug=("Bagger",), min_act=1),
        s(f"Baggerarbeiten durchgeführt Graben ausgehoben {SITE}", act_tokens=("bagger", "graben"), mach_sug=("Bagger",), min_act=1),
        s(f"Schotter eingebaut Splitt eingebaut {SITE}", mat_tokens=("schotter", "splitt")),
        s(f"Heute auf der {SITE} Erdarbeiten Schotter Splitt und morgen Pflaster", open_=True, open_must=("morgen", "pflaster")),
        s(
            f"Morgens Graben gebaggert mittags 3 m³ Schotter verdichtet nachmittags Splitt eingebaut {SITE}",
            act_tokens=("schotter", "splitt", "bagger", "graben"),
            mat_tokens=("schotter", "splitt"),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            f"Also heute {SITE} erst Untergrund frei gebaggert dann Schotter null 32 und drei Kubik Split zwei Fünfer und Feierabend",
            act_tokens=("schotter", "splitt", "graben", "bagger"),
            mat_tokens=("schotter", "splitt"),
            min_act=1,
        ),
        s(f"hamma graben frei gebaggert und 5 kubik schotter eingebaut {SITE}", act_tokens=("schotter", "graben", "bagger"), mat_tokens=("schotter",), min_act=1),
        s(
            f"Heute {SITE} Schotter Splitt eingebaut mit dem Bauherrn kurz gesprochen er ist zufrieden",
            mat_tokens=("schotter", "splitt"),
            customer=True,
            cust_must=("gesprochen", "zufrieden"),
        ),
        s(
            f"Problem Lieferung Schotter spät Offen Splitt morgen nachliefern {SITE}",
            problem=True,
            open_=True,
            prob_must=("liefer", "spät"),
            open_must=("morgen", "offen"),
        ),
        s(
            f"Radlader 4 std Bagger 6 std heute Schotterplanum und Splitt auf der {SITE}",
            act_tokens=("bagger", "radlader", "schotter", "splitt"),
            mat_tokens=("splitt",),
            min_act=1,
        ),
        s(f"Kies 2 m³ eingebaut Schotter 3 m³ Splitt 1 m³ {SITE}", mat_tokens=("schotter", "splitt", "kies")),
        s(f"Terrasse 22 m² Pflaster verlegt Schottertragschicht davor {SITE}", act_tokens=("pflaster",), mat_tokens=("schotter", "pflaster"), min_act=1),
        s(f"Drainage Graben Schotter Splitt Pflastersteinen gesetzt {SITE}", mat_tokens=("schotter", "splitt")),
        s(
            f"Heute {SITE} Untergrund gebaggert 4 m³ Schotter 0/32 verdichtet 3 Kubik Splitt 2/5 ohne Pflaster",
            act_tokens=("schotter", "splitt", "bagger"),
            mat_tokens=("schotter", "splitt"),
            forbid_future_pflaster=True,
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            f"Schotter eingebaut Splitt eingebaut Problem Maschine kaputt Offen Rest morgen {SITE}",
            mat_tokens=("schotter", "splitt"),
            problem=True,
            open_=True,
            prob_must=("maschine", "kaputt"),
            open_must=("morgen", "offen"),
        ),
        s(f"Erdplanum erstellt Frostschutz 8 m³ Schotter 0/45 {SITE}", mat_tokens=("schotter",)),
        s(
            f"Heute {SITE} 6 m³ Schotter null 32 eingebaut und 2 m³ Splitt 2/5 dann Feierabend",
            mat_tokens=("schotter", "splitt"),
            min_act=0,
        ),
        s(
            f"Untergrund gebaggert Schotter verdichtet Splitt verarbeitet Pflaster morgen {SITE}",
            mat_tokens=("schotter", "splitt"),
            open_=True,
            open_must=("morgen", "pflaster"),
            forbid_future_pflaster=True,
        ),
    ]


def _emit(items: list[dict]) -> str:
    lines = [
        '"""Pilot Real-Speech Welle 50 — 50 Basisszenarien (echte Diktat-Muster)."""',
        "",
        "from __future__ import annotations",
        "",
        "",
        "def all_base_scenarios() -> list[dict]:",
        "    return [",
    ]
    for it in items:
        lines.append("        {")
        lines.append(f'            "raw": {it["raw"]!r},')
        for key in (
            "acts", "act_tokens", "mats", "mat_tokens", "mach", "mach_sug", "sugs",
            "forbid_acts", "forbid_mats", "prob_must", "prob_not", "open_must", "open_not",
            "cust_must", "sum_qty", "sum_not",
        ):
            if it.get(key):
                lines.append(f'            "{key}": {it[key]!r},')
        for flag in ("problem", "open_", "customer", "forbid_future_pflaster", "strict"):
            if it.get(flag):
                lines.append(f'            "{flag}": True,')
        if it.get("min_act") is not None:
            lines.append(f'            "min_act": {it["min_act"]!r},')
        lines.append("        },")
    lines.append("    ]")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    items = all_base_scenarios()
    if len(items) != TARGET:
        raise SystemExit(f"Erwartet {TARGET} Szenarien, got {len(items)}")
    OUT.write_text(_emit(items) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} scenarios -> {OUT.name}")


if __name__ == "__main__":
    main()
