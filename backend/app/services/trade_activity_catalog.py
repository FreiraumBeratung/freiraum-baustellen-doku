from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogMatch:
    intent: str
    text: str
    priority: float


@dataclass(frozen=True)
class _CatalogRule:
    intent: str
    text: str
    priority: float
    must_match: tuple[str, ...]


_GALABAU_RULES: tuple[_CatalogRule, ...] = (
    _CatalogRule("flaeche_profiliert", "Fläche profiliert", 71.0, (r"\b(fl(ä|ae)che|gel(ä|ae)nde|boden)\b", r"\b(profiliert|modelliert|abgezogen|abgezogen)\b")),
    _CatalogRule("hecke_geschnitten", "Hecke geschnitten", 76.0, (r"\bhecke(n)?\b", r"\b(geschnitten|getrimmt|zurückgeschnitten|zurueckgeschnitten)\b")),
    _CatalogRule("rasenkantensteine_gesetzt", "Randsteine gesetzt", 84.0, (r"\b(rasenkantenstein(e|en)?|rasenkanten|randstein(e|en)?|kantenstein(e|en)?|bordstein(e|en)?)\b", r"\b(gesetzt|gestellt|verlegt|gelegt|benutzt|verbaut|verarbeitet|montiert|eingebaut|gebaut)\b")),
    _CatalogRule("pflanzen_gepflanzt", "Pflanzen gesetzt", 74.0, (r"\b(pflanzen|bäume|baeume|sträucher|straeucher)\b", r"\b(gesetzt|gepflanzt|eingepflanzt|bepflanzt)\b")),
    _CatalogRule("rasen_verlegt", "Rasen verlegt", 73.0, (r"\b(rollrasen|rasen)\b", r"\b(verlegt|gelegt|eingebracht)\b")),
    _CatalogRule("teichbau_ausgefuehrt", "Teichbau durchgeführt", 72.0, (r"\b(teich|bachlauf|wasserspiel)\b", r"\b(gebaut|angelegt|hergestellt)\b")),
    _CatalogRule("entwaesserung_eingebaut", "Entwässerung eingebaut", 75.0, (r"\b(drainage|entwässerung|entwaesserung)\b", r"\b(eingebaut|verlegt|hergestellt)\b")),
    _CatalogRule("terrasse_gebaut", "Terrasse gebaut", 70.0, (r"\bterrasse(n)?\b", r"\b(gebaut|verlegt|hergestellt)\b")),
    _CatalogRule("zaun_sichtschutz_montiert", "Zaun/Sichtschutz montiert", 69.0, (r"\b(zaun|sichtschutz)\b", r"\b(montiert|gestellt|aufgebaut)\b")),
    _CatalogRule("pergola_carport_aufgestellt", "Pergola/Carport aufgestellt", 68.0, (r"\b(pergola|carport|gartenhaus)\b", r"\b(aufgestellt|gebaut|montiert|errichtet|gestellt)\b")),
    _CatalogRule("pflegearbeiten", "Pflegearbeiten durchgeführt", 55.0, (r"\b(unkraut|laub|mulch|winterdienst)\b", r"\b(entfernt|durchgeführt|gemacht|verteilt|geräumt|gestreut)\b")),
)

_TROCKENBAU_RULES: tuple[_CatalogRule, ...] = (
    _CatalogRule("staenderwerk_montiert", "Ständerwerk montiert", 79.0, (r"\b(ständerwerk|staenderwerk|cw|uw|cw-profile?|uw-profile?)\b", r"\b(gebaut|montiert|gestellt|eingebaut)\b")),
    _CatalogRule("gipskarton_montiert", "Gipskartonplatten montiert", 90.0, (r"\b(gipskarton|rigips)\b", r"\b(montiert|angebracht|aufgebaut|gesetzt)\b")),
    _CatalogRule("trockenbauwand_geschlossen", "Trockenbauwand geschlossen", 96.0, (r"\b(trockenbauwand|wand)\b", r"\b(geschlossen|zugemacht|gestellt)\b")),
    _CatalogRule("decke_abgehaengt", "Decke abgehängt", 74.0, (r"\bdecke(n)?\b", r"\b(abgehängt|abgehaengt|abgehangen)\b")),
    _CatalogRule("trockenbau_fugen_verspachtelt", "Fugen verspachtelt", 62.0, (r"\b(fuge|fugen)\b", r"\b(verspachtelt|gespachtelt|zugemacht)\b")),
    _CatalogRule("daemmung_eingebaut", "Dämmung eingebaut", 71.0, (r"\b(dämmung|daemmung|steinwolle|mineralwolle)\b", r"\b(eingebaut|verlegt|angebracht)\b")),
    _CatalogRule("akustikdecke_eingebaut", "Akustikdecke eingebaut", 70.0, (r"\bakustikdecke(n)?\b", r"\b(eingebaut|montiert)\b")),
    _CatalogRule("brandschutzwand_hergestellt", "Brandschutzwand hergestellt", 72.0, (r"\b(brandschutzwand|brandschutz)\b", r"\b(hergestellt|gebaut|montiert)\b")),
    _CatalogRule("revisionsklappe_eingebaut", "Revisionsklappe eingebaut", 66.0, (r"\brevisionsklappe(n)?\b", r"\b(eingebaut|montiert)\b")),
)

