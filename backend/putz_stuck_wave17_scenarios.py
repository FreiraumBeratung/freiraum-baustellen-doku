"""Putz & Stuck Welle 17 — generierte Basisszenarien (Profil-Cluster)."""

from __future__ import annotations


def all_base_scenarios() -> list[dict]:
    return [
        {
            "raw": 'APU-Leiste 6mm montiert am Fensteranschluss mit Klebeputz.',
            "acts": ('APU-Leisten montiert',),
            "mats": ('APU-Leiste', 'Klebeputz'),
        },
        {
            "raw": 'Anputzleiste 9mm gesetzt Fensteranschlussprofil montiert.',
            "acts": ('APU-Leisten montiert',),
            "mats": ('APU-Leiste',),
            "min_act": 1,
        },
        {
            "raw": 'APU-Leiste mit Gewebe montiert Problem Material knapp Offen Rest morgen.',
            "acts": ('APU-Leisten montiert',),
            "problem": True,
            "open_": True,
        },
        {
            "raw": 'hamma APU-Leiste montiert fertig.',
            "acts": ('APU-Leisten montiert',),
            "min_act": 1,
        },
        {
            "raw": 'Eckschutzschiene Alu gesetzt an allen Außenecken.',
            "acts": ('Eckschutzprofile gesetzt',),
            "mats": ('Eckschutzschiene',),
        },
        {
            "raw": 'Eckprofil PVC montiert Kantenschutz verarbeitet.',
            "acts": ('Eckschutzprofile gesetzt',),
        },
        {
            "raw": 'Eckschutzprofile gesetzt mit Klebeputz und Spachtelmasse.',
            "acts": ('Eckschutzprofile gesetzt',),
            "mats": ('Eckschutzschiene', 'Klebeputz'),
        },
        {
            "raw": 'Leibungsprofil PVC am Fenster gesetzt.',
            "acts": ('Leibungsprofile gesetzt',),
            "mats": ('Leibungsprofil',),
        },
        {
            "raw": 'Laibungsprofil Alu montiert Fensterleibung fertig.',
            "acts": ('Leibungsprofile gesetzt',),
            "mats": ('Leibungsprofil',),
        },
        {
            "raw": 'Leibungsprofile gesetzt Dichtlippe montiert Kunde informiert.',
            "acts": ('Leibungsprofile gesetzt',),
            "customer": True,
        },
        {
            "raw": 'Sockelprofil 8mm montiert mit Tropfkante.',
            "acts": ('Sockelprofile montiert',),
            "mats": ('Sockelprofil',),
        },
        {
            "raw": 'Startprofil 10mm gesetzt Sockelschiene angebracht.',
            "acts": ('Sockelprofile montiert',),
            "mats": ('Sockelprofil',),
        },
        {
            "raw": 'Sockelprofile montiert Sockeldämmung und Noppenbahn verarbeitet.',
            "acts": ('Sockelprofile montiert',),
        },
        {
            "raw": 'Tropfkantenprofil Alu gesetzt unter Fensterbank.',
            "acts": ('Tropfkantenprofile gesetzt',),
            "mats": ('Tropfkantenprofil',),
        },
        {
            "raw": 'Abtropfkante PVC montiert Tropfkante mit Gewebe.',
            "acts": ('Tropfkantenprofile gesetzt',),
            "mats": ('Tropfkantenprofil',),
        },
        {
            "raw": 'Tropfkantenprofile gesetzt Klebeputz und Armierungsmörtel benutzt.',
            "acts": ('Tropfkantenprofile gesetzt',),
            "mats": ('Klebeputz', 'Armierungsmörtel'),
        },
        {
            "raw": 'WDVS Dämmung geklebt. Sockelprofil montiert. APU-Leiste montiert.',
            "acts": ('WDVS Dämmung geklebt', 'Sockelprofile montiert', 'APU-Leisten montiert'),
        },
        {
            "raw": 'Sockelprofil montiert APU-Leiste montiert Leibungsprofil gesetzt Eckschutz gesetzt.',
            "acts": ('Sockelprofile montiert', 'APU-Leisten montiert', 'Leibungsprofile gesetzt', 'Eckschutzprofile gesetzt'),
            "min_act": 3,
        },
        {
            "raw": 'Eckschutzprofile gesetzt. Tropfkantenprofile gesetzt. Reibputz aufgetragen.',
            "acts": ('Eckschutzprofile gesetzt', 'Tropfkantenprofile gesetzt', 'Reibputz aufgetragen'),
        },
        {
            "raw": 'An der Fassade WDVS gedübelt Armierungsgewebe eingebettet Sockelprofil montiert APU-Leisten montiert Leibungsprofile gesetzt Bauherr zufrieden Problem Wind Offen letzte Ecke Montag.',
            "acts": ('WDVS gedübelt', 'Armierung ausgeführt', 'Sockelprofile montiert', 'APU-Leisten montiert', 'Leibungsprofile gesetzt'),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 4,
        },
        {
            "raw": 'Leibungsprofil gesetzt. Eckschutzschiene gesetzt. Außenputz aufgetragen.',
            "acts": ('Leibungsprofile gesetzt', 'Eckschutzprofile gesetzt', 'Außenputz aufgetragen'),
        },
        {
            "raw": 'Sockelputz aufgetragen und verarbeitet.',
            "acts": ('Sockelputz aufgetragen',),
            "forbid_acts": ('Sockelprofile montiert',),
        },
        {
            "raw": 'Sockelleiste stuckiert Gesims angebracht.',
            "acts": ('Stuckarbeiten durchgeführt',),
            "forbid_acts": ('Sockelprofile montiert',),
        },
        {
            "raw": 'heute APU montiert und Eckschutz gemacht.',
            "acts": ('APU-Leisten montiert', 'Eckschutzprofile gesetzt'),
            "min_act": 1,
        },
        {
            "raw": 'ich hab Leibung und Tropfkante gesetzt.',
            "acts": ('Leibungsprofile gesetzt', 'Tropfkantenprofile gesetzt'),
            "min_act": 1,
        },
        {
            "raw": '40 Meter Eckschutzschiene gesetzt fertig.',
            "acts": ('Eckschutzprofile gesetzt',),
            "min_act": 1,
        },
        {
            "raw": 'Kundengespräch Profile abgestimmt Problem Lieferung spät Offen APU nächste Woche.',
            "acts": (),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 0,
        },
    ]
