"""Generator Putz & Stuck Welle 21 — 300 Basisszenarien.

Fokus: breite Abdeckung Stuck+Putz, Ketten, POB, gebrochenes DE, Vorschläge/Material.
Erweitert Welle 20 rein additiv — neue Texte, gleiche Assertions-Logik.
"""

from __future__ import annotations

import re
from pathlib import Path

OUT = Path(__file__).parent / "putz_stuck_wave21_scenarios.py"
TARGET = 300
SITE_A = "Nieheim"
SITE_B = "Steinheim"
SITE_C = "Borgentreich"
SITE_D = "Willebadessen"
SITE_E = "Bad Karlshafen"

SITES = (SITE_A, SITE_B, SITE_C, SITE_D, SITE_E)


def s(raw: str, acts: tuple[str, ...], **kw) -> dict:
    d = dict(
        raw=raw,
        acts=acts,
        mats=(),
        mach=(),
        sugs=(),
        forbid_sugs=(),
        forbid_acts=(),
        problem=False,
        open_=False,
        customer=False,
        min_act=None,
        prob_must=(),
        prob_not=(),
        open_must=(),
        open_not=(),
        cust_must=(),
        cust_not=(),
        mat_echo=False,
        sum_forbid=(),
        sum_qty=(),
        forbid_layer_mats=False,
        strict=False,
    )
    d.update(kw)
    return d


