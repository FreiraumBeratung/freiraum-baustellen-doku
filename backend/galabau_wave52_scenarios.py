"""Welle 52: GaLaBau-Schutznetz — 40 Basisszenarien (Gartenboys-Wortschatz + Alltag).

Rein additiv. Keine bestehenden Wellen aendern.
"""

from __future__ import annotations


def all_base_scenarios() -> list[dict]:
    return [
        {
            "raw": (
                "Heute Spritschutz kannte Steine gesetzt sowie Podest für Wassertonne. "
                "Zudem 3 l steine gesetzt."
            ),
            "acts": ("spritzschutz", "podest", "l-stein"),
            "mats": ("kantenstein", "l-stein"),
            "sugs": ("Beton",),
            "forbid_mats": ("Beton 0,5",),
            "forbid_acts": ("lfm", "Randsteine gesetzt"),
            "forbid_hours": True,
            "min_act": 3,
        },
        {
            "raw": "Heute 3 lstein gesetzt.",
            "acts": ("l-stein",),
            "mats": ("l-stein",),
            "sugs": ("Beton",),
            "forbid_acts": ("lfm",),
            "min_act": 1,
        },
        {
            "raw": "Heute 3 lsteine gesetzt.",
            "acts": ("l-stein",),
            "mats": ("l-stein",),
            "forbid_acts": ("lfm",),
            "min_act": 1,
        },
        {
            "raw": "Heute 3 l-steine gesetzt.",
            "acts": ("l-stein",),
            "mats": ("l-stein",),
            "forbid_acts": ("lfm",),
            "min_act": 1,
        },
        {
            "raw": "Heute 3 lfm Randsteine gesetzt.",
            "acts": ("lfm", "randstein"),
            "forbid_acts": ("l-stein",),
            "sugs": ("Beton",),
            "min_act": 1,
        },
        {
            "raw": "Wir haben tief vor Steine gesetzt.",
            "acts": ("randstein",),
            "forbid_acts": ("l-stein", "tiefbord"),
            "min_act": 1,
        },
        {
            "raw": (
                "Pflasterfläche aufgenommen im abgesackten Bereich Pflaster gestapelt seitlich. "
                "Schotter ca eine Schubkarre eingearbeitet verdichtet mittels Handstampfer "
                "Splitt aufgetragen höhengerecht abgezogen vorhandene Pflaster nach Muster neu verlegt "
                "mittels Kantholz und Gummihammer zurecht geschlagen einkehrmaterial eingearbeitet "
                "alte Holzleisten von der Gartenhütte demontiert neue Holzleisten zurechtgeschnitten und montiert "
                "alten Ilex Stamm mit der Kettensäge bodennah abgeschnitten Bauschutt und drei plastikstegplatten entsorgt."
            ),
            "acts": ("aufgenommen", "gestapelt", "schotter", "splitt", "muster", "holzleiste", "ilex", "bauschutt"),
            "mats": ("schotter", "splitt"),
            "forbid_acts": ("Gartenhütte demontiert",),
            "forbid_hours": True,
            "forbid_mats": ("1,5",),
            "min_act": 6,
        },
        {
            "raw": "Alte Holzleisten von der Gartenhütte demontiert neue Holzleisten zurechtgeschnitten und montiert.",
            "acts": ("holzleiste", "demontiert"),
            "forbid_acts": ("Gartenhütte demontiert",),
            "min_act": 1,
        },
        {
            "raw": "Alten Ilex Stamm mit der Kettensäge bodennah abgeschnitten und entsorgt.",
            "acts": ("ilex",),
            "forbid_hours": True,
            "min_act": 1,
        },
        {
            "raw": "Bauschutt aus dem Garten entsorgt ca eine Schubkarre voll drei plastikstegplatten mit entsorgt.",
            "acts": ("bauschutt", "stegplatten"),
            "min_act": 1,
        },
        {
            "raw": (
                "Heute 40 Quadratmeter Pflaster verlegt 12 laufende Meter Rasenkantensteine gesetzt "
                "und die Hecke geschnitten."
            ),
            "acts": ("pflaster", "rasenkantenstein", "hecke"),
            "mats": ("pflaster", "rasenkantenstein"),
            "sugs": ("Beton",),
            "forbid_mats": ("Beton 0",),
            "min_act": 3,
        },
        {
            "raw": "25 laufende Meter Rasenkantensteine gesetzt.",
            "acts": ("rasenkantenstein", "lfm"),
            "sugs": ("Beton",),
            "forbid_mats": ("Beton",),
            "min_act": 1,
        },
        {
            "raw": "Heute Randsteine gesetzt und 0,5 m³ Beton verarbeitet.",
            "acts": ("randstein",),
            "mats": ("beton",),
            "min_act": 1,
        },
        {
            "raw": "Palisaden gesetzt entlang der Terrasse.",
            "acts": ("palisad",),
            "sugs": ("Beton",),
            "min_act": 1,
        },
        {
            "raw": "Wir haben den Rasen gemäht vertikutiert und anschließend gedüngt.",
            "acts": ("gemäht", "vertikutiert", "gedüngt"),
            "min_act": 2,
        },
        {
            "raw": "100 Quadratmeter Rasen gemäht und Unkraut entfernt.",
            "acts": ("rasen", "unkraut"),
            "min_act": 2,
        },
        {
            "raw": "Laub entfernt und die Fläche mit Rindenmulch eingedeckt.",
            "acts": ("laub", "mulch"),
            "min_act": 2,
        },
        {
            "raw": "Hecke zurückgeschnitten Sträucher getrimmt und Beet angelegt.",
            "acts": ("hecke",),
            "min_act": 1,
        },
        {
            "raw": "Zwei Kubikmeter Schotter eingebaut und Splitt 2/5 aufgetragen und abgezogen.",
            "acts": ("schotter", "splitt"),
            "mats": ("schotter", "splitt"),
            "min_act": 2,
        },
        {
            "raw": "30 Quadratmeter Pflaster nach Muster neu verlegt Einkehrmaterial eingearbeitet.",
            "acts": ("pflaster", "einkehrmaterial"),
            "forbid_sugs": ("Fugensand",),
            "min_act": 2,
        },
        {
            "raw": "Pflasterfläche im abgesackten Bereich aufgenommen und Pflaster seitlich gestapelt.",
            "acts": ("aufgenommen", "gestapelt"),
            "forbid_acts": ("Gartenhütte",),
            "min_act": 2,
        },
        {
            "raw": "Splitt aufgetragen und höhengerecht abgezogen danach Pflaster mit Kantholz und Gummihammer zurecht geschlagen.",
            "acts": ("splitt", "kantholz"),
            "mats": ("splitt",),
            "min_act": 2,
        },
        {
            "raw": (
                "2 Stunden mit dem Bagger Erdaushub für die Einfahrt gemacht "
                "danach 3 Kubikmeter Schotter eingebaut."
            ),
            "acts": ("schotter", "bagger"),
            "mats": ("schotter",),
            "mach": ("Bagger: 2",),
            "min_act": 1,
        },
        {
            "raw": "Heute mit dem Bagger Aushub gemacht und Schotter verteilt.",
            "acts": ("schotter",),
            "mats": ("schotter",),
            "mach_sug": ("Bagger",),
            "forbid_hours": False,
            "min_act": 1,
        },
        {
            "raw": "Zaun gesetzt und Sichtschutz montiert am Garten.",
            "acts": ("zaun",),
            "min_act": 1,
        },
        {
            "raw": "20 Quadratmeter Keramikterrasse verlegt Geotextil verlegt und Splitt eingebaut.",
            "acts": ("keramik", "geotextil", "splitt"),
            "mats": ("splitt",),
            "min_act": 2,
        },
        {
            "raw": "Pflanzen gesetzt Pflanzkübel mit Erde befüllt und Fläche bewässert.",
            "acts": ("pflanzen",),
            "min_act": 1,
        },
        {
            "raw": "Kompost eingearbeitet Beet angelegt und Unkraut gejätet.",
            "acts": ("kompost", "unkraut"),
            "min_act": 1,
        },
        {
            "raw": (
                "Heute 50 Quadratmeter Pflaster verlegt Hecke geschnitten "
                "Bauherr kurz da Problem Lieferung kam spät Offen letzte Reihe morgen."
            ),
            "acts": ("pflaster", "hecke"),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 2,
        },
        {
            "raw": (
                "Rasenkantensteine gesetzt Pflaster verlegt Kundengespräch gelaufen "
                "Kunde war zufrieden Offen Fugen morgen."
            ),
            "acts": ("rasenkantenstein", "pflaster"),
            "sugs": ("Beton",),
            "open_": True,
            "customer": True,
            "min_act": 2,
        },
        {
            "raw": "Es hat den ganzen Nachmittag geregnet wir mussten die Pflasterarbeiten abbrechen.",
            "problem": True,
            "forbid_acts": (),
            "min_act": 0,
        },
        {
            "raw": "Heute Drainage im Garten verlegt und Filtervlies ausgelegt.",
            "acts": ("drainage",),
            "min_act": 1,
        },
        {
            "raw": "15 Quadratmeter Naturstein verlegt auf der Terrasse.",
            "acts": ("naturstein",),
            "min_act": 1,
        },
        {
            "raw": "Rollrasen verlegt 40 Quadratmeter und danach bewässert.",
            "acts": ("rasen",),
            "min_act": 1,
        },
        {
            "raw": "Heute Spritzschutz-Kantensteine gesetzt.",
            "acts": ("spritzschutz",),
            "mats": ("kantenstein",),
            "sugs": ("Beton",),
            "forbid_acts": ("Randsteine gesetzt",),
            "min_act": 1,
        },
        {
            "raw": "Podest für Wassertonne gesetzt hinterm Haus.",
            "acts": ("podest", "wassertonne"),
            "min_act": 1,
        },
        {
            "raw": "Einkehrmaterial eingearbeitet ein Sack nach dem Verlegen.",
            "acts": ("einkehrmaterial",),
            "min_act": 1,
        },
        {
            "raw": "Mit Handstampfer verdichtet Schotter eingearbeitet keine Stunden genannt.",
            "acts": ("schotter",),
            "forbid_hours": True,
            "min_act": 1,
        },
        {
            "raw": "Heute 3 l stein gesetzt und 8 lfm Randsteine gesetzt.",
            "acts": ("l-stein", "lfm", "randstein"),
            "forbid_hours": True,
            "min_act": 2,
        },
        {
            "raw": (
                "Morgens Pflaster aufgenommen gestapelt Schotter und Splitt eingebaut "
                "nachmittags Palisaden gesetzt Kunde kam vorbei war zufrieden "
                "Problem Untergrund nass Offen Reststeine morgen."
            ),
            "acts": ("pflaster", "schotter", "palisad"),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 2,
        },
    ]
