"""Welle 54: GaLaBau-Schutznetz — 100 Basisszenarien (letzte Welle heute).

Baustellensprache, Whisper, Kunde/Problem/Offen. Rein additiv.
"""

from __future__ import annotations


def all_base_scenarios() -> list[dict]:
    return [
        {"raw": "Heute 28 Quadratmeter Betonsteinpflaster auf dem Hof verlegt.", "acts": ("pflaster",), "mats": ("pflaster",), "min_act": 1},
        {"raw": "Ökopflaster 16 Quadratmeter verlegt mit Drainfuge Einfahrt.", "acts": ("pflaster",), "min_act": 1},
        {"raw": "Rasengittersteine gesetzt auf dem Stellplatz 12 Quadratmeter.", "acts": ("rasengitter",), "min_act": 1},
        {"raw": "Verbundsteine im Reihenverband verlegt hinterm Haus.", "acts": ("pflaster",), "min_act": 1},
        {"raw": "Klinker auf dem Gartenweg verlegt 8 Quadratmeter.", "acts": ("klinker",), "min_act": 1},
        {"raw": "Heute 9 l-steine gesetzt als Stützmauer zum Nachbarn.", "acts": ("l-stein",), "mats": ("l-stein",), "sugs": ("Beton",), "forbid_acts": ("lfm",), "forbid_hours": True, "min_act": 1},
        {"raw": "18 laufende Meter Rasenkantensteine gesetzt entlang der Wiese.", "acts": ("rasenkantenstein", "lfm"), "sugs": ("Beton",), "forbid_acts": ("l-stein",), "min_act": 1},
        {"raw": "Spritzschutz-Kantensteine gesetzt an der Hauswand.", "acts": ("spritzschutz",), "mats": ("kantenstein",), "sugs": ("Beton",), "forbid_acts": ("Randsteine gesetzt",), "min_act": 1},
        {"raw": "Pflaster im Halbverband verlegt 22 Quadratmeter Terrasse.", "acts": ("pflaster",), "min_act": 1},
        {"raw": "Abgesackte Stelle aufgenommen Schotter nachgestopft Pflaster wieder verlegt.", "acts": ("aufgenommen", "schotter", "pflaster"), "min_act": 2},
        {"raw": "Mit Kantholz und Gummihammer Pflaster auf Höhe zurechtgeschlagen.", "acts": ("kantholz", "pflaster"), "min_act": 1},
        {"raw": "Einkehrmaterial eingekehrt nach dem Verlegen der Fläche.", "acts": ("einkehrmaterial",), "forbid_sugs": ("Fugensand",), "min_act": 1},
        {"raw": "Fugen ausgekratzt und neu mit Fugensand gefüllt.", "acts": ("fugen",), "mats": ("fugensand",), "min_act": 1},
        {"raw": "Drei Kubikmeter Schotter 0/45 eingebaut Hofeinfahrt.", "acts": ("schotter",), "mats": ("schotter",), "min_act": 1},
        {"raw": "Splittschicht 2/5 aufgetragen und höhengerecht abgezogen.", "acts": ("splitt",), "mats": ("splitt",), "min_act": 1},
        {"raw": "Kies 16/32 eingebaut zwei Kubikmeter als Drainagekies.", "acts": ("kies",), "mats": ("kies",), "min_act": 1},
        {"raw": "Planum hergestellt und mit der Rüttelplatte 2 Stunden verdichtet.", "acts": ("planum",), "mach": ("Rüttelplatte: 2",), "min_act": 1},
        {"raw": "Schotterrasen angelegt 30 Quadratmeter am Carport.", "acts": ("schotter",), "min_act": 1},
        {"raw": "Mutterboden 2 Kubikmeter aufgetragen und grob planiert.", "acts": ("mutterboden",), "mats": ("mutterboden",), "min_act": 1},
        {"raw": "Oberboden abgeschoben und auf den Haufen gelagert.", "acts": ("oberboden",), "min_act": 1},
        {"raw": "Hinterfüllung hinter den L-Steinen mit Schotter gemacht.", "acts": ("l-stein", "schotter"), "min_act": 1},
        {"raw": "Heute 0,4 m³ Beton verarbeitet an den Palisaden.", "acts": ("palisad",), "mats": ("beton",), "min_act": 1},
        {"raw": "Palisaden gesetzt 6 laufende Meter.", "acts": ("palisad",), "sugs": ("Beton",), "min_act": 1},
        {"raw": "Sitzmauer aus Naturstein gebaut am Hang.", "acts": ("sitzmauer", "naturstein"), "min_act": 1},
        {"raw": "Gartenstufen aus Blockstufen gesetzt zur Terrasse.", "acts": ("stufen",), "min_act": 1},
        {"raw": "Mähkante aus Cortenstahl gesetzt ums Beet.", "acts": ("mähkante", "maehkante"), "min_act": 1},
        {"raw": "Beeteinfassung mit Kantensteinen gesetzt 11 laufende Meter.", "acts": ("kantenstein",), "sugs": ("Beton",), "min_act": 1},
        {"raw": "Thujahecke gepflanzt 15 Stück als Sichtschutz.", "acts": ("pflanzen",), "min_act": 1},
        {"raw": "Hortensien gesetzt ins Beet vor der Terrasse.", "acts": ("pflanzen",), "min_act": 1},
        {"raw": "Rosenbeet angelegt und mit Rindenmulch eingedeckt.", "acts": ("mulch",), "min_act": 1},
        {"raw": "Buchs in Form geschnitten Formschnitt vor der Tür.", "acts": ("formschnitt",), "min_act": 1},
        {"raw": "Bambus zurückgeschnitten und die Fläche gemulcht.", "acts": ("mulch",), "min_act": 1},
        {"raw": "Moos aus dem Rasen entfernt und danach gekalkt.", "acts": ("rasen", "moos"), "min_act": 1},
        {"raw": "Rasen aerifiziert und mit Sand besandet heute.", "acts": ("rasen",), "min_act": 1},
        {"raw": "Rasen gemäht getrimmt und die Kanten gestochen.", "acts": ("gemäht", "getrimmt"), "min_act": 1},
        {"raw": "Wildwuchs und Brombeeren entlang des Zauns entfernt.", "acts": ("unkraut",), "min_act": 1},
        {"raw": "Efeu vom Zaun gerissen und entsorgt.", "acts": ("zaun", "entsorgt"), "min_act": 1},
        {"raw": "Grünschnitt mit dem Häcksler zerkleinert und abgefahren.", "acts": ("grünschnitt",), "forbid_hours": True, "min_act": 1},
        {"raw": "Totholzhaufen angelegt aus dem Schnittgut hinterm Schuppen.", "acts": ("totholz",), "min_act": 1},
        {"raw": "Baumstücke mit der Kettensäge zersägt keine Stunden.", "acts": ("entsorgt",), "forbid_hours": True, "min_act": 1},
        {"raw": "Wurzelbrut am Gehweg entfernt und die Stelle verdichtet.", "acts": ("wurzel",), "min_act": 1},
        {"raw": "Ringdrainage ums Haus verlegt 22 Meter Drainagerohr.", "acts": ("drainage",), "min_act": 1},
        {"raw": "Sickerschacht gesetzt und an die Rinne angeschlossen.", "acts": ("sickerschacht",), "min_act": 1},
        {"raw": "Zisterne eingebaut im Garten und Überlauf angeschlossen.", "acts": ("zisterne",), "min_act": 1},
        {"raw": "Versenkregner im Rasen eingebaut 6 Stück.", "acts": ("versenkregner",), "min_act": 1},
        {"raw": "PE-Rohr für die Bewässerung verlegt im Beet.", "acts": ("bewässer", "tropf"), "min_act": 1},
        {"raw": "Kiesmulde zur Versickerung angelegt vor der Garage.", "acts": ("kies",), "min_act": 1},
        {"raw": "Gully gesetzt in der Hofeinfahrt und angeschlossen.", "acts": ("gully", "hofablauf"), "min_act": 1},
        {"raw": "Teichfolie nachgedichtet und den Rand mit Kies belegt.", "acts": ("teich",), "min_act": 1},
        {"raw": "Quellstein gesetzt und den Bachlauf mit Steinen gelegt.", "acts": ("teich",), "min_act": 1},
        {"raw": "Schwimmteich Ufer mit Naturstein gesetzt.", "acts": ("naturstein", "teich"), "min_act": 1},
        {"raw": "Filtervlies unter dem Splittweg ausgelegt.", "acts": ("vlies",), "min_act": 1},
        {"raw": "Geogitter auf dem Hang verlegt vor den Gabionen.", "acts": ("geogitter",), "min_act": 1},
        {"raw": "Böschungsmatte ausgelegt und mit Splitt beschwert.", "acts": ("splitt",), "min_act": 1},
        {"raw": "Holzsichtschutzzaun 12 Meter gesetzt zur Straße.", "acts": ("zaun", "sichtschutz"), "min_act": 1},
        {"raw": "Zaunpfosten gesetzt und mit Beton vergossen 8 Stück.", "acts": ("zaun",), "mats": ("beton",), "min_act": 1},
        {"raw": "WPC-Zaunfelder montiert zwischen den Pfosten.", "acts": ("zaun", "wpc"), "min_act": 1},
        {"raw": "Gartenhaus aufgestellt auf der vorbereiteten Fläche.", "acts": ("gartenhaus",), "min_act": 1},
        {"raw": "Carport aufgestellt und die Fläche danach gepflastert.", "acts": ("carport", "pflaster"), "min_act": 1},
        {"raw": "Unterkonstruktion für die Holzterrasse gebaut.", "acts": ("terrasse",), "min_act": 1},
        {"raw": "Poolumrandung mit Keramikplatten verlegt 14 Quadratmeter.", "acts": ("keramik",), "min_act": 1},
        {"raw": "Stelzlager gesetzt und die Keramikplatte drauf.", "acts": ("stelzlager", "keramik"), "min_act": 1},
        {"raw": "Grillplatz gepflastert 9 Quadratmeter hinterm Haus.", "acts": ("pflaster",), "min_act": 1},
        {"raw": "Feuerstelle mit Schamottesteinen gesetzt im Garten.", "acts": ("feuerstelle",), "min_act": 1},
        {"raw": "Mülltonnenstellplatz gepflastert neben der Einfahrt.", "acts": ("pflaster",), "min_act": 1},
        {"raw": "Briefkastenstele gesetzt am Zaun vorne.", "acts": ("zaun",), "min_act": 1},
        {"raw": "Fahrradbügel gesetzt neben dem Fahrradständer.", "acts": ("fahrradständer", "fahrradstaender"), "min_act": 1},
        {"raw": "Spielrasen gemäht und die Kanten sauber getrimmt.", "acts": ("rasen", "gemäht"), "min_act": 1},
        {"raw": "Trampolinplatz mit Fallschutzsplitt aufgefüllt.", "acts": ("splitt",), "mats": ("splitt",), "min_act": 1},
        {"raw": "Heute 4 Stunden mit dem Radlader Schotter verteilt.", "acts": ("schotter",), "mats": ("schotter",), "mach": ("Radlader: 4",), "min_act": 1},
        {"raw": "2 Stunden Dumper Erde gefahren zur Hinterfüllung.", "acts": ("dumper",), "mach": ("Dumper: 2",), "min_act": 1},
        {"raw": "Mit Freischneider die Böschung gemäht keine Stunden.", "acts": ("gemäht",), "forbid_hours": True, "min_act": 1},
        {"raw": "Laub mit dem Laubbläser zusammengeblasen und entsorgt.", "acts": ("laub",), "forbid_hours": True, "min_act": 1},
        {"raw": "Rasenmäher eingesetzt Fläche gemäht keine Maschinenstunden.", "acts": ("gemäht",), "forbid_hours": True, "min_act": 1},
        {"raw": "Heute 5 l steine gesetzt Hang und 10 lfm Randsteine gesetzt.", "acts": ("l-stein", "lfm", "randstein"), "forbid_hours": True, "min_act": 2},
        {"raw": "Handstampfer Schotter verdichtet keine Stampferstunden.", "acts": ("schotter",), "forbid_hours": True, "min_act": 1},
        {"raw": "Holzleisten an der Gartenhütte nachgearbeitet alte demontiert.", "acts": ("holzleiste",), "forbid_acts": ("Gartenhütte demontiert",), "min_act": 1},
        {"raw": "Ilex-Stamm entsorgt Kettensäge ohne Stundenangabe.", "acts": ("ilex",), "forbid_hours": True, "min_act": 1},
        {"raw": "Bauschutt und alte Platten vom Weg entsorgt.", "acts": ("bauschutt",), "min_act": 1},
        {"raw": "Kompost aufs Beet gebracht und flach eingearbeitet.", "acts": ("kompost",), "min_act": 1},
        {"raw": "Unkrautvlies ausgelegt Splittweg 2/5 darauf.", "acts": ("vlies", "splitt"), "mats": ("splitt",), "min_act": 1},
        {"raw": "Hochbeet mit Mutterboden befüllt und Salat gepflanzt.", "acts": ("hochbeet", "pflanzen"), "min_act": 1},
        {"raw": "Gabionen mit Bruchstein gefüllt zweite Reihe.", "acts": ("gabionen",), "min_act": 1},
        {"raw": "Trockenmauer fugenlos gesetzt und hinten hinterfüllt.", "acts": ("trockenmauer",), "min_act": 1},
        {
            "raw": (
                "Heute 40 Quadratmeter Pflaster verlegt Kundin hat die Farbe bestätigt "
                "Problem Material knapp Offen letzte drei Reihen morgen."
            ),
            "acts": ("pflaster",),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Hecke geschnitten Bauherr vor Ort war zufrieden "
                "Offen Formschnitt andere Seite morgen."
            ),
            "acts": ("hecke",),
            "open_": True,
            "customer": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Pflasterarbeiten angefangen Problem Untergrund zu nass mussten abbrechen "
                "Offen weiter wenn es trocken ist Kunde informiert."
            ),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 0,
        },
        {
            "raw": (
                "L-Steine gesetzt Problem Lieferung Schotter kam spät "
                "Offen Hinterfüllung morgen Kunde gred war ok."
            ),
            "acts": ("l-stein",),
            "sugs": ("Beton",),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Drainage verlegt Problem Wasser stand im Graben "
                "Offen Restrohr morgen Bauleitung informiert."
            ),
            "acts": ("drainage",),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 1,
        },
        {
            "raw": "Es hat den ganzen Vormittag geregnet wir mussten die Gartenarbeiten abbrechen.",
            "problem": True,
            "min_act": 0,
        },
        {
            "raw": (
                "Rasen gemäht Unkraut gejätet mit dem Kunden abgestimmt früher Schluss "
                "Offen Hecke morgen."
            ),
            "acts": ("rasen", "unkraut"),
            "open_": True,
            "customer": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Zaun gesetzt Nachbar war da Grenze abgestimmt "
                "Kunde informiert Offen Tor morgen montieren."
            ),
            "acts": ("zaun",),
            "open_": True,
            "customer": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Heute Splitt aufgetragen Pflaster verlegt Problem Frost in der Nacht "
                "Offen Fugen kehren wenn es taut."
            ),
            "acts": ("splitt", "pflaster"),
            "problem": True,
            "open_": True,
            "min_act": 1,
        },
        {
            "raw": (
                "Morgens Palisaden gesetzt nachmittags Hochbeet gebaut "
                "Kunde kam vorbei war zufrieden Problem Erde fehlt "
                "Offen Befüllung nächste Woche."
            ),
            "acts": ("palisad", "hochbeet"),
            "sugs": ("Beton",),
            "problem": True,
            "open_": True,
            "customer": True,
            "min_act": 2,
        },
        {
            "raw": (
                "Pflaster aufgenommen gestapelt Schotter und Splitt eingebaut "
                "Einkehrmaterial eingearbeitet Kunde kurz da Offen Reststeine morgen."
            ),
            "acts": ("aufgenommen", "schotter", "einkehrmaterial"),
            "open_": True,
            "customer": True,
            "forbid_hours": True,
            "min_act": 2,
        },
        {"raw": "Heute mit dem Bagger Aushub für die Sitzmauer gemacht.", "acts": ("aushub",), "mach_sug": ("Bagger",), "min_act": 1},
        {"raw": "1 Stunde Rüttelplatte auf dem Planum der Einfahrt.", "acts": (), "mach": ("Rüttelplatte: 1",), "min_act": 0},
        {"raw": "Drainagesplitt eingebaut und Vlies verteilt am Haus.", "acts": ("splitt", "vlies"), "min_act": 1},
        {"raw": "Podest für die Regentonne gesetzt und angeschlossen.", "acts": ("podest", "regentonne"), "min_act": 1},
        {"raw": "Heute 3 lstein gesetzt und Hecke geschnitten.", "acts": ("l-stein", "hecke"), "sugs": ("Beton",), "forbid_acts": ("lfm",), "min_act": 2},
    ]