_FLIESEN_RULES: tuple[_CatalogRule, ...] = (
    _CatalogRule("grundierung_aufgetragen", "Grundierung aufgetragen", 67.0, (r"\b(grundierung|grundiert)\b", r"\b(aufgetragen|aufgebracht|grundiert)\b")),
    _CatalogRule("abdichtung_hergestellt", "Abdichtung hergestellt", 71.0, (r"\b(abdichtung|fl(ü|ue)ssigfolie|dichtschl(ä|ae)mme|dichtband)\b", r"\b(hergestellt|aufgebracht|eingebaut|montiert)\b")),
    _CatalogRule("fliesen_verlegt", "Fliesen verlegt", 100.0, (r"\b(fliesen?|platten|mosaik|feinsteinzeug)\b", r"\b(verlegt|gelegt|gesetzt)\b")),
    _CatalogRule("fliesenkleber", "Fliesenkleber aufgetragen", 68.0, (r"\b(kleber|flexkleber|mittelbettm(ö|oe)rtel|d(ü|ue)nnbettm(ö|oe)rtel)\b", r"\b(aufgetragen|aufgebracht|gezogen|benutzt|verwendet|verarbeitet|gemacht)\b")),
    _CatalogRule("fliesen_verfugt", "Fliesen verfugt", 56.0, (r"\b(fugenm(ö|oe)rtel|fugen)\b", r"\b(verfugt|eingebracht|gezogen)\b")),
    _CatalogRule("silikonfugen_silikoniert", "Silikonfugen silikoniert", 58.0, (r"\bsilikonfugen?|silikon\b", r"\b(gezogen|hergestellt|ausgef(ü|ue)hrt)\b")),
    _CatalogRule("fliesen_reparatur", "Fliesen repariert", 63.0, (r"\b(fliesen?)\b", r"\b(ausgetauscht|repariert|erneuert)\b")),
)

_SHK_RULES: tuple[_CatalogRule, ...] = (
    _CatalogRule("wasserleitungen_verlegt", "Wasserleitungen verlegt", 87.0, (r"\b(wasserleitung(en)?|trinkwasser|mehrschichtverbundrohr|kupferrohr|edelstahlpress)\b", r"\b(verlegt|montiert|installiert|angeschlossen)\b")),
    _CatalogRule("ht_rohre_verlegt", "HT-Rohre verlegt", 88.5, (r"\b(ht-?\s*rohre?|ht\s*dn\s*\d+)\b", r"\b(verlegt|montiert|eingebaut)\b")),
    _CatalogRule("kg_rohre_verlegt", "KG-Rohre verlegt", 89.0, (r"\b(kg-?\s*rohre?|kg\s*dn\s*\d+)\b", r"\b(verlegt|montiert|eingebaut)\b")),
    _CatalogRule("heizungsanschluesse_montiert", "Heizungsanschlüsse montiert", 88.0, (r"\b(heizung|heizungsanschl(ü|ue)sse)\b", r"\b(angeschlossen|montiert|installiert)\b")),
    _CatalogRule("heizkoerper_montiert", "Heizkörper montiert", 80.0, (r"\bheizk(ö|oe)rper\b", r"\b(montiert|angebracht|eingebaut)\b")),
    _CatalogRule("fussbodenheizung_verlegt", "Fußbodenheizung verlegt", 81.0, (r"\b(fu(ß|ss)bodenheizung)\b", r"\b(verlegt|eingebaut|installiert)\b")),
    _CatalogRule("waermepumpe_installiert", "Wärmepumpe installiert", 82.0, (r"\b(w(ä|ae)rmepumpe|gastherme|heizkessel)\b", r"\b(installiert|montiert|eingebaut)\b")),
    _CatalogRule("lueftung_klima_installiert", "Lüftungs-/Klimatechnik installiert", 69.0, (r"\b(l(ü|ue)ftung|klimaanlage|wohnrauml(ü|ue)ftung)\b", r"\b(installiert|eingebaut|montiert)\b")),
)

