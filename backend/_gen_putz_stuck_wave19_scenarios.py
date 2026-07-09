"""Generator Putz & Stuck Welle 19 — 150 Basisszenarien.

Fokus: Materialvorschläge, Werkzeugvorschläge, POB-Struktur (keine Dubletten/Fantasie),
kurz/lang, Umgangssprache, Katalogtiefe. Rein additiv.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "putz_stuck_wave19_scenarios.py"
TARGET = 150
SITE_A = "Höxter"
SITE_B = "Warburg"
SITE_C = "Beverungen"


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
    )
    d.update(kw)
    return d


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
            min_act=1,
        ),
        s(
            "Unterputz aufgetragen Grundputz vorher fertig.",
            ("Unterputz aufgetragen",),
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
        s(raw3, ("Altputz entfernt", "Wand geschliffen", "Unterputz aufgetragen", "WDVS gedübelt", "Armierung ausgeführt", "Reibputz aufgetragen", "Putz filziert", "Außenputz aufgetragen"), problem=True, open_=True, customer=True, prob_must=("feuchte",), open_must=("montag",), cust_must=("kundengespräch",), min_act=5),
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
    ]


def _short_broken() -> list[dict]:
    return [
        s("innenputz gipsputz drauf 40 qm", ("Innenputz aufgetragen",), min_act=1),
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
    ]


def _qty_pad(count: int) -> list[dict]:
    templates: list[dict] = [
        {
            "raw": lambda q: f"{q} Quadratmeter Innenputz Gipsputz aufgetragen.",
            "acts": ("Innenputz aufgetragen",),
            "mats": ("Gipsputz",),
            "sugs": ("Putzmaschine benutzt?",),
        },
        {
            "raw": lambda q: f"{q} Quadratmeter WDVS Dämmung geklebt EPS {q+15} Millimeter.",
            "acts": ("WDVS Dämmung geklebt",),
            "mats": ("EPS Dämmplatten",),
            "sugs": ("Zahntraufel benutzt?",),
        },
        {
            "raw": lambda q: f"Putz geglättet {q} Quadratmeter Feinputz Decke.",
            "acts": ("Putz geglättet",),
            "mats": ("Feinputz",),
            "sugs": ("Glättkelle benutzt?",),
            "forbid_sugs": ("Feinputz benutzt?",),
        },
        {
            "raw": lambda q: f"WDVS gedübelt {q} Quadratmeter Tellerdübel gesetzt.",
            "acts": ("WDVS gedübelt",),
            "mats": ("Tellerdübel",),
            "forbid_sugs": ("Tellerdübel benutzt?",),
        },
        {
            "raw": lambda q: f"{q} Meter APU-Leiste montiert Eckschutzschiene gesetzt.",
            "acts": ("APU-Leisten montiert", "Eckschutzprofile gesetzt"),
            "sugs": ("Klebeputz benutzt?",),
        },
        {
            "raw": lambda q: f"{q} Quadratmeter Außenputz Kratzputz Reibputz Putz filziert.",
            "acts": ("Kratzputz aufgetragen", "Putz filziert"),
            "mats": ("Reibputz",),
            "sugs": ("Filzbrett benutzt?",),
        },
        {
            "raw": lambda q: f"Sockelprofil {q} Millimeter montiert Tropfkante gesetzt.",
            "acts": ("Sockelprofile montiert", "Tropfkantenprofile gesetzt"),
            "mats": ("Sockelprofil",),
            "sugs": ("Sockeldämmung benutzt?",),
        },
        {
            "raw": lambda q: (
                f"Leibungsprofil PVC gesetzt {q} Fenster Problem Material fehlt Offen Rest Donnerstag."
            ),
            "acts": ("Leibungsprofile gesetzt",),
            "mats": ("Leibungsprofil",),
            "sugs": ("Klebeputz benutzt?",),
            "problem": True,
            "open_": True,
            "prob_must": ("material",),
            "open_must": ("donnerstag",),
        },
    ]
    out: list[dict] = []
    q = 40
    i = 0
    while len(out) < count:
        tpl = templates[i % len(templates)]
        raw = tpl["raw"](q)
        kw = {k: v for k, v in tpl.items() if k not in ("raw", "acts")}
        out.append(s(raw, tpl["acts"], **kw))
        i += 1
        if i % 3 == 0:
            q += 5
    return out


def build() -> list[dict]:
    items: list[dict] = []
    items += _suggestion_positive()
    items += _suggestion_negative()
    items += _pob_deep()
    items += _material_chains()
    items += _long_and_mega()
    items += _short_broken()
    need = TARGET - len(items)
    if need > 0:
        items += _qty_pad(need)
    return items[:TARGET]


def _emit(scenarios: list[dict]) -> str:
    lines = [
        '"""Putz & Stuck Welle 19 — 150 Basisszenarien (generiert)."""',
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
        "cust_must", "cust_not", "sum_forbid",
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
