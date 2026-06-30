"""Welle 22: Frische Basisszenarien für Cross-Validierung P1/P2/P3.

Bewusst andere Texte als Welle 20/21 — Fokus Summary, Kundengespräch, Problem/Offen.
"""

from __future__ import annotations

from typing import Any, Iterator

# Spec-Keys:
#   raw, acts, mats, forbid_acts, min_act
#   problem, open_, customer
#   mat_echo (P1), sum_forbid
#   cust_not, cust_must (P2)
#   prob_must, prob_not, open_must, open_not (P3)

SCENARIOS: dict[str, list[dict[str, Any]]] = {
    "GaLaBau": [
        {
            "raw": (
                "Am Vormittag 42 Quadratmeter Rasen verlegt Rollrasen verwendet "
                "Problem Regenwasser abpumpen Offen Abschlusskante Donnerstag "
                "mit der Bauherrin kurz gesprochen sie ist einverstanden."
            ),
            "acts": ("42 m² Rasen verlegt",),
            "mats": ("Rollrasen",),
            "problem": True,
            "open_": True,
            "customer": True,
            "mat_echo": True,
            "cust_not": ("42", "rasen verlegt", "quadratmeter", "rollrasen"),
            "cust_must": ("gesprochen", "einverstanden"),
            "prob_must": ("regen",),
            "prob_not": ("rasen verlegt", "42", "quadratmeter"),
            "open_must": ("donnerstag", "kante", "offen"),
            "open_not": ("rasen", "42"),
        },
        {
            "raw": (
                "22 Quadratmeter Klinker verlegt Klinker verarbeitet "
                "Problem Frost im Unterbau Offen Randstein morgen."
            ),
            "acts": ("22 m² Klinker verlegt",),
            "mats": ("Klinker",),
            "forbid_acts": ("Klinker verarbeitet",),
            "problem": True,
            "open_": True,
            "mat_echo": True,
            "sum_forbid": ("Klinker verarbeitet", "zum Einsatz"),
            "prob_must": ("frost",),
            "prob_not": ("klinker verlegt", "22"),
            "open_must": ("randstein", "morgen", "offen"),
            "open_not": ("klinker verlegt",),
        },
        {
            "raw": (
                "Acht Ziersträucher gesetzt und Einfassung montiert danach mit dem Auftraggeber "
                "unterhalten er freut sich auf die Fertigstellung."
            ),
            "acts": ("Ziersträucher gesetzt", "Einfassung montiert"),
            "customer": True,
            "cust_not": ("gesetzt", "montiert", "acht", "einfassung"),
            "cust_must": ("unterhalten", "auftraggeber"),
        },
        {
            "raw": "Hecke geschnitten Problem Motorsäge defekt Offen Laubentsorgung Freitag.",
            "acts": ("Hecke geschnitten",),
            "problem": True,
            "open_": True,
            "prob_must": ("motorsäge", "defekt"),
            "prob_not": ("hecke",),
            "open_must": ("laub", "freitag", "offen"),
        },
        {
            "raw": (
                "35 qm Terrassenplatten verlegt Platten verarbeitet "
                "Kundin vor Ort Farbe bestätigt."
            ),
            "acts": ("35 m² Terrassenplatten verlegt",),
            "mats": ("Terrassenplatten",),
            "forbid_acts": ("Platten verarbeitet",),
            "customer": True,
            "mat_echo": True,
            "cust_not": ("35", "verlegt", "platten verarbeitet"),
            "cust_must": ("kundin", "farbe"),
        },
        {
            "raw": (
                "12 qm Einfahrt gepflastert Pflastersteine eingebaut problem werkzeug kaputt "
                "offen fugen morgen kunde zufrieden"
            ),
            "acts": ("12 m² Pflaster verlegt",),
            "mats": ("Pflastersteine",),
            "problem": True,
            "open_": True,
            "customer": True,
            "mat_echo": True,
            "cust_not": ("12", "pflaster", "qm", "fugen"),
            "cust_must": ("zufrieden",),
            "prob_must": ("werkzeug", "kaputt"),
            "prob_not": ("pflaster", "12", "einfahrt"),
            "open_must": ("fugen", "morgen", "offen"),
        },
        {
            "raw": "Mit dem Kunden Rücksprache gehalten nächster Termin abgestimmt.",
            "acts": (),
            "min_act": 0,
            "customer": True,
            "cust_must": ("rücksprache", "abgestimmt"),
            "cust_not": ("verlegt", "m²"),
        },
        {
            "raw": "Rollrasen 28 Quadratmeter verlegt Problem Lieferwagen zu spät Offen Kante Samstag.",
            "acts": ("28 m² Rasen verlegt",),
            "mats": ("Rollrasen",),
            "problem": True,
            "open_": True,
            "mat_echo": True,
            "prob_must": ("liefer", "spät"),
            "open_must": ("kante", "samstag", "offen"),
        },
        {
            "raw": "Unkraut entfernt und Boden aufgefräst.",
            "acts": ("Unkraut entfernt",),
            "min_act": 1,
        },
        {
            "raw": (
                "Sichtschutz montiert 6 Laufende Meter Problem Befestigung fehlt "
                "Offen Endkappe nächste Woche Bauherr informiert."
            ),
            "acts": ("Sichtschutz montiert",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("informiert", "bauherr"),
            "cust_not": ("6", "laufende", "sichtschutz montiert"),
            "prob_must": ("befestigung", "fehlt"),
            "open_must": ("endkappe", "woche", "offen"),
        },
    ],
    "Trockenbau": [
        {
            "raw": (
                "Zwei Trennwände geschlossen Gipskartonplatten montiert Gipskarton verarbeitet "
                "Problem Akustikdämmung knapp Offen Spachtel morgen Kundin zufrieden."
            ),
            "acts": ("Trockenbauwand geschlossen", "Gipskartonplatten montiert"),
            "mats": ("Gipskartonplatten",),
            "forbid_acts": ("Gipskarton verarbeitet",),
            "problem": True,
            "open_": True,
            "customer": True,
            "mat_echo": True,
            "cust_not": ("gipskarton", "trennwand", "geschlossen"),
            "prob_must": ("akustik", "knapp"),
            "open_must": ("spachtel", "morgen", "offen"),
        },
        {
            "raw": (
                "Decke abgehängt UK-Stützen gesetzt Problem Lieferverzug Offen Rigips Rest Freitag "
                "mit dem Bauherrn gesprochen alles abgestimmt."
            ),
            "acts": ("Decke abgehängt",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("gesprochen", "abgestimmt"),
            "cust_not": ("decke", "abgehängt"),
            "prob_must": ("liefer",),
            "open_must": ("rigips", "freitag", "offen"),
        },
        {
            "raw": "Ständerwerk montiert Dämmung eingebaut.",
            "acts": ("Ständerwerk montiert", "Dämmung eingebaut"),
            "mats": ("Mineralwolle",),
        },
        {
            "raw": (
                "Trockenbau komplett Wände Decke Spachtelarbeiten Kundin mega zufrieden "
                "Problem Staub im Treppenhaus Offen Rest Montag."
            ),
            "acts": ("Trockenbauwand geschlossen",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_not": ("spachtel", "decke", "wände"),
            "cust_must": ("zufrieden", "kundin"),
            "prob_must": ("staub",),
            "open_must": ("montag", "offen"),
        },
        {
            "raw": "Kundengespräch gehabt Farbton für Spachtel gewählt Problem Raum zu kalt Offen Heizung an.",
            "acts": (),
            "min_act": 0,
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("kundengespräch", "farb"),
            "prob_must": ("kalt",),
            "open_must": ("heizung", "offen"),
        },
        {
            "raw": "45 qm Gipskarton verlegt Gipskartonplatten verwendet.",
            "acts": ("Gipskartonplatten montiert",),
            "mats": ("Gipskartonplatten",),
            "mat_echo": True,
            "sum_forbid": ("Gipskarton verarbeitet", "zum Einsatz"),
        },
        {
            "raw": "Brandschutzplatten eingebaut Problem Schrauben falsch Offen Nachbestell Dienstag.",
            "acts": ("Brandschutzplatten eingebaut",),
            "problem": True,
            "open_": True,
            "prob_must": ("schrauben",),
            "open_must": ("nachbestell", "dienstag", "offen"),
        },
        {
            "raw": "Auftraggeber kurz informiert nächste Phase besprochen.",
            "customer": True,
            "min_act": 0,
            "cust_must": ("informiert", "auftraggeber"),
        },
        {
            "raw": "Trockenbauwand geschlossen Problem Maßabweichung Offen Ausgleich morgen.",
            "acts": ("Trockenbauwand geschlossen",),
            "problem": True,
            "open_": True,
            "prob_must": ("maß",),
            "open_must": ("ausgleich", "morgen", "offen"),
        },
        {
            "raw": "Fugen gespachtelt und geschliffen.",
            "acts": ("Fugen gespachtelt",),
            "min_act": 1,
        },
    ],
    "Fliesen": [
        {
            "raw": (
                "Gästebad 18 Quadratmeter Fliesen verlegt Fliesenkleber verwendet "
                "Problem Wand nicht lotrecht Offen Silikon morgen Kunde gred war ok."
            ),
            "acts": ("18 m² Fliesen verlegt",),
            "mats": ("Fliesen", "Fliesenkleber"),
            "problem": True,
            "open_": True,
            "customer": True,
            "mat_echo": True,
            "cust_not": ("18", "fliesen verlegt", "bad"),
            "cust_must": ("kunde", "einverstanden"),
            "prob_must": ("lotrecht",),
            "open_must": ("silikon", "morgen", "offen"),
        },
        {
            "raw": (
                "Großformatfliesen 32 qm verlegt Großformat verarbeitet "
                "Problem Schnittkante Offen Restfliesen Freitag."
            ),
            "acts": ("32 m² Fliesen verlegt",),
            "mats": ("Fliesen",),
            "forbid_acts": ("Großformat verarbeitet",),
            "problem": True,
            "open_": True,
            "mat_echo": True,
            "prob_must": ("schnitt",),
            "open_must": ("rest", "freitag", "offen"),
        },
        {
            "raw": (
                "Bodenablauf eingebaut Abdichtung aufgetragen mit der Kundin gesprochen "
                "sie hat Muster bestätigt."
            ),
            "acts": ("Bodenablauf eingebaut", "Abdichtung aufgetragen"),
            "customer": True,
            "cust_not": ("bodenablauf", "abdichtung", "eingebaut"),
            "cust_must": ("gesprochen", "muster"),
        },
        {
            "raw": "Nischen verfugt Problem Fuge zu schmal Offen Nacharbeit nächste Woche.",
            "acts": ("Fliesen verfugt",),
            "problem": True,
            "open_": True,
            "prob_must": ("fuge",),
            "open_must": ("nacharbeit", "woche", "offen"),
        },
        {
            "raw": "22 qm Wandfliesen verlegt Problem Kleber härtet zu langsam Offen Türschwelle morgen.",
            "acts": ("22 m² Fliesen verlegt",),
            "mats": ("Fliesen",),
            "problem": True,
            "open_": True,
            "mat_echo": True,
            "prob_must": ("kleber",),
            "open_must": ("schwelle", "morgen", "offen"),
        },
        {
            "raw": "Bauherrin war vor Ort und sehr happy mit dem Fortschritt.",
            "customer": True,
            "min_act": 0,
            "cust_must": ("bauherrin", "happy"),
        },
        {
            "raw": (
                "Dusche gefliest 14 Quadratmeter Fliesen verarbeitet "
                "offen Armatur montieren problem Dichtband fehlt"
            ),
            "acts": ("14 m² Fliesen verlegt",),
            "mats": ("Fliesen",),
            "problem": True,
            "open_": True,
            "mat_echo": True,
            "prob_must": ("dichtband", "fehlt"),
            "open_must": ("armatur", "offen"),
            "prob_not": ("14", "dusche gefliest"),
            "open_not": ("fliesen verlegt",),
        },
        {
            "raw": "Grundierung aufgetragen und Haftbrücke verarbeitet.",
            "acts": ("Grundierung aufgetragen",),
            "min_act": 1,
        },
        {
            "raw": "Kundengespräch Fliesenformat und Fugenfarbe festgelegt Problem Lieferung Offen Rest Donnerstag.",
            "acts": (),
            "min_act": 0,
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("kundengespräch", "fugen"),
            "prob_must": ("lieferung",),
            "open_must": ("donnerstag", "offen"),
        },
        {
            "raw": "Silikonfugen im WC gemacht.",
            "acts": ("Silikonfugen",),
            "min_act": 1,
        },
    ],
    "SHK": [
        {
            "raw": (
                "Heizkörper getauscht Thermostatventile eingebaut Problem Dichtung undicht "
                "Offen Entlüftung morgen mit dem Kunden gesprochen er ist zufrieden."
            ),
            "acts": ("Heizkörper getauscht", "Thermostatventile eingebaut"),
            "mats": ("Thermostatventile",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_not": ("heizkörper", "thermostat", "getauscht"),
            "cust_must": ("gesprochen", "zufrieden"),
            "prob_must": ("dichtung", "undicht"),
            "open_must": ("entlüftung", "morgen", "offen"),
        },
        {
            "raw": (
                "Fußbodenheizung verlegt Heizrohre eingebaut Heizrohre verarbeitet "
                "Problem Manometer defekt Offen Dämmung Freitag."
            ),
            "acts": ("Fußbodenheizung verlegt",),
            "mats": ("Heizrohre",),
            "forbid_acts": ("Heizrohre verarbeitet",),
            "problem": True,
            "open_": True,
            "mat_echo": True,
            "prob_must": ("manometer",),
            "open_must": ("dämmung", "freitag", "offen"),
        },
        {
            "raw": "WC montiert Spülkasten angeschlossen.",
            "acts": ("WC montiert",),
            "min_act": 1,
        },
        {
            "raw": (
                "Rohrleitung verlegt Problem Pressfitting fehlt Offen Nachlieferung Dienstag "
                "Bauleitung informiert."
            ),
            "acts": ("Rohrleitung verlegt",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("informiert", "bauleitung"),
            "prob_must": ("pressfitting", "fehlt"),
            "open_must": ("nachliefer", "dienstag", "offen"),
        },
        {
            "raw": (
                "12 Heizkörper montiert Problem Anschluss zu eng Offen Ventile morgen "
                "Kundin vor Ort zufrieden."
            ),
            "acts": ("Heizkörper montiert",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_not": ("12", "heizkörper montiert"),
            "cust_must": ("zufrieden", "kundin"),
            "prob_must": ("anschluss", "eng"),
            "open_must": ("ventile", "morgen", "offen"),
        },
        {
            "raw": "Sanitärinstallation im Bad abgeschlossen Auftraggeber abgestimmt.",
            "acts": ("Sanitärinstallation",),
            "customer": True,
            "cust_must": ("abgestimmt", "auftraggeber"),
        },
        {
            "raw": "DN 50 Abwasserrohr eingebaut Problem Gefälle zu flach Offen Korrektur morgen.",
            "acts": ("Abwasserrohr eingebaut",),
            "problem": True,
            "open_": True,
            "prob_must": ("gefälle",),
            "open_must": ("korrektur", "morgen", "offen"),
        },
        {
            "raw": (
                "Wärmepumpe angeschlossen Problem Stromkreis Offen Elektriker Termin "
                "mit Kunde Rücksprache."
            ),
            "acts": ("Wärmepumpe angeschlossen",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("rücksprache", "kunde"),
            "prob_must": ("strom",),
            "open_must": ("elektriker", "offen"),
        },
        {
            "raw": "Thermostatventile eingebaut Thermostatventile verarbeitet.",
            "acts": ("Thermostatventile eingebaut",),
            "mats": ("Thermostatventile",),
            "mat_echo": True,
        },
        {
            "raw": "Rücklaufverschraubungen montiert.",
            "acts": ("Rücklaufverschraubungen montiert",),
            "min_act": 1,
        },
    ],
    "Hochbau": [
        {
            "raw": (
                "Fundament betoniert Bewehrung eingebaut Problem Betonpumpe verspätet "
                "Offen Abziehen morgen Bauherr kurz informiert."
            ),
            "acts": ("Fundament betoniert", "Bewehrung eingebaut"),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("informiert", "bauherr"),
            "cust_not": ("fundament", "betoniert"),
            "prob_must": ("betonpumpe", "verspät"),
            "open_must": ("abziehen", "morgen", "offen"),
        },
        {
            "raw": (
                "Schalung erstellt Beton gegossen Beton verarbeitet "
                "Problem Riss in Ecke Offen Nachbehandlung Freitag."
            ),
            "acts": ("Schalung erstellt", "Beton gegossen"),
            "mats": ("Beton",),
            "forbid_acts": ("Beton verarbeitet",),
            "problem": True,
            "open_": True,
            "mat_echo": True,
            "prob_must": ("riss",),
            "open_must": ("nachbehandlung", "freitag", "offen"),
        },
        {
            "raw": "Mauerwerk hochgezogen Problem Mörtel zu nass Offen Reststein morgen.",
            "acts": ("Mauerwerk hochgezogen",),
            "problem": True,
            "open_": True,
            "prob_must": ("mörtel",),
            "open_must": ("reststein", "morgen", "offen"),
        },
        {
            "raw": (
                "Filigrandecke montiert Problem Kranwartezeit Offen Verbindung nächste Woche "
                "mit dem Kunden unterhalten alles klar."
            ),
            "acts": ("Filigrandecke montiert",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("unterhalten", "kunden"),
            "cust_not": ("filigrandecke", "montiert"),
            "prob_must": ("kran",),
            "open_must": ("verbindung", "woche", "offen"),
        },
        {
            "raw": "Betondecke geschalt Bewehrung verlegt.",
            "acts": ("Betondecke geschalt", "Bewehrung verlegt"),
            "min_act": 1,
        },
        {
            "raw": (
                "40 Kubikmeter Beton gegossen Beton verarbeitet Problem Wetter Offen Abbinden morgen "
                "Kundin zufrieden mit Fortschritt."
            ),
            "acts": ("Beton gegossen",),
            "mats": ("Beton",),
            "forbid_acts": ("Beton verarbeitet",),
            "problem": True,
            "open_": True,
            "customer": True,
            "mat_echo": True,
            "cust_not": ("40", "kubik", "beton gegossen"),
            "prob_must": ("wetter",),
            "open_must": ("abbinden", "morgen", "offen"),
        },
        {
            "raw": "Auftraggeber war da und einverstanden mit dem Baufortschritt.",
            "customer": True,
            "min_act": 0,
            "cust_must": ("einverstanden", "auftraggeber"),
        },
        {
            "raw": "Schalung gestellt Problem Holz feucht Offen Trocknung Dienstag.",
            "acts": ("Schalung gestellt",),
            "problem": True,
            "open_": True,
            "prob_must": ("feucht",),
            "open_must": ("trocknung", "dienstag", "offen"),
        },
        {
            "raw": (
                "Kundengespräch Bauablauf besprochen Problem Genehmigung Offen Unterlagen Freitag."
            ),
            "min_act": 0,
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("kundengespräch", "besprochen"),
            "prob_must": ("genehmigung",),
            "open_must": ("unterlagen", "freitag", "offen"),
        },
        {
            "raw": "Treppenhaus betoniert.",
            "acts": ("Treppenhaus betoniert",),
            "min_act": 1,
        },
    ],
    "Tiefbau": [
        {
            "raw": (
                "Kanalgraben 18 Meter ausgehoben Problem Grundwasser Offen Rohrleitung morgen "
                "mit Bauleitung Rücksprache."
            ),
            "acts": ("Kanalgraben ausgehoben",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("rücksprache", "bauleitung"),
            "cust_not": ("18", "meter", "ausgehoben"),
            "prob_must": ("grundwasser",),
            "open_must": ("rohrleitung", "morgen", "offen"),
        },
        {
            "raw": (
                "Schottertragschicht eingebaut Schotter verarbeitet "
                "Problem Verdichtung ungleich Offen Asphalt Donnerstag."
            ),
            "acts": ("Schotter eingebaut",),
            "mats": ("Schotter",),
            "forbid_acts": ("Schotter verarbeitet",),
            "problem": True,
            "open_": True,
            "mat_echo": True,
            "prob_must": ("verdichtung",),
            "open_must": ("asphalt", "donnerstag", "offen"),
        },
        {
            "raw": "KG-Rohr verlegt Problem Gefälle Offen Anschluss morgen Kunde informiert.",
            "acts": ("KG-Rohr verlegt",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("informiert", "kunde"),
            "prob_must": ("gefälle",),
            "open_must": ("anschluss", "morgen", "offen"),
        },
        {
            "raw": "Baugrube ausgehoben und gesichert.",
            "acts": ("Baugrube ausgehoben",),
            "min_act": 1,
        },
        {
            "raw": (
                "25 qm Pflasterdecke verlegt Pflastersteine eingebaut problem werkzeug defekt "
                "offen einbau morgen kundin zufrieden"
            ),
            "acts": ("25 m² Pflaster verlegt",),
            "mats": ("Pflastersteine",),
            "problem": True,
            "open_": True,
            "customer": True,
            "mat_echo": True,
            "cust_not": ("25", "pflaster", "qm"),
            "prob_must": ("werkzeug", "defekt"),
            "open_must": ("morgen", "offen"),
            "prob_not": ("pflasterdecke", "25"),
        },
        {
            "raw": "Entwässerung verlegt Problem Fallrohr fehlt Offen Nachlieferung Freitag.",
            "acts": ("Entwässerung verlegt",),
            "problem": True,
            "open_": True,
            "prob_must": ("fallrohr", "fehlt"),
            "open_must": ("nachliefer", "freitag", "offen"),
        },
        {
            "raw": "Bauherr war vor Ort und happy mit der Planung.",
            "customer": True,
            "min_act": 0,
            "cust_must": ("bauherr", "happy"),
        },
        {
            "raw": (
                "Fundamentplanum hergestellt Problem Regen Offen Drainage nächste Woche "
                "Auftraggeber abgesprochen."
            ),
            "acts": ("Fundamentplanum hergestellt",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("abgesprochen", "auftraggeber"),
            "prob_must": ("regen",),
            "open_must": ("drainage", "woche", "offen"),
        },
        {
            "raw": "Rohrgraben 30 laufende Meter fertiggestellt.",
            "acts": ("Rohrgraben fertiggestellt",),
            "min_act": 1,
        },
        {
            "raw": "Kundengespräch Trassenführung geklärt Problem Leitungskreuzung Offen Freigabe Montag.",
            "min_act": 0,
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("kundengespräch", "geklärt"),
            "prob_must": ("leitungs",),
            "open_must": ("freigabe", "montag", "offen"),
        },
    ],
    "Putz": [
        {
            "raw": (
                "Außenputz 120 Quadratmeter aufgetragen Außenputz verarbeitet "
                "Problem Gerüstwind Offen Armierung morgen Kunde zufrieden."
            ),
            "acts": ("Außenputz aufgetragen",),
            "mats": ("Außenputz",),
            "forbid_acts": ("Außenputz verarbeitet",),
            "problem": True,
            "open_": True,
            "customer": True,
            "mat_echo": True,
            "cust_not": ("120", "außenputz", "aufgetragen"),
            "cust_must": ("zufrieden",),
            "prob_must": ("gerüst", "wind"),
            "open_must": ("armierung", "morgen", "offen"),
        },
        {
            "raw": (
                "Innenputz im OG verputzt Problem Riss im Altbau Offen Spachtel Freitag "
                "mit der Kundin gesprochen sie ist einverstanden."
            ),
            "acts": ("Innenputz verputzt",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("einverstanden",),
            "cust_not": ("innenputz", "verputzt"),
            "prob_must": ("riss",),
            "open_must": ("spachtel", "freitag", "offen"),
        },
        {
            "raw": "WDVS montiert Problem Dübel zu kurz Offen Nachbestell Dienstag.",
            "acts": ("WDVS montiert",),
            "problem": True,
            "open_": True,
            "prob_must": ("dübel",),
            "open_must": ("nachbestell", "dienstag", "offen"),
        },
        {
            "raw": "Grundputz aufgetragen Haftgrund verarbeitet.",
            "acts": ("Grundputz aufgetragen",),
            "mats": ("Haftgrund",),
            "mat_echo": True,
            "sum_forbid": ("Haftgrund verarbeitet", "zum Einsatz"),
        },
        {
            "raw": (
                "Stuckateurarbeiten Fensterlaibungen Problem Profil fehlt Offen Lieferung morgen "
                "Bauherrin informiert."
            ),
            "acts": ("Stuckateurarbeiten",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_must": ("informiert", "bauherrin"),
            "prob_must": ("profil", "fehlt"),
            "open_must": ("lieferung", "morgen", "offen"),
        },
        {
            "raw": (
                "65 qm Oberputz aufgebracht Problem Temperatur zu niedrig Offen Heizphase Donnerstag "
                "Kundengespräch Farbton bestätigt."
            ),
            "acts": ("Oberputz aufgetragen",),
            "problem": True,
            "open_": True,
            "customer": True,
            "mat_echo": True,
            "cust_must": ("kundengespräch", "farb"),
            "prob_must": ("temperatur",),
            "open_must": ("heizphase", "donnerstag", "offen"),
        },
        {
            "raw": "Auftraggeber kurz da alles abgestimmt.",
            "customer": True,
            "min_act": 0,
            "cust_must": ("abgestimmt", "auftraggeber"),
        },
        {
            "raw": "Fassade gerüstet Problem Anlegeplatz eng Offen Materialumschlag morgen.",
            "acts": ("Fassade gerüstet",),
            "problem": True,
            "open_": True,
            "prob_must": ("anlegeplatz",),
            "open_must": ("material", "morgen", "offen"),
        },
        {
            "raw": (
                "problem Gerüst nicht frei offen putz montag kundin zufrieden "
                "40 qm sockelputz aufgetragen"
            ),
            "acts": ("Sockelputz aufgetragen",),
            "problem": True,
            "open_": True,
            "customer": True,
            "cust_not": ("40", "sockelputz", "qm"),
            "prob_must": ("gerüst",),
            "open_must": ("putz", "montag", "offen"),
            "prob_not": ("sockelputz", "40"),
        },
        {
            "raw": "Laibungen gespachtelt.",
            "acts": ("Laibungen gespachtelt",),
            "min_act": 1,
        },
    ],
}


def all_base_scenarios() -> Iterator[tuple[str, dict[str, Any]]]:
    for trade, specs in SCENARIOS.items():
        for spec in specs:
            yield trade, spec
