"""Generator Putz & Stuck Welle 16 — JSON-Katalog Engine-Welle A.

Fokus: WDVS kleben/dübeln, Putz glätten/filizen, Materialtiefe.
Rein additiv; Welle 15 bleibt Regression.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "putz_stuck_wave16_scenarios.py"


def s(raw: str, acts: tuple[str, ...], **kw) -> dict:
    d = dict(
        raw=raw,
        acts=acts,
        mats=(),
        forbid_acts=(),
        problem=False,
        open_=False,
        customer=False,
        min_act=None,
    )
    d.update(kw)
    return d


SCENARIOS: list[dict] = [
    # ── WDVS Dämmung kleben ──
    s(
        "WDVS Dämmung geklebt mit EPS und Klebe- und Armierungsmörtel 120 Quadratmeter.",
        ("WDVS Dämmung geklebt",),
        mats=("EPS Dämmplatten", "Klebe- und Armierungsmörtel"),
    ),
    s(
        "Dämmplatten geklebt Mineralwolle 80 Millimeter WDVS kleben fertig.",
        ("WDVS Dämmung geklebt",),
        mats=("Mineralwolle Dämmplatten",),
    ),
    s(
        "Heute WDVS kleben mit Zahntraufel Holzfaserplatten angebracht.",
        ("WDVS Dämmung geklebt",),
        mats=("Holzfaserplatten",),
    ),
    s(
        "WDVS Dämmung kleben Problem Kleber knapp Offen Rest morgen Kunde informiert.",
        ("WDVS Dämmung geklebt",),
        problem=True,
        open_=True,
        customer=True,
    ),
    s(
        "hamma WDVS Dämmung geklebt mit EPS fertig.",
        ("WDVS Dämmung geklebt",),
        min_act=1,
    ),
    # ── WDVS dübeln ──
    s(
        "WDVS gedübelt mit Tellerdübel 160 Millimeter überall befestigt.",
        ("WDVS gedübelt",),
        mats=("Tellerdübel",),
    ),
    s(
        "Dämmung dübeln WDVS befestigen Tellerdübel gesetzt.",
        ("WDVS gedübelt",),
        mats=("Tellerdübel",),
    ),
    s(
        "Nach dem Kleben WDVS gedübelt Schlagdübel und Tellerdübel.",
        ("WDVS gedübelt",),
        mats=("Tellerdübel",),
    ),
    s(
        "WDVS dübeln fertig Problem Bohrer defekt Offen Sockel morgen.",
        ("WDVS gedübelt",),
        problem=True,
        open_=True,
    ),
    s(
        "ich hab WDVS gedübelt mit Tellerdübel gemacht.",
        ("WDVS gedübelt",),
        min_act=1,
    ),
    # ── WDVS Kette (generisch bleibt für angeklebt) ──
    s(
        "WDVS Platten angeklebt Armierungsgewebe eingebettet Reibputz drauf.",
        ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen"),
    ),
    s(
        "Fassade gedämmt Gewebe reingemacht Außenputz aufgetragen.",
        ("WDVS ausgeführt", "Fassadenarmierung ausgeführt", "Außenputz aufgetragen"),
    ),
    # ── Putz glätten ──
    s(
        "Putz geglättet mit Feinputz und Glättkelle 45 Quadratmeter.",
        ("Putz geglättet",),
        mats=("Feinputz",),
    ),
    s(
        "Innenputz glätten fertig Feinputz verarbeitet.",
        ("Putz geglättet",),
        mats=("Feinputz",),
    ),
    s(
        "Oberfläche finishen Putz glätten Schwammbrett benutzt.",
        ("Putz geglättet",),
    ),
    s(
        "Putz glätten Problem Gerüst spät Offen Decke morgen Bauherr informiert.",
        ("Putz geglättet",),
        problem=True,
        open_=True,
        customer=True,
    ),
    # ── Putz filzen ──
    s(
        "Putz filziert mit Filzbrett Struktur fertig.",
        ("Putz filziert",),
        mats=("Feinputz",),
    ),
    s(
        "Außenputz filzen Feinputz verarbeitet fertig.",
        ("Putz filziert",),
    ),
    s(
        "Putz filzen mit Schwammbrett gemacht.",
        ("Putz filziert",),
        min_act=1,
    ),
    # ── Materialtiefe Putz ──
    s(
        "Gipsputz aufgetragen 60 Quadratmeter Innenputz verarbeitet.",
        ("Innenputz aufgetragen",),
        mats=("Gipsputz",),
    ),
    s(
        "Kalkputz und Lehmputz im Wohnbereich aufgebracht.",
        ("Innenputz aufgetragen",),
        mats=("Kalkputz", "Lehmputz"),
        min_act=1,
    ),
    s(
        "Silikatputz an der Fassade aufgetragen Außenputz verarbeitet.",
        ("Außenputz aufgetragen",),
        mats=("Silikatputz",),
    ),
    s(
        "Silikonharzputz außen aufgebracht Kratzputz vorbereitet.",
        ("Außenputz aufgetragen",),
        mats=("Silikonharzputz",),
        min_act=1,
    ),
    # ── Komplett-Ketten ──
    s(
        (
            "Morgens WDVS Dämmung geklebt mittags WDVS gedübelt "
            "nachmittags Armierungsgewebe eingebettet Reibputz aufgetragen "
            "Bauleitung zufrieden Problem Wind Offen letzte Fläche Montag."
        ),
        (
            "WDVS Dämmung geklebt",
            "WDVS gedübelt",
            "Armierung ausgeführt",
            "Reibputz aufgetragen",
        ),
        problem=True,
        open_=True,
        customer=True,
    ),
    s(
        (
            "Unterputz aufgetragen Oberputz aufgetragen Putz geglättet "
            "mit Feinputz fertig."
        ),
        ("Unterputz aufgetragen", "Oberputz aufgetragen", "Putz geglättet"),
        mats=("Feinputz",),
    ),
    s(
        "Kratzputz aufgetragen Putz filziert Außenputz strukturiert.",
        ("Kratzputz aufgetragen", "Putz filziert", "Außenputz aufgetragen"),
    ),
    s(
        "WDVS Dämmung geklebt WDVS gedübelt Armierungsgewebe eingebettet.",
        ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt"),
        min_act=2,
    ),
    s(
        "Heute nur Material geliefert Offen WDVS kleben morgen.",
        (),
        open_=True,
        min_act=0,
    ),
    s(
        "Kundengespräch Putzmuster gewählt Problem Feuchte Offen nächste Woche.",
        (),
        problem=True,
        open_=True,
        customer=True,
        min_act=0,
    ),
]


def _emit() -> str:
    lines = [
        '"""Putz & Stuck Welle 16 — generierte Basisszenarien (JSON Engine-Welle A)."""',
        "",
        "from __future__ import annotations",
        "",
        "",
        "def all_base_scenarios() -> list[dict]:",
        "    return [",
    ]
    for spec in SCENARIOS:
        lines.append("        {")
        lines.append(f'            "raw": {spec["raw"]!r},')
        lines.append(f'            "acts": {spec["acts"]!r},')
        if spec.get("mats"):
            lines.append(f'            "mats": {spec["mats"]!r},')
        if spec.get("forbid_acts"):
            lines.append(f'            "forbid_acts": {spec["forbid_acts"]!r},')
        if spec.get("problem"):
            lines.append('            "problem": True,')
        if spec.get("open_"):
            lines.append('            "open_": True,')
        if spec.get("customer"):
            lines.append('            "customer": True,')
        if spec.get("min_act") is not None:
            lines.append(f'            "min_act": {spec["min_act"]!r},')
        lines.append("        },")
    lines.append("    ]")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUT.write_text(_emit(), encoding="utf-8")
    print(f"Wrote {len(SCENARIOS)} scenarios -> {OUT}")


if __name__ == "__main__":
    main()
