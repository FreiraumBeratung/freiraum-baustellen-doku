"""Straßenbau-Szenarien — deckt Dimensionen der Wellen 2–25 ab (additiv).

Gruppen:
- core: Tätigkeiten, Material, Kurz/Lang, ASR, gebrochenes Deutsch (Welle 2–16)
- problem_customer: P2 Kundengespräch, P3 Problem/Offen implizit+explizit (Welle 20–24)
- cross_trade: GaLaBau + Tiefbau + Straßenbau gemischt (Welle 25)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StrassenbauScenario:
    raw: str
    expect_activities: tuple[str, ...]
    expect_materials: tuple[str, ...] = field(default_factory=tuple)
    expect_material_suggestions: tuple[str, ...] = field(default_factory=tuple)
    expect_machine_suggestions: tuple[str, ...] = field(default_factory=tuple)
    forbid_activities: tuple[str, ...] = field(default_factory=tuple)
    expect_problem: bool = False
    expect_open: bool = False
    expect_customer: bool = False
    min_activity_count: int | None = None


def core_scenarios() -> list[StrassenbauScenario]:
  """Herz-Nieren Straßenbau / Tiefbau-Straße (Pilot + JSON-Vokabular)."""
  return [
      # ── Pilot GaLaBau/öffentlicher Bereich ──
      StrassenbauScenario(
          "50 Meter Graben verfüllt und verdichtet.",
          ("Graben verfüllt", "Untergrund verdichtet"),
          expect_materials=("Kies",),
      ),
      StrassenbauScenario(
          (
              "Kopfloch für Wasserleitung ausgehoben 11 Meter Asphalt geschnitten "
              "24 Quadratmeter asphaltiert."
          ),
          ("Graben ausgehoben", "Asphalt schneiden", "Asphalt eingebaut"),
          expect_materials=("Asphalt",),
      ),
      StrassenbauScenario(
          (
              "Morgens 11 lfm Asphalt schneiden dann 24 m² asphaltiert mit Walze verdichtet "
              "Bauherr kurz da Kundengespräch Problem Temperatur zu niedrig Offen letzte Bahn morgen."
          ),
          ("Asphalt schneiden", "Asphalt eingebaut"),
          expect_problem=True,
          expect_open=True,
          expect_customer=True,
      ),
      # ── JSON-Kern Tätigkeiten ──
      StrassenbauScenario("11 Meter Asphalt schneiden fertig.", ("Asphalt schneiden",), min_activity_count=1),
      StrassenbauScenario("Deckschicht abgefräst mit Kaltfräse.", ("Asphalt fräsen",), min_activity_count=1),
      StrassenbauScenario("24 Quadratmeter SMA asphaltiert.", ("Asphalt eingebaut",), expect_materials=("SMA",)),
      StrassenbauScenario(
          "Asphaltdecke eingebaut und mit Walze verdichtet.",
          ("Asphalt eingebaut",),
          min_activity_count=1,
      ),
      StrassenbauScenario(
          "Frostschutzschicht 0/45 hergestellt und verdichtet.",
          ("Frostschutzschicht hergestellt",),
          min_activity_count=1,
      ),
      StrassenbauScenario(
          "Frostschutz eingebaut und Untergrund verdichtet.",
          ("Frostschutz eingebaut", "Untergrund verdichtet"),
      ),
      StrassenbauScenario(
          "Schottertragschicht STS 0/32 hergestellt.",
          ("Schottertragschicht hergestellt",),
          min_activity_count=1,
      ),
      StrassenbauScenario("Planum hergestellt und verdichtet.", ("Planum hergestellt",), min_activity_count=1),
      StrassenbauScenario(
          "Hochbord gesetzt und Rinnensteine verlegt.",
          ("Borde gesetzt", "Rinnenstein"),
      ),
      StrassenbauScenario("Gully gesetzt.", ("Straßenabläufe gesetzt",), min_activity_count=1),
      StrassenbauScenario(
          "Haftbrücke mit Bitumenemulsion hergestellt.",
          ("Schichtenverbund hergestellt",),
          expect_materials=("Bitumenemulsion",),
      ),
      StrassenbauScenario("Asphaltnaht mit Heißbitumen hergestellt.", ("Nähte hergestellt",), min_activity_count=1),
      # ── Tiefbau-Mix (KG, Graben — Regression) ──
      StrassenbauScenario(
          "Graben ausgehoben 20 lfm KG-Rohre DN 110 verlegt Graben verfüllt.",
          ("Graben ausgehoben", "KG-Rohre", "Graben verfüllt"),
          expect_materials=("KG-Rohre",),
      ),
      StrassenbauScenario(
          "Leitungstrasse hergestellt Hausanschluss hergestellt.",
          ("Leitungstrasse hergestellt", "Hausanschluss"),
      ),
      StrassenbauScenario(
          "Straßenausbau Asphalt eingebaut Untergrund verdichtet.",
          ("Asphalt eingebaut", "Untergrund verdichtet"),
      ),
      # ── Ketten / Lang ──
      StrassenbauScenario(
          (
              "Heute haben wir zuerst den Graben ausgehoben dann Frostschutz eingebaut "
              "danach Schotter eingebaut und Planum verdichtet und zum Schluss "
              "24 Quadratmeter Asphalt eingebaut."
          ),
          ("Graben ausgehoben", "Frostschutz", "Asphalt eingebaut"),
          min_activity_count=3,
      ),
      StrassenbauScenario(
          (
              "An der Hauptstraße Frostschutz eingebaut Schotter eingebaut "
              "Deckschicht abgefräst 24 Quadratmeter asphaltiert Borde gesetzt."
          ),
          ("Frostschutz", "Schotter", "Borde"),
          min_activity_count=3,
      ),
      # ── Kurz / Umgangssprache ──
      StrassenbauScenario("Asphalt gemacht fertig.", ("Asphalt eingebaut",), min_activity_count=1),
      StrassenbauScenario("asphaltieren 30 qm.", ("Asphalt eingebaut",), min_activity_count=1),
      StrassenbauScenario("Frostschutz eingebaut und walzen.", ("Frostschutz",), min_activity_count=1),
      StrassenbauScenario("Bordstein setzen 15 lfm.", ("Borde gesetzt",), min_activity_count=1),
      # ── Gebrochenes Deutsch ──
      StrassenbauScenario(
          "heute ich hab gemacht 11 meter asphalt schneiden und 24 quadrat asphaltiert.",
          ("Asphalt schneiden", "Asphalt eingebaut"),
          min_activity_count=2,
      ),
      StrassenbauScenario(
          "heute auf baustelle graben verfuellt und frostschutz reingemacht.",
          ("Graben verfüllt", "Frostschutz"),
          min_activity_count=2,
      ),
      # ── Aufzählung geteiltes Verb ──
      StrassenbauScenario(
          "11 Meter Asphalt schneiden und 24 Quadratmeter asphaltiert.",
          ("Asphalt schneiden", "Asphalt eingebaut"),
      ),
      StrassenbauScenario(
          "Hochbord gesetzt. Rinnensteine gesetzt.",
          ("Borde gesetzt", "Rinnensteine gesetzt"),
      ),
      # ── Maschinen-Hinweise ──
      StrassenbauScenario(
          "Mit dem Asphaltfertiger 18 Tonnen AC eingebaut.",
          ("Asphalt eingebaut",),
          expect_machine_suggestions=("Asphaltfertiger?",),
      ),
      StrassenbauScenario(
          "Kaltfräse auf der Baustelle Deckschicht abgefräst.",
          ("Asphalt fräsen",),
      ),
  ]


def problem_customer_scenarios() -> list[StrassenbauScenario]:
  """P2/P3 — Kundengespräch, Problem, Offen (implizit + explizit)."""
  return [
      StrassenbauScenario(
          (
              "Asphalt eingebaut Bauherr war da und zufrieden Problem es hat geregnet "
              "Offen morgen letzte Bahn Kundengespräch lief gut."
          ),
          ("Asphalt eingebaut",),
          expect_problem=True,
          expect_open=True,
          expect_customer=True,
      ),
      StrassenbauScenario(
          (
              "11 Meter Asphalt geschnitten leider Maschine kaputt mussten abbrechen "
              "morgen weiter Auftraggeber informiert."
          ),
          ("Asphalt schneiden",),
          expect_problem=True,
          expect_open=True,
          expect_customer=True,
      ),
      StrassenbauScenario(
          "Frostschutz eingebaut Problem Lieferung fehlt Offen Rest morgen.",
          ("Frostschutz",),
          expect_problem=True,
          expect_open=True,
      ),
      StrassenbauScenario(
          "Planum verdichtet mussten wegen Regen abbrechen morgen Asphalt einbauen.",
          ("Planum",),
          expect_problem=True,
          expect_open=True,
      ),
      StrassenbauScenario(
          "Schottertragschicht hergestellt Offen noch Walzen nächste Woche.",
          ("Schottertragschicht",),
          expect_open=True,
      ),
      StrassenbauScenario(
          "Gully gesetzt Kundengespräch mit Bauleitung Abstimmung Termin nächste Woche.",
          ("Straßenabläufe",),
          expect_customer=True,
      ),
      StrassenbauScenario(
          "Asphaltfräse unterwegs Problem Verkehrssicherung Offen Abschluss Freitag.",
          ("Asphalt fräsen",),
          expect_problem=True,
          expect_open=True,
      ),
      StrassenbauScenario(
          "Nähte hergestellt Kunde nicht da Offen Nacharbeit Montag.",
          ("Nähte",),
          expect_open=True,
      ),
      StrassenbauScenario(
          "Haftbrücke aufgetragen Auftraggeber kurz gesprochen alles abgestimmt.",
          ("Schichtenverbund",),
          expect_customer=True,
      ),
      StrassenbauScenario(
          "Kundengespräch gehabt Leitungsplan besprochen Problem Grundwasser Offen Rest nächste Woche.",
          (),
          expect_problem=True,
          expect_open=True,
          expect_customer=True,
          min_activity_count=0,
      ),
      StrassenbauScenario(
          "Heute nur gesprochen mit Kunde wegen Asphalttermin keine Arbeit wegen Regen.",
          (),
          expect_problem=True,
          expect_customer=True,
          min_activity_count=0,
      ),
      StrassenbauScenario(
          (
              "Graben ausgehoben KG-Rohre verlegt Problem Leitungsplan fehlt "
              "Offen Schacht setzen morgen nach Kundengespräch."
          ),
          ("Graben ausgehoben", "KG-Rohre"),
          expect_problem=True,
          expect_open=True,
          expect_customer=True,
      ),
      StrassenbauScenario(
          "Borde gesetzt leider Material knapp Offen letzte Strecke Donnerstag.",
          ("Borde",),
          expect_problem=True,
          expect_open=True,
      ),
      StrassenbauScenario(
          "24 m² asphaltiert Problem Temperatur Offen Nacharbeit morgen Bauherr informiert.",
          ("Asphalt eingebaut",),
          expect_problem=True,
          expect_open=True,
          expect_customer=True,
      ),
      StrassenbauScenario(
          "FSS und STS hergestellt warten auf Asphaltlieferung nächste Woche.",
          ("Frostschutz", "Schottertragschicht"),
          expect_open=True,
          min_activity_count=1,
      ),
  ]


def cross_trade_scenarios() -> list[StrassenbauScenario]:
  """GaLaBau + Tiefbau + Straßenbau im selben Tagesbericht."""
  return [
      StrassenbauScenario(
          (
              "Morgens 40 m² Pflaster verlegt am Gehweg danach 11 Meter Asphalt schneiden "
              "und 24 m² asphaltiert Randsteine am Beet gesetzt."
          ),
          ("Pflaster verlegt", "Asphalt schneiden", "Asphalt eingebaut"),
          min_activity_count=3,
      ),
      StrassenbauScenario(
          (
              "Graben für Wasserleitung ausgehoben KG-Rohre verlegt Graben verfüllt "
              "dann Straße asphaltiert 18 m²."
          ),
          ("Graben ausgehoben", "KG-Rohre", "Asphalt eingebaut"),
          min_activity_count=3,
      ),
      StrassenbauScenario(
          (
              "Öffentliche Fläche: Schotter eingebaut Pflaster verlegt Borde gesetzt "
              "Hecke zurückgeschnitten."
          ),
          ("Schotter eingebaut", "Pflaster verlegt", "Borde gesetzt"),
          min_activity_count=3,
      ),
      StrassenbauScenario(
          (
              "Parkplatz: Frostschutz eingebaut Asphalt eingebaut Rasenkantensteine gesetzt "
              "Laub entfernt."
          ),
          ("Frostschutz", "Asphalt eingebaut"),
          min_activity_count=2,
      ),
      StrassenbauScenario(
          (
              "Mit Bagger Graben ausgehoben 15 lfm KG verlegt Planum verdichtet "
              "Asphaltdecke eingebaut Bauherr zufrieden."
          ),
          ("Graben ausgehoben", "KG-Rohre", "Asphalt eingebaut"),
          expect_customer=True,
          min_activity_count=3,
      ),
      StrassenbauScenario(
          (
              "Gehweg saniert: alte Platten raus Asphalt gefräst neue Deckschicht "
              "24 m² asphaltiert Pflastersteine am Eingang verlegt."
          ),
          ("Asphalt fräsen", "Asphalt eingebaut", "Pflaster"),
          min_activity_count=2,
      ),
      StrassenbauScenario(
          (
              "Kanal angeschlossen Schacht gesetzt Straße aufgemacht Asphalt eingebaut "
              "Problem Verkehr Offen Markierung morgen."
          ),
          ("Kanal", "Asphalt eingebaut"),
          expect_problem=True,
          expect_open=True,
          min_activity_count=2,
      ),
      StrassenbauScenario(
          (
              "50 m Graben verfüllt Splitt eingebaut Pflaster verlegt am Vorplatz "
              "Kundengespräch mit Stadt."
          ),
          ("Graben verfüllt", "Pflaster verlegt"),
          expect_customer=True,
          min_activity_count=2,
      ),
      StrassenbauScenario(
          (
              "Einfahrt: Schottertragschicht hergestellt Asphalt eingebaut "
              "Rasen am Rand getrimmt."
          ),
          ("Schottertragschicht", "Asphalt eingebaut"),
          min_activity_count=2,
      ),
      StrassenbauScenario(
          (
              "Baustelle Mix: Drainage verlegt Gehweg asphaltiert 12 m² "
              "Unkraut am Rand entfernt."
          ),
          ("Drainage", "Asphalt eingebaut"),
          min_activity_count=2,
      ),
      StrassenbauScenario(
          (
              "Großprojekt Hotel: Leitungstrasse hergestellt Straße asphaltiert "
              "Terrasse Pflaster verlegt Problem Wind Offen Montag."
          ),
          ("Leitungstrasse", "Asphalt", "Pflaster"),
          expect_problem=True,
          expect_open=True,
          min_activity_count=2,
      ),
      StrassenbauScenario(
          (
              "heute ich hab gemacht pflaster und asphalt 20 quadrat und graben verfuellt "
              "kunde gred alles ok."
          ),
          ("Pflaster", "Asphalt", "Graben verfüllt"),
          expect_customer=True,
          min_activity_count=2,
      ),
  ]