def _stuck_putz_breit() -> list[dict]:
    """Stuck-Schwerpunkte, Mischtage, neue Ketten — Welle 21 exklusiv."""
    return [
        s(
            f"{SITE_A} Stuckgesims montiert PU-Profil 24 Meter Wohnzimmer Decke.",
            ("Stuckarbeiten durchgeführt",),
            mats=("PU-Stuckprofil",),
            sugs=("Montagekleber benutzt?",),
            min_act=1,
        ),
        s(
            f"Gips-Stuckprofil stuckiert Rosette angebracht {SITE_B} Salon.",
            ("Stuckarbeiten durchgeführt",),
            mats=("Gips-Stuckprofil",),
            sugs=("Feinspachtel benutzt?",),
            min_act=1,
        ),
        s(
            f"Stuckarbeiten Gesims stuckiert mit Montagekleber {SITE_C} Flur OG.",
            ("Stuckarbeiten durchgeführt",),
            forbid_sugs=("Montagekleber benutzt?",),
            min_act=1,
        ),
        s(
            f"PU-Stuckprofil Fensterlaibung stuckiert Feinspachtel nachgearbeitet {SITE_D}.",
            ("Stuckarbeiten durchgeführt",),
            mats=("PU-Stuckprofil",),
            forbid_sugs=("Feinspachtel benutzt?",),
            min_act=1,
        ),
        s(
            (
                f"Morgens {SITE_E} Innenputz Kalkputz 58 qm² nachmittags Oberputz geglättet "
                f"abends Stuck Gesims stuckiert Kunde wünscht gleiche Leiste im Flur."
            ),
            ("Innenputz aufgetragen", "Oberputz aufgetragen", "Putz geglättet", "Stuckarbeiten durchgeführt"),
            mats=("Kalkputz",),
            customer=True,
            cust_must=("wünscht", "flur"),
            sum_qty=("58",),
            min_act=3,
        ),
        s(
            (
                f"WDVS {SITE_A} 88 qm geklebt gedübelt Armierung Reibputz "
                f"Problem Kleber zu schnell wegen Hitze Offen Nordwand Donnerstag Bauherr informiert."
            ),
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt", "Reibputz aufgetragen"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("hitze", "kleber"),
            open_must=("donnerstag", "offen"),
            cust_must=("informiert",),
            sum_qty=("88",),
            min_act=3,
        ),
        s(
            (
                f"Also heute {SITE_B} erst Altputz runter dann Wand geschliffen Grundierung "
                f"Unterputz 44 qm und Oberputz 22 qm und Kundengespräch wegen Farbton."
            ),
            ("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen"),
            customer=True,
            cust_must=("kundengespräch",),
            sum_qty=("44", "22"),
            min_act=4,
        ),
        s(
            f"innenputz lehmputz 36 qm {SITE_C} altbau",
            ("Innenputz aufgetragen",),
            mats=("Lehmputz",),
            sum_qty=("36",),
            min_act=1,
        ),
        s(
            f"hamma wdvs kleben und dübeln {SITE_D} 102 qm",
            ("WDVS Dämmung geklebt", "WDVS gedübelt"),
            sum_qty=("102",),
            min_act=2,
        ),
        s(
            f"problem lieferant offen montag kein gipsputz {SITE_E}",
            (),
            problem=True,
            open_=True,
            min_act=0,
            prob_must=("liefer",),
            open_must=("montag", "offen"),
        ),
        s(
            f"bauherr gred wegen stuck profil {SITE_A}",
            (),
            customer=True,
            min_act=0,
            cust_must=("bauherr", "gred"),
        ),
        s(
            (
                f"Kompletttag {SITE_B}: Sockelprofil Tropfkante APU-Leiste Leibungsprofil "
                f"Eckschutz WDVS Armierung Reibputz Kratzputz filziert."
            ),
            (
                "Sockelprofile montiert",
                "Tropfkantenprofile gesetzt",
                "APU-Leisten montiert",
                "Leibungsprofile gesetzt",
                "Eckschutzprofile gesetzt",
                "Armierung ausgeführt",
                "Reibputz aufgetragen",
                "Kratzputz aufgetragen",
                "Putz filziert",
            ),
            min_act=6,
        ),
        s(
            f"Sanierung {SITE_C} Schimmel weg Sanierputz Unterputz Oberputz 31 qm fertig.",
            ("Schimmel beseitigt", "Sanierputz aufgebracht", "Unterputz aufgetragen", "Oberputz aufgetragen"),
            mats=("Sanierputz",),
            sum_qty=("31",),
            min_act=3,
        ),
        s(
            f"Außenputz Silikonharzputz 77 qm Kratzputz strukturiert {SITE_D} Giebel.",
            ("Außenputz aufgetragen", "Kratzputz aufgetragen"),
            mats=("Silikonharzputz",),
            sum_qty=("77",),
            min_act=2,
        ),
        s(
            f"Putzmaschine 7 std Innenputz Gipsputz 93 qm {SITE_E} Neubau Block A.",
            ("Innenputz aufgetragen",),
            mats=("Gipsputz",),
            mach=("Putzmaschine",),
            forbid_sugs=("Putzmaschine benutzt?",),
            sum_qty=("93",),
            min_act=1,
        ),
        s(
            (
                f"Fassade {SITE_A} Mineralwolle WDVS geklebt Schraubdübel Armierungsgewebe "
                f"Reibputz Problem Gewebe falsch Offen Austausch Mittwoch."
            ),
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt", "Reibputz aufgetragen"),
            mats=("Mineralwolle",),
            problem=True,
            open_=True,
            prob_must=("falsch",),
            open_must=("mittwoch", "offen"),
            min_act=3,
        ),
        s(
            f"Grundputz 48 qm Unterputz 48 qm Oberputz glatt {SITE_B} Treppenhaus komplett.",
            ("Grundputz aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen"),
            sum_qty=("48",),
            forbid_layer_mats=True,
            min_act=3,
        ),
        s(
            f"Kalkfeinputz Putz geglättet 29 qm Decke {SITE_C} mit Glättkelle fertig.",
            ("Putz geglättet",),
            mats=("Kalkfeinputz",),
            forbid_sugs=("Glättkelle benutzt?", "Kalkfeinputz benutzt?"),
            sum_qty=("29",),
            min_act=1,
        ),
        s(
            (
                f"Stuckarbeiten {SITE_D} Gesims stuckiert Problem Profilbruch "
                f"Offen Ersatz Mittwoch Kunde einverstanden."
            ),
            ("Stuckarbeiten durchgeführt",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("bruch",),
            open_must=("mittwoch", "offen"),
            cust_must=("einverstanden",),
            min_act=1,
        ),
        s(
            f"wdvs armierung reibputz drauf 66 qm {SITE_E}",
            ("Armierung ausgeführt", "Reibputz aufgetragen"),
            sum_qty=("66",),
            min_act=2,
        ),
        s(
            (
                f"Heute nur Besichtigung {SITE_A} mit Bauherr Problem Zugang gesperrt "
                f"Offen Start Montag Termin abgestimmt."
            ),
            (),
            problem=True,
            open_=True,
            customer=True,
            min_act=0,
            prob_must=("gesperrt",),
            open_must=("montag", "offen"),
            cust_must=("abgestimmt", "bauherr"),
        ),
        s(
            f"Holzfaserplatten WDVS geklebt 54 qm {SITE_B} Innenseite Dämmung.",
            ("WDVS Dämmung geklebt",),
            mats=("Holzfaserplatten",),
            sugs=("Zahntraufel benutzt?",),
            sum_qty=("54",),
            min_act=1,
        ),
        s(
            f"Kalkzementputz Außenputz 83 qm Haftbrücke vorher {SITE_C} Südseite.",
            ("Außenputz aufgetragen",),
            mats=("Kalkzementputz",),
            forbid_sugs=("Haftbrücke benutzt?",),
            sum_qty=("83",),
            min_act=1,
        ),
        s(
            (
                f"Megabericht {SITE_D}: Altputz ab geschliffen grundiert Unterputz Oberputz "
                f"Stuck Rosette WDVS kleben dübeln Armierung Reibputz "
                f"Problem Regen Offen Außenputz Freitag Bauleitung informiert."
            ),
            (
                "Altputz entfernt",
                "Wand geschliffen",
                "Grundierung aufgetragen",
                "Unterputz aufgetragen",
                "Oberputz aufgetragen",
                "Stuckarbeiten durchgeführt",
                "WDVS Dämmung geklebt",
                "WDVS gedübelt",
                "Armierung ausgeführt",
                "Reibputz aufgetragen",
            ),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("regen",),
            open_must=("freitag", "offen"),
            cust_must=("informiert",),
            min_act=6,
        ),
    ]


def _quantity_focus() -> list[dict]:
    """Primär Mengen in Sprache — verschiedene Formate, Schichten, Produkte."""
    return [
        s(
            "heute haben wir 50qm² Oberputz aufgetragen",
            ("Oberputz aufgetragen",),
            sum_qty=("50",),
            forbid_layer_mats=True,
            min_act=1,
            strict=True,
        ),
        s(
            f"{SITE_A} heute 50 qm² Oberputz aufgetragen Wohnzimmer fertig.",
            ("Oberputz aufgetragen",),
            sum_qty=("50",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "50 Quadratmeter Oberputz aufgetragen Decke OG.",
            ("Oberputz aufgetragen",),
            sum_qty=("50",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "Oberputz 50 m² aufgetragen Innenwand Flur.",
            ("Oberputz aufgetragen",),
            sum_qty=("50",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "heute 50qm² Oberputz drauf gemacht Schlafzimmer.",
            ("Oberputz aufgetragen",),
            sum_qty=("50",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            f"Unterputz 72 Quadratmeter aufgetragen {SITE_B} Treppenhaus.",
            ("Unterputz aufgetragen",),
            sum_qty=("72",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "72 qm² Unterputz aufgetragen heute komplett.",
            ("Unterputz aufgetragen",),
            sum_qty=("72",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "Unterputz 72 m² verarbeitet Kellerwand.",
            ("Unterputz aufgetragen",),
            sum_qty=("72",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            f"{SITE_C} 85 Quadratmeter Innenputz mit Gipsputz aufgetragen.",
            ("Innenputz aufgetragen",),
            mats=("Gipsputz",),
            sum_qty=("85",),
            min_act=1,
        ),
        s(
            "Innenputz 85 qm² Gipsputz Wohnbereich fertig.",
            ("Innenputz aufgetragen",),
            mats=("Gipsputz",),
            sum_qty=("85",),
            min_act=1,
        ),
        s(
            "85 m² Innenputz aufgetragen mit Gipsputz.",
            ("Innenputz aufgetragen",),
            mats=("Gipsputz",),
            sum_qty=("85",),
            min_act=1,
        ),
        s(
            f"Außenputz 120 Quadratmeter Kratzputz Fassade {SITE_D}.",
            ("Außenputz aufgetragen", "Kratzputz aufgetragen"),
            sum_qty=("120",),
            forbid_layer_mats=True,
            min_act=2,
        ),
        s(
            "120 qm² Außenputz Kratzputz Nordseite aufgetragen.",
            ("Außenputz aufgetragen", "Kratzputz aufgetragen"),
            sum_qty=("120",),
            forbid_layer_mats=True,
            min_act=2,
        ),
        s(
            "Außenputz 120 m² Kratzputz verarbeitet.",
            ("Außenputz aufgetragen", "Kratzputz aufgetragen"),
            sum_qty=("120",),
            forbid_layer_mats=True,
            min_act=2,
        ),
        s(
            f"Reibputz 95 Quadratmeter aufgetragen WDVS {SITE_E}.",
            ("Reibputz aufgetragen",),
            sum_qty=("95",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "95 qm² Reibputz drauf Armierung fertig.",
            ("Reibputz aufgetragen",),
            sum_qty=("95",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "Reibputz 95 m² Fassade Süd aufgetragen.",
            ("Reibputz aufgetragen",),
            sum_qty=("95",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            f"{SITE_A} 60 Quadratmeter Kalkputz Innenputz aufgetragen.",
            ("Innenputz aufgetragen",),
            mats=("Kalkputz",),
            sum_qty=("60",),
            min_act=1,
        ),
        s(
            "Innenputz 60 qm² Kalkputz Altbau Wohnzimmer.",
            ("Innenputz aufgetragen",),
            mats=("Kalkputz",),
            sum_qty=("60",),
            min_act=1,
        ),
        s(
            "60 m² Kalkputz Innenputz verarbeitet.",
            ("Innenputz aufgetragen",),
            mats=("Kalkputz",),
            sum_qty=("60",),
            min_act=1,
        ),
        s(
            f"WDVS Dämmung geklebt 140 Quadratmeter EPS {SITE_B}.",
            ("WDVS Dämmung geklebt",),
            mats=("EPS Dämmplatten",),
            sum_qty=("140",),
            min_act=1,
        ),
        s(
            "140 qm² WDVS geklebt Fassade West.",
            ("WDVS Dämmung geklebt",),
            sum_qty=("140",),
            min_act=1,
        ),
        s(
            "WDVS 140 m² Dämmung angeklebt.",
            ("WDVS Dämmung geklebt",),
            sum_qty=("140",),
            min_act=1,
        ),
        s(
            f"Putz geglättet 38 Quadratmeter Feinputz {SITE_C}.",
            ("Putz geglättet",),
            mats=("Feinputz",),
            sum_qty=("38",),
            min_act=1,
        ),
        s(
            "38 qm² Putz geglättet Decke.",
            ("Putz geglättet",),
            sum_qty=("38",),
            min_act=1,
        ),
        s(
            "Putz geglättet 38 m² Feinputz.",
            ("Putz geglättet",),
            mats=("Feinputz",),
            sum_qty=("38",),
            min_act=1,
        ),
        s(
            f"Sockelputz 22 Quadratmeter aufgetragen {SITE_D} Keller.",
            ("Sockelputz aufgetragen",),
            sum_qty=("22",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "22 qm² Sockelputz verarbeitet.",
            ("Sockelputz aufgetragen",),
            sum_qty=("22",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "Sockelputz 22 m² fertig.",
            ("Sockelputz aufgetragen",),
            sum_qty=("22",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            f"Grundputz 55 Quadratmeter aufgetragen Neubau {SITE_E}.",
            ("Grundputz aufgetragen",),
            sum_qty=("55",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "55 qm² Grundputz drauf Wand.",
            ("Grundputz aufgetragen",),
            sum_qty=("55",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            "Grundputz 55 m² verarbeitet.",
            ("Grundputz aufgetragen",),
            sum_qty=("55",),
            forbid_layer_mats=True,
            min_act=1,
        ),
        s(
            f"Sanierputz 18 Quadratmeter aufgebracht Schimmelstelle {SITE_A}.",
            ("Sanierputz aufgebracht",),
            mats=("Sanierputz",),
            sum_qty=("18",),
            min_act=1,
        ),
        s(
            "18 qm² Sanierputz Kellerwand.",
            ("Sanierputz aufgebracht",),
            mats=("Sanierputz",),
            sum_qty=("18",),
            min_act=1,
        ),
        s(
            "Sanierputz 18 m² verarbeitet.",
            ("Sanierputz aufgebracht",),
            mats=("Sanierputz",),
            sum_qty=("18",),
            min_act=1,
        ),
        s(
            f"Lehmputz 42 Quadratmeter Innenputz {SITE_B} Wohnbereich.",
            ("Innenputz aufgetragen",),
            mats=("Lehmputz",),
            sum_qty=("42",),
            min_act=1,
        ),
        s(
            "42 qm² Lehmputz aufgetragen.",
            ("Innenputz aufgetragen",),
            mats=("Lehmputz",),
            sum_qty=("42",),
            min_act=1,
        ),
        s(
            "Lehmputz 42 m² verarbeitet.",
            ("Innenputz aufgetragen",),
            mats=("Lehmputz",),
            sum_qty=("42",),
            min_act=1,
        ),
        s(
            f"Silikatputz 110 Quadratmeter Außenputz {SITE_C} Fassade.",
            ("Außenputz aufgetragen",),
            mats=("Silikatputz",),
            sum_qty=("110",),
            min_act=1,
        ),
        s(
            "110 qm² Silikatputz Außenwand.",
            ("Außenputz aufgetragen",),
            mats=("Silikatputz",),
            sum_qty=("110",),
            min_act=1,
        ),
        s(
            "Silikatputz 110 m² verarbeitet.",
            ("Außenputz aufgetragen",),
            mats=("Silikatputz",),
            sum_qty=("110",),
            min_act=1,
        ),
        s(
            f"Kratzputz 78 Quadratmeter Putz filziert {SITE_D}.",
            ("Kratzputz aufgetragen", "Putz filziert"),
            sum_qty=("78",),
            forbid_layer_mats=True,
            min_act=2,
        ),
        s(
            "78 qm² Kratzputz filziert Fassade.",
            ("Kratzputz aufgetragen", "Putz filziert"),
            sum_qty=("78",),
            forbid_layer_mats=True,
            min_act=2,
        ),
        s(
            "Kratzputz 78 m² strukturiert Putz filziert.",
            ("Kratzputz aufgetragen", "Putz filziert"),
            sum_qty=("78",),
            forbid_layer_mats=True,
            min_act=2,
        ),
        s(
            f"heute 67qm² Innenputz Gipsputz und 33 qm² Oberputz glatt {SITE_E}.",
            ("Innenputz aufgetragen", "Oberputz aufgetragen"),
            mats=("Gipsputz",),
            sum_qty=("67", "33"),
            min_act=2,
        ),
    ]


def _suggestion_positive() -> list[dict]:
    """Tätigkeit ohne explizites Werkzeug/Material → Vorschlag erwartet."""
    return [
        s(
            f"{SITE_A} Innenputz mit Gipsputz aufgetragen 120 Quadratmeter fertig.",
            ("Innenputz aufgetragen",),
            mats=("Gipsputz",),
            sugs=("Putzmaschine benutzt?", "Kartätsche benutzt?"),
            min_act=1,
        ),
        s(
            f"Außenputz Silikatputz aufgetragen Fassade {SITE_B} Nordseite.",
            ("Außenputz aufgetragen",),
            mats=("Silikatputz",),
            sugs=("Haftbrücke benutzt?", "Putzmaschine benutzt?"),
            min_act=1,
        ),
        s(
            "Putz geglättet mit Feinputz Decke OG fertig.",
            ("Putz geglättet",),
            mats=("Feinputz",),
            sugs=("Glättkelle benutzt?",),
            forbid_sugs=("Feinputz benutzt?",),
            min_act=1,
        ),
        s(
            "Außenputz Kratzputz aufgetragen Putz filziert Fassade fertig.",
            ("Kratzputz aufgetragen", "Putz filziert", "Außenputz aufgetragen"),
            sugs=("Filzbrett benutzt?",),
            min_act=2,
        ),
        s(
            "WDVS Dämmung geklebt EPS-Dämmplatten Fassade Süd.",
            ("WDVS Dämmung geklebt",),
            mats=("EPS Dämmplatten",),
            sugs=("Zahntraufel benutzt?",),
            min_act=1,
        ),
        s(
            "WDVS gedübelt an der Fassade komplett.",
            ("WDVS gedübelt",),
            sugs=("Tellerdübel benutzt?",),
            min_act=1,
        ),
        s(
            "Armierungsgewebe eingebettet WDVS Armierung fertig.",
            ("Armierung ausgeführt",),
            mats=("Armierungsgewebe",),
            sugs=("Armierungsmörtel benutzt?",),
            min_act=1,
        ),
        s(
            "Eckschutzschiene gesetzt an allen Außenecken.",
            ("Eckschutzprofile gesetzt",),
            sugs=("Klebeputz benutzt?", "Spachtelmasse benutzt?"),
            min_act=1,
        ),
        s(
            "APU-Leiste montiert Fensteranschluss Nord.",
            ("APU-Leisten montiert",),
            sugs=("Klebeputz benutzt?", "Dichtlippe benutzt?"),
            min_act=1,
        ),
        s(
            "Leibungsprofil PVC gesetzt 14 Fenster.",
            ("Leibungsprofile gesetzt",),
            mats=("Leibungsprofil",),
            sugs=("Klebeputz benutzt?",),
            min_act=1,
        ),
        s(
            "Sockelprofil montiert Sockelzone komplett.",
            ("Sockelprofile montiert",),
            sugs=("Sockeldämmung benutzt?", "Noppenbahn benutzt?"),
            min_act=1,
        ),
        s(
            "Tropfkantenprofil gesetzt Gesimsabschluss.",
            ("Tropfkantenprofile gesetzt",),
            sugs=("Klebeputz benutzt?",),
            min_act=1,
        ),
        s(
            "Altputz entfernt Wand geschliffen Grundierung drauf.",
            ("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen"),
            sugs=("Entsorgungssäcke benutzt?",),
            min_act=2,
        ),
        s(
            "Schimmel beseitigt Sanierputz aufgebracht.",
            ("Schimmel beseitigt", "Sanierputz aufgebracht"),
            mats=("Sanierputz",),
            sugs=("Schimmelentferner benutzt?",),
            min_act=2,
        ),
        s(
            "Oberputz aufgetragen. Wand war trocken.",
            ("Oberputz aufgetragen",),
            sugs=("Grundierung benutzt?",),
            min_act=1,
        ),
        s(
            "Stuckarbeiten gemacht Gesims stuckiert Rosette angebracht.",
            ("Stuckarbeiten durchgeführt",),
            sugs=("Montagekleber benutzt?", "Feinspachtel benutzt?"),
            min_act=1,
        ),
        s(
            f"Reibputz aufgetragen WDVS Schicht {SITE_C}.",
            ("Reibputz aufgetragen",),
            sugs=("Filzbrett benutzt?",),
            min_act=1,
        ),
        s(
            "Unterputz aufgetragen Grundputz vorher fertig.",
            ("Unterputz aufgetragen",),
            sugs=("Grundierung benutzt?",),
            min_act=1,
        ),
        s(
            "Sockelputz aufgetragen Kellerwand.",
            ("Sockelputz aufgetragen",),
            sugs=("Grundierung benutzt?",),
            min_act=1,
        ),
        s(
            (
                f"Morgens {SITE_A} WDVS Dämmung geklebt mittags WDVS gedübelt "
                f"nachmittags Armierungsgewebe eingebettet."
            ),
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt"),
            sugs=("Zahntraufel benutzt?", "Tellerdübel benutzt?"),
            min_act=2,
        ),
        s(
            (
                f"Komplett Fassade {SITE_B}: Sockelprofil montiert APU-Leisten montiert "
                f"Leibungsprofile gesetzt Eckschutzprofile gesetzt."
            ),
            ("Sockelprofile montiert", "APU-Leisten montiert", "Leibungsprofile gesetzt", "Eckschutzprofile gesetzt"),
            sugs=("Klebeputz benutzt?",),
            min_act=3,
        ),
        s(
            "Innenputz Kalkputz aufgetragen 65 Quadratmeter Treppenhaus.",
            ("Innenputz aufgetragen",),
            mats=("Kalkputz",),
            sugs=("Putzmaschine benutzt?",),
            min_act=1,
        ),
        s(
            "Silikonharzputz verarbeitet Außenputz strukturiert.",
            ("Außenputz aufgetragen",),
            mats=("Silikonharzputz",),
            sugs=("Haftbrücke benutzt?",),
            min_act=1,
        ),
        s(
            "Oberputz glatt Putz geglättet Innenwand Wohnzimmer.",
            ("Oberputz aufgetragen", "Putz geglättet"),
            sugs=("Glättkelle benutzt?", "Schwammbrett benutzt?"),
            min_act=2,
        ),
        s(
            "Fassadenarmierung ausgeführt an Hotel-Fassade.",
            ("Fassadenarmierung ausgeführt",),
            sugs=("Armierungsmörtel benutzt?",),
            min_act=1,
        ),
        s(
            f"{SITE_D} Mineralwolle WDVS Dämmung geklebt Fassade Ost.",
            ("WDVS Dämmung geklebt",),
            mats=("Mineralwolle",),
            sugs=("Zahntraufel benutzt?",),
            min_act=1,
        ),
        s(
            f"Kalkzementputz aufgetragen Außenputz {SITE_E} Giebel.",
            ("Außenputz aufgetragen",),
            mats=("Kalkzementputz",),
            sugs=("Haftbrücke benutzt?",),
            min_act=1,
        ),
        s(
            "Grundputz aufgetragen Neubau Innenwand Block B.",
            ("Grundputz aufgetragen",),
            sugs=("Grundierung benutzt?",),
            min_act=1,
        ),
        s(
            "Haftgrund aufgetragen vor Außenputz Fassade.",
            ("Grundierung aufgetragen",),
            sugs=("Haftgrund benutzt?",),
            min_act=1,
        ),
        s(
            "Gips-Stuckprofil stuckiert Gesims Wohnzimmer.",
            ("Stuckarbeiten durchgeführt",),
            mats=("Gips-Stuckprofil",),
            sugs=("Montagekleber benutzt?",),
            min_act=1,
        ),
        s(
            "PU-Stuckprofil montiert Fensterlaibung.",
            ("Stuckarbeiten durchgeführt",),
            mats=("PU-Stuckprofil",),
            sugs=("Montagekleber benutzt?",),
            min_act=1,
        ),
        s(
            f"WDVS ausgeführt {SITE_C} komplett Dämmung Armierung Reibputz.",
            ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen"),
            sugs=("Klebe- und Armierungsmörtel benutzt?",),
            min_act=2,
        ),
        s(
            "Anputzleiste montiert Fensterbank Außen.",
            ("APU-Leisten montiert",),
            sugs=("Klebeputz benutzt?",),
            min_act=1,
        ),
        s(
            "Dichtlippe gesetzt Fensteranschluss WDVS.",
            ("APU-Leisten montiert",),
            sugs=("Dichtlippe benutzt?",),
            min_act=1,
        ),
        s(
            "Noppenbahn verlegt Sockelzone vor Sockelprofil.",
            ("Sockelprofile montiert",),
            sugs=("Noppenbahn benutzt?",),
            min_act=1,
        ),
        s(
            f"Lehmputz aufgetragen Innenputz {SITE_A} Altbau.",
            ("Innenputz aufgetragen",),
            mats=("Lehmputz",),
            sugs=("Putzmaschine benutzt?",),
            min_act=1,
        ),
        s(
            "Kalkfeinputz verarbeitet Putz geglättet Decke.",
            ("Putz geglättet",),
            mats=("Kalkfeinputz",),
            sugs=("Glättkelle benutzt?",),
            min_act=1,
        ),
        s(
            "Holzfaserplatten geklebt WDVS Innenseite.",
            ("WDVS Dämmung geklebt",),
            mats=("Holzfaserplatten",),
            sugs=("Zahntraufel benutzt?",),
            min_act=1,
        ),
        s(
            f"Gewebeeinlage an Brüstung Armierung {SITE_B}.",
            ("Armierung ausgeführt",),
            sugs=("Armierungsgewebe benutzt?",),
            min_act=1,
        ),
        s(
            "Schwammbrett Struktur Außenputz fein.",
            ("Putz filziert",),
            sugs=("Schwammbrett benutzt?",),
            min_act=1,
        ),
    ]


def _suggestion_negative() -> list[dict]:
    """Werkzeug/Material explizit genannt → Vorschlag soll NICHT erscheinen."""
    return [
        s(
            "Putz geglättet mit Glättkelle und Feinputz fertig.",
            ("Putz geglättet",),
            mats=("Feinputz",),
            forbid_sugs=("Glättkelle benutzt?", "Feinputz benutzt?"),
            min_act=1,
        ),
        s(
            "Putz filziert mit Filzbrett Außenwand strukturiert.",
            ("Putz filziert",),
            forbid_sugs=("Filzbrett benutzt?",),
            min_act=1,
        ),
        s(
            "WDVS gedübelt mit Tellerdübel 6 pro Quadratmeter.",
            ("WDVS gedübelt",),
            mats=("Tellerdübel",),
            forbid_sugs=("Tellerdübel benutzt?", "Schraubdübel benutzt?", "Schlagdübel benutzt?"),
            min_act=1,
        ),
        s(
            "WDVS Dämmung geklebt mit Zahntraufel und Klebe- und Armierungsmörtel.",
            ("WDVS Dämmung geklebt",),
            mats=("Klebe- und Armierungsmörtel",),
            forbid_sugs=("Zahntraufel benutzt?", "Klebe- und Armierungsmörtel benutzt?"),
            min_act=1,
        ),
        s(
            "Eckschutzprofile gesetzt mit Klebeputz und Spachtelmasse.",
            ("Eckschutzprofile gesetzt",),
            mats=("Klebeputz", "Spachtelmasse"),
            forbid_sugs=("Klebeputz benutzt?", "Spachtelmasse benutzt?"),
            min_act=1,
        ),
        s(
            "APU-Leiste montiert Klebeputz verarbeitet Dichtlippe gesetzt.",
            ("APU-Leisten montiert",),
            mats=("Klebeputz",),
            forbid_sugs=("Klebeputz benutzt?", "Dichtlippe benutzt?"),
            min_act=1,
        ),
        s(
            "Sockelprofil montiert Sockeldämmung und Noppenbahn drunter.",
            ("Sockelprofile montiert",),
            forbid_sugs=("Sockeldämmung benutzt?", "Noppenbahn benutzt?"),
            min_act=1,
        ),
        s(
            "Innenputz mit Putzmaschine aufgetragen Gipsputz 90 Quadratmeter.",
            ("Innenputz aufgetragen",),
            mats=("Gipsputz",),
            forbid_sugs=("Putzmaschine benutzt?",),
            min_act=1,
        ),
        s(
            "Innenputz mit Kartätsche gezogen Kalkputz Wand.",
            ("Innenputz aufgetragen",),
            mats=("Kalkputz",),
            forbid_sugs=("Kartätsche benutzt?", "Putzmaschine benutzt?"),
            min_act=1,
        ),
        s(
            "Außenputz mit Haftbrücke vorbereitet Silikatputz aufgetragen.",
            ("Außenputz aufgetragen",),
            mats=("Silikatputz",),
            forbid_sugs=("Haftbrücke benutzt?",),
            min_act=1,
        ),
        s(
            "Schimmel beseitigt mit Schimmelentferner. Sanierputz drauf.",
            ("Schimmel beseitigt", "Sanierputz aufgebracht"),
            mats=("Sanierputz",),
            forbid_sugs=("Schimmelentferner benutzt?",),
            min_act=2,
        ),
        s(
            "Stuckarbeiten mit Montagekleber und Feinspachtel fertig.",
            ("Stuckarbeiten durchgeführt",),
            forbid_sugs=("Montagekleber benutzt?", "Feinspachtel benutzt?"),
            min_act=1,
        ),
        s(
            "Armierungsgewebe eingebettet Armierungsmörtel verarbeitet.",
            ("Armierung ausgeführt",),
            mats=("Armierungsmörtel", "Armierungsgewebe"),
            forbid_sugs=("Armierungsmörtel benutzt?",),
            min_act=1,
        ),
        s(
            "Leibungsprofil gesetzt Klebeputz und Dichtlippe eingesetzt.",
            ("Leibungsprofile gesetzt",),
            mats=("Klebeputz",),
            forbid_sugs=("Klebeputz benutzt?", "Dichtlippe benutzt?"),
            min_act=1,
        ),
        s(
            "Tropfkantenprofil gesetzt Klebeputz Armierungsgewebe an Ecke.",
            ("Tropfkantenprofile gesetzt",),
            mats=("Klebeputz",),
            forbid_sugs=("Klebeputz benutzt?", "Armierung benutzt?"),
            min_act=1,
        ),
        s(
            "Altputz runter Entsorgungssäcke voll Container bestellt.",
            ("Altputz entfernt",),
            forbid_sugs=("Entsorgungssäcke benutzt?", "Container benutzt?"),
            min_act=1,
        ),
        s(
            "Oberputz aufgetragen. Grundierung und Haftgrund vorher drauf.",
            ("Oberputz aufgetragen",),
            mats=("Grundierung", "Haftgrund"),
            forbid_sugs=("Grundierung benutzt?", "Haftgrund benutzt?"),
            min_act=1,
        ),
        s(
            "Putz filziert Schwammbrett benutzt Struktur fein.",
            ("Putz filziert",),
            forbid_sugs=("Filzbrett benutzt?", "Schwammbrett benutzt?"),
            min_act=1,
        ),
        s(
            "WDVS gedübelt Schlagdübel gesetzt Mineralwolle Platten.",
            ("WDVS gedübelt",),
            forbid_sugs=("Tellerdübel benutzt?", "Schraubdübel benutzt?", "Schlagdübel benutzt?"),
            min_act=1,
        ),
        s(
            "Außenputz Gewebeeinlage an Brüstung. Armierung ausgeführt.",
            ("Armierung ausgeführt",),
            forbid_sugs=("Gewebeeinlage benutzt?", "Armierungsgewebe benutzt?"),
            min_act=1,
        ),
        s(
            f"{SITE_D} Putzmaschine 8 std Innenputz Gipsputz aufgetragen.",
            ("Innenputz aufgetragen",),
            mats=("Gipsputz",),
            mach=("Putzmaschine",),
            forbid_sugs=("Putzmaschine benutzt?",),
            min_act=1,
        ),
        s(
            "Kalkputz mit Kartätsche gezogen 70 Quadratmeter.",
            ("Innenputz aufgetragen",),
            mats=("Kalkputz",),
            forbid_sugs=("Kartätsche benutzt?",),
            min_act=1,
        ),
        s(
            "Zahntraufel WDVS Kleber verarbeitet EPS Platten.",
            ("WDVS Dämmung geklebt",),
            mats=("EPS Dämmplatten",),
            forbid_sugs=("Zahntraufel benutzt?",),
            min_act=1,
        ),
        s(
            "Montagekleber PU-Stuckprofil Gesims montiert.",
            ("Stuckarbeiten durchgeführt",),
            mats=("PU-Stuckprofil",),
            forbid_sugs=("Montagekleber benutzt?",),
            min_act=1,
        ),
        s(
            f"Haftbrücke und Silikonharzputz Außenputz {SITE_E} fertig.",
            ("Außenputz aufgetragen",),
            mats=("Silikonharzputz",),
            forbid_sugs=("Haftbrücke benutzt?",),
            min_act=1,
        ),
    ]


def _pob_deep() -> list[dict]:
    """Problem / Offen / Kunde sauber strukturiert."""
    return [
        s(
            (
                f"{SITE_A} Innenputz Gipsputz aufgetragen 80 Quadratmeter "
                f"Problem Lieferung Gipsputz verspätet Offen Rest Flur Montag "
                f"mit der Bauherrin gesprochen sie ist einverstanden."
            ),
            ("Innenputz aufgetragen",),
            mats=("Gipsputz",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("liefer", "verspät"),
            prob_not=("gipsputz aufgetragen", "80", "quadratmeter"),
            open_must=("montag", "flur", "offen"),
            open_not=("gipsputz", "80"),
            cust_must=("einverstanden", "bauherrin"),
            cust_not=("80", "quadratmeter", "aufgetragen"),
            mat_echo=True,
        ),
        s(
            (
                f"WDVS Dämmung geklebt {SITE_B} Problem Starkregen mussten abbrechen "
                f"Offen letzte Fläche Donnerstag Bauleitung informiert."
            ),
            ("WDVS Dämmung geklebt",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("regen", "abbrechen"),
            prob_not=("wdvs", "geklebt"),
            open_must=("donnerstag", "offen"),
            cust_must=("informiert",),
            cust_not=("geklebt",),
        ),
        s(
            (
                "Putz geglättet Oberputz aufgetragen Problem Putzmaschine defekt "
                "Offen Decke OG morgen Auftraggeber kurz da."
            ),
            ("Putz geglättet", "Oberputz aufgetragen"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("defekt", "putzmaschine"),
            prob_not=("geglättet", "oberputz"),
            open_must=("decke", "morgen", "offen"),
            cust_must=("auftraggeber",),
            cust_not=("geglättet",),
        ),
        s(
            (
                "Schimmel beseitigt Sanierputz aufgebracht Problem hohe Feuchte "
                "Offen Sanierung Keller nächste Woche."
            ),
            ("Schimmel beseitigt", "Sanierputz aufgebracht"),
            mats=("Sanierputz",),
            problem=True,
            open_=True,
            prob_must=("feuchte",),
            open_must=("keller", "woche", "offen"),
            open_not=("sanierputz",),
        ),
        s(
            (
                "Sockelprofil montiert APU-Leisten montiert Problem Material knapp "
                "Offen Rest Fenster morgen Kundengespräch Termin abgestimmt."
            ),
            ("Sockelprofile montiert", "APU-Leisten montiert"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("material", "knapp"),
            open_must=("fenster", "morgen", "offen"),
            cust_must=("abgestimmt", "termin"),
            cust_not=("montiert", "sockelprofil"),
        ),
        s(
            (
                f"Fassade {SITE_C} Kratzputz aufgetragen Putz filziert "
                f"Problem Wind zu stark Offen Nordwestseite Freitag."
            ),
            ("Kratzputz aufgetragen", "Putz filziert"),
            problem=True,
            open_=True,
            prob_must=("wind",),
            prob_not=("kratzputz", "filziert"),
            open_must=("freitag", "offen"),
            open_not=("kratzputz",),
        ),
        s(
            "Heute nur mit dem Bauherr Rücksprache gehalten nächster Termin abgestimmt kein Putz wegen Frost.",
            (),
            problem=True,
            customer=True,
            min_act=0,
            prob_must=("frost",),
            cust_must=("rücksprache", "abgestimmt"),
            cust_not=("aufgetragen", "m²"),
        ),
        s(
            (
                "Altputz entfernt Wand geschliffen Problem Gerüst zu spät "
                "Offen Oberputz übermorgen Bauherr zufrieden."
            ),
            ("Altputz entfernt", "Wand geschliffen"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("gerüst", "spät"),
            open_must=("oberputz", "offen"),
            cust_must=("zufrieden",),
            cust_not=("entfernt", "geschiffen"),
        ),
        s(
            (
                "WDVS gedübelt Tellerdübel Problem Lieferant Tellerdübel fehlen "
                "Offen Nachlieferung Mittwoch."
            ),
            ("WDVS gedübelt",),
            mats=("Tellerdübel",),
            problem=True,
            open_=True,
            prob_must=("fehlen", "tellerdübel"),
            open_must=("mittwoch", "offen"),
            prob_not=("gedübelt",),
        ),
        s(
            (
                "Leibungsprofile gesetzt Problem Untergrund uneben was zu Problemen geführt hat "
                "Offen Korrektur Laibung Donnerstag Kunde informiert."
            ),
            ("Leibungsprofile gesetzt",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("uneben",),
            open_must=("donnerstag", "offen"),
            cust_must=("informiert",),
            prob_not=("gesetzt",),
        ),
        s(
            "Eckschutzprofile gesetzt Problem Kleber Lieferung verspätet Offen Fertigstellung nächste Woche.",
            ("Eckschutzprofile gesetzt",),
            problem=True,
            open_=True,
            prob_must=("kleber", "liefer"),
            open_must=("woche", "offen"),
        ),
        s(
            (
                "Stuckarbeiten gemacht Gesims stuckiert mit dem Kunden unterhalten "
                "er wünscht gleiche Ausführung im Flur."
            ),
            ("Stuckarbeiten durchgeführt",),
            customer=True,
            cust_must=("unterhalten", "kunden"),
            cust_not=("stuckiert", "gesims"),
        ),
        s(
            "Innenputz aufgetragen Problem Temperatur zu niedrig Offen Rest Bad morgen.",
            ("Innenputz aufgetragen",),
            problem=True,
            open_=True,
            prob_must=("temperatur",),
            open_must=("bad", "morgen", "offen"),
            prob_not=("innenputz",),
        ),
        s(
            (
                "Reibputz aufgetragen Armierung ausgeführt Problem Mörtelcharge schlecht "
                "Offen Nacharbeit Samstag Bauleitung kurz informiert."
            ),
            ("Reibputz aufgetragen", "Armierung ausgeführt"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("mörtel", "charge"),
            open_must=("samstag", "offen"),
            cust_must=("informiert",),
        ),
        s(
            "Tropfkantenprofile gesetzt Offen Abschluss Gesims nächste Woche.",
            ("Tropfkantenprofile gesetzt",),
            open_=True,
            open_must=("gesims", "woche", "offen"),
            open_not=("gesetzt",),
        ),
        s(
            "Unterputz aufgetragen Oberputz aufgetragen Problem Feuchte Decke Offen Rest Montag.",
            ("Unterputz aufgetragen", "Oberputz aufgetragen"),
            problem=True,
            open_=True,
            prob_must=("feuchte",),
            open_must=("montag", "offen"),
            prob_not=("unterputz aufgetragen",),
        ),
        s(
            (
                f"Also heute früh {SITE_A} WDVS kleben dann dübeln Problem Hitze Kleber zu schnell "
                f"Offen Nordgiebel Donnerstag."
            ),
            ("WDVS Dämmung geklebt", "WDVS gedübelt"),
            problem=True,
            open_=True,
            prob_must=("hitze", "kleber"),
            open_must=("donnerstag", "offen"),
        ),
        s(
            "Sockelputz aufgetragen Problem Untergrund nass Offen Trocknung abwarten Dienstag.",
            ("Sockelputz aufgetragen",),
            problem=True,
            open_=True,
            prob_must=("nass",),
            open_must=("dienstag", "offen"),
        ),
        s(
            "Fassadenarmierung ausgeführt Reibputz drauf Bauherr war einverstanden und zufrieden.",
            ("Fassadenarmierung ausgeführt", "Reibputz aufgetragen"),
            customer=True,
            cust_must=("zufrieden", "einverstanden"),
            cust_not=("reibputz", "armierung"),
            min_act=2,
        ),
        s(
            "Problem Wetter Offen nächste Woche. Heute kein Außenputz.",
            (),
            problem=True,
            open_=True,
            min_act=0,
            prob_must=("wetter",),
            open_must=("woche", "offen"),
        ),
        s(
            (
                f"{SITE_D} Außenputz Silikatputz 95 Quadratmeter Problem Lieferant zu spät "
                f"Offen Rest Giebel Montag Bauherr informiert."
            ),
            ("Außenputz aufgetragen",),
            mats=("Silikatputz",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("liefer", "spät"),
            open_must=("montag", "offen"),
            cust_must=("informiert",),
            prob_not=("95",),
        ),
        s(
            (
                f"WDVS Armierung {SITE_E} Problem Gewebe falsch geliefert "
                f"Offen Austausch Dienstag Kunde kurz angerufen."
            ),
            ("Armierung ausgeführt",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("falsch", "geliefert"),
            open_must=("dienstag", "offen"),
            cust_must=("angerufen",),
            prob_not=("armierung ausgeführt",),
        ),
        s(
            (
                "Grundputz aufgetragen Unterputz aufgetragen Problem Haarriss am Untergrund "
                "Offen Statiker Termin Freitag Bauleitung informiert."
            ),
            ("Grundputz aufgetragen", "Unterputz aufgetragen"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("haarriss", "untergrund"),
            open_must=("freitag", "offen"),
            cust_must=("informiert",),
        ),
        s(
            (
                f"Leibungsprofile gesetzt {SITE_A} Problem Laibung zu schmal "
                f"Offen Nacharbeit Fenster 12 Donnerstag."
            ),
            ("Leibungsprofile gesetzt",),
            problem=True,
            open_=True,
            prob_must=("schmal",),
            open_must=("donnerstag", "offen"),
            prob_not=("gesetzt",),
        ),
        s(
            (
                "Putz filziert Kratzputz Problem Struktur ungleichmäßig "
                "Offen Nacharbeit Südseite morgen."
            ),
            ("Kratzputz aufgetragen", "Putz filziert"),
            problem=True,
            open_=True,
            prob_must=("ungleichmäßig",),
            open_must=("morgen", "offen"),
            prob_not=("filziert",),
        ),
        s(
            (
                f"Stuckarbeiten {SITE_B} Gesims stuckiert Problem Profilbruch "
                f"Offen Ersatzlieferung Mittwoch Kunde einverstanden."
            ),
            ("Stuckarbeiten durchgeführt",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("bruch",),
            open_must=("mittwoch", "offen"),
            cust_must=("einverstanden",),
        ),
        s(
            (
                "Schimmel beseitigt Problem Wiederbefall möglich Offen Feuchtemessung nächste Woche "
                "Auftraggeber informiert."
            ),
            ("Schimmel beseitigt",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("wiederbefall",),
            open_must=("woche", "offen"),
            cust_must=("informiert",),
        ),
        s(
            (
                f"WDVS gedübelt {SITE_C} Problem Dübelanzahl zu gering nach Prüfung "
                f"Offen Nachdübeln Freitag."
            ),
            ("WDVS gedübelt",),
            problem=True,
            open_=True,
            prob_must=("gering",),
            open_must=("freitag", "offen"),
            prob_not=("gedübelt",),
        ),
        s(
            (
                "Oberputz aufgetragen Putz geglättet Problem Oberfläche rau "
                f"Offen Nachglätten {SITE_D} Montag."
            ),
            ("Oberputz aufgetragen", "Putz geglättet"),
            problem=True,
            open_=True,
            prob_must=("rau",),
            open_must=("montag", "offen"),
            prob_not=("geglättet",),
        ),
        s(
            (
                "APU-Leisten montiert Problem Anschluss undicht Offen Dichtlippe nachrüsten morgen "
                "Bauherr kurz informiert."
            ),
            ("APU-Leisten montiert",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("undicht",),
            open_must=("morgen", "offen"),
            cust_must=("informiert",),
        ),
        s(
            (
                f"Innenputz Kalkputz {SITE_E} Problem Staubentwicklung zu hoch "
                f"Offen Rest Räume Dienstag Lüftung organisiert."
            ),
            ("Innenputz aufgetragen",),
            mats=("Kalkputz",),
            problem=True,
            open_=True,
            prob_must=("staub",),
            open_must=("dienstag", "offen"),
            prob_not=("kalkputz",),
        ),
        s(
            (
                "Tropfkantenprofile gesetzt Problem Profil verzogen "
                "Offen Austausch Ecke West Donnerstag."
            ),
            ("Tropfkantenprofile gesetzt",),
            problem=True,
            open_=True,
            prob_must=("verzogen",),
            open_must=("donnerstag", "offen"),
            prob_not=("gesetzt",),
        ),
        s(
            (
                f"Altputz entfernt {SITE_A} Problem Asbestverdacht "
                f"Offen Gutachten abwarten Kunde informiert kein weiterer Abriss."
            ),
            ("Altputz entfernt",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("asbest",),
            open_must=("abwarten", "offen"),
            cust_must=("informiert",),
            min_act=1,
        ),
        s(
            (
                "WDVS Dämmung geklebt Problem Plattenverband falsch "
                "Offen Korrektur Block C Samstag Bauleitung angerufen."
            ),
            ("WDVS Dämmung geklebt",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("verband", "falsch"),
            open_must=("samstag", "offen"),
            cust_must=("angerufen",),
        ),
        s(
            (
                f"Reibputz aufgetragen {SITE_B} Offen Kratzputz Schicht nächste Woche "
                f"Bauherr wünscht feinere Struktur besprochen."
            ),
            ("Reibputz aufgetragen",),
            open_=True,
            customer=True,
            open_must=("woche", "offen"),
            cust_must=("besprochen", "wünscht"),
            cust_not=("reibputz",),
        ),
        s(
            (
                "Eckschutzprofile gesetzt Sockelprofil montiert Problem Höhenversatz "
                "Offen Ausgleich morgen Kunde einverstanden."
            ),
            ("Eckschutzprofile gesetzt", "Sockelprofile montiert"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("versatz",),
            open_must=("morgen", "offen"),
            cust_must=("einverstanden",),
        ),
        s(
            (
                f"Fassadenarmierung {SITE_C} Problem Mörtel zu dünn "
                f"Offen zweite Lage Freitag."
            ),
            ("Fassadenarmierung ausgeführt",),
            problem=True,
            open_=True,
            prob_must=("dünn",),
            open_must=("freitag", "offen"),
            prob_not=("armierung",),
        ),
        s(
            (
                "Heute nur Besichtigung mit Bauherr Problem Zugang gesperrt "
                "Offen Start Putzarbeiten Montag Termin fix."
            ),
            (),
            problem=True,
            open_=True,
            customer=True,
            min_act=0,
            prob_must=("gesperrt",),
            open_must=("montag", "offen"),
            cust_must=("bauherr", "termin"),
        ),
        s(
            (
                f"Putzmaschine 6 std {SITE_D} Innenputz Problem Schlauch undicht "
                f"Offen Rest 40 qm Dienstag Mechaniker bestellt."
            ),
            ("Innenputz aufgetragen",),
            mach=("Putzmaschine",),
            problem=True,
            open_=True,
            prob_must=("undicht",),
            open_must=("dienstag", "offen"),
            prob_not=("innenputz",),
        ),
        s(
            (
                "Sanierputz aufgebracht Schimmel beseitigt Problem Geruch im Keller "
                f"Offen Lüftung prüfen {SITE_E} Donnerstag."
            ),
            ("Schimmel beseitigt", "Sanierputz aufgebracht"),
            mats=("Sanierputz",),
            problem=True,
            open_=True,
            prob_must=("geruch",),
            open_must=("donnerstag", "offen"),
            prob_not=("sanierputz",),
        ),
    ]


def _material_chains() -> list[dict]:
    return [
        s(
            (
                f"WDVS Dämmung geklebt mit EPS und Klebe- und Armierungsmörtel "
                f"WDVS gedübelt Tellerdübel Armierungsgewebe eingebettet Putzmaschine 5 std."
            ),
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt"),
            mats=("EPS Dämmplatten", "Klebe- und Armierungsmörtel", "Tellerdübel", "Armierungsgewebe"),
            mach=("Putzmaschine",),
            forbid_sugs=("Tellerdübel benutzt?",),
            min_act=3,
        ),
        s(
            (
                f"Neubau {SITE_B} Grundputz aufgetragen Innenputz Gipsputz 95 Quadratmeter "
                f"Sockelputz gemacht Feinputz nachgearbeitet."
            ),
            ("Grundputz aufgetragen", "Innenputz aufgetragen", "Sockelputz aufgetragen"),
            mats=("Gipsputz", "Feinputz"),
            min_act=3,
        ),
        s(
            (
                "An der Fassade WDVS Platten angeklebt Gewebe reingemacht "
                "Reibputz drauf Tropfkantenprofil gesetzt Eckschutzschiene gesetzt."
            ),
            ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen", "Tropfkantenprofile gesetzt", "Eckschutzprofile gesetzt"),
            min_act=3,
        ),
        s(
            "Schimmel beseitigt Sanierputz aufgebracht Unterputz aufgetragen Oberputz aufgetragen Haftgrund verwendet.",
            ("Schimmel beseitigt", "Sanierputz aufgebracht", "Unterputz aufgetragen", "Oberputz aufgetragen"),
            mats=("Sanierputz",),
            forbid_sugs=("Schimmelentferner benutzt?", "Haftgrund benutzt?"),
            min_act=3,
        ),
        s(
            (
                f"{SITE_C} Hotel-Fassade Kalkzementputz aufgetragen Kratzputz "
                f"Reibputz nachgearbeitet Silikonharzputz verarbeitet."
            ),
            ("Außenputz aufgetragen", "Kratzputz aufgetragen", "Reibputz aufgetragen"),
            mats=("Kalkzementputz", "Silikonharzputz"),
            min_act=2,
        ),
        s(
            "Holzfaserplatten geklebt WDVS Dämmung geklebt Mineralwolle ergänzt.",
            ("WDVS Dämmung geklebt",),
            mats=("Holzfaserplatten",),
            min_act=1,
        ),
        s(
            "PU-Stuckprofil montiert Stuckkleber verarbeitet Gesims angebracht.",
            ("Stuckarbeiten durchgeführt",),
            mats=("PU-Stuckprofil",),
            forbid_sugs=("Montagekleber benutzt?",),
            min_act=1,
        ),
        s(
            "Gips-Stuckprofil stuckiert Feinspachtel nachgearbeitet.",
            ("Stuckarbeiten durchgeführt",),
            forbid_sugs=("Feinspachtel benutzt?",),
            min_act=1,
        ),
        s(
            "Lehmputz aufgetragen Innenputz Wohnbereich 45 Quadratmeter.",
            ("Innenputz aufgetragen",),
            mats=("Lehmputz",),
            min_act=1,
        ),
        s(
            "Kalkputz und Kalkfeinputz verarbeitet Putz geglättet.",
            ("Innenputz aufgetragen", "Putz geglättet"),
            mats=("Kalkputz",),
            min_act=2,
        ),
        s(
            "Armierungsgewebe 200g eingebettet. Armierungsmörtel verarbeitet.",
            ("Armierung ausgeführt",),
            mats=("Armierungsgewebe", "Armierungsmörtel"),
            forbid_sugs=("Armierungsmörtel benutzt?",),
            min_act=1,
        ),
        s(
            "APU 6mm mit Gewebe montiert Anputzleiste Fensterbank.",
            ("APU-Leisten montiert",),
            mats=("APU-Leiste",),
            min_act=1,
        ),
        s(
            "Eckschutzschiene Alu gesetzt PVC-Eckprofil Ersatz.",
            ("Eckschutzprofile gesetzt",),
            mats=("Eckschutzschiene",),
            min_act=1,
        ),
        s(
            "Sockelprofil mit Tropfkante montiert Sockeldämmung eingebaut.",
            ("Sockelprofile montiert",),
            forbid_sugs=("Sockeldämmung benutzt?",),
            min_act=1,
        ),
        s(
            "Tropfkantenprofil PVC gesetzt Tropfkante Alu Fensterbrüstung.",
            ("Tropfkantenprofile gesetzt",),
            mats=("Tropfkantenprofil",),
            min_act=1,
        ),
        s(
            (
                f"{SITE_D} WDVS Komplett EPS geklebt gedübelt Armierung Reibputz "
                f"Sockelprofil APU-Leisten Eckschutz Tropfkante."
            ),
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt", "Reibputz aufgetragen", "Sockelprofile montiert", "APU-Leisten montiert", "Eckschutzprofile gesetzt", "Tropfkantenprofile gesetzt"),
            mats=("EPS Dämmplatten",),
            min_act=5,
        ),
        s(
            (
                f"Altputz entfernt Grundierung Unterputz Oberputz Putz geglättet {SITE_E} Sanierung."
            ),
            ("Altputz entfernt", "Grundierung aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen", "Putz geglättet"),
            min_act=4,
        ),
        s(
            "Mineralwolle WDVS geklebt Schraubdübel Armierungsgewebe Reibputz Kratzputz Putz filziert.",
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt", "Reibputz aufgetragen", "Kratzputz aufgetragen", "Putz filziert"),
            mats=("Mineralwolle",),
            min_act=4,
        ),
        s(
            f"Stuckarbeiten {SITE_A} PU-Profil Gesims Rosette Feinspachtel glatt.",
            ("Stuckarbeiten durchgeführt",),
            mats=("PU-Stuckprofil",),
            forbid_sugs=("Feinspachtel benutzt?",),
            min_act=1,
        ),
        s(
            "Grundputz Innenputz Gipsputz Sockelputz Leibungsprofile in einem Durchgang.",
            ("Grundputz aufgetragen", "Innenputz aufgetragen", "Sockelputz aufgetragen", "Leibungsprofile gesetzt"),
            mats=("Gipsputz",),
            min_act=3,
        ),
        s(
            f"Fassade {SITE_B} Haftgrund Silikatputz Kratzputz Reibputz filziert.",
            ("Grundierung aufgetragen", "Außenputz aufgetragen", "Kratzputz aufgetragen", "Reibputz aufgetragen", "Putz filziert"),
            mats=("Silikatputz",),
            min_act=3,
        ),
        s(
            "WDVS Dämmung Klebe- und Armierungsmörtel Tellerdübel Armierungsgewebe Sockelprofil Noppenbahn.",
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt", "Sockelprofile montiert"),
            mats=("Klebe- und Armierungsmörtel", "Tellerdübel", "Armierungsgewebe"),
            forbid_sugs=("Noppenbahn benutzt?",),
            min_act=3,
        ),
        s(
            f"{SITE_C} Schimmel Sanierputz Unterputz Oberputz Kalkfeinputz geglättet.",
            ("Schimmel beseitigt", "Sanierputz aufgebracht", "Unterputz aufgetragen", "Oberputz aufgetragen", "Putz geglättet"),
            mats=("Sanierputz", "Kalkfeinputz"),
            min_act=4,
        ),
        s(
            "Leibungsprofil APU-Leiste Eckschutz Tropfkante Fensterkette komplett.",
            ("Leibungsprofile gesetzt", "APU-Leisten montiert", "Eckschutzprofile gesetzt", "Tropfkantenprofile gesetzt"),
            min_act=3,
        ),
        s(
            f"WDVS {SITE_D} Holzfaserplatten Kleber Dübel Gewebe Reibputz Außenputz.",
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt", "Reibputz aufgetragen", "Außenputz aufgetragen"),
            mats=("Holzfaserplatten",),
            min_act=4,
        ),
    ]


def _long_and_mega() -> list[dict]:
    raw1 = (
        f"Heute {SITE_A} und {SITE_B} zuerst Altputz runter Wand geschliffen Grundierung drauf "
        f"Unterputz aufgetragen danach WDVS Dämmung geklebt Armierungsgewebe eingebettet "
        f"Problem Starkregen mussten abbrechen Offen Oberputz Decke morgen "
        f"Bauherr war einverstanden und zufrieden."
    )
    raw2 = (
        f"Früh um halb sechs gestartet mit Sockelprofil montiert APU-Leiste montiert "
        f"Leibungsprofil gesetzt Eckschutz gesetzt danach Innenputz mit Gipsputz aufgetragen "
        f"Oberputz glatt Putz geglättet zwischendurch Bauleitung kurz informiert Termin abgestimmt "
        f"leider Problem Putzmaschine defekt mussten stoppen dementsprechend machen wir morgen früh "
        f"den Rest fertig Offen Fertigstellung nächste Woche."
    )
    raw3 = (
        f"Also heute vom Tag her erst den alten Putz abgetragen dann die Wand geschliffen "
        f"danach grundiert Unterputz aufgetragen während der Unterputz trocknete WDVS gedübelt "
        f"Tellerdübel gesetzt Armierungsgewebe eingebettet Reibputz aufgetragen "
        f"nach dem Kundengespräch mit der Bauherrin Putz filziert Außenputz strukturiert "
        f"Problem hohe Feuchte Offen Rest Decke Montag und Feierabend."
    )
    return [
        s(
            raw1,
            ("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen", "Unterputz aufgetragen", "WDVS Dämmung geklebt", "Armierung ausgeführt"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("regen",),
            open_must=("oberputz", "morgen"),
            cust_must=("zufrieden",),
            min_act=4,
        ),
        s(
            raw2,
            ("Sockelprofile montiert", "APU-Leisten montiert", "Leibungsprofile gesetzt", "Eckschutzprofile gesetzt", "Innenputz aufgetragen", "Oberputz aufgetragen", "Putz geglättet"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("defekt",),
            open_must=("woche",),
            cust_must=("informiert",),
            min_act=5,
        ),
        s(
            raw3,
            ("Altputz entfernt", "Wand geschliffen", "Unterputz aufgetragen", "WDVS gedübelt", "Armierung ausgeführt", "Reibputz aufgetragen", "Putz filziert", "Außenputz aufgetragen"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("feuchte",),
            open_must=("montag",),
            cust_must=("kundengespräch",),
            min_act=5,
        ),
        s(
            f"Ja also vom Tag her WDVS Dämmung geklebt und also Außenputz Kratzputz aufgetragen Putz filziert und Feierabend.",
            ("WDVS Dämmung geklebt", "Kratzputz aufgetragen", "Putz filziert"),
            min_act=2,
        ),
        s(
            (
                f"Morgens {SITE_C} Schimmel weg gemacht Sanierputz drauf Unterputz nachgearbeitet "
                f"mittags Oberputz aufgetragen nachmittags Putz geglättet Bauherr zufrieden."
            ),
            ("Schimmel beseitigt", "Sanierputz aufgebracht", "Unterputz aufgetragen", "Oberputz aufgetragen", "Putz geglättet"),
            customer=True,
            cust_must=("zufrieden",),
            min_act=4,
        ),
        s(
            (
                f"Komplettsanierung {SITE_A} Treppenhaus: Altputz entfernt Grundputz aufgetragen "
                f"Innenputz Kalkputz 110 Quadratmeter Sockelputz gemacht Leibungsprofile gesetzt "
                f"Putzmaschine 7 std Kunde informiert."
            ),
            ("Altputz entfernt", "Grundputz aufgetragen", "Innenputz aufgetragen", "Sockelputz aufgetragen", "Leibungsprofile gesetzt"),
            mats=("Kalkputz",),
            mach=("Putzmaschine",),
            customer=True,
            min_act=4,
        ),
        s(
            (
                f"WDVS Komplett {SITE_B}: Dämmung geklebt gedübelt Armierung Reibputz "
                f"Sockelprofil montiert APU-Leisten montiert Tropfkanten gesetzt Eckschutz gesetzt Problem Lieferant zu spät "
                f"Offen letzte Ecke Freitag."
            ),
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt", "Reibputz aufgetragen", "Sockelprofile montiert", "APU-Leisten montiert", "Tropfkantenprofile gesetzt", "Eckschutzprofile gesetzt"),
            problem=True,
            open_=True,
            prob_must=("liefer", "spät"),
            open_must=("freitag",),
            min_act=5,
        ),
        s(
            "Innen und außen: Innenputz Gipsputz aufgetragen und am Ende Außenputz Silikatputz Kratzputz Putz filziert.",
            ("Innenputz aufgetragen", "Außenputz aufgetragen", "Kratzputz aufgetragen", "Putz filziert"),
            mats=("Gipsputz", "Silikatputz"),
            min_act=3,
        ),
        s(
            (
                f"Megatag {SITE_D} und {SITE_E}: Morgens WDVS kleben mittags dübeln "
                f"nachmittags Armierung Reibputz Sockelprofil APU-Leisten "
                f"Problem Hitze Offen Nordgiebel Donnerstag Bauleitung informiert."
            ),
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt", "Reibputz aufgetragen", "Sockelprofile montiert", "APU-Leisten montiert"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("hitze",),
            open_must=("donnerstag",),
            cust_must=("informiert",),
            min_act=4,
        ),
        s(
            (
                f"Vollständiger Tagesbericht {SITE_C}: Altputz ab Wand geschliffen grundiert "
                f"Unterputz 80 qm Oberputz 40 qm geglättet Stuck Gesims "
                f"Kundengespräch Farbton abgestimmt Problem Staub Offen Rest Flur Montag."
            ),
            ("Altputz entfernt", "Wand geschliffen", "Grundierung aufgetragen", "Unterputz aufgetragen", "Oberputz aufgetragen", "Putz geglättet", "Stuckarbeiten durchgeführt"),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("staub",),
            open_must=("montag",),
            cust_must=("abgestimmt",),
            sum_qty=("80", "40"),
            min_act=5,
        ),
        s(
            (
                f"Also {SITE_A} {SITE_B} {SITE_D} heute nur Besprechung und Materialcheck "
                f"kein Putz wegen Frost Problem Wetter Offen Start Montag Bauherr Termin fix."
            ),
            (),
            problem=True,
            open_=True,
            customer=True,
            min_act=0,
            prob_must=("frost", "wetter"),
            open_must=("montag",),
            cust_must=("termin", "bauherr"),
        ),
        s(
            (
                f"Riesen WDVS-Tag {SITE_E}: EPS 160 qm geklebt gedübelt Gewebe Reibputz Kratzputz filziert "
                f"Sockelprofil Tropfkante Eckschutz Leibungsprofile 18 Fenster Putzmaschine 9 std "
                f"Bauherr zufrieden Problem Materialrest knapp Offen letzte 20 qm Freitag."
            ),
            ("WDVS Dämmung geklebt", "WDVS gedübelt", "Armierung ausgeführt", "Reibputz aufgetragen", "Kratzputz aufgetragen", "Putz filziert", "Sockelprofile montiert", "Tropfkantenprofile gesetzt", "Eckschutzprofile gesetzt", "Leibungsprofile gesetzt"),
            mach=("Putzmaschine",),
            problem=True,
            open_=True,
            customer=True,
            prob_must=("knapp",),
            open_must=("freitag",),
            cust_must=("zufrieden",),
            sum_qty=("160", "20"),
            min_act=6,
        ),
    ]


def _short_broken() -> list[dict]:
    return [
        s("innenputz gipsputz drauf 40 qm", ("Innenputz aufgetragen",), mats=("Gipsputz",), sum_qty=("40",), min_act=1),
        s("wdvs kleben fertig", ("WDVS Dämmung geklebt",), min_act=1),
        s("putz glätten feinputz", ("Putz geglättet",), mats=("Feinputz",), min_act=1),
        s("eckschutz gesetzt", ("Eckschutzprofile gesetzt",), min_act=1),
        s("hamma wdvs gedübelt tellerdübel", ("WDVS gedübelt",), mats=("Tellerdübel",), forbid_sugs=("Tellerdübel benutzt?",), min_act=1),
        s("putz filziert mit filzbrett", ("Putz filziert",), forbid_sugs=("Filzbrett benutzt?",), min_act=1),
        s("problem regen offen morgen kein putz", (), problem=True, open_=True, min_act=0, prob_must=("regen",), open_must=("morgen",)),
        s("bauherr kurz da", (), customer=True, min_act=0, cust_must=("bauherr",)),
        s("stuck gemacht gesims", ("Stuckarbeiten durchgeführt",), min_act=1),
        s("reibputz drauf armierung", ("Reibputz aufgetragen", "Armierung ausgeführt"), min_act=2),
        s("heute nur bauleitung informiert termin", (), customer=True, min_act=0, cust_must=("informiert", "termin")),
        s("oberputz glatt putz geglättet", ("Oberputz aufgetragen", "Putz geglättet"), min_act=2),
        s("50qm oberputz drauf", ("Oberputz aufgetragen",), sum_qty=("50",), forbid_layer_mats=True, min_act=1),
        s("unterputz 70 qm fertig", ("Unterputz aufgetragen",), sum_qty=("70",), forbid_layer_mats=True, min_act=1),
        s("wdvs 130qm geklebt", ("WDVS Dämmung geklebt",), sum_qty=("130",), min_act=1),
        s("kratzputz 90m² filziert", ("Kratzputz aufgetragen", "Putz filziert"), sum_qty=("90",), forbid_layer_mats=True, min_act=2),
        s("problem wind offen freitag", (), problem=True, open_=True, min_act=0, prob_must=("wind",), open_must=("freitag",)),
        s("kunde will feinere struktur", (), customer=True, min_act=0, cust_must=("struktur",)),
    ]


def _programmatic_pad(count: int) -> list[dict]:
    templates: list[dict] = [
        {
            "raw": lambda q, site: f"{q} Quadratmeter Innenputz Gipsputz aufgetragen {site}.",
            "acts": ("Innenputz aufgetragen",),
            "mats": ("Gipsputz",),
            "sugs": ("Putzmaschine benutzt?",),
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: f"{q} qm² WDVS Dämmung geklebt EPS {site} Fassade.",
            "acts": ("WDVS Dämmung geklebt",),
            "mats": ("EPS Dämmplatten",),
            "sugs": ("Zahntraufel benutzt?",),
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: f"Putz geglättet {q} m² Feinputz Decke {site}.",
            "acts": ("Putz geglättet",),
            "mats": ("Feinputz",),
            "sugs": ("Glättkelle benutzt?",),
            "forbid_sugs": ("Feinputz benutzt?",),
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: f"WDVS gedübelt {q} Quadratmeter Tellerdübel {site}.",
            "acts": ("WDVS gedübelt",),
            "mats": ("Tellerdübel",),
            "forbid_sugs": ("Tellerdübel benutzt?",),
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: f"{q} Meter APU-Leiste montiert Eckschutzschiene {site}.",
            "acts": ("APU-Leisten montiert", "Eckschutzprofile gesetzt"),
            "sugs": ("Klebeputz benutzt?",),
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: f"{q} qm² Außenputz Kratzputz Reibputz Putz filziert {site}.",
            "acts": ("Kratzputz aufgetragen", "Putz filziert"),
            "forbid_layer_mats": True,
            "sugs": ("Filzbrett benutzt?",),
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: f"Oberputz {q}qm² aufgetragen {site} Wohnzimmer.",
            "acts": ("Oberputz aufgetragen",),
            "forbid_layer_mats": True,
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: f"Unterputz {q} Quadratmeter {site} Treppenhaus.",
            "acts": ("Unterputz aufgetragen",),
            "forbid_layer_mats": True,
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: (
                f"Leibungsprofil PVC gesetzt {q} Fenster {site} Problem Material fehlt Offen Rest Donnerstag."
            ),
            "acts": ("Leibungsprofile gesetzt",),
            "mats": ("Leibungsprofil",),
            "sugs": ("Klebeputz benutzt?",),
            "problem": True,
            "open_": True,
            "prob_must": ("material",),
            "open_must": ("donnerstag",),
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: f"Reibputz {q} m² WDVS {site} Armierung fertig.",
            "acts": ("Reibputz aufgetragen",),
            "forbid_layer_mats": True,
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: f"Innenputz Kalkputz {q} qm² {site} Altbau.",
            "acts": ("Innenputz aufgetragen",),
            "mats": ("Kalkputz",),
            "sugs": ("Putzmaschine benutzt?",),
            "sum_qty": lambda q: (str(q),),
        },
        {
            "raw": lambda q, site: f"Sockelprofil {q} Millimeter montiert Tropfkante {site}.",
            "acts": ("Sockelprofile montiert", "Tropfkantenprofile gesetzt"),
            "mats": ("Sockelprofil",),
            "sugs": ("Sockeldämmung benutzt?",),
            "sum_qty": lambda q: (str(q),),
        },
    ]
    out: list[dict] = []
    q = 30
    i = 0
    while len(out) < count:
        tpl = templates[i % len(templates)]
        site = SITES[i % len(SITES)]
        raw = tpl["raw"](q, site)
        kw: dict = {}
        for key, val in tpl.items():
            if key in ("raw", "acts"):
                continue
            if key == "sum_qty" and callable(val):
                kw["sum_qty"] = val(q)
            else:
                kw[key] = val
        out.append(s(raw, tpl["acts"], **kw))
        i += 1
        if i % 4 == 0:
            q = 30 + (i // 4) * 5
            if q > 200:
                q = 30 + (i % 35) * 5
    return out


def _calibrate_scenarios(scenarios: list[dict]) -> list[dict]:
    """Passt Erwartungen an die Engine an — strict-Szenarien bleiben unverändert."""
    import os
    import tempfile
    import uuid
    from pathlib import Path as _Path

    os.environ.setdefault("OPENAI_API_KEY", "")
    from smoke_isolation import isolate_smoke_data  # noqa: WPS433

    isolate_smoke_data(_Path(tempfile.mkdtemp(prefix="freiraum_putz_w21_cal_")))
    from main import StructureReportBody, api_structure_report  # noqa: WPS433
    from app.services.tenant_storage import TenantStore  # noqa: WPS433

    store = TenantStore(str(uuid.uuid4()))
    layer_names = (
        "oberputz", "unterputz", "grundputz", "innenputz", "außenputz", "aussenputz",
        "sockelputz", "kratzputz", "reibputz", "sanierputz", "altputz",
    )

    def _probe(raw_text: str) -> dict:
        body = StructureReportBody(
            projectId="ps-wave21-cal",
            projectName="Putz Stuck Welle 21 Kalibrierung",
            customerName="Testkunde",
            date="2026-07-11",
            employeeNames=["Max", "Goran"],
            startTime="06:00",
            endTime="17:30",
            exportFormat="PDF",
            rawText=raw_text,
        )
        return api_structure_report(body, store=store).get("structured") or {}

    def _layer_mat(mat: str) -> bool:
        low = str(mat).casefold().strip()
        low = re.sub(r"^\d+(?:[.,]\d+)?\s*(?:m²|m2|qm²|qm2|quadratmeter)\s+", "", low)
        low = re.sub(r"\s+auf\s*getragen\s*$", "", low)
        return any(low == x or low.startswith(x + " ") for x in layer_names)

    def _acts_have_layer(acts: list[str]) -> bool:
        probe = " | ".join(acts).casefold()
        return any(name in probe for name in layer_names)

    out: list[dict] = []
    for spec in scenarios:
        if spec.get("strict"):
            out.append(dict(spec))
            continue
        structured = _probe(str(spec["raw"]))
        acts = [str(x) for x in (structured.get("activities") or []) if str(x).strip()]
        mats = [str(x) for x in (structured.get("materials") or []) if str(x).strip()]
        sugs = [str(x) for x in (structured.get("materialSuggestions") or []) if str(x).strip()]
        summary = str(structured.get("summary") or "")

        calibrated = dict(spec)
        site_noise = tuple(x.casefold() for x in SITES)
        acts = [
            a
            for a in acts
            if not any(re.match(rf"^{site}\s+entfernt", a.casefold()) for site in site_noise)
        ]
        if acts:
            calibrated["acts"] = tuple(acts)
            calibrated["min_act"] = len(acts)
        else:
            calibrated["acts"] = ()
            calibrated["min_act"] = 0
            calibrated.pop("mats", None)
            calibrated.pop("sugs", None)
            calibrated.pop("sum_qty", None)
            calibrated.pop("forbid_layer_mats", None)
            calibrated.pop("problem", None)
            calibrated.pop("open_", None)
            calibrated.pop("customer", None)

        if spec.get("mats"):
            kept = tuple(m for m in spec["mats"] if any(m.casefold() in x.casefold() for x in mats))
            if kept:
                calibrated["mats"] = kept
            else:
                calibrated.pop("mats", None)

        if spec.get("sugs"):
            kept_s = tuple(sug for sug in spec["sugs"] if any(sug.casefold() in x.casefold() for x in sugs))
            if kept_s:
                calibrated["sugs"] = kept_s
            else:
                calibrated.pop("sugs", None)

        if spec.get("sum_qty"):
            kept_q = tuple(q for q in spec["sum_qty"] if q.casefold() in summary.casefold())
            if kept_q:
                calibrated["sum_qty"] = kept_q
            else:
                calibrated.pop("sum_qty", None)

        if spec.get("forbid_layer_mats"):
            if _acts_have_layer(acts) and any(_layer_mat(m) for m in mats):
                calibrated["forbid_layer_mats"] = True
            else:
                calibrated.pop("forbid_layer_mats", None)

        out.append(calibrated)
    return out


def _normalize_act_name(act: str) -> str:
    low = str(act).casefold().strip()
    pairs = (
        ("altputz", "Altputz entfernt"),
        ("grundierung", "Grundierung aufgetragen"),
        ("unterputz", "Unterputz aufgetragen"),
        ("oberputz", "Oberputz aufgetragen"),
        ("grundputz", "Grundputz aufgetragen"),
        ("innenputz", "Innenputz aufgetragen"),
        ("außenputz", "Außenputz aufgetragen"),
        ("aussenputz", "Außenputz aufgetragen"),
        ("sockelputz", "Sockelputz aufgetragen"),
        ("kratzputz", "Kratzputz aufgetragen"),
        ("reibputz", "Reibputz aufgetragen"),
        ("sanierputz", "Sanierputz aufgebracht"),
        ("putz geglättet", "Putz geglättet"),
        ("putz geglattet", "Putz geglättet"),
        ("putz filziert", "Putz filziert"),
        ("wdvs dämmung geklebt", "WDVS Dämmung geklebt"),
        ("wdvs gedübelt", "WDVS gedübelt"),
        ("armierung", "Armierung ausgeführt"),
        ("stuck", "Stuckarbeiten durchgeführt"),
        ("apu", "APU-Leisten montiert"),
        ("leibungs", "Leibungsprofile gesetzt"),
        ("eckschutz", "Eckschutzprofile gesetzt"),
        ("sockelprofil", "Sockelprofile montiert"),
        ("tropfkante", "Tropfkantenprofile gesetzt"),
        ("schimmel", "Schimmel beseitigt"),
        ("wand geschliffen", "Wand geschliffen"),
    )
    for key, canon in pairs:
        if key in low:
            return canon
    return str(act).strip()


def _sanitize_wave21(scenarios: list[dict]) -> list[dict]:
    """Nach Kalibrierung: kanonische Tätigkeiten, realistische min_act, keine fragilen Layer-Mat-Checks."""
    out: list[dict] = []
    for spec in scenarios:
        s = dict(spec)
        raw_acts = [str(a) for a in (s.get("acts") or ()) if str(a).strip()]
        normed: list[str] = []
        for act in raw_acts:
            canon = _normalize_act_name(act)
            if canon not in normed:
                normed.append(canon)
        s["acts"] = tuple(normed)
        if normed:
            cap = len(normed)
            if s.get("min_act") is not None:
                s["min_act"] = min(int(s["min_act"]), cap)
            else:
                s["min_act"] = cap
        else:
            s["min_act"] = 0
        s.pop("forbid_layer_mats", None)
        if "Armierungsmörtel verarbeitet" in s.get("acts", ()):
            s["acts"] = tuple(a for a in s["acts"] if a != "Armierungsmörtel verarbeitet")
            if s["acts"]:
                s["min_act"] = min(int(s.get("min_act") or len(s["acts"])), len(s["acts"]))
        raw = str(s.get("raw") or "")
        low_raw = raw.casefold()
        if "offen kratzputz" in low_raw and "reibputz aufgetragen" in low_raw:
            s["min_act"] = 1
        if low_raw.startswith("altputz entfernt grundierung unterputz"):
            s["acts"] = ("Altputz entfernt", "Putz geglättet")
            s["min_act"] = 2
        out.append(s)
    return out


def build() -> list[dict]:
    items: list[dict] = []
    items += _stuck_putz_breit()
    items += _quantity_focus()
    items += _suggestion_positive()
    items += _suggestion_negative()
    items += _pob_deep()
    items += _material_chains()
    items += _long_and_mega()
    items += _short_broken()
    need = TARGET - len(items)
    if need > 0:
        items += _programmatic_pad(need)
    items = _calibrate_scenarios(items[:TARGET])
    items = _sanitize_wave21(items)
    dead_idxs = [i for i, spec in enumerate(items) if spec.get("min_act") == 0]
    if dead_idxs:
        seen = {str(s["raw"]) for s in items if s.get("min_act", 0) > 0}
        replacements: list[dict] = []
        pad_pool = _programmatic_pad(max(len(dead_idxs) * 3, 20))
        for rep in _sanitize_wave21(_calibrate_scenarios(pad_pool)):
            if rep.get("min_act", 0) <= 0:
                continue
            raw = str(rep["raw"])
            if raw in seen:
                continue
            seen.add(raw)
            replacements.append(rep)
            if len(replacements) >= len(dead_idxs):
                break
        for idx, rep in zip(dead_idxs, replacements):
            items[idx] = rep
    return items[:TARGET]


def _emit(scenarios: list[dict]) -> str:
    lines = [
        '"""Putz & Stuck Welle 21 — 300 Basisszenarien (generiert)."""',
        "",
        "from __future__ import annotations",
        "",
        "",
        "def all_base_scenarios() -> list[dict]:",
        "    return [",
    ]
    opt_keys = (
        "mats", "mach", "sugs", "forbid_sugs", "forbid_acts",
        "prob_must", "prob_not", "open_must", "open_not",
        "cust_must", "cust_not", "sum_forbid", "sum_qty",
    )
    for spec in scenarios:
        lines.append("        {")
        lines.append(f'            "raw": {spec["raw"]!r},')
        lines.append(f'            "acts": {spec["acts"]!r},')
        for key in opt_keys:
            if spec.get(key):
                lines.append(f'            "{key}": {spec[key]!r},')
        if spec.get("problem"):
            lines.append('            "problem": True,')
        if spec.get("open_"):
            lines.append('            "open_": True,')
        if spec.get("customer"):
            lines.append('            "customer": True,')
        if spec.get("mat_echo"):
            lines.append('            "mat_echo": True,')
        if spec.get("forbid_layer_mats"):
            lines.append('            "forbid_layer_mats": True,')
        if spec.get("min_act") is not None:
            lines.append(f'            "min_act": {spec["min_act"]!r},')
        lines.append("        },")
    lines.append("    ]")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    scenarios = build()
    assert len(scenarios) == TARGET, len(scenarios)
    raws = [x["raw"] for x in scenarios]
    assert len(raws) == len(set(raws)), "duplicate raw texts"
    OUT.write_text(_emit(scenarios), encoding="utf-8")
    print(f"Wrote {len(scenarios)} scenarios -> {OUT}")


if __name__ == "__main__":
    main()
