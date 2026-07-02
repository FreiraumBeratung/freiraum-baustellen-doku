"""Generator Pilot-Monster-Welle 25 — 60 Szenarien × 7 Gewerke. Einmal: python _gen_pilot_monster_wave25_scenarios.py"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "pilot_monster_wave25_scenarios.py"
TRADES = ("GaLaBau", "Trockenbau", "Fliesen", "SHK", "Hochbau", "Tiefbau", "Putz")


def s(raw: str, acts: tuple[str, ...], **kw) -> dict:
    d = dict(raw=raw, acts=acts, mats=(), forbid_acts=(), problem=False, open_=False, customer=False,
              cust_not=(), cust_must=(), sum_forbid=(), mat_echo=False,
              prob_must=(), prob_not=(), open_must=(), open_not=(), sum_min_len=0)
    d.update(kw)
    return d


VOCAB: dict[str, dict] = {
    "GaLaBau": dict(
        w1="heute haben wir 50 Quadratmeter Pflaster gelegt und 5 Quadratmeter Gartenmauer gebaut",
        w2="heute haben wir 40 Quadratmeter Pflaster verlegt zwei Kubikmeter Schotter eingebaut",
        w3="35 Quadratmeter Terrassenplatten verlegt Hecke geschnitten",
        rain="leider mussten wir die Arbeiten abbrechen weil es geregnet hat",
        rain2="wir mussten die Arbeiten leider abbrechen weil es angefangen hat zu regnen",
        uneben="leider war der Untergrund sehr uneben was zu Problemen geführt hat",
        open="morgen müssen wir noch fünf weitere Quadratmeter legen",
        open2="morgen müssen wir noch 20 Meter Hecke schneiden",
        plan="dementsprechend werden wir morgen dort weitermachen",
        cust="die Kundin war trotzdem zufrieden mit unserer Arbeit und freut sich auf weitere Auftraege",
        cust2="mit dem Bauherr kurz gesprochen er ist einverstanden",
        prob="Problem Lieferung Pflastersteine zu spaet",
        open_exp="Offen letzte Reihe morgen",
        a1=("50 m² Pflaster verlegt", "Gartenmauer gebaut"), a2=("40 m² Pflaster verlegt", "Schotter eingebaut"),
        a3=("35 m² Terrassenplatten verlegt", "Hecke geschnitten"), mats=("Pflastersteine",),
        qty_act=lambda q: (f"{q} m² Pflaster verlegt",),
    ),
    "Trockenbau": dict(
        w1="heute haben wir zwei Trennwände geschlossen und 45 Quadratmeter Gipskarton montiert",
        w2="heute haben wir Decke abgehängt und 30 Quadratmeter Rigips verarbeitet",
        w3="heute haben wir Spachtelarbeiten im Flur gemacht",
        rain="leider mussten wir wegen Staub im Treppenhaus die Arbeiten abbrechen",
        rain2="mussten die Arbeiten abbrechen weil die Lieferung zu spaet kam",
        uneben="leider war die Wand sehr uneben was zu Problemen geführt hat",
        open="morgen müssen wir noch die Spachtelarbeiten fertigstellen",
        open2="morgen müssen wir noch Rigips Rest montieren",
        plan="dementsprechend machen wir morgen den Rest",
        cust="der Bauherr war kurz da und ist zufrieden",
        cust2="mit dem Auftraggeber Rücksprache gehalten er ist einverstanden",
        prob="Problem Akustikdaemmung knapp",
        open_exp="Offen Spachtel morgen",
        a1=("Trockenbauwand geschlossen", "45 m² Gipskarton montiert"), a2=("Decke abgehängt",),
        a3=("Spachtelarbeiten durchgeführt",), mats=("Gipskarton",),
        qty_act=lambda q: (f"{q} m² Gipskarton montiert",),
    ),
    "Fliesen": dict(
        w1="heute haben wir 18 Quadratmeter Fliesen im Bad verlegt",
        w2="heute haben wir 32 Quadratmeter Grossformatfliesen verlegt",
        w3="heute haben wir Silikonfugen im Bad gezogen",
        rain="mussten leider abbrechen weil der Kleber zu schnell abbindet bei Hitze",
        rain2="wir mussten die Arbeiten abbrechen weil die Wand nicht lotrecht ist",
        uneben="leider war die Wand sehr uneben was zu Problemen geführt hat",
        open="morgen müssen wir noch die Silikonfugen ziehen",
        open2="morgen müssen wir noch Restfliesen verlegen",
        plan="dementsprechend werden wir morgen die Fugen fertig machen",
        cust="die Kundin hat die Farbe bestätigt und ist zufrieden",
        cust2="Mit der Kundin besprochen Muster bestätigt",
        prob="Problem Wand nicht lotrecht",
        open_exp="Offen Silikon morgen",
        a1=("18 m² Fliesen verlegt",), a2=("32 m² Fliesen verlegt",), a3=("Silikonfugen gezogen",),
        mats=("Fliesen",), qty_act=lambda q: (f"{q} m² Fliesen verlegt",),
    ),
    "SHK": dict(
        w1="heute haben wir Heizkoerper getauscht und Thermostatventile eingebaut",
        w2="heute haben wir WC montiert und Waschtisch angeschlossen",
        w3="heute haben wir Rohrleitung im Keller verlegt",
        rain="mussten abbrechen weil die Dichtung undicht war",
        rain2="leider mussten wir stoppen weil Pressfitting fehlt",
        uneben="Problem Anschluss zu eng was zu Problemen geführt hat",
        open="morgen müssen wir noch die Entlueftung machen",
        open2="morgen müssen wir noch die Rohrleitung fertig verlegen",
        plan="dementsprechend werden wir morgen weitermachen",
        cust="mit dem Kunden gesprochen er ist zufrieden",
        cust2="Mit dem Bauherrn abgesprochen alles klar",
        prob="Problem Dichtung undicht",
        open_exp="Offen Entlueftung morgen",
        a1=("Heizkörper getauscht", "Thermostatventile eingebaut"), a2=("WC montiert",),
        a3=("Rohrleitung verlegt",), mats=(), qty_act=lambda q: ("Heizkörper getauscht",),
    ),
    "Hochbau": dict(
        w1="heute haben wir Fundament betoniert und Bewehrung eingebaut",
        w2="heute haben wir Mauerwerk hochgezogen",
        w3="heute haben wir Decke geschalt",
        rain="mussten abbrechen weil die Betonpumpe verspaetet kam",
        rain2="leider mussten wir wegen Regen die Arbeiten abbrechen",
        uneben="leider war das Gefaelle falsch was zu Problemen geführt hat",
        open="morgen müssen wir noch das Fundament abziehen",
        open2="morgen müssen wir noch die Decke schalen",
        plan="dementsprechend betonieren wir morgen weiter",
        cust="Bauherr kurz informiert",
        cust2="Mit der Bauleitung Rücksprache gehalten",
        prob="Problem Betonpumpe verspaetet",
        open_exp="Offen Abziehen morgen",
        a1=("Fundament betoniert", "Bewehrung eingebaut"), a2=("Mauerwerk hochgezogen",),
        a3=("Decke geschalt",), mats=(), qty_act=lambda q: ("Mauerwerk hochgezogen",),
    ),
    "Tiefbau": dict(
        w1="heute haben wir Kanalgraben ausgehoben und KG-Rohr verlegt",
        w2="heute haben wir Schotter eingebaut und verdichtet",
        w3="heute haben wir Asphaltdecke eingebaut",
        rain="mussten abbrechen weil Grundwasser im Graben stand",
        rain2="leider mussten wir wegen Regen stoppen",
        uneben="Problem Gefaelle zu flach was zu Problemen geführt hat",
        open="morgen müssen wir noch die Verfuellung machen",
        open2="morgen müssen wir noch Asphalt einbauen",
        plan="dementsprechend werden wir morgen den Graben verfuellen",
        cust="Bauleitung informiert",
        cust2="Mit der Bauleitung abgestimmt",
        prob="Problem Wasser im Graben",
        open_exp="Offen Verfuellung morgen",
        a1=("Kanalgraben ausgehoben", "KG-Rohr verlegt"), a2=("Schotter eingebaut",),
        a3=("Asphaltdecke eingebaut",), mats=(), qty_act=lambda q: ("Kanalgraben ausgehoben",),
    ),
    "Putz": dict(
        w1="heute haben wir grundiert und den Unterputz aufgetragen",
        w2="heute haben wir 120 Quadratmeter Aussenputz aufgetragen",
        w3="heute haben wir Innenputz gespachtelt",
        rain="mussten abbrechen weil der Putz bei Regen nicht trocknet",
        rain2="leider mussten wir wegen Wind die Arbeiten abbrechen",
        uneben="leider war der Untergrund sehr uneben was zu Problemen geführt hat",
        open="morgen müssen wir auf der Baustelle mit Oberputz abschliessen",
        open2="morgen müssen wir noch den zweiten Anstrich auftragen",
        plan="dementsprechend schliessen wir morgen mit Oberputz ab",
        cust="die Kundin ist zufrieden mit dem Fortschritt",
        cust2="Mit der Kundin besprochen Farbe bestätigt",
        prob="Problem Trocknung zu langsam",
        open_exp="Offen Anstrich Freitag",
        a1=("Grundierung aufgetragen", "Unterputz aufgetragen"), a2=("120 m² Putz aufgetragen",),
        a3=("Spachtelarbeiten durchgeführt",), mats=(), qty_act=lambda q: (f"{q} m² Putz aufgetragen",),
    ),
}

PROB_OPEN = {
    "GaLaBau": (("regen", "unterbrochen"), ("morgen", "offen")),
    "Trockenbau": (("staub", "unterbrochen", "liefer"), ("morgen", "offen")),
    "Fliesen": (("kleber", "hitze", "lotrecht", "unterbrochen"), ("morgen", "offen")),
    "SHK": (("dichtung", "pressfitting", "eng"), ("morgen", "entlueft", "offen")),
    "Hochbau": (("betonpumpe", "regen", "gefälle"), ("morgen", "offen")),
    "Tiefbau": (("grundwasser", "wasser", "regen", "gefälle"), ("morgen", "verfuell", "offen")),
    "Putz": (("regen", "wind", "uneben", "trocknung"), ("morgen", "oberputz", "offen")),
}


def _core_live(v: dict, trade: str) -> list[dict]:
    pm, om = PROB_OPEN[trade]
    return [
        s(f"{v['w1']} {v['rain']} {v['open']}", v["a1"], mats=v["mats"], problem=True, open_=True,
          prob_must=pm[:2], open_must=om, prob_not=("morgen",), sum_min_len=25),
        s(f"{v['w2']} {v['rain2']}", v["a2"], problem=True, prob_must=pm),
        s(f"{v['w3']} {v['uneben']} {v['cust']}", v["a3"], problem=True, customer=True,
          prob_must=("uneben", "gefälle", "eng"), cust_must=("zufrieden",), cust_not=("uneben",)),
        s(f"{v['w1']} {v['open2']}", v["a1"], open_=True, open_must=om),
        s(f"{v['w2']} {v['rain2']} {v['plan']}", v["a2"], problem=True, open_=True,
          prob_must=pm, open_must=om, prob_not=("dementsprechend", "weitermachen")),
        s(f"{v['w1']} {v['open']}", v["a1"], open_=True, open_must=om + (("oberputz",) if trade == "Putz" else ())),
        s(f"{v['w3']} {v['prob']} {v['open_exp']}", v["a3"], problem=True, open_=True, prob_must=pm, open_must=om),
        s(f"{v['w2']} {v['cust']}", v["a2"], customer=True, cust_must=("zufrieden", "informiert"), cust_not=("verlegt", "montiert", "quadratmeter")),
    ]


def _explicit_markers(v: dict, trade: str) -> list[dict]:
    pm, om = PROB_OPEN[trade]
    return [
        s(f"{v['w2']} {v['prob']} {v['open_exp']}", v["a2"], problem=True, open_=True, prob_must=pm, open_must=om),
        s(f"{v['w3']} Problem Material knapp Offen Rest morgen.", v["a3"], problem=True, open_=True,
          prob_must=("material", "knapp", "liefer"), open_must=("morgen", "offen")),
        s(f"{v['w1']} leider mussten wir abbrechen wegen schlechtem Wetter morgen weiter.", v["a1"],
          problem=True, open_=True, prob_must=("wetter", "unterbrochen"), open_must=("morgen", "offen")),
        s("Problem Werkzeug defekt Offen Ersatz morgen.", (), problem=True, open_=True, min_act=0,
          prob_must=("defekt", "kaputt"), open_must=("morgen", "offen")),
    ]


def _customer_rich(v: dict) -> list[dict]:
    return [
        s(f"{v['w2']} {v['cust2']}", (), customer=True, min_act=1, cust_must=("gesprochen", "besprochen", "abgesprochen", "rücksprache", "abgestimmt")),
        s(f"{v['w2']} {v['cust']}", v["a2"], customer=True, cust_must=("zufrieden", "informiert")),
        s(f"{v['w1']} Nach den Arbeiten Kundin happy mit der Arbeit und freut sich auf weitere Auftraege.", v["a1"],
          customer=True, cust_must=("zufrieden", "auftrag"), cust_not=("quadratmeter", "verlegt", "montiert")),
        s(f"{v['w3']} Kundin lobt die Arbeit und empfiehlt uns weiter.", v["a3"], customer=True,
          cust_must=("lobt", "weiterempfehl"), cust_not=("verlegt", "montiert")),
    ]


def _work_runon(v: dict, trade: str) -> list[dict]:
    items = [
        s(v["w1"], v["a1"], mats=v["mats"], sum_min_len=25),
        s(v["w2"], v["a2"], sum_min_len=20),
        s(v["w3"], v["a3"], min_act=1),
    ]
    if trade == "GaLaBau":
        items += [
            s("60 Quadratmeter Pflaster verlegt 25 laufende Meter Rasenkantensteine gesetzt Hecke geschnitten.",
              ("60 m² Pflaster verlegt", "Rasenkantensteine gesetzt", "Hecke geschnitten"), mats=v["mats"], sum_min_len=35),
            s("heute ich hab gemacht 15 meter Palisaden gesetzt und 30 quadrat Rollrasen verlegt.",
              ("Palisaden gesetzt", "30 m² Rasen verlegt"), min_act=2),
        ]
    elif trade == "Putz":
        items.append(s("Fassade grundiert Putzprofil montiert Unterputz aufgetragen.",
                       ("Grundierung aufgetragen", "Putzprofil montiert", "Unterputz aufgetragen"), min_act=2, sum_min_len=30))
    else:
        items.append(s(f"{v['w1']} danach {v['w3']}", v["a1"] + v["a3"], min_act=2, sum_min_len=30))
    return items


def _broken_short(v: dict, trade: str) -> list[dict]:
    pm, om = PROB_OPEN[trade]
    work = v["w2"]
    return [
        s(f"heute {work} problem regen offen rest morgen kundin zufrieden", v["a2"],
          problem=True, open_=True, customer=True, prob_must=pm, open_must=om, min_act=1),
        s(f"heute {work} problem lieferung offen morgen", v["a2"],
          problem=True, open_=True, prob_must=("liefer", "spaet"), open_must=("morgen", "offen"), min_act=1),
        s(f"{v['w3']} bauherr kurz da und zufrieden", v["a3"], customer=True, cust_must=("zufrieden", "informiert"), min_act=1),
    ]


def _mega_mix(v: dict, trade: str) -> list[dict]:
    pm, om = PROB_OPEN[trade]
    raw = (
        f"{v['w1']} {v['rain']} {v['open']} {v['cust']} "
        f"Problem Lieferung spaet Offen Rest Montag"
    )
    return [
        s(raw, v["a1"], mats=v["mats"], problem=True, open_=True, customer=True,
          prob_must=pm, open_must=om + ("montag",), cust_not=("pflaster", "quadratmeter", "verlegt"),
          mat_echo=(trade == "GaLaBau"), sum_min_len=30),
        s(f"{v['w2']} {v['rain2']} {v['plan']} {v['cust2']}", v["a2"], problem=True, open_=True, customer=True,
          prob_must=pm, open_must=om, cust_must=("gesprochen", "informiert", "abgestimmt")),
    ]


def _qty_variants(v: dict, trade: str, start: int, step: int, count: int) -> list[dict]:
    pm, om = PROB_OPEN[trade]
    tails = [
        ("", False, False, False, (), ()),
        (" leider mussten wir wegen Regen abbrechen morgen müssen wir noch Rest fertig machen.", True, True, False, pm, om),
        (" Bauherr informiert.", False, False, True, (), ()),
        (" Kundin zufrieden.", False, False, True, (), ()),
        (" Problem Wetter Offen nächste Woche.", True, True, False, ("wetter", "regen"), ("woche", "offen")),
    ]
    out: list[dict] = []
    for i, qty in enumerate(range(start, start + step * count, step)):
        tail, prob, opn, cust, pms, oms = tails[i % len(tails)]
        raw = f"{qty} Quadratmeter Arbeit verlegt{tail}" if trade not in {"SHK", "Tiefbau"} else f"Arbeit Tag {qty}{tail}"
        if trade == "GaLaBau":
            raw = f"{qty} Quadratmeter Pflaster verlegt{tail}"
        elif trade == "Tiefbau":
            raw = f"{qty} Meter Kanalgraben ausgehoben{tail}"
        elif trade == "SHK":
            raw = f"Heizkörper getauscht Thermostatventile eingebaut{tail}"
        elif trade == "Putz":
            raw = f"{qty} Quadratmeter Putz aufgetragen{tail}"
        elif trade == "Fliesen":
            raw = f"{qty} Quadratmeter Fliesen verlegt{tail}"
        elif trade == "Trockenbau":
            raw = f"{qty} Quadratmeter Gipskarton montiert{tail}"
        out.append(s(raw, (), mats=v["mats"], problem=prob, open_=opn, customer=cust,
                       prob_must=pms or pm, open_must=oms or om,
                       cust_must=("zufrieden", "informiert") if cust else (),
                       cust_not=("quadratmeter", "verlegt") if cust else (), min_act=1))
    return out


def build_trade(trade: str) -> list[dict]:
    v = VOCAB[trade]
    items: list[dict] = []
    items += _core_live(v, trade)
    items += _explicit_markers(v, trade)
    items += _customer_rich(v)
    items += _work_runon(v, trade)
    items += _broken_short(v, trade)
    items += _mega_mix(v, trade)
    starts = {"GaLaBau": 18, "Trockenbau": 20, "Fliesen": 12, "SHK": 1, "Hochbau": 5, "Tiefbau": 10, "Putz": 40}
    steps = {"GaLaBau": 4, "Trockenbau": 5, "Fliesen": 4, "SHK": 1, "Hochbau": 4, "Tiefbau": 5, "Putz": 5}
    need = 60 - len(items)
    items += _qty_variants(v, trade, starts[trade], steps[trade], max(need, 1))
    return items[:60]


def main() -> None:
    lines = [
        '"""Pilot-Monster-Welle 25 — 60 Basisszenarien pro Gewerk (generiert)."""',
        "from __future__ import annotations",
        "from typing import Any, Iterator",
        f"TRADES = {TRADES!r}",
        "TRADE_SCENARIOS: dict[str, list[dict[str, Any]]] = {",
    ]
    for trade in TRADES:
        scenarios = build_trade(trade)
        assert len(scenarios) == 60, (trade, len(scenarios))
        lines.append(f'    "{trade}": [')
        for spec in scenarios:
            lines.append(f"        {spec!r},")
        lines.append("    ],")
    lines += [
        "}",
        "",
        "def all_base_scenarios() -> Iterator[tuple[str, dict[str, Any]]]:",
        "    for trade in TRADES:",
        "        for spec in TRADE_SCENARIOS[trade]:",
        "            yield trade, spec",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} — {len(TRADES) * 60} scenarios")


if __name__ == "__main__":
    main()