_TIEFBAU_RULES: tuple[_CatalogRule, ...] = (
    _CatalogRule("graben_ausgehoben", "Graben ausgehoben", 79.0, (r"\b(graben|baugrube)\b", r"\b(ausgehoben|gezogen|erstellt)\b")),
    _CatalogRule("untergrund_verdichtet", "Untergrund verdichtet", 76.5, (r"\b(untergrund|boden)\b", r"\b(verdichtet|verdichtung|abger(ü|ue)ttelt)\b")),
    _CatalogRule("kg_rohre_verlegt", "KG-Rohre verlegt", 89.0, (r"\b(kg-?\s*rohre?|kg\s*dn\s*\d+)\b", r"\b(verlegt|eingebaut|montiert)\b")),
    _CatalogRule("drainage_entwaesserung", "Drainage/Entwässerung eingebaut", 75.0, (r"\b(drainage|entw(ä|ae)sserung)\b", r"\b(eingebaut|verlegt|hergestellt)\b")),
    _CatalogRule("kanal_schacht", "Kanal-/Schachtarbeiten durchgeführt", 77.0, (r"\b(kanal|schacht|sch(ä|ae)chte)\b", r"\b(gesetzt|eingebaut|angeschlossen|betoniert)\b")),
    _CatalogRule("strassenbau_ausgefuehrt", "Straßen-/Wegebau ausgeführt", 78.0, (r"\b(asphalt|bordstein|gehweg|radweg|parkfl(ä|ae)che|stra(ß|ss)e)\b", r"\b(gebaut|hergestellt|asphaltiert|gesetzt|eingebaut|verlegt|eingebracht)\b")),
    _CatalogRule("verbau_gesetzt", "Verbau gesetzt", 73.0, (r"\bverbau|spundwand\b", r"\b(gesetzt|gestellt|eingebaut)\b")),
)

_HOCHBAU_RULES: tuple[_CatalogRule, ...] = (
    _CatalogRule("mauerwerk_erstellt", "Mauerwerk erstellt", 84.0, (r"\b(mauer|ziegel|kalksandstein|porenbeton)\b", r"\b(gemauert|gebaut|erstellt)\b")),
    _CatalogRule("schalung_erstellt", "Schalung erstellt", 83.0, (r"\bschalung\b", r"\b(erstellt|gebaut|gestellt)\b")),
    _CatalogRule("bewehrung_eingebaut", "Bewehrung eingebaut", 84.0, (r"\b(bewehrung|bewehrungsstahl|armierung)\b", r"\b(eingebaut|verlegt|gestellt)\b")),
    _CatalogRule("beton_eingebracht", "Beton eingebracht", 86.0, (r"\bbeton\b", r"\b(eingebracht|gegossen|verarbeitet|betoniert)\b")),
    _CatalogRule("fundament_erstellt", "Fundament erstellt", 85.0, (r"\bfundament(e)?\b", r"\b(erstellt|betoniert|gebaut)\b")),
    _CatalogRule("filigrandecke_montiert", "Filigrandecke montiert", 82.0, (r"\bfiligrandecke(n)?\b", r"\b(montiert|gesetzt|eingebaut)\b")),
)

_STUCK_RULES: tuple[_CatalogRule, ...] = (
    _CatalogRule("innenputz_aufgetragen", "Innenputz aufgetragen", 74.0, (r"\b(innenputz|gipsputz|kalkputz|lehmputz)\b", r"\b(aufgetragen|aufgebracht|verarbeitet)\b")),
    _CatalogRule("aussenputz_aufgetragen", "Außenputz aufgetragen", 74.0, (r"\b(aussenputz|au(ß|ss)enputz|fassade)\b", r"\b(aufgetragen|aufgebracht|strukturiert)\b")),
    _CatalogRule("wdvs_ausgefuehrt", "WDVS ausgeführt", 73.0, (r"\bwdvs|d(ä|ae)mmplatten|eps|mineralwolle|holzfaser\b", r"\b(angebracht|ged(ä|ae)mmt|ausgef(ü|ue)hrt|ged(ü|ue)belt)\b")),
    _CatalogRule("fassadenarmierung", "Fassadenarmierung ausgeführt", 72.0, (r"\b(armierungsgewebe|fassadenarmierung|gewebe)\b", r"\b(eingebettet|aufgebracht|ausgef(ü|ue)hrt)\b")),
    _CatalogRule("stuckarbeiten", "Stuckarbeiten durchgeführt", 62.0, (r"\bstuck|zierleisten|rosetten|gesimse\b", r"\b(montiert|hergestellt|angebracht)\b")),
)


def match_catalog_activity(norm_chunk: str) -> CatalogMatch | None:
    text = str(norm_chunk or "").strip()
    if not text:
        return None

    for rule in (
        _GALABAU_RULES
        + _TROCKENBAU_RULES
        + _FLIESEN_RULES
        + _SHK_RULES
        + _TIEFBAU_RULES
        + _HOCHBAU_RULES
        + _STUCK_RULES
    ):
        if _matches_all(text, rule.must_match):
            return CatalogMatch(intent=rule.intent, text=rule.text, priority=rule.priority)
    return None


def _matches_all(text: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        if not re.search(pattern, text, flags=re.IGNORECASE):
            return False
    return True

