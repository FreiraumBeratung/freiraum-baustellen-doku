"""Welle 53: GaLaBau-Schutznetz — 70 Basisszenarien (Gartenalltag, Whisper, Kunde/Problem).

Rein additiv. Keine bestehenden Wellen aendern.
"""

from __future__ import annotations


def all_base_scenarios() -> list[dict]:
    return [
        {
            "raw": "Heute 18 Quadratmeter Granitpflaster im Halbverband verlegt Einfahrt.",
            "acts": ("pflaster",),
            "mats": ("pflaster",),
            "min_act": 1,
        },
        {
            "raw": "12 Quadratmeter Waschbetonplatten auf der Einfahrt verlegt.",
            "acts": ("platten",),
            "min_act": 1,
        },
        {
            "raw": "Gartenweg mit Trittplatten gesetzt durchs Beet.",
            "acts": ("platten",),
            "min_act": 1,
        },
        {
            "raw": "Heute 6 l-steine als Hangabfang gesetzt hinter der Terrasse.",
            "acts": ("l-stein",),
            "mats": ("l-stein",),
            "sugs": ("Beton",),
            "forbid_acts": ("lfm",),
            "forbid_hours": True,
            "min_act": 1,
        },
        {
            "raw": "10 laufende Meter Tiefbordsteine an der Einfahrt gesetzt.",
            "acts": ("tiefbord",),
            "forbid_acts": ("l-stein",),
            "min_act": 1,
        },
        {
            "raw": "Heute 35 Quadratmeter Pflaster im Drittelverband verlegt.",
            "acts": ("pflaster", "drittelverband"),
            "min_act": 1,
        },
        {
            "raw": "Fugen mit Fugensand gefüllt nach dem Verlegen.",
            "acts": ("fugen",),
            "mats": ("fugensand",),
            "min_act": 1,
        },
        {
            "raw": "Altes Pflaster aufgenommen und neue Pflastersteine nach Muster verlegt.",
            "acts": ("aufgenommen", "pflaster"),
            "min_act": 1,
        },
        {
            "raw": "Vier Kubikmeter Mutterboden eingebaut auf die Beete.",
            "acts": ("mutterboden",),
            "mats": ("mutterboden",),
            "min_act": 1,
        },
        {
            "raw": "Oberboden abgetragen und seitlich gelagert für später.",
            "acts": ("oberboden",),
            "min_act": 1,
        },
        {
            "raw": "Fünf Kubikmeter Frostschutz eingebaut und verdichtet Einfahrt.",
            "acts": ("frostschutz",),
            "min_act": 1,
        },
        {
            "raw": "Kiesbeet angelegt zwei Kubikmeter Kies eingebaut.",
            "acts": ("kies",),
            "mats": ("kies",),
            "min_act": 1,
        },
        {
            "raw": "Edelsplitt 8/16 aufgetragen auf den Gartenweg und abgezogen.",
            "acts": ("splitt",),
            "mats": ("splitt",),
            "min_act": 1,
        },
        {
            "raw": "Heute 12 Liguster als Hecke gepflanzt entlang der Grenze.",
            "acts": ("pflanzen",),
            "min_act": 1,
        },
        {
            "raw": "Kirschlorbeer gesetzt als Sichtschutz an der Nachbarseite.",
            "acts": ("pflanzen",),
            "min_act": 1,
        },
        {
            "raw": "Drei Bäume gepflanzt und angebunden im Vorgarten.",
            "acts": ("pflanzen",),
            "min_act": 1,
        },
        {
            "raw": "Staudenbeet angelegt und Unkraut gejätet davor.",
            "acts": ("unkraut",),
            "min_act": 1,
        },
        {
            "raw": "Grünschnitt gehäckelt und entsorgt eine Anhängerladung.",
            "acts": ("grünschnitt",),
            "forbid_hours": True,
            "min_act": 1,
        },
        {
            "raw": "Alten Wurzelstock ausgefräst neben der Terrasse keine Stunden genannt.",
            "acts": ("wurzelstock",),
            "forbid_hours": True,
            "min_act": 1,
        },
        {
            "raw": "Kahle Stellen im Rasen nachgesät und danach bewässert.",
            "acts": ("rasen",),
            "min_act": 1,
        },
        {
            "raw": "Sträucher zurückgeschnitten und Hecke getrimmt vorne.",
            "acts": ("hecke",),
            "min_act": 1,
        },
        {
            "raw": "Gartenteich angelegt und Teichfolie verlegt heute.",
            "acts": ("teich",),
            "min_act": 1,
        },
        {
            "raw": "Bachlauf hergestellt vom Teich zur Senke.",
            "acts": ("teich",),
            "min_act": 1,
        },
        {
            "raw": "15 Meter Drainagerohr DN 100 verlegt im Garten.",
            "acts": ("drainage",),
            "min_act": 1,
        },
        {
            "raw": "Rigole eingebaut vor der Einfahrt gegen das Wasser.",
            "acts": ("rigole",),
            "min_act": 1,
        },
        {
            "raw": "Hofablauf gesetzt und an die Drainage angeschlossen.",
            "acts": ("hofablauf",),
            "min_act": 1,
        },
        {
            "raw": "Tropfbewässerung im Beet verlegt und angeschlossen.",
            "acts": ("tropf",),
            "min_act": 1,
        },
        {
            "raw": "Regentonne angeschlossen an das Fallrohr hinterm Haus.",
            "acts": ("regentonne", "wassertonne"),
            "min_act": 1,
        },
        {
            "raw": "Doppelstabmattenzaun 20 Meter gesetzt an der Grenze.",
            "acts": ("zaun",),
            "min_act": 1,
        },
        {
            "raw": "Gartentor montiert in den neuen Zaun.",
            "acts": ("tor",),
            "min_act": 1,
        },
        {
            "raw": "Pergola aufgestellt an der Terrasse heute Nachmittag.",
            "acts": ("pergola",),
            "min_act": 1,
        },
        {
            "raw": "Hochbeet gebaut und mit Erde befüllt zwei Stück.",
            "acts": ("hochbeet",),
            "min_act": 1,
        },
        {
            "raw": "Sichtschutzmatte am Zaun befestigt gegen den Nachbarn.",
            "acts": ("sichtschutz",),
            "min_act": 1,
        },
        {
            "raw": "15 Quadratmeter WPC Terrasse gebaut auf der Unterkonstruktion.",
            "acts": ("wpc", "terrasse"),
            "min_act": 1,
        },
        {
            "raw": "Carport Stellfläche 20 Quadratmeter Pflaster verlegt.",
            "acts": ("pflaster",),
            "min_act": 1,
        },
        {
            "raw": "Gabionenwand vier Meter gesetzt und mit Steinen gefüllt.",
            "acts": ("gabionen",),
            "min_act": 1,
        },
        {
            "raw": "Trockenmauer aus Naturstein gesetzt am Hang.",
            "acts": ("trockenmauer",),
            "min_act": 1,
        },
        {
            "raw": "Drei Findlinge im Beet gesetzt als Blickfang.",
            "acts": ("findling",),
            "min_act": 1,
        },
        {
            "raw": "Unkrautvlies ausgelegt und danach Rindenmulch eingedeckt.",
            "acts": ("vlies", "mulch"),
            "min_act": 1,
        },
        {
            "raw": "Sandkasten angelegt im Spielbereich mit Spielsand.",
            "acts": ("sandkasten",),
            "min_act": 1,
        },
        {
            "raw": "Fallschutz Splitt unter der Schaukel eingebaut.",
            "acts": ("splitt",),
            "mats": ("splitt",),
            "min_act": 1,
        },
        {
            "raw": "Fahrradständer gesetzt vor der Garage.",
            "acts": ("fahrradständer", "fahrradstaender"),
            "min_act": 1,
        },
        {
            "raw": "Stellfläche mit der Rüttelplatte 1,5 Stunden abgerüttelt.",
            "acts": ("rüttel", "abgerüttelt"),
            "mach": ("Rüttelplatte: 1,5",),
            "min_act": 1,
        },
        {
            "raw": "3 Stunden mit dem Minibagger Aushub für den Teich gemacht.",
            "acts": ("bagger",),
            "mach": ("Bagger: 3",),
            "min_act": 1,
        },
        {
            "raw": "Heute 4 l steine gesetzt Hangabfang keine Betonmenge genannt.",
            "acts": ("l-stein",),
            "mats": ("l-stein",),
            "sugs": ("Beton",),
            "forbid_mats": ("Beton 0",),
            "forbid_hours": True,
            "min_act": 1,
        },
        {
            "raw": "14 laufende Meter Kantensteine gesetzt.",
            "acts": ("kantenstein", "lfm"),
            "forbid_acts": ("l-stein",),
            "sugs": ("Beton",),
            "min_act": 1,
        },
        {
            "raw": "Schotter eingearbeitet mit Handstampfer verdichtet keine Maschinenstunden.",
            "acts": ("schotter",),
            "forbid_hours": True,
            "min_act": 1,
        },
        {
            "raw": "Totholz mit der Kettensäge zerkleinert und entsorgt keine Stunden.",
            "acts": ("entsorgt",),
            "forbid_hours": True,
            "min_act": 1,
        },
        {
            "raw": "Palisaden gesetzt 8 laufende Meter.",
            "acts": ("palisad",),
            "sugs": ("Beton",),
            "forbid_mats": ("Beton 0",),
            "min_act": 1,
        },
        {
            "raw": "Pflaster verlegt Einkehrmaterial eingearbeitet ein Sack.",
            "acts": ("pflaster", "einkehrmaterial"),
            "forbid_sugs": ("Fugensand",),
            "min_act": 1,
        },
        {
            "raw": "Neue Holzleisten an der Gartenhütte montiert alte demontiert.",
            "acts": ("holzleiste",),
            "forbid_acts": ("Gartenhütte demontiert",),
            "min_act": 1,
        },
        {
            "raw": "Ilex mit der Kettensäge bodennah abgeschnitten keine Stunden.",
            "acts": ("ilex",),
            "forbid_hours": True,
            "min_act": 1,
        },
        {
            "raw": "Zwei Kubikmeter Schotter und Splitt 5/8 eingebaut Hof.",
            "acts": ("schotter", "splitt"),
            "mats": ("schotter", "splitt"),
            "min_act": 2,
        },
        {
            "raw": (
                "Heute Pflaster verlegt Kundin hat die Steinfarbe bestätigt "
                "Problem nachts Frost Offen Fugen morgen kehren."
            ),
            "acts": ("pflaster",),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Gefälle nachgearbeitet Problem das Gefälle war falsch "
                "Bauherr hat gemeckert war unzufrieden Offen Restgefälle morgen prüfen."
            ),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 0,
        },
        {
            "raw": (
                "Palisaden wollten wir setzen Problem Lieferung Palisaden fehlt "
                "Offen nächste Woche weiter Kunde informiert."
            ),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 0,
        },
        {
            "raw": (
                "Sturm Äste entfernt und Grünschnitt entsorgt "
                "Kunde informiert war in Ordnung."
            ),
            "acts": ("entsorgt",),
            "customer": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Starkregen Grube voll Problem wir mussten abbrechen "
                "Offen Aushub morgen weiter."
            ),
            "problem": True,
            "open_": True,
            "min_act": 0,
        },
        {
            "raw": (
                "Splitt kam zu spät Problem Lieferung danach noch 10 Quadratmeter "
                "Pflaster verlegt Offen Restreihe morgen."
            ),
            "acts": ("pflaster",),
            "problem": True,
            "open_": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Hecke geschnitten Kundin sehr zufrieden "
                "Offen zweite Seite morgen schneiden."
            ),
            "acts": ("hecke",),
            "open_": True,
            "customer": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Heute 22 Quadratmeter Pflaster verlegt Problem es wurde zu dunkel "
                "mussten aufhören Offen Rest pflastern morgen."
            ),
            "acts": ("pflaster",),
            "problem": True,
            "open_": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Aushub angefangen Problem Bagger defekt mussten stoppen "
                "Offen Aushub nächste Woche Kunde informiert."
            ),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 0,
        },
        {
            "raw": (
                "Mit dem Kunden abgestimmt früher Feierabend wegen Nachbar Lärm "
                "heute Rasen gemäht und Laub entfernt."
            ),
            "acts": ("rasen", "laub"),
            "customer": True,
            "min_act": 1,
        },
        {
            "raw": "Heute 8 lfm Rasenkantensteine gesetzt und Hecke geschnitten.",
            "acts": ("rasenkantenstein", "hecke"),
            "sugs": ("Beton",),
            "forbid_acts": ("l-stein",),
            "min_act": 2,
        },
        {
            "raw": "Rollrasen 25 Quadratmeter verlegt und gründlich bewässert.",
            "acts": ("rasen",),
            "min_act": 1,
        },
        {
            "raw": "Beet mit Kompost eingearbeitet und Pflanzen gesetzt.",
            "acts": ("kompost", "pflanzen"),
            "min_act": 1,
        },
        {
            "raw": "Noppenbahn an der Hauswand verlegt und Drainage daneben.",
            "acts": ("drainage",),
            "min_act": 1,
        },
        {
            "raw": "Heute mit dem Radlader Schotter verteilt keine Stunden gesagt.",
            "acts": ("schotter",),
            "mats": ("schotter",),
            "mach_sug": ("Radlader",),
            "forbid_hours": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Morgens L-Steine gesetzt nachmittags Palisaden gesetzt "
                "Kunde kam vorbei war zufrieden Problem Untergrund nass "
                "Offen Hinterfüllung morgen."
            ),
            "acts": ("l-stein", "palisad"),
            "sugs": ("Beton",),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 2,
        },
        {
            "raw": (
                "Pflaster aufgenommen gestapelt Schotter und Splitt eingebaut "
                "Einkehrmaterial eingearbeitet Holzleisten von der Gartenhütte demontiert "
                "Ilex abgeschnitten keine Stunden Kettensäge."
            ),
            "acts": ("aufgenommen", "schotter", "holzleiste", "ilex"),
            "forbid_acts": ("Gartenhütte demontiert",),
            "forbid_hours": True,
            "min_act": 3,
        },
    ]
