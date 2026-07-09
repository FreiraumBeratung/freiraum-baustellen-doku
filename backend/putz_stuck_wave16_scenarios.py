"""Putz & Stuck Welle 16 — generierte Basisszenarien (JSON Engine-Welle A)."""

from __future__ import annotations


def all_base_scenarios() -> list[dict]:
    return [
        {
            "raw": 'WDVS Dämmung geklebt mit EPS und Klebe- und Armierungsmörtel 120 Quadratmeter.',
            "acts": ('WDVS Dämmung geklebt',),
            "mats": ('EPS Dämmplatten', 'Klebe- und Armierungsmörtel'),
        },
        {
            "raw": 'Dämmplatten geklebt Mineralwolle 80 Millimeter WDVS kleben fertig.',
            "acts": ('WDVS Dämmung geklebt',),
            "mats": ('Mineralwolle Dämmplatten',),
        },
        {
            "raw": 'Heute WDVS kleben mit Zahntraufel Holzfaserplatten angebracht.',
            "acts": ('WDVS Dämmung geklebt',),
            "mats": ('Holzfaserplatten',),
        },
        {
            "raw": 'WDVS Dämmung kleben Problem Kleber knapp Offen Rest morgen Kunde informiert.',
            "acts": ('WDVS Dämmung geklebt',),
            "problem": True,
            "open_": True,
            "customer": True,
        },
        {
            "raw": 'hamma WDVS Dämmung geklebt mit EPS fertig.',
            "acts": ('WDVS Dämmung geklebt',),
            "min_act": 1,
        },
        {
            "raw": 'WDVS gedübelt mit Tellerdübel 160 Millimeter überall befestigt.',
            "acts": ('WDVS gedübelt',),
            "mats": ('Tellerdübel',),
        },
        {
            "raw": 'Dämmung dübeln WDVS befestigen Tellerdübel gesetzt.',
            "acts": ('WDVS gedübelt',),
            "mats": ('Tellerdübel',),
        },
        {
            "raw": 'Nach dem Kleben WDVS gedübelt Schlagdübel und Tellerdübel.',
            "acts": ('WDVS gedübelt',),
            "mats": ('Tellerdübel',),
        },
        {
            "raw": 'WDVS dübeln fertig Problem Bohrer defekt Offen Sockel morgen.',
            "acts": ('WDVS gedübelt',),
            "problem": True,
            "open_": True,
        },
        {
            "raw": 'ich hab WDVS gedübelt mit Tellerdübel gemacht.',
            "acts": ('WDVS gedübelt',),
            "min_act": 1,
        },
        {
            "raw": 'WDVS Platten angeklebt Armierungsgewebe eingebettet Reibputz drauf.',
            "acts": ('WDVS ausgeführt', 'Armierung ausgeführt', 'Reibputz aufgetragen'),
        },
        {
            "raw": 'Fassade gedämmt Gewebe reingemacht Außenputz aufgetragen.',
            "acts": ('WDVS ausgeführt', 'Fassadenarmierung ausgeführt', 'Außenputz aufgetragen'),
        },
        {
            "raw": 'Putz geglättet mit Feinputz und Glättkelle 45 Quadratmeter.',
            "acts": ('Putz geglättet',),
            "mats": ('Feinputz',),
        },
        {
            "raw": 'Innenputz glätten fertig Feinputz verarbeitet.',
            "acts": ('Putz geglättet',),
            "mats": ('Feinputz',),
        },
        {
            "raw": 'Oberfläche finishen Putz glätten Schwammbrett benutzt.',
            "acts": ('Putz geglättet',),
        },
        {
            "raw": 'Putz glätten Problem Gerüst spät Offen Decke morgen Bauherr informiert.',
            "acts": ('Putz geglättet',),
            "problem": True,
            "open_": True,
            "customer": True,
        },
        {
            "raw": 'Putz filziert mit Filzbrett Struktur fertig.',
            "acts": ('Putz filziert',),
            "mats": ('Feinputz',),
        },
        {
            "raw": 'Außenputz filzen Feinputz verarbeitet fertig.',
            "acts": ('Putz filziert',),
        },
        {
            "raw": 'Putz filzen mit Schwammbrett gemacht.',
            "acts": ('Putz filziert',),
            "min_act": 1,
        },
        {
            "raw": 'Gipsputz aufgetragen 60 Quadratmeter Innenputz verarbeitet.',
            "acts": ('Innenputz aufgetragen',),
            "mats": ('Gipsputz',),
        },
        {
            "raw": 'Kalkputz und Lehmputz im Wohnbereich aufgebracht.',
            "acts": ('Innenputz aufgetragen',),
            "mats": ('Kalkputz', 'Lehmputz'),
            "min_act": 1,
        },
        {
            "raw": 'Silikatputz an der Fassade aufgetragen Außenputz verarbeitet.',
            "acts": ('Außenputz aufgetragen',),
            "mats": ('Silikatputz',),
        },
        {
            "raw": 'Silikonharzputz außen aufgebracht Kratzputz vorbereitet.',
            "acts": ('Außenputz aufgetragen',),
            "mats": ('Silikonharzputz',),
            "min_act": 1,
        },
        {
            "raw": 'Morgens WDVS Dämmung geklebt mittags WDVS gedübelt nachmittags Armierungsgewebe eingebettet Reibputz aufgetragen Bauleitung zufrieden Problem Wind Offen letzte Fläche Montag.',
            "acts": ('WDVS Dämmung geklebt', 'WDVS gedübelt', 'Armierung ausgeführt', 'Reibputz aufgetragen'),
            "problem": True,
            "open_": True,
            "customer": True,
        },
        {
            "raw": 'Unterputz aufgetragen Oberputz aufgetragen Putz geglättet mit Feinputz fertig.',
            "acts": ('Unterputz aufgetragen', 'Oberputz aufgetragen', 'Putz geglättet'),
            "mats": ('Feinputz',),
        },
        {
            "raw": 'Kratzputz aufgetragen Putz filziert Außenputz strukturiert.',
            "acts": ('Kratzputz aufgetragen', 'Putz filziert', 'Außenputz aufgetragen'),
        },
        {
            "raw": 'WDVS Dämmung geklebt WDVS gedübelt Armierungsgewebe eingebettet.',
            "acts": ('WDVS Dämmung geklebt', 'WDVS gedübelt', 'Armierung ausgeführt'),
            "min_act": 2,
        },
        {
            "raw": 'Heute nur Material geliefert Offen WDVS kleben morgen.',
            "acts": (),
            "open_": True,
            "min_act": 0,
        },
        {
            "raw": 'Kundengespräch Putzmuster gewählt Problem Feuchte Offen nächste Woche.',
            "acts": (),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 0,
        },
    ]
