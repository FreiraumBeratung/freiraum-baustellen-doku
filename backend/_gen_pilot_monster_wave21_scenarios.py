"""Einmal-Generator für pilot_monster_wave21_scenarios.py — nicht in Smoke ausführen."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

OUT = Path(__file__).parent / "pilot_monster_wave21_scenarios.py"


def s(
    raw: str,
    acts: tuple[str, ...],
    *,
    mats: tuple[str, ...] = (),
    forbid_acts: tuple[str, ...] = (),
    problem: bool = False,
    open_: bool = False,
    customer: bool = False,
    min_act: int | None = None,
    cust_not: tuple[str, ...] = (),
    sum_forbid: tuple[str, ...] = (),
    mat_echo: bool = False,
) -> dict:
    return dict(
        raw=raw,
        acts=acts,
        mats=mats,
        forbid_acts=forbid_acts,
        problem=problem,
        open_=open_,
        customer=customer,
        min_act=min_act,
        cust_not=cust_not,
        sum_forbid=sum_forbid,
        mat_echo=mat_echo,
    )


def _galabau() -> list[dict]:
    items: list[dict] = [
        s("50 Quadratmeter Pflaster verlegt zwei Kubikmeter Schotter eingebaut Hecke geschnitten Bauherr kurz da Problem Lieferung spät Offen letzte Reihe morgen Mit der Kundin gesprochen sie war sehr zufrieden.", ("50 m² Pflaster verlegt", "Schotter eingebaut", "Hecke geschnitten"), mats=("Pflastersteine", "Schotter"), problem=True, open_=True, customer=True, cust_not=("50", "pflaster", "schotter", "m²"), forbid_acts=("Pflastersteine verarbeitet",), mat_echo=True),
        s("Heute haben wir 50 qm² pflaster gelegt. Anschließend haben wir uns mit der Kundin unterhalten und die Kundin war sehr zufrieden.", ("50 m² Pflaster verlegt",), mats=("Pflastersteine",), customer=True, cust_not=("50", "pflaster", "qm")),
        s("heute 30 quadrat pflaster gelegt und schotter reingemacht und kundin zufrieden problem regen offen rest montag", ("30 m² Pflaster verlegt", "Schotter eingebaut"), mats=("Pflastersteine", "Schotter"), problem=True, open_=True, customer=True, cust_not=("30", "schotter")),
        s("Kundengespräch gehabt Pflastermuster gewählt Problem Drainage Offen Rest nächste Woche.", (), problem=True, open_=True, customer=True, min_act=0),
        s("Wir haben den Rasen gemäht vertikutiert und anschließend gedüngt sowie die Fläche bewässert.", ("Rasen gemäht", "Rasen vertikutiert", "Rasen gedüngt", "Fläche bewässert")),
        s("60 Quadratmeter Pflaster verlegt 25 laufende Meter Rasenkantensteine gesetzt Hecke geschnitten Rindenmulch eingedeckt.", ("60 m² Pflaster verlegt", "Rasenkantensteine gesetzt", "Hecke geschnitten", "Rindenmulch eingedeckt"), mats=("Pflastersteine", "Rasenkantensteine")),
        s("3 Stunden mit dem Bagger Erdaushub gemacht danach 40 Quadratmeter Pflaster verlegt zwei Kubikmeter Schotter eingebaut.", ("40 m² Pflaster verlegt", "Schotter eingebaut"), mats=("Pflastersteine", "Schotter")),
        s("30 Quadratmeter Keramikterrasse verlegt Geotextil verlegt Splitt 2/5 mm eingebaut.", ("30 m² Keramikterrasse verlegt", "Geotextil verlegt", "Splitt 2/5 mm eingebaut"), mats=("Keramikplatten", "Geotextil", "Splitt")),
        s("2,5 Stunden Radlader Schotter verteilt Untergrund verdichtet 35 Quadratmeter Pflaster verlegt.", ("Schotter eingebaut", "Untergrund verdichtet", "35 m² Pflaster verlegt"), mats=("Pflastersteine", "Schotter")),
        s("Winterdienst durchgeführt Schnee geräumt Streugut gestreut 12 Quadratmeter WPC Terrasse gebaut.", ("Winterdienst durchgeführt", "12 m² Holz-/WPC-Terrasse gebaut"), mats=("Streugut",)),
        s("30 Quadratmeter Pflaster verlegt 10 Quadratmeter Gartenmauer gebaut 15 laufende Meter Palisaden gesetzt Hecke geschnitten.", ("30 m² Pflaster verlegt", "Gartenmauer gebaut", "Palisaden gesetzt", "Hecke geschnitten")),
        s("heute ich hab gemacht 15 meter Palisaden gesetzt und 30 quadrat Rollrasen verlegt.", ("Palisaden gesetzt", "30 m² Rasen verlegt")),
        s("Mit dem Bagger Fläche vorbereitet 25 Quadratmeter Pflaster verlegt Schotter eingebaut.", ("25 m² Pflaster verlegt", "Schotter eingebaut"), mats=("Pflastersteine", "Schotter")),
        s("Radlader Mulch verteilt 20 Quadratmeter Pflaster verlegt Hecke geschnitten.", ("20 m² Pflaster verlegt", "Hecke geschnitten")),
        s("Vormittags Rasen getrimmt Unkraut gezupft Hecke zurückgeschnitten.", ("Rasen getrimmt", "Unkraut entfernt", "Hecke geschnitten")),
        s("30 Quadratmeter Pflaster gelegt Schotter reingemacht Laub gefegt.", ("30 m² Pflaster verlegt", "Schotter eingebaut", "Laub entfernt"), mats=("Pflastersteine", "Schotter")),
        s("Heute den ganzen Garten freigeschnitten Unkraut weg gemacht.", ("Rasen getrimmt", "Unkraut entfernt")),
        s("fünfundzwanzig laufende Meter Rasenkantensteine gesetzt.", ("Rasenkantensteine gesetzt",), mats=("Rasenkantensteine",), min_act=1),
        s("Drei Pflanzkübel mit Erde befüllt Beet angelegt Pflanzen gesetzt.", ("Pflanzkübel", "Pflanzen gesetzt"), min_act=1),
        s("30 Quadratmeter Rollrasen verlegt Untergrund verdichtet.", ("30 m² Rasen verlegt", "Untergrund verdichtet")),
        s("heute ich machen 50 quadrat Pflaster Hecke schneiden Unkraut weg machen.", ("50 m² Pflaster verlegt", "Hecke geschnitten", "Unkraut entfernt")),
        s("heute auf baustell ich hab gearbeitet 30 quadrat Pflaster.", ("30 m² Pflaster verlegt",), min_act=1),
        s("55 Quadratmeter Pflaster verlegt 20 laufende Meter Rasenkantensteine gesetzt Hecke geschnitten Bauherr zufrieden Problem Regen Offen letzte Fläche Montag.", ("55 m² Pflaster verlegt", "Rasenkantensteine gesetzt", "Hecke geschnitten"), mats=("Pflastersteine",), problem=True, open_=True, customer=True),
        s("40 Quadratmeter Pflaster verlegt zwei Kubikmeter Schotter eingebaut Hecke geschnitten Mulch eingedeckt.", ("40 m² Pflaster verlegt", "Schotter eingebaut", "Hecke geschnitten"), mats=("Pflastersteine", "Schotter")),
        s("50 qm Pflaster gelegt zwei Kubik Schotter rein zwei fünfer Split eingebaut.", ("50 m² Pflaster verlegt", "2 m³ Schotter eingebaut", "Splitt 2/5 mm"), mats=("Pflastersteine", "Schotter", "Splitt")),
        s("Beet angelegt Pflanzen gesetzt Fläche bewässert.", ("Pflanzen gesetzt", "Fläche bewässert")),
        s("heute ich machen Rasen mähen 100 quadrat.", ("100 m² Rasen gemäht",), min_act=1),
        s("Laub entfernt Gehweg kehren fertig.", ("Laub entfernt",), min_act=1),
        s("15 Quadratmeter Naturstein verlegt Fugen verfugt.", ("Naturstein verlegt", "Fliesen verfugt")),
        s("45 qm Pflaster verlegt Pflastersteine verbaut Schotter eingebaut Kundin zufrieden.", ("45 m² Pflaster verlegt", "Schotter eingebaut"), mats=("Pflastersteine", "Schotter"), customer=True, forbid_acts=("Pflastersteine verarbeitet",), mat_echo=True, cust_not=("pflaster", "qm")),
        s("Terrasse neu 35 Quadratmeter Keramikplatten verlegt Splitt eingebaut Bauherrin sehr happy Problem falsche Farbe Offen Umtausch nächste Woche.", ("35 m² Keramikterrasse verlegt",), mats=("Keramikplatten",), problem=True, open_=True, customer=True),
        s("Mit dem Kunden gesprochen er möchte weiter mit uns arbeiten.", (), customer=True, min_act=0),
        s("Heute 40 Quadratmeter Pflaster verlegt Feierabend.", ("40 m² Pflaster verlegt",), mats=("Pflastersteine",), min_act=1),
    ]
    qtys = [18, 22, 28, 33, 38, 42, 48, 52, 58, 65, 70, 75, 80, 85, 90, 95, 105]
    tails = [
        ("", False, False, False, ()),
        (" Problem Material knapp Offen Rest morgen.", True, True, False, ()),
        (" Bauherr informiert alles abgestimmt.", False, False, True, ("bauherr",)),
        (" Kundin mega zufrieden.", False, False, True, ("pflaster", "qm")),
        (" Auftraggeber kurz gesprochen Problem Wetter Offen nächste Woche.", True, True, True, ("pflaster", "meter")),
    ]
    for i, qty in enumerate(qtys):
        tail, prob, opn, cust, cnot = tails[i % len(tails)]
        items.append(s(
            f"{qty} Quadratmeter Pflaster verlegt{tail}",
            (f"{qty} m² Pflaster verlegt",),
            mats=("Pflastersteine",),
            problem=prob,
            open_=opn,
            customer=cust,
            cust_not=cnot,
            min_act=1,
        ))
    assert len(items) == 50, len(items)
    return items


def _trockenbau() -> list[dict]:
    items: list[dict] = [
        s("Gipskartonplatten montiert Decke abgehängt Problem Lieferung Offen letzte Wand mit der Bauleitung Rücksprache gehalten.", ("Gipskartonplatten montiert", "Decke abgehängt"), mats=("Gipskartonplatten",), problem=True, open_=True, customer=True, cust_not=("gipskarton", "decke")),
        s("Trockenbauwand geschlossen Ständerwerk montiert.", ("Trockenbauwand geschlossen", "Ständerwerk montiert")),
        s("Brandschutzwand hergestellt Akustikdecke eingebaut.", ("Brandschutzwand hergestellt", "Akustikdecke eingebaut")),
        s("heute ich hab gipskarton gemacht decke abhaengen problem schrauben offen morgen", ("Gipskartonplatten montiert",), problem=True, open_=True, min_act=1),
        s("CW-Profil und UW-Profil montiert Dämmmatte eingesetzt zwei Lagen Gipskarton verschraubt Fugenspachtel gezogen Bauleitung abgesprochen Problem Lieferverzug Offen Revisionsöffnung Freitag.", ("Gipskartonplatten montiert",), problem=True, open_=True, customer=True, min_act=1),
        s("Decke abgehängt CD-Profile montiert Abhänger gesetzt.", ("Decke abgehängt",), min_act=1),
        s("Ständerwerk montiert Dämmung eingebaut Gipskartonplatten montiert.", ("Ständerwerk montiert", "Dämmung eingebaut", "Gipskartonplatten montiert"), mats=("Gipskartonplatten",)),
        s("Fugen verspachtelt und geschliffen.", ("Fugen verspachtelt",), min_act=1),
        s("Revisionsklappe eingebaut.", ("Revisionsklappe eingebaut",), min_act=1),
        s("Kundengespräch gehabt Wandaufbau besprochen Problem Schrauben Offen Rest nächste Woche.", (), problem=True, open_=True, customer=True, min_act=0),
        s("rigips dran gemacht wand zugemacht.", ("Gipskartonplatten montiert", "Trockenbauwand geschlossen")),
        s("heute auf baustell ich hab rigips montiert 40 quadratmeter.", ("Gipskartonplatten montiert",), min_act=1),
        s("Zwei Trockenbauwände geschlossen Decke abgehängt Kunde war da und happy Problem Folie knapp Offen Rest morgen.", ("Trockenbauwand geschlossen", "Decke abgehängt"), problem=True, open_=True, customer=True),
        s("Akustikdecke eingebaut Mineralwolle eingebaut.", ("Akustikdecke eingebaut",), min_act=1),
        s("Brandschutzwand hergestellt zweifach beplankt.", ("Brandschutzwand hergestellt",), min_act=1),
        s("Gipskarton im Bad montiert Feuchtraumplatten gesetzt.", ("Gipskartonplatten montiert",), min_act=1),
        s("Trennwand gestellt Dämmung reingepackt Platten geschraubt.", ("Trockenbauwand geschlossen", "Dämmung eingebaut"), min_act=1),
        s("Mit dem Kunden gesprochen er war zufrieden.", (), customer=True, min_act=0),
        s("Spachtelarbeiten durchgeführt.", ("Spachtelarbeiten durchgeführt",), min_act=1),
        s("Staenderwerk montiert CW Profile gesetzt.", ("Ständerwerk montiert",), min_act=1),
        s("Decke abhaengen und GK Platten montiert Problem Lieferung Offen letzte Ecke.", ("Decke abgehängt", "Gipskartonplatten montiert"), problem=True, open_=True, min_act=1),
        s("Bauleitung informiert Wand fertig.", ("Trockenbauwand geschlossen",), customer=True, min_act=1),
        s("Doppelständerwand gebaut Schallschutz eingebaut.", ("Trockenbauwand geschlossen",), min_act=1),
        s("Installationswand vorbereitet Unterkonstruktion montiert.", ("Ständerwerk montiert",), min_act=1),
        s("Fugenspachtel aufgetragen geschliffen grundiert.", ("Fugen verspachtelt",), min_act=1),
        s("Gipskartonplatten montiert Gipskartonplatten verarbeitet.", ("Gipskartonplatten montiert",), mats=("Gipskartonplatten",), forbid_acts=("Gipskartonplatten verarbeitet",), mat_echo=True, min_act=1),
        s("Trockenbau komplett Wände Decke Spachtel Kundin zufrieden Problem Staub Offen Rest Freitag.", ("Gipskartonplatten montiert",), problem=True, open_=True, customer=True, min_act=1),
        s("Nur Feierabend.", (), min_act=0),
        s("Eine Wand zugemacht fertig.", ("Trockenbauwand geschlossen",), min_act=1),
        s("Abhangdecke montiert Lichtkuppel vorbereitet.", ("Decke abgehängt",), min_act=1),
        s("Brandschutz F90 Wand hergestellt.", ("Brandschutzwand hergestellt",), min_act=1),
        s("Dachausbau Rigips komplett montiert.", ("Gipskartonplatten montiert",), min_act=1),
    ]
    extras = [
        (12, " Problem Profile fehlen Offen morgen nachliefern.", True, True, False),
        (18, " Bauherr kurz informiert.", False, False, True),
        (24, " Kundin sehr zufrieden.", False, False, True),
        (30, " Auftraggeber da Problem Plan Offen Schacht.", True, True, True),
        (36, "", False, False, False),
        (44, " Problem Lieferung Offen Rest.", True, True, False),
        (52, " mit dem Kunden gesprochen zufrieden.", False, False, True),
        (60, " Bauleitung abgesprochen.", False, False, True),
        (68, " Problem Schrauben Offen Wand.", True, True, False),
        (76, " Kunde vor Ort.", False, False, True),
        (84, "", False, False, False),
        (92, " Problem Staub Offen Reinigung.", True, True, False),
        (100, " Bauherr zufrieden.", False, False, True),
        (108, " Kundengespräch gehabt.", False, False, True),
        (116, " Problem Dämmung Offen Rest.", True, True, False),
        (124, " Rücksprache mit Kunde.", False, False, True),
        (132, "", False, False, False),
        (140, " Problem Spachtel Offen Schliff.", True, True, False),
    ]
    for qty, tail, prob, opn, cust in extras:
        items.append(s(
            f"{qty} Quadratmeter Gipskartonplatten montiert{tail}",
            (f"{qty} m² Gipskartonplatten montiert",) if qty <= 100 else ("Gipskartonplatten montiert",),
            mats=("Gipskartonplatten",),
            problem=prob,
            open_=opn,
            customer=cust,
            min_act=1,
        ))
    assert len(items) == 50, len(items)
    return items


def _fliesen() -> list[dict]:
    items: list[dict] = [
        s("Im Bad 25 Quadratmeter Fliesen verlegt Silikonfugen gemacht Problem Wasserdruck zu niedrig Offen Armatur morgen mit dem Kunden gesprochen er war zufrieden.", ("25 m² Fliesen verlegt", "Silikonfugen"), mats=("Fliesen",), problem=True, open_=True, customer=True, cust_not=("25", "fliesen", "bad")),
        s("40 Quadratmeter Fliesen verlegt Fliesenkleber verwendet.", ("40 m² Fliesen verlegt", "Fliesenkleber"), mats=("Fliesen", "Fliesenkleber")),
        s("35 qm Fliesen gelegt Fliesen verarbeitet.", ("35 m² Fliesen verlegt",), mats=("Fliesen",), forbid_acts=("Fliesen verarbeitet",), mat_echo=True),
        s("WC montiert Waschbecken montiert.", ("WC montiert", "Waschbecken montiert"), min_act=1),
        s("Im Bad erst Wandfliesen drauf geklebt Bodenfliesen verlegt verfugt Abdichtung Duschbereich Nivelliermasse gezogen Kunde meckert wegen Farbe Problem Wand schief Offen Rest Silikon Donnerstag.", ("Fliesen verlegt",), problem=True, open_=True, customer=True, min_act=1),
        s("Wand grundiert Abdichtung hergestellt 40 Quadratmeter Fliesen verlegt verfugt Silikonfugen Kundin hat Farbe bestätigt Problem Untergrund uneben Offen Restfugen morgen.", ("40 m² Fliesen verlegt",), mats=("Fliesen",), problem=True, open_=True, customer=True, min_act=1),
        s("Großformatfliesen verlegt Nivelliersystem verwendet.", ("Großformatfliesen verlegt",), min_act=1),
        s("Bodenablauf eingebaut Fliesen im Bad verlegt.", ("Bodenablauf eingebaut", "Fliesen verlegt"), min_act=1),
        s("Naturstein verlegt und verfugt.", ("Naturstein verlegt",), min_act=1),
        s("Kundengespräch gehabt Fliesenmuster gewählt Problem Lieferung Offen Rest nächste Woche.", (), problem=True, open_=True, customer=True, min_act=0),
        s("fliesen gelegt kleber gezogen verfugt fertig.", ("Fliesen verlegt", "Fliesenkleber"), min_act=1),
        s("heute ich hab 22 quadrat fliesen im bad gemacht.", ("Fliesen verlegt",), min_act=1),
        s("Dusche fliesen Wand und Boden Abdichtung Silikon Kundin zufrieden Problem Fuge Offen Rest morgen.", ("Fliesen verlegt",), problem=True, open_=True, customer=True, min_act=1),
        s("Mosaikfliesen gesetzt Wandfliesen verlegt.", ("Fliesen verlegt",), min_act=1),
        s("Nivelliermasse aufgetragen Fliesen verlegt.", ("Nivelliermasse aufgetragen", "Fliesen verlegt")),
        s("Silikonfugen hergestellt im Bad.", ("Silikonfugen",), min_act=1),
        s("Mit dem Kunden gesprochen alles abgestimmt.", (), customer=True, min_act=0),
        s("15 qm fliesen nur boden fertig.", ("Fliesen verlegt",), min_act=1),
        s("Bad komplett fertig fliesen verfugt silikon.", ("Fliesen verlegt", "Fliesen verfugt"), min_act=1),
        s("Bauherr informiert Fliesenfarbe passt.", ("Fliesen verlegt",), customer=True, min_act=1),
        s("Abdichtung im Bad hergestellt.", ("Abdichtung hergestellt",), min_act=1),
        s("Fliesen im Flur und Bad verlegt.", ("Fliesen verlegt",), min_act=1),
        s("Problem Kleber härtet nicht Offen Wand neu machen Kunde informiert.", (), problem=True, open_=True, customer=True, min_act=0),
        s("sockel fliesen gesetzt.", ("Fliesen verlegt",), min_act=1),
        s("Duschwanne eingebaut fliesen drum herum.", ("Dusche montiert", "Fliesen verlegt"), min_act=1),
        s("40 qm Fliesen verlegt Fliesenkleber aufgetragen Fliesen verarbeitet.", ("40 m² Fliesen verlegt",), mats=("Fliesen", "Fliesenkleber"), forbid_acts=("Fliesen verarbeitet",), mat_echo=True),
        s("Kunde war da und happy Problem Farbe Offen Muster.", (), problem=True, open_=True, customer=True, min_act=0),
        s("Feierabend.", (), min_act=0),
        s("Nur verfugt heute.", ("Fliesen verfugt",), min_act=1),
        s("Spiegelfliesen montiert.", ("Fliesen verlegt",), min_act=1),
        s("Balkonfliesen verlegt Gefälle eingebaut.", ("Fliesen verlegt",), min_act=1),
        s("Terrassenplatten verlegt.", ("Fliesen verlegt",), min_act=1),
    ]
    for qty in [12, 16, 20, 24, 28, 32, 36, 44, 48, 52, 56, 64, 72, 80, 88, 96, 104, 112]:
        prob = qty % 3 == 0
        opn = qty % 4 == 0
        cust = qty % 5 == 0
        tail = ""
        if prob:
            tail += " Problem Fuge."
        if opn:
            tail += " Offen Rest."
        if cust:
            tail += " Kundin zufrieden."
        items.append(s(
            f"{qty} Quadratmeter Fliesen verlegt{tail}",
            (f"{qty} m² Fliesen verlegt",),
            mats=("Fliesen",),
            problem=prob,
            open_=opn,
            customer=cust,
            cust_not=("fliesen", "qm") if cust else (),
            min_act=1,
        ))
    assert len(items) == 50, len(items)
    return items


def _shk() -> list[dict]:
    items: list[dict] = [
        s("40 laufende Meter KG-Rohre verlegt HT-Manschette montiert Problem Anschluss undicht Offen Druckprüfung morgen Kunde informiert war einverstanden.", ("KG-Rohre verlegt", "HT-Manschette montiert"), problem=True, open_=True, customer=True, cust_not=("kg", "rohr", "manschette")),
        s("Heizkörper montiert Thermostatventile eingebaut Problem Umlauf Offen hydraulischer Abgleich mit dem Kunden gesprochen zufrieden.", ("Heizkörper montiert",), problem=True, open_=True, customer=True, cust_not=("heizkörper",)),
        s("Dusche montiert Armaturen montiert Kundin sehr zufrieden.", ("Dusche montiert", "Armaturen montiert"), customer=True, cust_not=("dusche", "armatur")),
        s("Druckprüfung durchgeführt.", ("Druckprüfung durchgeführt",), min_act=1),
        s("Morgens 20 laufende Meter KG-Rohre DN 160 verlegt HT-Rohre DN 50 verlegt drei Heizkörper montiert WC gesetzt Waschbecken montiert Druckprüfung durchgeführt Bauleitung kurz da Problem KG-Bogen fehlte Offen Bogen morgen nach dem Kundengespräch Feierabend.", ("KG-Rohre", "Heizkörper montiert", "WC montiert", "Waschbecken montiert", "Druckprüfung durchgeführt"), mats=("KG-Rohre",), problem=True, open_=True, customer=True),
        s("Wasserleitungen verlegt Fußbodenheizung verlegt hydraulischen Abgleich durchgeführt.", ("Wasserleitungen verlegt", "Fußbodenheizung verlegt", "Hydraulischer Abgleich durchgeführt")),
        s("WC montiert Waschbecken montiert Dusche montiert.", ("WC montiert", "Waschbecken montiert", "Dusche montiert"), min_act=1),
        s("20 laufende Meter KG-Rohre verlegt vier Heizkörper montiert WC gesetzt Druckprüfung durchgeführt Bauherr zufrieden Problem Lieferung spät Offen Rest Sanitär nächste Woche.", ("KG-Rohre verlegt", "Heizkörper montiert", "WC montiert", "Druckprüfung durchgeführt"), problem=True, open_=True, customer=True),
        s("Heizungsanschlüsse montiert Thermostatventile eingebaut.", ("Heizungsanschlüsse montiert", "Thermostatventile eingebaut")),
        s("Kundengespräch gehabt Heizungsplan besprochen Problem Material fehlt Offen Rest nächste Woche.", (), problem=True, open_=True, customer=True, min_act=0),
        s("rohre gelegt heizung angeschlossen fertig.", ("Rohrleitungen installiert",), min_act=1),
        s("heute ich hab kg rohre 15 meter verlegt.", ("KG-Rohre verlegt",), min_act=1),
        s("HT-Rohre verlegt HT-Manschette montiert Problem Dichtung Offen Prüfung morgen.", ("HT-Rohre verlegt", "HT-Manschette montiert"), problem=True, open_=True, min_act=1),
        s("Wärmepumpe installiert Heizungsanschlüsse montiert.", ("Wärmepumpe installiert", "Heizungsanschlüsse montiert"), min_act=1),
        s("Gastherme eingebaut Abgasanlage montiert.", ("Gastherme installiert",), min_act=1),
        s("Mit dem Kunden gesprochen er war einverstanden.", (), customer=True, min_act=0),
        s("Bodenablauf eingebaut HT-Rohr angeschlossen.", ("Bodenablauf eingebaut",), min_act=1),
        s("Rücklaufverschraubung montiert Heizkörper eingebaut.", ("Heizkörper montiert",), min_act=1),
        s("Problem undichtes Rohr Druckprüfung verschoben Kundengespräch gehabt Offen morgen nacharbeiten.", (), problem=True, open_=True, customer=True, min_act=0),
        s("Armaturen montiert Waschbecken angeschlossen.", ("Armaturen montiert", "Waschbecken montiert")),
        s("Abwasser HT-Rohre 12 laufende Meter verlegt Wasserleitungen angeschlossen Rücksprache mit Kunde Problem Manschette undicht Offen morgen tauschen.", ("HT-Rohre verlegt",), problem=True, open_=True, customer=True, min_act=1),
        s("Hydraulischer Abgleich durchgeführt.", ("Hydraulischer Abgleich durchgeführt",), min_act=1),
        s("WC und Waschbecken komplett montiert.", ("WC montiert", "Waschbecken montiert")),
        s("Heizkessel angeschlossen Vorlauf Rücklauf montiert.", ("Heizungsanschlüsse montiert",), min_act=1),
        s("Kunde informiert alles ok.", (), customer=True, min_act=0),
        s("Feierabend.", (), min_act=0),
        s("Nur Druckprüfung heute.", ("Druckprüfung durchgeführt",), min_act=1),
        s("Dusche komplett montiert Abdichtung geprüft.", ("Dusche montiert",), min_act=1),
        s("Fußbodenheizung verlegt Verteiler angeschlossen.", ("Fußbodenheizung verlegt",), min_act=1),
        s("Kanalanschluss hergestellt KG-Rohre verlegt.", ("KG-Rohre verlegt",), min_act=1),
        s("Sanitär komplett Bad montiert Kundin happy Problem Armatur Offen morgen.", ("WC montiert", "Waschbecken montiert"), problem=True, open_=True, customer=True, min_act=1),
        s("Rohrleitungen verlegt Fittings verbaut.", ("Rohrleitungen installiert",), min_act=1),
    ]
    for lfm in [8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76]:
        prob = lfm % 6 == 0
        opn = lfm % 8 == 0
        cust = lfm % 10 == 0
        tail = ""
        if prob:
            tail += " Problem Bogen fehlt."
        if opn:
            tail += " Offen morgen."
        if cust:
            tail += " Bauherr zufrieden."
        items.append(s(
            f"{lfm} laufende Meter KG-Rohre verlegt{tail}",
            (f"{lfm} lfm KG-Rohre verlegt",) if lfm <= 50 else ("KG-Rohre verlegt",),
            mats=("KG-Rohre",),
            problem=prob,
            open_=opn,
            customer=cust,
            min_act=1,
        ))
    assert len(items) == 50, len(items)
    return items


def _hochbau() -> list[dict]:
    items: list[dict] = [
        s("Fundament betoniert Schalung erstellt Problem Wetter Offen Bewehrung Montag Bauleitung informiert.", ("Fundament erstellt", "Schalung erstellt"), problem=True, open_=True, customer=True, cust_not=("fundament", "beton", "schalung")),
        s("Mauerwerk erstellt Bewehrung eingebaut.", ("Mauerwerk erstellt", "Bewehrung eingebaut")),
        s("Filigrandecke montiert Fußbodenheizung verlegt.", ("Filigrandecke montiert", "Fußbodenheizung verlegt")),
        s("heute beton gegossen problem regen offen rest morgen kunde gred war ok", ("Beton eingebracht",), problem=True, open_=True, customer=True, min_act=1),
        s("Fundamentplatte geschalt 15er Poroton hochgemauert Bewehrungsstahl gebunden 8 Kubikmeter Beton gegossen Schalung abgebaut Bauherr zufrieden Problem Frost Offen Nachbehandlung.", ("Schalung erstellt", "Mauerwerk erstellt", "Bewehrung eingebaut", "Beton eingebracht"), mats=("Beton",), problem=True, open_=True, customer=True),
        s("Erdarbeiten gemacht Schalung gestellt Betondecke gegossen Fundament erstellt.", ("Erdarbeiten durchgeführt", "Schalung erstellt", "Beton eingebracht", "Fundament erstellt")),
        s("11,5er Poroton gemauert.", ("Mauerwerk erstellt",), min_act=1),
        s("5 Kubik Beton gegossen fertig.", ("Beton eingebracht",), min_act=1),
        s("Schalung erstellt Bewehrung eingebaut Beton eingebracht.", ("Schalung erstellt", "Bewehrung eingebaut", "Beton eingebracht"), mats=("Beton",)),
        s("Kundengespräch gehabt Bauplan besprochen Problem Material Offen Rest Woche.", (), problem=True, open_=True, customer=True, min_act=0),
        s("mauer gebaut beton gemacht.", ("Mauerwerk erstellt", "Beton eingebracht"), min_act=1),
        s("heute ich hab 20 quadrat mauerwerk gemacht.", ("Mauerwerk erstellt",), min_act=1),
        s("Decke betoniert Schalung gestellt Problem Regen Offen Abbinden.", ("Beton eingebracht", "Schalung erstellt"), problem=True, open_=True, min_act=1),
        s("Stürze gesetzt Fensteröffnungen gemauert.", ("Mauerwerk erstellt",), min_act=1),
        s("Bewehrung gebunden für Decke.", ("Bewehrung eingebaut",), min_act=1),
        s("Mit dem Kunden gesprochen zufrieden.", (), customer=True, min_act=0),
        s("Fundament erstellt Erdarbeiten durchgeführt.", ("Fundament erstellt", "Erdarbeiten durchgeführt")),
        s("Beton eingebracht Beton verarbeitet.", ("Beton eingebracht",), mats=("Beton",), forbid_acts=("Beton verarbeitet",), mat_echo=True),
        s("Auftraggeber kurz gesprochen.", (), customer=True, min_act=0),
        s("Feierabend.", (), min_act=0),
        s("Nur Schalung heute.", ("Schalung erstellt",), min_act=1),
        s("Ringanker betoniert.", ("Beton eingebracht",), min_act=1),
        s("Mauerwerk 17,5er KS hochgezogen.", ("Mauerwerk erstellt",), min_act=1),
        s("Bodenplatte geschalt bewehrt betoniert Problem Lieferung Offen Rest.", ("Schalung erstellt", "Bewehrung eingebaut", "Beton eingebracht"), problem=True, open_=True, min_act=1),
        s("Bauherr zufrieden Mauerwerk fertig.", ("Mauerwerk erstellt",), customer=True, min_act=1),
        s("Filigrandecke montiert.", ("Filigrandecke montiert",), min_act=1),
        s("Treppenhaus mauern Stürze setzen.", ("Mauerwerk erstellt",), min_act=1),
        s("Bewehrung Decke komplett.", ("Bewehrung eingebaut",), min_act=1),
        s("8 Kubik Beton gegossen Schalung steht Problem Hitze Offen Nachbehandlung Plane.", ("Beton eingebracht",), mats=("Beton",), problem=True, open_=True, min_act=1),
        s("Rohbau EG fertig Kundin informiert.", ("Mauerwerk erstellt",), customer=True, min_act=1),
        s("Erdung Fundamenterder gesetzt.", ("Fundament erstellt",), min_act=1),
        s("Balkonplatte geschalt betoniert.", ("Schalung erstellt", "Beton eingebracht"), min_act=1),
    ]
    for m3 in [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]:
        prob = m3 % 3 == 0
        opn = m3 % 4 == 0
        cust = m3 % 5 == 0
        tail = ""
        if prob:
            tail += " Problem Wetter."
        if opn:
            tail += " Offen Rest."
        if cust:
            tail += " Bauleitung informiert."
        items.append(s(
            f"{m3} Kubikmeter Beton eingebracht{tail}",
            (f"{m3} m³ Beton eingebracht",) if m3 <= 15 else ("Beton eingebracht",),
            mats=("Beton",),
            problem=prob,
            open_=opn,
            customer=cust,
            min_act=1,
        ))
    assert len(items) == 50, len(items)
    return items


def _tiefbau() -> list[dict]:
    items: list[dict] = [
        s("Graben ausgehoben Kanalrohre verlegt Problem Leitung Offen Verfüllung morgen Auftraggeber kurz gesprochen.", ("Graben ausgehoben",), problem=True, open_=True, customer=True, cust_not=("graben", "kanal")),
        s("Asphalt eingebaut Untergrund verdichtet Problem Maschine Offen letzte Bahn.", ("Asphalt eingebaut", "Untergrund verdichtet"), problem=True, open_=True, min_act=1),
        s("Verbau gesetzt Spundwand eingebaut.", ("Verbau gesetzt",), min_act=1),
        s("Hausanschluss hergestellt Problem Wasserdruck Offen Anmeldung Kunde zufrieden.", ("Hausanschluss hergestellt",), problem=True, open_=True, customer=True, min_act=1),
        s("Erdaushub gemacht 22 laufende Meter KG Rohre DN 125 verlegt Splittschicht reingepackt Graben verfüllt Planum verdichtet Auftraggeber informiert Problem Material knapp Offen Rest morgen.", ("Graben ausgehoben", "KG-Rohre", "Splitt eingebaut", "Graben verfüllt", "Untergrund verdichtet"), mats=("KG-Rohre",), problem=True, open_=True, customer=True),
        s("Baugrube ausgehoben Kanal angeschlossen Drainage verlegt Leitungstrasse angelegt.", ("Graben ausgehoben", "Kanal-/Schachtarbeiten durchgeführt", "Drainage/Entwässerung eingebaut", "Leitungstrasse hergestellt")),
        s("Sand reingepackt und verdichtet.", ("Sand eingebaut", "Untergrund verdichtet")),
        s("15 Meter KG verlegt fertig.", ("KG-Rohre",), min_act=1),
        s("Erdaushub gemacht 22 laufende Meter KG Rohre verlegt Splittschicht Graben verfüllt Hausanschluss vorbereitet Auftraggeber da Problem Plan fehlt Offen Schacht setzen.", ("Graben ausgehoben", "KG-Rohre"), mats=("KG-Rohre",), problem=True, open_=True, customer=True),
        s("Kundengespräch gehabt Trassenplan besprochen Problem Genehmigung Offen Rest.", (), problem=True, open_=True, customer=True, min_act=0),
        s("graben gezogen boden verdichtet.", ("Graben ausgehoben", "Untergrund verdichtet"), min_act=1),
        s("heute ich hab 18 meter kg rohre verlegt.", ("KG-Rohre verlegt",), min_act=1),
        s("Kanalisation angeschlossen Schacht gesetzt Problem Rohr Offen morgen.", ("Kanal-/Schachtarbeiten durchgeführt",), problem=True, open_=True, min_act=1),
        s("Asphaltdecke eingebaut Tragschicht verdichtet.", ("Asphalt eingebaut", "Untergrund verdichtet")),
        s("Leitungstrasse hergestellt Kies eingebaut.", ("Leitungstrasse hergestellt",), min_act=1),
        s("Mit dem Kunden gesprochen einverstanden.", (), customer=True, min_act=0),
        s("Spundwand gezogen Verbau gesetzt.", ("Verbau gesetzt",), min_act=1),
        s("Drainage verlegt Kies drumherum.", ("Drainage/Entwässerung eingebaut",), min_act=1),
        s("Bauherr zufrieden Graben fertig.", ("Graben ausgehoben",), customer=True, min_act=1),
        s("Feierabend.", (), min_act=0),
        s("Nur verdichten heute.", ("Untergrund verdichtet",), min_act=1),
        s("Hausanschluss Wasser und Abwasser.", ("Hausanschluss hergestellt",), min_act=1),
        s("Straßenausbau Asphalt eingebaut Problem Temperatur Offen letzte Bahn.", ("Asphalt eingebaut",), problem=True, open_=True, min_act=1),
        s("Rücksprache mit Kunde Trasse besprochen.", (), customer=True, min_act=0),
        s("KG Schacht gesetzt Rohre angeschlossen.", ("Kanal-/Schachtarbeiten durchgeführt",), min_act=1),
        s("Erdaushub 50 Kubik Aushub entsorgt.", ("Graben ausgehoben",), min_act=1),
        s("Frostschutz eingebaut Planum verdichtet.", ("Untergrund verdichtet",), min_act=1),
        s("Bodenaustausch gemacht Schotter eingebaut.", ("Schotter eingebaut",), mats=("Schotter",), min_act=1),
        s("Komplett Tag Graben KG verfüllen verdichten Auftraggeber informiert Problem Leitung Offen morgen.", ("Graben ausgehoben",), problem=True, open_=True, customer=True, min_act=1),
        s("HT-Rohre im Graben verlegt.", ("HT-Rohre verlegt",), min_act=1),
        s("Baugrube ausgehoben gesichert.", ("Graben ausgehoben",), min_act=1),
        s("Kanal TV-Inspektion vorbereitet.", ("Kanal-/Schachtarbeiten durchgeführt",), min_act=1),
    ]
    for lfm in [10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50, 54, 58, 62, 66, 70, 74, 78]:
        prob = lfm % 5 == 0
        opn = lfm % 7 == 0
        cust = lfm % 9 == 0
        tail = ""
        if prob:
            tail += " Problem Rohr."
        if opn:
            tail += " Offen Verfüllung."
        if cust:
            tail += " Auftraggeber da."
        items.append(s(
            f"{lfm} laufende Meter KG-Rohre verlegt Graben verfüllt{tail}",
            ("KG-Rohre verlegt", "Graben verfüllt"),
            mats=("KG-Rohre",),
            problem=prob,
            open_=opn,
            customer=cust,
            min_act=1,
        ))
    assert len(items) == 50, len(items)
    return items


def _putz() -> list[dict]:
    items: list[dict] = [
        s("120 Quadratmeter Außenputz aufgetragen Grundierung aufgetragen Problem Gerüst zu spät Offen Sockel nächste Woche Bauherr kurz informiert alles abgestimmt.", ("Außenputz aufgetragen", "Grundierung aufgetragen"), problem=True, open_=True, customer=True, cust_not=("120", "putz", "m²")),
        s("80 qm Putz aufgetragen Putz verarbeitet.", ("Putz aufgebracht",), mats=("Putz",), sum_forbid=("Putz verarbeitet",), mat_echo=True),
        s("WDVS gedämmt Fassadenarmierung ausgeführt.", ("WDVS ausgeführt", "Fassadenarmierung"), min_act=1),
        s("Stuck geschlagen Gesims hergestellt Problem Form Offen Rest Freitag.", ("Stuckarbeiten",), problem=True, open_=True, min_act=1),
        s("WDVS Platten angeklebt Armierungsgewebe eingebettet Reibputz drauf gemacht Sockelleiste stucken Kunde informiert Problem Kleber knapp Offen Rest morgen.", ("WDVS ausgeführt", "Armierung ausgeführt", "Reibputz aufgetragen"), problem=True, open_=True, customer=True, min_act=1),
        s("Fassade gedämmt Gewebe reingemacht Außenputz aufgetragen Gesims stuckiert.", ("WDVS ausgeführt", "Fassadenarmierung ausgeführt", "Außenputz aufgetragen")),
        s("Unterputz aufgetragen Oberputz aufgetragen.", ("Unterputz aufgetragen", "Oberputz aufgetragen")),
        s("Sanierputz aufgetragen Altputz entfernt.", ("Sanierputz aufgetragen", "Altputz entfernt"), mats=("Sanierputz",)),
        s("Schimmelbefall behandelt Sanierputz aufgebracht.", ("Schimmelbeseitigung durchgeführt", "Sanierputz aufgetragen"), min_act=1),
        s("Kundengespräch gehabt Putzfarbe besprochen Problem Lieferung Offen Rest.", (), problem=True, open_=True, customer=True, min_act=0),
        s("putz drauf gemacht grundierung gemacht.", ("Putz aufgebracht", "Grundierung aufgetragen"), min_act=1),
        s("heute ich hab 60 quadrat aussenputz gemacht.", ("Außenputz aufgetragen",), min_act=1),
        s("Innenputz Küche und Flur aufgetragen Kundin zufrieden Problem Riss Offen Nacharbeit.", ("Innenputz aufgetragen",), problem=True, open_=True, customer=True, min_act=1),
        s("Sockelputz aufgetragen Reibputz Fassade.", ("Sockelputz aufgetragen", "Reibputz aufgetragen")),
        s("Kratzputz aufgetragen Grundierung vorher.", ("Kratzputz aufgetragen", "Grundierung aufgetragen")),
        s("Mit dem Kunden gesprochen Farbe ok.", (), customer=True, min_act=0),
        s("Stuckarbeiten Gesims Fenster.", ("Stuckarbeiten durchgeführt",), min_act=1),
        s("WDVS komplett gedämmt armiert putz.", ("WDVS ausgeführt",), min_act=1),
        s("Bauherr zufrieden Fassade fertig.", ("Außenputz aufgetragen",), customer=True, min_act=1),
        s("Feierabend.", (), min_act=0),
        s("Nur Grundierung heute.", ("Grundierung aufgetragen",), min_act=1),
        s("Abdichtung Kellerwand hergestellt.", ("Abdichtung hergestellt",), min_act=1),
        s("Außenputz zweiter Anstrich.", ("Außenputz aufgetragen",), min_act=1),
        s("Problem Gerüst rutscht Offen Sicherung Kunde informiert.", (), problem=True, open_=True, customer=True, min_act=0),
        s("Risse geschlossen Spachtelgrund aufgetragen.", ("Spachtelarbeiten durchgeführt",), min_act=1),
        s("Stuck stuckiert Decke Zierleiste.", ("Stuckarbeiten durchgeführt",), min_act=1),
        s("Fassadenarmierung ausgeführt WDVS.", ("Fassadenarmierung ausgeführt",), min_act=1),
        s("Innenputz Bad aufgetragen.", ("Innenputz aufgetragen",), min_act=1),
        s("100 qm Putz Außen Kunde meckert wegen Farbe Problem Ton Offen Muster.", ("Außenputz aufgetragen",), problem=True, open_=True, customer=True, min_act=1),
        s("Oberputz aufgetragen Oberputz verarbeitet.", ("Oberputz aufgetragen",), mats=("Oberputz",), mat_echo=True, sum_forbid=("Oberputz verarbeitet",)),
        s("Rücksprache mit Kunde Putzplan.", (), customer=True, min_act=0),
        s("Laibungen putz fertig.", ("Putz aufgebracht",), min_act=1),
    ]
    for qm in [25, 35, 45, 55, 65, 75, 85, 95, 105, 115, 125, 135, 145, 155, 165, 175, 185, 195]:
        prob = qm % 30 == 0
        opn = qm % 40 == 0
        cust = qm % 50 == 0
        tail = ""
        if prob:
            tail += " Problem Gerüst."
        if opn:
            tail += " Offen Sockel."
        if cust:
            tail += " Bauherr informiert."
        items.append(s(
            f"{qm} Quadratmeter Außenputz aufgetragen{tail}",
            (f"{qm} m² Außenputz aufgetragen",) if qm <= 150 else ("Außenputz aufgetragen",),
            problem=prob,
            open_=opn,
            customer=cust,
            min_act=1,
        ))
    assert len(items) == 50, len(items)
    return items


TRADES: dict[str, list[dict]] = {
    "GaLaBau": _galabau(),
    "Trockenbau": _trockenbau(),
    "Fliesen": _fliesen(),
    "SHK": _shk(),
    "Hochbau": _hochbau(),
    "Tiefbau": _tiefbau(),
    "Putz": _putz(),
}


def _emit() -> str:
    lines = [
        '"""Szenario-Daten für Pilot-Monster-Welle 21 — 50 Basisszenarien pro Gewerk."""',
        "",
        "from __future__ import annotations",
        "",
        "TRADE_SCENARIOS: dict[str, list[dict]] = {",
    ]
    for trade, items in TRADES.items():
        lines.append(f'    "{trade}": [')
        for it in items:
            lines.append("        {")
            lines.append(f'            "raw": {it["raw"]!r},')
            lines.append(f'            "acts": {it["acts"]!r},')
            if it.get("mats"):
                lines.append(f'            "mats": {it["mats"]!r},')
            if it.get("forbid_acts"):
                lines.append(f'            "forbid_acts": {it["forbid_acts"]!r},')
            if it.get("problem"):
                lines.append('            "problem": True,')
            if it.get("open_"):
                lines.append('            "open_": True,')
            if it.get("customer"):
                lines.append('            "customer": True,')
            if it.get("min_act") is not None:
                lines.append(f'            "min_act": {it["min_act"]!r},')
            if it.get("cust_not"):
                lines.append(f'            "cust_not": {it["cust_not"]!r},')
            if it.get("sum_forbid"):
                lines.append(f'            "sum_forbid": {it["sum_forbid"]!r},')
            if it.get("mat_echo"):
                lines.append('            "mat_echo": True,')
            lines.append("        },")
        lines.append("    ],")
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("def all_base_scenarios() -> list[tuple[str, dict]]:")
    lines.append('    """Liefert (trade, scenario_dict) für alle 350 Basisszenarien."""')
    lines.append("    out: list[tuple[str, dict]] = []")
    lines.append("    for trade, items in TRADE_SCENARIOS.items():")
    lines.append("        if len(items) != 50:")
    lines.append('            raise ValueError(f"{trade}: erwartet 50, got {len(items)}")')
    lines.append("        for item in items:")
    lines.append("            out.append((trade, item))")
    lines.append("    return out")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    OUT.write_text(_emit(), encoding="utf-8")
    total = sum(len(v) for v in TRADES.values())
    print(f"Wrote {OUT.name}: {total} scenarios across {len(TRADES)} trades")
