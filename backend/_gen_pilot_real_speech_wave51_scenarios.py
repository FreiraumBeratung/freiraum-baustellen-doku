"""Generator Pilot Real-Speech Welle 51 — 40 Basisszenarien (heutige Diktat-Muster)."""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "pilot_real_speech_wave51_scenarios.py"
TARGET = 40
SITE_A = "Schmitz Außenanlage"
SITE_B = "Müller Gartenbau"


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
        # ── Gold: heute validiert (Screenshots / Pilot-Diktat) ──
        s(
            (
                "Oh hab ich gemacht heute die Bagger mit Lock hab ich gemacht dann drei Kubik Schotter 32 "
                "danach ich hab gemacht Split ungefähr zwei Kubik dann hat viel geregnet Arbeit stopp"
            ),
            strict=True,
            act_tokens=("schotter", "splitt", "graben", "bagger"),
            mat_tokens=("schotter",),
            problem=True,
            prob_must=("regen",),
            forbid_acts=("Pflasterfugen verfugt",),
            mach_sug=("Bagger",),
            min_act=2,
        ),
        s(
            (
                "Als erstes haben wir den Untergrund vorbereitet mit dem Bagger das ging ungefähr 3 Stunden "
                "danach haben wir 5 m³ Frostschutzschotter null 32 reingepackt danach ging noch 2 m³ Split zwei Fünfer rein "
                "dann haben wir die Pflasterfläche von 40 m² fertig gestellt morgen müssen wir dann noch mal zur Baustelle "
                "und die Fugen mit Fugensand füllen"
            ),
            strict=True,
            act_tokens=("frostschutz", "splitt", "pflaster", "unterbau"),
            mat_tokens=("schotter", "splitt"),
            open_=True,
            open_must=("fugensand", "offen"),
            forbid_acts=("Pflasterfugen verfugt",),
            mach_sug=("Bagger",),
            min_act=2,
        ),
        s(
            (
                "Heute haben wir erst mal den Unterbau mit dem Bagger vorgearbeitet und fertig gestellt "
                "dann haben wir 5 m³ Schotter eingebaut und 3 m³ Pflaster wir wollten dann gerade mit dem "
                "Pflastern anfangen für 40 m² leider hat uns das Wetter Strich durch die Rechnung gemacht "
                "und es hat angefangen zu regnen und wir mussten die Arbeiten abbrechen Trotzdem war die "
                "Kundin sehr froh und stolz auf unsere Arbeit"
            ),
            strict=True,
            act_tokens=("unterbau", "schotter", "bagger"),
            mat_tokens=("schotter",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("regen",),
            open_must=("pflaster", "offen"),
            forbid_acts=("Pflaster verlegt", "wollten", "Graben ausgehoben"),
            forbid_mats=("wollten", "3 m³ Pflaster"),
            mach_sug=("Bagger",),
            cust_must=("kundin", "froh"),
            sum_not=("pflaster verlegt",),
            min_act=2,
        ),
        # ── Gebrochenes Deutsch / Baustellen-Slang ──
        s(
            (
                "Heute wir ham gemacht Bagger mit Loch dann fünf Kubik Schotter 32 danach zwei Kubik Split "
                "zwei Fünfer und dann viel Regen Arbeit stopp"
            ),
            act_tokens=("schotter", "splitt", "bagger"),
            mat_tokens=("schotter", "splitt"),
            problem=True,
            prob_must=("regen",),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                "Ich hab gemacht heute Untergrund mit Bagger dann drei Kubik Schotter null 32 "
                "danach Split ungefähr zwei Kubik und Feierabend"
            ),
            act_tokens=("schotter", "splitt", "bagger"),
            mat_tokens=("schotter",),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                "Also heute Bagger mit Lock hab ich gemacht dann vier Kubik Schotter 32 "
                "danach ich hab gemacht Split zwei Kubik dann hat viel geregnet"
            ),
            act_tokens=("schotter", "splitt", "graben", "bagger"),
            mat_tokens=("schotter",),
            problem=True,
            prob_must=("regen",),
            min_act=1,
        ),
        s(
            (
                "Morgens hamma den Graben frei gebaggert mittags drei Kubik Schotter 32 reingemacht "
                "nachmittags zwei Kubik Split rein"
            ),
            act_tokens=("schotter", "splitt", "graben", "bagger"),
            mat_tokens=("schotter", "splitt"),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                "Heute auf der Baustelle Baggerarbeiten dann fünf m³ Schotter eingebaut "
                "danach Split zwei Fünfer ich hab gemacht fertig"
            ),
            act_tokens=("schotter", "splitt", "bagger"),
            mat_tokens=("schotter", "splitt"),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                "Wir haben heute Untergrund gebaggert und 6 Kubik Schotter null 32 verdichtet "
                "und drei Kubik Split verarbeitet Kunde war zufrieden"
            ),
            act_tokens=("schotter", "splitt", "bagger"),
            mat_tokens=("schotter", "splitt"),
            customer=True,
            cust_must=("zufrieden",),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        # ── Langketten: Unterbau → Schotter → Splitt → Pflaster → morgen Fugen ──
        s(
            (
                f"Zuerst {SITE_A} Untergrund mit Bagger vorbereitet circa 2 Stunden dann 5 m³ Frostschutzschotter "
                "0/32 reingepackt danach 2 m³ Splitt 2/5 eingebaut Pflasterfläche 32 m² fertig gestellt "
                "morgen müssen wir die Fugen mit Fugensand füllen noch offen"
            ),
            act_tokens=("frostschutz", "splitt", "pflaster", "unterbau"),
            mat_tokens=("schotter", "splitt"),
            open_=True,
            open_must=("fugensand", "offen"),
            forbid_acts=("Pflasterfugen verfugt",),
            mach_sug=("Bagger",),
            min_act=2,
        ),
        s(
            (
                f"Auf {SITE_B} Bagger drei Stunden Unterbau fertig dann 4 m³ Schotter null 32 "
                "danach ging noch 2 m³ Split zwei Fünfer rein 28 m² Pflasterfläche fertig gestellt "
                "morgen müssen wir die Fugen mit Fugensand füllen"
            ),
            act_tokens=("schotter", "splitt", "pflaster", "unterbau"),
            mat_tokens=("schotter",),
            open_=True,
            open_must=("fugensand",),
            forbid_acts=("Pflasterfugen verfugt",),
            mach_sug=("Bagger",),
            min_act=2,
        ),
        s(
            (
                "Den Unterbau haben wir mit dem Bagger vorgearbeitet und fertig gestellt "
                "5 m³ Frostschutzschotter null 32 eingebaut 2 m³ Splitt 2/5 mm eingebaut "
                "45 m² Pflasterfläche fertig gestellt morgen müssen wir Fugensand in die Fugen füllen"
            ),
            act_tokens=("frostschutz", "splitt", "pflaster"),
            mat_tokens=("schotter",),
            open_=True,
            open_must=("fugensand", "offen"),
            forbid_acts=("Pflasterfugen verfugt",),
            mach_sug=("Bagger",),
            min_act=2,
        ),
        s(
            (
                f"Heute {SITE_A} Untergrund gebaggert Schotterplanum 4 m³ Schotter 0/32 verdichtet "
                "Splitt 2/5 eingebaut 36 m² Pflaster gelegt morgen noch Fugen mit Sand füllen"
            ),
            act_tokens=("schotter", "splitt", "pflaster", "bagger"),
            mat_tokens=("schotter", "splitt"),
            open_=True,
            open_must=("fugen", "offen"),
            forbid_acts=("Pflasterfugen verfugt",),
            mach_sug=("Bagger",),
            min_act=2,
        ),
        # ── Wetter-Abbruch: wollten Pflastern, Regen, offen ──
        s(
            (
                f"{SITE_B} Unterbau mit Bagger fertig 5 m³ Schotter eingebaut wir wollten gerade "
                "mit dem Pflastern anfangen für 32 m² leider hat es angefangen zu regnen und wir mussten abbrechen "
                "Rest morgen Pflaster noch offen"
            ),
            act_tokens=("unterbau", "schotter", "bagger"),
            mat_tokens=("schotter",),
            problem=True,
            open_=True,
            prob_must=("regen",),
            open_must=("pflaster", "offen"),
            forbid_acts=("Pflaster verlegt", "wollten", "Graben ausgehoben"),
            forbid_future_pflaster=True,
            sum_not=("pflaster verlegt",),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                "Schotter und Splitt heute eingebaut wir wollten gerade mit dem Pflastern anfangen "
                "für 25 m² Wetter hat Strich durch die Rechnung gemacht angefangen zu regnen "
                "Arbeiten abbrechen"
            ),
            act_tokens=("schotter", "splitt"),
            mat_tokens=("schotter", "splitt"),
            problem=True,
            open_=True,
            prob_must=("regen",),
            open_must=("pflaster", "offen"),
            forbid_acts=("Pflaster verlegt",),
            forbid_future_pflaster=True,
            min_act=1,
        ),
        s(
            (
                f"Heute {SITE_A} 4 m³ Schotter 0/32 verdichtet 2 m³ Splitt eingebaut "
                "wir wollten gerade mit dem Pflastern anfangen für 38 m² leider mussten wegen Regen stoppen"
            ),
            act_tokens=("schotter", "splitt"),
            mat_tokens=("schotter",),
            problem=True,
            prob_must=("regen",),
            forbid_acts=("Pflaster verlegt", "Graben ausgehoben"),
            forbid_future_pflaster=True,
            min_act=1,
        ),
        s(
            (
                "Unterbau mit Bagger vorbereitet 5 m³ Schotter eingebaut wir wollten gerade "
                "mit dem Pflastern anfangen für 42 m² Problem wegen Regen mussten die Arbeiten abbrechen "
                "Offen Rest Pflaster morgen"
            ),
            act_tokens=("unterbau", "schotter", "bagger"),
            mat_tokens=("schotter",),
            problem=True,
            open_=True,
            prob_must=("regen",),
            open_must=("pflaster", "offen"),
            forbid_acts=("Pflaster verlegt", "wollten"),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                f"Graben frei gebaggert Schotter null 32 Splitt eingebaut wollten Pflaster legen 30 m² "
                f"leider Regen {SITE_B} dementsprechend Pflastern morgen noch offen"
            ),
            act_tokens=("schotter", "splitt", "graben", "bagger"),
            mat_tokens=("schotter", "splitt"),
            problem=True,
            open_=True,
            prob_must=("regen",),
            open_must=("morgen", "pflaster", "offen"),
            forbid_acts=("30 m² Pflaster verlegt",),
            forbid_future_pflaster=True,
            mach_sug=("Bagger",),
            min_act=1,
        ),
        # ── Morgen / Offen / Verschiebung ──
        s(
            f"morgen müssen wir noch 22 m² Pflaster legen {SITE_A}",
            open_=True,
            open_must=("morgen", "pflaster", "offen"),
            forbid_future_pflaster=True,
            min_act=0,
        ),
        s(
            (
                f"Heute Schotter eingebaut Splitt verarbeitet dementsprechend verschiebt sich das Pflastern "
                f"auf morgen {SITE_B}"
            ),
            act_tokens=("schotter", "splitt"),
            mat_tokens=("schotter", "splitt"),
            open_=True,
            open_must=("morgen", "pflaster", "verschoben"),
            forbid_future_pflaster=True,
            min_act=1,
        ),
        s(
            (
                f"Untergrund gebaggert 3 m³ Schotter verdichtet zwei Kubik Splitt und morgen Pflaster legen "
                f"noch offen {SITE_A}"
            ),
            act_tokens=("schotter", "splitt", "bagger"),
            mat_tokens=("schotter", "splitt"),
            open_=True,
            open_must=("morgen", "pflaster", "offen"),
            forbid_future_pflaster=True,
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                f"Schotterplanum hergestellt Splitt eingebaut Rest Pflaster morgen legen {SITE_B}"
            ),
            mat_tokens=("splitt",),
            open_=True,
            open_must=("morgen", "pflaster", "offen"),
            min_act=0,
        ),
        # ── Problem / Regen / Lieferung ──
        s(
            (
                f"Untergrund gebaggert Schotter verdichtet leider mussten wir abbrechen weil es angefangen "
                f"zu regnen {SITE_A}"
            ),
            act_tokens=("schotter", "bagger"),
            problem=True,
            prob_must=("regen",),
            mach_sug=("Bagger",),
            min_act=0,
        ),
        s(
            (
                "3 m³ Schotter eingebaut leider mussten wir die Arbeiten abrechnen weil es stark "
                "angefangen zu regnen"
            ),
            mat_tokens=("schotter",),
            problem=True,
            prob_must=("regen",),
            min_act=0,
        ),
        s(
            f"Problem Lieferung Schotter spät Offen Splitt morgen nachliefern {SITE_B}",
            problem=True,
            open_=True,
            prob_must=("liefer", "spät"),
            open_must=("morgen", "offen"),
        ),
        s(
            (
                f"Baggerarbeiten Graben Schotter verdichtet Problem Wetter Offen Rest morgen Pflaster {SITE_A}"
            ),
            act_tokens=("bagger", "schotter"),
            problem=True,
            open_=True,
            prob_must=("wetter",),
            open_must=("morgen", "pflaster"),
            mach_sug=("Bagger",),
            min_act=0,
        ),
        # ── Material / Kubik / Kornung ──
        s(f"5 m³ Schotter 0/32 eingebaut {SITE_A}", mat_tokens=("schotter",)),
        s(f"drei Kubik Splitt zwei Fünfer eingebaut {SITE_B}", act_tokens=("splitt",), mat_tokens=("splitt",)),
        s(f"zwei Kubikmeter Schotter null 45 verdichtet {SITE_A}", mat_tokens=("schotter",)),
        s(f"4 Kubik Split 0/8 eingebaut auf der {SITE_B}", mat_tokens=("splitt",)),
        s(f"Schotter 0/32 6 m³ eingebaut Splitt 2/5 2 m³ {SITE_A}", mat_tokens=("schotter", "splitt")),
        s(
            f"Frostschutz 5 m³ Schotter null 32 reingepackt Splitt 2/5 2 m³ {SITE_B}",
            act_tokens=("frostschutz", "splitt"),
            mat_tokens=("schotter", "splitt"),
            min_act=1,
        ),
        # ── Erledigt: Pflaster heute (positiv) ──
        s(
            f"heute 35 Quadratmeter Pflaster gelegt {SITE_A}",
            act_tokens=("pflaster",),
            mat_tokens=("pflaster",),
            min_act=1,
        ),
        s(
            (
                f"Untergrund gebaggert 4 m³ Schotter null 32 Splitt 2/5 eingebaut und 40 m² Pflaster "
                f"eingebaut {SITE_B}"
            ),
            act_tokens=("schotter", "splitt", "pflaster", "bagger"),
            mat_tokens=("schotter", "splitt"),
            mach_sug=("Bagger",),
            min_act=2,
        ),
        # ── Kundengespräch ──
        s(
            (
                f"Heute {SITE_A} Schotter Splitt eingebaut mit der Kundin gesprochen sie ist sehr zufrieden"
            ),
            mat_tokens=("schotter", "splitt"),
            customer=True,
            cust_must=("gesprochen", "zufrieden"),
            min_act=0,
        ),
        s(
            (
                f"Bauherr war da Pflaster Muster gewählt Schotter heute eingebaut {SITE_B}"
            ),
            mat_tokens=("schotter",),
            customer=True,
            cust_must=("bauherr",),
            min_act=0,
        ),
        # ── Kurz / Misch ──
        s(
            f"Also heute {SITE_A} erst Untergrund frei gebaggert dann Schotter null 32 und drei Kubik Splitt zwei Fünfer",
            act_tokens=("schotter", "splitt", "bagger", "graben"),
            mat_tokens=("schotter", "splitt"),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            f"hamma graben frei gebaggert und 5 kubik schotter eingebaut {SITE_B}",
            act_tokens=("schotter", "graben", "bagger"),
            mat_tokens=("schotter",),
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                f"Heute {SITE_A} Untergrund gebaggert 4 m³ Schotter 0/32 verdichtet 3 Kubik Splitt 2/5 ohne Pflaster"
            ),
            act_tokens=("schotter", "splitt", "bagger"),
            mat_tokens=("schotter", "splitt"),
            forbid_future_pflaster=True,
            mach_sug=("Bagger",),
            min_act=1,
        ),
        s(
            (
                f"Schotter eingebaut Splitt eingebaut Problem Maschine kaputt Offen Rest morgen {SITE_B}"
            ),
            mat_tokens=("schotter", "splitt"),
            problem=True,
            open_=True,
            prob_must=("maschine", "kaputt"),
            open_must=("morgen", "offen"),
            min_act=0,
        ),
    ]


def _emit(items: list[dict]) -> str:
    lines = [
        '"""Pilot Real-Speech Welle 51 — 40 Basisszenarien (Diktat-Muster Session 11.07.)."""',
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
