"""Generator Putz & Stuck Welle 18 — 100 Basisszenarien (PANZEK-Style).

Kurz/lang, Umgangssprache, gebrochenes Deutsch, Ketten, WDVS+Profile+Putz.
Rein additiv; Welle 15/16/17 bleiben Regression.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "putz_stuck_wave18_scenarios.py"
TARGET = 100
SITE_A = "Höxter"
SITE_B = "Warburg"
SITE_C = "Beverungen"


def s(raw: str, acts: tuple[str, ...], **kw) -> dict:
    d = dict(
        raw=raw,
        acts=acts,
        mats=(),
        mach=(),
        forbid_acts=(),
        problem=False,
        open_=False,
        customer=False,
        min_act=None,
    )
    d.update(kw)
    return d


V = dict(
    w1="Altputz runter Wand geschliffen Grundierung drauf Unterputz aufgetragen",
    w2="WDVS Dämmung geklebt Armierungsgewebe eingebettet Reibputz aufgetragen",
    w3="Sockelprofil montiert APU-Leiste montiert Leibungsprofil gesetzt Eckschutz gesetzt",
    w4="Innenputz mit Gipsputz aufgetragen Oberputz glatt Putz geglättet",
    w5="Außenputz Kratzputz aufgetragen Putz filziert Silikatputz verarbeitet",
    w6="WDVS gedübelt Tropfkantenprofil gesetzt Außenputz strukturiert",
    w7="Schimmel weg gemacht Sanierputz drauf Unterputz nachgearbeitet",
    w8="Stuckarbeiten gemacht Gesims stuckiert",
    a1=("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen", "Unterputz aufgetragen"),
    a2=("WDVS Dämmung geklebt", "Armierung ausgeführt", "Reibputz aufgetragen"),
    a3=("Sockelprofile montiert", "APU-Leisten montiert", "Leibungsprofile gesetzt", "Eckschutzprofile gesetzt"),
    a4=("Innenputz aufgetragen", "Oberputz aufgetragen", "Putz geglättet"),
    a5=("Kratzputz aufgetragen", "Putz filziert", "Außenputz aufgetragen"),
    a6=("WDVS gedübelt", "Tropfkantenprofile gesetzt", "Außenputz aufgetragen"),
    a7=("Schimmel beseitigt", "Sanierputz aufgebracht", "Unterputz aufgetragen"),
    a8=("Stuckarbeiten durchgeführt",),
    rain="Problem Starkregen mussten abbrechen",
    rain2="Problem Putzmaschine defekt mussten stoppen",
    uneben="Untergrund war uneben was zu Problemen geführt hat",
    open="Offen Oberputz Decke morgen",
    open2="Offen WDVS letzte Fläche Donnerstag",
    plan="machen wir morgen früh den Rest fertig",
    cust="Bauherr war einverstanden und zufrieden",
    cust2="Bauleitung kurz informiert Termin abgestimmt",
    prob="Problem Kleber Lieferung verspätet",
    open_exp="Offen Fertigstellung nächste Woche",
)


def _core_live() -> list[dict]:
    return [
        s(f"Nachmittag {SITE_A} {V['w1']} {V['rain']} {V['open']} {V['cust']}.", V["a1"], problem=True, open_=True, customer=True, min_act=2),
        s(f"{V['w2']} {V['rain2']}.", V["a2"], problem=True, min_act=2),
        s(f"Baustelle {SITE_B} {V['w3']} {V['uneben']} {V['cust2']}.", V["a3"], problem=True, customer=True, min_act=2),
        s(f"{V['w4']} {V['open2']}.", V["a4"], open_=True, min_act=2),
        s(f"{SITE_C} Hotel-Fassade {V['w5']} {V['prob']} {V['open_exp']}.", V["a5"], problem=True, open_=True, min_act=2),
        s(f"{V['w6']} {V['open']} {V['plan']}.", V["a6"], open_=True, min_act=2),
        s(f"{V['w7']} {V['cust']}.", V["a7"], customer=True, min_act=2),
        s(f"Heute nur {V['cust2']} wegen Besprechung kein Putz wegen Wetter.", (), problem=True, customer=True, min_act=0),
    ]


def _chains() -> list[dict]:
    return [
        s(V["w1"], V["a1"], min_act=2),
        s(f"Erst {V['w2']} dann {V['w3']}.", V["a2"] + V["a3"], min_act=3),
        s(f"{V['w4']} und am Ende {V['w5']}.", V["a4"] + V["a5"], min_act=3),
        s(
            (
                f"Morgens {SITE_A} Altputz abgetragen Wand geschliffen mittags Grundierung "
                f"Unterputz aufgetragen nachmittags Oberputz aufgetragen Putz geglättet "
                f"Bauherr zufrieden Problem Feuchte Offen Rest Montag."
            ),
            ("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen", "Putz geglättet"),
            mats=("Feinputz",),
            problem=True,
            open_=True,
            customer=True,
            min_act=4,
        ),
        s(
            (
                f"WDVS Dämmung geklebt mit EPS und Klebe- und Armierungsmörtel "
                f"WDVS gedübelt Tellerdübel Armierungsgewebe eingebettet "
                f"Sockelprofil montiert APU-Leisten montiert Putzmaschine 6 std."
            ),
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt", "Sockelprofile montiert", "APU-Leisten montiert"),
            mats=("EPS Dämmplatten", "Klebe- und Armierungsmörtel", "Tellerdübel"),
            mach=("Putzmaschine",),
            min_act=4,
        ),
        s(
            (
                f"Fassade {SITE_B} Kratzputz aufgetragen Reibputz nachgearbeitet "
                f"Putz filziert Außenputz aufgetragen Silikonharzputz verarbeitet."
            ),
            ("Kratzputz aufgetragen", "Reibputz aufgetragen", "Putz filziert", "Außenputz aufgetragen"),
            mats=("Silikonharzputz",),
            min_act=3,
        ),
        s(
            (
                f"Neubau Treppenhaus Grundputz aufgetragen Innenputz Gipsputz 85 Quadratmeter "
                f"Sockelputz gemacht Leibungsprofile gesetzt."
            ),
            ("Grundputz aufgetragen", "Innenputz aufgetragen", "Sockelputz aufgetragen", "Leibungsprofile gesetzt"),
            mats=("Gipsputz",),
            min_act=3,
        ),
        s(
            (
                f"An der Fassade WDVS Platten angeklebt Gewebe reingemacht "
                f"Reibputz drauf Tropfkantenprofil gesetzt Eckschutzschiene gesetzt."
            ),
            ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen", "Tropfkantenprofile gesetzt", "Eckschutzprofile gesetzt"),
            min_act=3,
        ),
        s(
            f"Schimmel beseitigt Sanierputz aufgebracht Unterputz aufgetragen Oberputz aufgetragen fertig.",
            ("Schimmel beseitigt", "Sanierputz aufgebracht", "Unterputz aufgetragen", "Oberputz aufgetragen"),
            mats=("Sanierputz",),
            min_act=3,
        ),
        s(
            f"Sockelleiste stuckiert Gesims angebracht Stuckarbeiten gemacht Kunde informiert.",
            ("Stuckarbeiten durchgeführt",),
            customer=True,
            min_act=1,
        ),
    ]


def _explicit_pob() -> list[dict]:
    return [
        s(f"{V['w3']} Problem Material knapp Offen Rest morgen.", V["a3"], problem=True, open_=True, min_act=2),
        s(f"{V['w2']} Problem Tellerdübel fehlen Offen nächste Woche.", V["a2"], problem=True, open_=True, min_act=2),
        s(f"{V['w1']} leider mussten wir abbrechen morgen weiter.", V["a1"], problem=True, open_=True, min_act=2),
        s(f"{V['w5']} Kundengespräch mit Bauleitung Abstimmung Termin.", V["a5"], customer=True, min_act=2),
        s("Problem Gerüst zu spät Offen Ersatz übermorgen.", (), problem=True, open_=True, min_act=0),
        s(f"{V['w8']} Bauherr zufrieden.", V["a8"], customer=True, min_act=1),
        s("Problem Feuchte im Mauerwerk Offen Sanierung nächste Woche Bauleitung informiert.", (), problem=True, open_=True, customer=True, min_act=0),
        s(f"{V['w6']} Auftraggeber kurz da.", V["a6"], customer=True, min_act=2),
    ]


def _broken_and_short() -> list[dict]:
    return [
        s(
            "heute altputz runter wand geschliffen unterputz auf getragen problem feuchte offen morgen kunde zufrieden putzmaschine 4 std",
            ("Altputz entfernt", "Wand geschliffen", "Unterputz aufgetragen"),
            mach=("Putzmaschine",),
            problem=True,
            open_=True,
            customer=True,
            min_act=2,
        ),
        s("heute auf baustelle wdvs kleben fertig", ("WDVS Dämmung geklebt",), min_act=1),
        s(f"{V['w5']} bauherr kurz da", V["a5"], customer=True, min_act=2),
        s("Oberputz gemacht.", ("Oberputz aufgetragen",), min_act=1),
        s("Armierungsgewebe eingebettet.", ("Armierung ausgeführt",), min_act=1),
        s("heute ich hab gemacht APU montiert und Eckschutz", ("APU-Leisten montiert", "Eckschutzprofile gesetzt"), min_act=1),
        s("hamma wdvs gedübelt mit tellerdübel", ("WDVS gedübelt",), mats=("Tellerdübel",), min_act=1),
        s("putz filzen mit filzbrett fertig", ("Putz filziert",), min_act=1),
        s("innenputz glätten feinputz verarbeitet", ("Putz geglättet",), mats=("Feinputz",), min_act=1),
        s("laibungsprofil gesetzt fenster fertig", ("Leibungsprofile gesetzt",), min_act=1),
    ]


def _mega_and_long() -> list[dict]:
    raw = (
        f"Heute {SITE_A} und {SITE_B} zuerst {V['w1']} danach {V['w2']} "
        f"{V['rain']} {V['open']} {V['cust']} Problem Lieferant zu spät Offen Rest Donnerstag."
    )
    long_chain = (
        f"Früh um halb sechs gestartet mit {V['w3']} danach {V['w4']} "
        f"zwischendurch {V['cust2']} leider {V['rain2']} "
        f"dementsprechend {V['plan']} {V['open_exp']}."
    )
    return [
        s(raw, V["a1"], problem=True, open_=True, customer=True, min_act=2),
        s(long_chain, V["a3"] + V["a4"][:2], problem=True, open_=True, customer=True, min_act=3),
        s(f"Ja also vom Tag her {V['w2']} und also {V['w5']} und Feierabend.", V["a2"][:2] + V["a5"][:2], min_act=2),
        s(
            (
                f"Also heute früh erst den alten Putz abgetragen dann die Wand geschliffen "
                f"danach grundiert Unterputz aufgetragen während der Unterputz trocknete "
                f"Bauleitung kurz da Problem Feuchte im Mauerwerk Offen Rest Decke morgen "
                f"nach dem Kundengespräch Oberputz aufgetragen und Feierabend."
            ),
            ("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen"),
            problem=True,
            open_=True,
            customer=True,
            min_act=4,
        ),
    ]


def _qty_pad(count: int) -> list[dict]:
    tails = [
        ("", False, False, False, ()),
        (" leider Regen abbrechen morgen weiter.", True, True, False, ()),
        (" Bauherr informiert.", False, False, True, ()),
        (" Problem Wetter Offen nächste Woche. Putzmaschine 5 std.", True, True, False, ("Putzmaschine",)),
    ]

    def raw_at(q: int, i: int) -> tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        opts = (
            (
                f"{q} Quadratmeter Innenputz Gipsputz aufgetragen Kalkputz nachgearbeitet.",
                ("Innenputz aufgetragen",),
                ("Gipsputz", "Kalkputz"),
                (),
            ),
            (
                f"{q} Quadratmeter WDVS Dämmung geklebt EPS {q+20} Millimeter Mineralwolle.",
                ("WDVS Dämmung geklebt",),
                ("EPS Dämmplatten",),
                (),
            ),
            (
                f"{q} Meter APU-Leiste montiert Eckschutzschiene gesetzt Klebeputz verarbeitet.",
                ("APU-Leisten montiert", "Eckschutzprofile gesetzt"),
                ("Klebeputz",),
                (),
            ),
            (
                f"{q} Quadratmeter Außenputz Kratzputz Reibputz Putz filziert.",
                ("Kratzputz aufgetragen", "Putz filziert"),
                ("Reibputz",),
                (),
            ),
            (
                f"WDVS gedübelt {q} Quadratmeter Tellerdübel Armierungsgewebe eingebettet.",
                ("WDVS gedübelt", "Armierung ausgeführt"),
                ("Tellerdübel", "Armierungsgewebe"),
                (),
            ),
            (
                f"{q} Quadratmeter Unterputz aufgetragen Oberputz aufgetragen Putz geglättet.",
                ("Unterputz aufgetragen", "Oberputz aufgetragen", "Putz geglättet"),
                ("Feinputz",),
                (),
            ),
            (
                f"Sockelprofil {q} Millimeter montiert Tropfkante gesetzt.",
                ("Sockelprofile montiert", "Tropfkantenprofile gesetzt"),
                ("Sockelprofil",),
                (),
            ),
            (
                f"Leibungsprofil PVC gesetzt {q} Fenster Anputzleiste montiert.",
                ("Leibungsprofile gesetzt", "APU-Leisten montiert"),
                ("Leibungsprofil",),
                (),
            ),
        )
        return opts[i % len(opts)]

    out: list[dict] = []
    i = 0
    q = 35
    while len(out) < count:
        raw_tpl, acts, mats, mach = raw_at(q, i)
        tail, prob, opn, cust, mach_tail = tails[i % len(tails)]
        mach_use = mach_tail or mach
        out.append(
            s(
                raw_tpl + tail,
                acts,
                mats=mats,
                mach=mach_use,
                problem=prob,
                open_=opn,
                customer=cust,
                min_act=0 if not acts else 1,
            )
        )
        i += 1
        if i % 4 == 0:
            q += 7
    return out


def build() -> list[dict]:
    items: list[dict] = []
    items += _core_live()
    items += _chains()
    items += _explicit_pob()
    items += _mega_and_long()
    items += _broken_and_short()
    need = TARGET - len(items)
    items += _qty_pad(max(need, 1))
    return items[:TARGET]


def _emit(scenarios: list[dict]) -> str:
    lines = [
        '"""Putz & Stuck Welle 18 — 100 Basisszenarien (generiert)."""',
        "",
        "from __future__ import annotations",
        "",
        "",
        "def all_base_scenarios() -> list[dict]:",
        "    return [",
    ]
    for spec in scenarios:
        lines.append("        {")
        lines.append(f'            "raw": {spec["raw"]!r},')
        lines.append(f'            "acts": {spec["acts"]!r},')
        if spec.get("mats"):
            lines.append(f'            "mats": {spec["mats"]!r},')
        if spec.get("mach"):
            lines.append(f'            "mach": {spec["mach"]!r},')
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
    scenarios = build()
    assert len(scenarios) == TARGET, len(scenarios)
    OUT.write_text(_emit(scenarios), encoding="utf-8")
    print(f"Wrote {len(scenarios)} scenarios -> {OUT}")


if __name__ == "__main__":
    main()
