from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.human_language_engine import humanize_activity
from app.services.trade_activity_catalog import match_catalog_activity
from app.services.trade_phrase_memory import apply_trade_phrase_memory


@dataclass
class CanonicalActivity:
    intent: str
    text: str
    priority: float
    has_quantity: bool


def canonicalize_activities(raw_activities: list[str], *, raw_text: str = "") -> list[str]:
    chunks: list[str] = []
    for item in raw_activities:
        chunks.extend(_split_chunks(str(item or "")))

    if raw_text.strip():
        chunks.extend(_split_chunks(raw_text))

    selected: dict[str, CanonicalActivity] = {}
    for chunk in chunks:
        c = _canonicalize_chunk(chunk, raw_text=raw_text)
        if not c:
            continue
        prev = selected.get(c.intent)
        if prev is None or _is_better(c, prev):
            selected[c.intent] = c

    ordered = sorted(selected.values(), key=lambda x: x.priority + (2.0 if x.has_quantity else 0.0), reverse=True)
    return _compact_activity_items([x.text for x in ordered])


def _split_chunks(text: str) -> list[str]:
    t = str(text or "").strip()
    if not t:
        return []
    t = re.sub(r"[;!?]", ".", t)
    t = re.sub(r"\bwir haben\b", ".", t, flags=re.IGNORECASE)
    t = re.sub(r"\bhaben wir\b", ".", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:dann noch|dann|anschließend|anschliessend|sowie|und dann)\b", ".", t, flags=re.IGNORECASE)
    t = re.sub(r"\bdabei\b", ".", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfür den untergrund\b", ".", t, flags=re.IGNORECASE)
    t = re.sub(r"\bden graben\b", ". den graben", t, flags=re.IGNORECASE)
    t = re.sub(r"\bund\b", ".", t, flags=re.IGNORECASE)
    parts = [p.strip(" ,.;") for p in re.split(r"[.]", t) if p.strip(" ,.;")]
    out: list[str] = []
    for part in parts:
        first = _split_by_verb_transition(part)
        for inner in first:
            out.extend(_split_by_semantic_comma(inner))
    return [x for x in out if x]


_TRANSITION_VERBS = (
    "angebracht",
    "montiert",
    "verlegt",
    "abgehängt",
    "abgehaengt",
    "verspachtelt",
    "verfugt",
    "aufgetragen",
    "aufgebracht",
    "eingebaut",
    "gebaut",
    "gesetzt",
    "geschnitten",
    "befüllt",
    "befuellt",
    "ausgehoben",
    "verdichtet",
    "entfernt",
    "beseitigt",
    "saniert",
    "angeschlossen",
    "installiert",
    "geschlossen",
    "hergestellt",
    "ausgeführt",
    "ausgefuehrt",
    "durchgeführt",
    "durchgefuehrt",
    "erstellt",
    "gegossen",
    "betoniert",
    "fertiggestellt",
)

_FOLLOW_NOUNS = (
    "eine",
    "einen",
    "ein",
    "die",
    "der",
    "das",
    "den",
    "fugen",
    "gipskarton",
    "gipskartonplatten",
    "rigips",
    "dämmung",
    "daemmung",
    "trockenbauwand",
    "wand",
    "decke",
    "decken",
    "akustikdecke",
    "hecke",
    "untergrund",
    "pflaster",
    "pflastersteine",
    "fliesen",
    "rohre",
    "kg-rohre",
    "ht-rohre",
    "rasenkanten",
    "rasenkantensteine",
    "pflanzen",
    "pflanzkübel",
    "pflanzkuebel",
    "schotter",
    "splitt",
    "sanierputz",
    "altputz",
    "putz",
    "innenputz",
    "außenputz",
    "aussenputz",
    "silikon",
    "silikonfugen",
    "beton",
    "mauerwerk",
    "ziegel",
    "poroton",
    "porenbeton",
    "ytong",
    "kalksandstein",
    "ks-stein",
    "ks stein",
    "bewehrung",
    "schalung",
    "fundament",
    "wasserleitungen",
    "heizung",
    "heizkörper",
    "heizkoerper",
    "heizungsanschlüsse",
    "heizungsanschluesse",
    "filigrandecke",
    "fußbodenheizung",
    "fussbodenheizung",
    "wärmepumpe",
    "waermepumpe",
    "ständerwerk",
    "staenderwerk",
    "brandschutzwand",
    "revisionsklappe",
    "abdichtung",
    "grundierung",
    "fliesenkleber",
    "kleber",
    "fugenmörtel",
    "fugenmoertel",
    "fugenspachtel",
    "mulch",
    "unkraut",
    "laub",
    "graben",
    "drainage",
    "entwässerung",
    "entwaesserung",
    "kanal",
    "schacht",
    "asphalt",
    "wdvs",
    "stuck",
    "fassade",
    "fassadenarmierung",
    "armierungsgewebe",
    "rasen",
    "rollrasen",
    "terrasse",
    "pergola",
    "carport",
    "zaun",
    "sichtschutz",
)


_NUMBER_WORDS = (
    "eins",
    "eine",
    "ein",
    "zwei",
    "drei",
    "vier",
    "fünf",
    "fuenf",
    "sechs",
    "sieben",
    "acht",
    "neun",
    "zehn",
    "elf",
    "zwölf",
    "zwoelf",
)


def _split_by_verb_transition(part: str) -> list[str]:
    t = str(part or "").strip()
    if not t:
        return []
    # Trennt lange Diktatketten wie
    # "... Gipskartonplatten angebracht Decke abgehängt Fugen verspachtelt ..."
    # oder "...Pflaster verlegt drei Kubikmeter Schotter eingebaut..."
    # in fachlich getrennte Aktivitätssegmente. Wir splitten nach einem
    # Tätigkeitsverb, sobald ein Artikel, ein bekanntes Fach-Substantiv
    # oder eine Mengenangabe (Ziffer oder Wortzahl) folgt.
    verbs_pattern = "|".join(_TRANSITION_VERBS)
    follow_pattern = "|".join(re.escape(w) for w in _FOLLOW_NOUNS)
    number_words_pattern = "|".join(_NUMBER_WORDS)
    pattern = (
        rf"\b({verbs_pattern})\b\s+"
        rf"(?=(?:{follow_pattern}|{number_words_pattern}|\d)\b|\d)"
    )
    marked = re.sub(pattern, r"\1. ", t, flags=re.IGNORECASE)
    splits = [p.strip(" ,.;") for p in re.split(r"[.]", marked) if p.strip(" ,.;")]
    return splits if splits else [t]


def _split_by_semantic_comma(part: str) -> list[str]:
    t = str(part or "").strip()
    if not t:
        return []
    pattern = r",\s+"
    splits = [p.strip(" ,.;") for p in re.split(pattern, t, flags=re.IGNORECASE) if p.strip(" ,.;")]
    return splits if splits else [t]


def _normalize_for_match(text: str) -> str:
    out = text.casefold()
    # Whisper-Fehler im Rohrkontext: "den/de en/d n 150 kg" -> "dn 150 kg"
    out = re.sub(
        r"\b(?:den|de\s*en|d\s*n)\s*(\d{2,3})\s*(?=(?:kg|ht|kanal)\b)",
        r"dn \1 ",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\b((?:kg|ht|kanal)(?:\s*rohre?|\s*rohr)?)\s*(?:den|de\s*en|d\s*n)\s*(\d{2,3})\b",
        r"\1 dn \2",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(r"\bquadratmeter\b|\bqm\b", "m²", out)
    out = re.sub(r"\bmeter quadrat\b", "m²", out)
    out = re.sub(r"\bkubikmeter\b|\bkubik\b", "m³", out)
    out = re.sub(r"\blaufende meter\b|\blfd\.?\s*meter\b|\blfm\b", "lfm", out)
    out = re.sub(r"\bkg-?\s*rohre\b", "kg rohre", out)
    out = re.sub(r"\bht-?\s*rohre\b", "ht rohre", out)
    # Häufige Whisper-Verhörer bei Trockenbau-Profilen.
    out = re.sub(r"\buwe\b(?=\s*[-]?\s*profil)", "uw", out)
    out = re.sub(r"\bcwe\b(?=\s*[-]?\s*profil)", "cw", out)
    out = re.sub(r"\buae\b(?=\s*[-]?\s*profil)", "ua", out)
    out = re.sub(r"\bkg\s*dn\s*\d+\b", "kg rohre", out)
    out = re.sub(r"\bht\s*dn\s*\d+\b", "ht rohre", out)
    out = re.sub(r"\brasen[\s-]*kanten[\s-]*steine?\b", "rasenkantensteine", out)
    out = re.sub(r"\brasen[\s-]*kanten\b", "rasenkanten", out)
    out = re.sub(r"\bbew(ä|ae)hrung\b|\bbewahrung\b", "bewehrung", out)
    out = re.sub(r"\b(puroton|porroton|poriton|porit)\b", "poroton", out)
    out = re.sub(r"\b(yetong|yton)\b", "ytong", out)
    out = _normalize_masonry_size_notation(out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def _normalize_masonry_size_notation(text: str) -> str:
    t = str(text or "")
    if not re.search(r"\b(poroton|porenbeton|ytong|kalksandstein|ks(?:-stein)?|mauerwerk|ziegel|stein)\b", t):
        return t
    # Baustellen-/Whisper-Varianten wie "11 fünfer", "17 fünfer".
    t = re.sub(r"\b(\d{1,2})\s*(fünfer|fuenfer)\b", lambda m: f"{m.group(1)},5er", t, flags=re.IGNORECASE)
    # Häufiger Whisper-Fehler: "l5/l5er/el5er" statt "11,5er".
    t = re.sub(r"\b(?:l|el)\s*5(?:er)?\b", "11,5er", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:l|el)\s*(fünfer|fuenfer)\b", "11,5er", t, flags=re.IGNORECASE)
    return t


def _extract_qty_m2(text: str) -> str | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(m²|m2|qm|quadratmeter)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    w = re.search(
        r"\b(eins|eine|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwoelf)\s*(m²|quadratmeter)\b",
        text,
        flags=re.IGNORECASE,
    )
    return _word_to_number(w.group(1)) if w else None


def _extract_qty_m3(text: str) -> str | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(m³|m3|kubikmeter|kubik)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    w = re.search(
        r"\b(eins|eine|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwoelf)\s*(m³|kubikmeter|kubik)\b",
        text,
        flags=re.IGNORECASE,
    )
    return _word_to_number(w.group(1)) if w else None


def _extract_splitt_size(text: str) -> str | None:
    low = text.casefold()
    m = re.search(r"\b(\d{1,2})\s*/\s*(\d{1,2})\b", low)
    if m:
        return f"{m.group(1)}/{m.group(2)} mm"
    m2 = re.search(r"\b(\d{1,2})\s*er\b", low)
    if m2:
        n = m2.group(1)
        if len(n) == 2:
            return f"{n[0]}/{n[1]} mm"
    if re.search(r"\bzwei[\s-]*(fünfer|fuenfer|fünf|fuenf)\b", low):
        return "2/5 mm"
    return None


def _extract_piece_count(text: str) -> str | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(stück|stk)\b", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    w = re.search(
        r"\b(eins|eine|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwoelf)\s*(stück|pflanzkübel|pflanzkuebel)\b",
        text,
        flags=re.IGNORECASE,
    )
    return _word_to_number(w.group(1)) if w else None


def _extract_qty_lfm(text: str) -> str | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(lfm|laufende meter|meter)\b", text, flags=re.IGNORECASE)
    return m.group(1) if m else None


def _extract_dn(text: str, *, kind: str) -> str | None:
    t = str(text or "")
    if kind == "kg":
        # Varianten wie "DN 150 KG Rohr", "KG DN 160", "DN150 kg-rohre"
        m = re.search(r"\b(?:dn|den|de\s*en|d\s*n)\s*(\d{2,3})\s*[-\s]?(?:kg|kanal)\b", t, flags=re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(
            r"\b(?:kg|kanal)\s*[-\s]?(?:rohre?|rohr)?\s*(?:dn|den|de\s*en|d\s*n)\s*(\d{2,3})\b",
            t,
            flags=re.IGNORECASE,
        )
        if m:
            return m.group(1)
        # Umgangssprache im Tief-/GaLaBau:
        # "100er/Hunderter KG-Rohr" => DN 110
        # "150er/Hundertfuffziger KG-Rohr" => DN 160
        if re.search(
            r"\b(100er|hunderter|hundert(?:er)?)\b.{0,24}\b(kg|kanal|kg[-\s]?rohr(?:e)?)\b",
            t,
            flags=re.IGNORECASE,
        ):
            return "110"
        if re.search(
            r"\b(150er|hundertf(ü|ue|u)nfzig(?:er)?|hundertfuffzig(?:er)?)\b.{0,24}\b(kg|kanal|kg[-\s]?rohr(?:e)?)\b",
            t,
            flags=re.IGNORECASE,
        ):
            return "160"
    if kind == "ht":
        m = re.search(r"\b(?:dn|den|de\s*en|d\s*n)\s*(\d{2,3})\s*[-\s]?ht\b", t, flags=re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(
            r"\bht\s*[-\s]?(?:rohre?|rohr)?\s*(?:dn|den|de\s*en|d\s*n)\s*(\d{2,3})\b",
            t,
            flags=re.IGNORECASE,
        )
        if m:
            return m.group(1)
    return None


def _extract_stone_piece_count(text: str) -> str | None:
    m = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(?:st(ü|ue)ck|stk)?\s*"
        r"(randstein(?:e|en)?|kantenstein(?:e|en)?|rasenkantenstein(?:e|en)?|bordstein(?:e|en)?)\b",
        text,
        flags=re.IGNORECASE,
    )
    return m.group(1) if m else None


def _has_any_quantity(text: str) -> bool:
    return bool(re.search(r"\b\d+(?:[.,]\d+)?\s*(m²|m2|qm|m³|m3|lfm|stück|stk|kg|t)\b", text, flags=re.IGNORECASE))


def _canonicalize_chunk(chunk: str, *, raw_text: str) -> CanonicalActivity | None:
    base = apply_trade_phrase_memory(humanize_activity(chunk), raw_text=raw_text)
    t = _normalize_for_match(base)
    if not t:
        return None

    # Fliesenleger
    if "grundierung" in t and re.search(r"\b(aufgetragen|aufgebracht)\b", t):
        return CanonicalActivity("grundierung_aufgetragen", "Grundierung aufgetragen", 67.0, False)
    if "abdichtung" in t and re.search(r"\b(hergestellt|aufgebracht|eingebaut)\b", t):
        return CanonicalActivity("abdichtung_hergestellt", "Abdichtung hergestellt", 71.0, False)
    if "fliesen" in t and re.search(r"\b(verlegt|gelegt)\b", t):
        qty = _extract_qty_m2(t)
        text = f"{_qty_prefix(raw_text)}{qty} m² Fliesen verlegt" if qty else "Fliesen verlegt"
        return CanonicalActivity("fliesen_verlegt", text, 100.0, bool(qty))
    if ("kleber" in t or "flexkleber" in t or "mittelbettmörtel" in t or "mittelbettmoertel" in t or "dünnbettmörtel" in t or "duennbettmoertel" in t) and re.search(
        r"\b(gezogen|aufgetragen|aufgebracht|benutzt|verwendet|verarbeitet|gemacht|drauf)\b",
        t,
    ):
        return CanonicalActivity("fliesenkleber", "Fliesenkleber aufgetragen", 68.0, False)
    if "silikonfugen" in t or (
        "silikon" in t
        and re.search(
            r"\b(gemacht|gezogen|silikoniert|hergestellt|abgeschlossen|verarbeitet|"
            r"aufgetragen|nachgearbeitet|ausgef(ü|ue)hrt|fertig(gemacht|gestellt))\b",
            t,
        )
    ):
        return CanonicalActivity("silikonfugen_silikoniert", "Silikonfugen silikoniert", 58.0, False)
    if _is_fliesen_fuge_context(t, raw_text=raw_text):
        return CanonicalActivity("fliesen_verfugt", "Fliesen verfugt", 56.0, False)

    # GaLaBau
    if ("hecke" in t or "hecken" in t) and re.search(r"\b(geschnitten|zurückgeschnitten|getrimmt)\b", t):
        return CanonicalActivity("hecke_geschnitten", "Hecke geschnitten", 76.0, False)
    # Rand-/Rasenkantensteine MUSS vor "rasen" geprüft werden, damit
    # "Rasenkantensteine" nicht versehentlich als "Rasen verlegt" interpretiert wird.
    if re.search(
        r"\b(rasenkantenstein(e|en)?|rasenkanten|randstein(e|en)?|kantenstein(e|en)?|bordstein(e|en)?)\b",
        t,
    ) and re.search(r"\b(gesetzt|gestellt|verlegt|gelegt|benutzt|verbaut|verarbeitet|montiert|eingebaut|gebaut)\b", t):
        qty_lfm = _extract_qty_lfm(t)
        qty_stk = _extract_stone_piece_count(t)
        is_rand = bool(re.search(r"\b(randstein(e|en)?|kantenstein(e|en)?|bordstein(e|en)?)\b", t))
        label = "Randsteine" if is_rand else "Rasenkantensteine"
        if qty_lfm:
            text = f"{qty_lfm} lfm {label} gesetzt"
            return CanonicalActivity("rasenkantensteine_gesetzt", text, 84.0, True)
        if qty_stk:
            text = f"{qty_stk} Stück {label} gesetzt"
            return CanonicalActivity("rasenkantensteine_gesetzt", text, 84.0, True)
        return CanonicalActivity("rasenkantensteine_gesetzt", f"{label} gesetzt", 84.0, False)
    if ("rasen" in t or "rollrasen" in t) and re.search(r"\b(verlegt|gelegt|eingebracht)\b", t):
        return CanonicalActivity("rasen_verlegt", "Rasen verlegt", 73.0, False)
    if ("pflanzen" in t or "bäume" in t or "baeume" in t or "sträucher" in t or "straeucher" in t) and re.search(
        r"\b(gesetzt|gepflanzt|eingepflanzt|bepflanzt)\b",
        t,
    ):
        return CanonicalActivity("pflanzen_gepflanzt", "Pflanzen gesetzt", 74.0, False)
    if ("unkraut" in t or "laub" in t or "mulch" in t) and re.search(r"\b(entfernt|gemacht|durchgeführt|verteilt)\b", t):
        return CanonicalActivity("pflegearbeiten", "Pflegearbeiten durchgeführt", 55.0, False)
    if "pflaster" in t and re.search(r"\b(verlegt|gelegt)\b", t):
        qty = _extract_qty_m2(t)
        text = f"{_qty_prefix(raw_text)}{qty} m² Pflaster verlegt" if qty else "Pflaster verlegt"
        return CanonicalActivity("pflaster_verlegt", text, 102.0, bool(qty))
    if ("gartenmauer" in t or ("mauer" in t and re.search(r"\b(garten|beet|aussenanlage|außenanlage|hof|terrasse)\b", t))) and re.search(
        r"\b(gebaut|erstellt|hochgezogen|gemauert)\b",
        t,
    ):
        qty = _extract_qty_m2(t)
        text = f"{_qty_prefix(raw_text)}{qty} m² Gartenmauer gebaut" if qty else "Gartenmauer gebaut"
        return CanonicalActivity("gartenmauer_gebaut", text, 95.0, bool(qty))
    if "schotter" in t and re.search(r"\b(eingebaut|verarbeitet|eingebracht|verdichtet|rein|verwendet)\b", t):
        qty = _extract_qty_m3(t)
        text = f"{qty} m³ Schotter eingebaut" if qty else "Schotter eingebaut"
        return CanonicalActivity("schotter_eingebaut", text, 82.0, bool(qty))
    if "splitt" in t or "split" in t:
        size = _extract_splitt_size(t)
        if size:
            return CanonicalActivity("splitt_eingebaut", f"Splitt {size} eingebaut", 72.0, False)
        return CanonicalActivity("splitt_eingebaut", "Splitt eingebaut", 70.0, False)
    if "pflanzkübel" in t or "pflanzkuebel" in t:
        if "erde" in t or "substrat" in t or re.search(r"\b(befüllt|befuellt|gefüllt|gefuellt)\b", t):
            return CanonicalActivity("pflanzkuebel_befuellt", "Pflanzkübel mit Erde befüllt", 64.0, False)
    if ("erde" in t or "substrat" in t) and re.search(r"pflanzk(ü|ue)bel", raw_text, flags=re.IGNORECASE):
        return CanonicalActivity("pflanzkuebel_befuellt", "Pflanzkübel mit Erde befüllt", 64.0, False)
    if "pflanzkübel" in t or "pflanzkuebel" in t:
        qty = _extract_piece_count(t)
        if re.search(r"\b(fertiggestellt|gestellt|gesetzt|aufgestellt)\b", t):
            text = f"{_qty_prefix(raw_text)}{qty} Pflanzkübel fertiggestellt" if qty else "Pflanzkübel fertiggestellt"
            return CanonicalActivity("pflanzkuebel_fertiggestellt", text, 66.0, bool(qty))
        text = f"{_qty_prefix(raw_text)}{qty} Pflanzkübel bearbeitet" if qty else "Pflanzkübel bearbeitet"
        return CanonicalActivity("pflanzkuebel_bearbeitet", text, 50.0, bool(qty))

    # Trockenbau
    if ("ständerwerk" in t or "staenderwerk" in t or "cw profil" in t or "uw profil" in t or "profile" in t) and re.search(
        r"\b(gebaut|montiert|gestellt|eingebaut)\b",
        t,
    ):
        return CanonicalActivity("staenderwerk_montiert", "Ständerwerk montiert", 79.0, False)
    if "trockenbauwand" in t or "schließen einer trockenbauwand" in t:
        return CanonicalActivity("trockenbauwand_geschlossen", "Trockenbauwand geschlossen", 96.0, False)
    if _is_trockenbau_fuge_context(t, raw_text=raw_text):
        return CanonicalActivity("trockenbau_fugen_verspachtelt", "Fugen verspachtelt", 62.0, False)
    if "decke" in t and re.search(r"\b(abgehängt|abgehaengt|abgehangen)\b", t):
        return CanonicalActivity("decke_abgehaengt", "Decke abgehängt", 74.0, False)
    if "gipskarton" in t or "rigips" in t:
        if re.search(r"\b(montiert|angebracht|dran gemacht|aufgebaut)\b", t):
            return CanonicalActivity("gipskarton_montiert", "Gipskartonplatten montiert", 90.0, False)
    if "spachtel" in t or re.search(r"\bzugespachtelt\b", t):
        return CanonicalActivity("spachtelarbeiten", "Spachtelarbeiten durchgeführt", 60.0, False)
    if _is_pflaster_fuge_context(t, raw_text=raw_text):
        return CanonicalActivity("pflasterfugen_verfugt", "Pflasterfugen verfugt", 57.0, False)

    # SHK
    if "heizungsanschl" in t or ("heizung" in t and "ansch" in t):
        return CanonicalActivity("heizungsanschluesse_montiert", "Heizungsanschlüsse montiert", 88.0, False)
    if "wasserleitung" in t or "rohrleitung" in t or "rohre gelegt" in t:
        return CanonicalActivity("wasserleitungen_verlegt", "Wasserleitungen verlegt", 87.0, False)
    if ("kg rohre" in t or "kg rohr" in t or "kanalrohr" in t or "entwässerungsrohr" in t) and re.search(
        r"\b(verlegt|gelegt|eingebaut|montiert)\b",
        t,
    ):
        qty = _extract_qty_lfm(t)
        dn = _extract_dn(base, kind="kg")
        if qty and dn:
            text = f"{qty} lfm KG-Rohre DN {dn} verlegt"
        elif qty:
            text = f"{qty} lfm KG-Rohre verlegt"
        elif dn:
            text = f"KG-Rohre DN {dn} verlegt"
        else:
            text = "KG-Rohre verlegt"
        return CanonicalActivity("kg_rohre_verlegt", text, 89.0, bool(qty))
    if re.search(r"\babzweig(e)?\b", t) and re.search(r"\b(eingebaut|gesetzt|montiert|verbaut)\b", t):
        context_probe = f"{t} | {str(raw_text or '').casefold()}"
        if "kg" in context_probe or "kanal" in context_probe:
            return CanonicalActivity("kg_abzweig_eingebaut", "KG-Abzweig eingebaut", 63.0, False)
        if "ht" in context_probe or "abwasser" in context_probe:
            return CanonicalActivity("ht_abzweig_eingebaut", "HT-Abzweig eingebaut", 62.0, False)
        return CanonicalActivity("abzweig_eingebaut", "Abzweig eingebaut", 58.0, False)
    if "fittings" in t:
        return CanonicalActivity("fittings_eingebaut", "Fittings eingebaut", 52.0, False)
    if ("ht rohre" in t or "ht rohr" in t or "innenabflussrohr" in t or "abwasserrohr" in t) and re.search(
        r"\b(verlegt|gelegt|eingebaut|montiert)\b",
        t,
    ):
        qty = _extract_qty_lfm(t)
        dn = _extract_dn(base, kind="ht")
        if qty and dn:
            text = f"{qty} lfm HT-Rohre DN {dn} verlegt"
        elif qty:
            text = f"{qty} lfm HT-Rohre verlegt"
        elif dn:
            text = f"HT-Rohre DN {dn} verlegt"
        else:
            text = "HT-Rohre verlegt"
        return CanonicalActivity("ht_rohre_verlegt", text, 88.5, bool(qty))
    if ("heizkörper" in t or "heizkoerper" in t) and re.search(r"\b(montiert|angebracht|eingebaut)\b", t):
        return CanonicalActivity("heizkoerper_montiert", "Heizkörper montiert", 80.0, False)
    if "fußbodenheizung" in t or "fussbodenheizung" in t:
        if re.search(r"\b(verlegt|eingebaut|installiert)\b", t):
            return CanonicalActivity("fussbodenheizung_verlegt", "Fußbodenheizung verlegt", 81.0, False)
    if ("lüftung" in t or "lueftung" in t or "klima" in t) and re.search(r"\b(installiert|eingebaut|montiert)\b", t):
        return CanonicalActivity("lueftung_klima_installiert", "Lüftungs-/Klimatechnik installiert", 69.0, False)

    # Sanierung
    if "altputz" in t or "putz runter" in t:
        return CanonicalActivity("altputz_entfernt", "Altputz entfernt", 91.0, False)
    if "schimmel" in t:
        return CanonicalActivity("schimmel_beseitigt", "Schimmel beseitigt", 85.0, False)
    if "sanierputz" in t:
        return CanonicalActivity("sanierputz_aufgebracht", "Sanierputz aufgebracht", 92.0, False)
    if "oberputz" in t and re.search(r"\b(aufgetragen|aufgebracht|verarbeitet)\b", t):
        return CanonicalActivity("oberputz_aufgetragen", "Oberputz aufgetragen", 78.0, False)
    if "grundputz" in t and re.search(r"\b(aufgetragen|aufgebracht|verarbeitet)\b", t):
        return CanonicalActivity("grundputz_aufgetragen", "Grundputz aufgetragen", 77.0, False)
    if ("innenputz" in t or "aussenputz" in t or "außenputz" in t) and re.search(r"\b(aufgetragen|aufgebracht|verarbeitet)\b", t):
        if "innenputz" in t:
            return CanonicalActivity("innenputz_aufgetragen", "Innenputz aufgetragen", 76.0, False)
        return CanonicalActivity("aussenputz_aufgetragen", "Außenputz aufgetragen", 76.0, False)
    if re.search(r"\bputz\b", t) and re.search(r"\b(aufgebracht|aufgetragen|verarbeitet)\b", t):
        return CanonicalActivity("putz_aufgebracht", "Putz aufgebracht", 76.0, False)
    if ("fassade" in t or "armierung" in t or "gewebe" in t) and re.search(r"\b(hergestellt|aufgebracht|eingebettet)\b", t):
        return CanonicalActivity("fassadenarmierung", "Fassadenarmierung ausgeführt", 72.0, False)
    if "wdvs" in t and re.search(r"\b(gedämmt|angebracht|montiert|ausgeführt)\b", t):
        return CanonicalActivity("wdvs_ausgefuehrt", "WDVS ausgeführt", 73.0, False)
    if "stuck" in t and re.search(r"\b(montiert|hergestellt|angebracht)\b", t):
        return CanonicalActivity("stuckarbeiten", "Stuckarbeiten durchgeführt", 62.0, False)

    # Hochbau / Tiefbau (breiter Kern)
    if (
        re.search(r"\b(bewehrung|bewehrungsstahl|armierung)\b", t)
        and re.search(r"\b(eingebaut|verlegt|gestellt|verarbeitet|verbaut)\b", t)
    ):
        return CanonicalActivity("bewehrung_eingebaut", "Bewehrung eingebaut", 84.0, False)
    if (
        re.search(r"\b(mauerwerk|poroton|porenbeton|ytong|kalksandstein|ks(?:-stein)?|ziegel|stein)\b", t)
        and re.search(r"\b(gemauert|gebaut|erstellt|gesetzt)\b", t)
        and "gartenmauer" not in t
    ):
        qty = _extract_qty_m2(t)
        text = f"{_qty_prefix(raw_text)}{qty} m² Mauerwerk erstellt" if qty else "Mauerwerk erstellt"
        return CanonicalActivity("mauerwerk_erstellt", text, 84.0, bool(qty))
    if "schalung" in t and re.search(r"\b(erstellt|gestellt|gebaut)\b", t):
        return CanonicalActivity("schalung_erstellt", "Schalung erstellt", 83.0, False)
    if "beton" in t and re.search(r"\b(gegossen|eingebracht|verarbeitet)\b", t):
        qty = _extract_qty_m3(t)
        text = f"{qty} m³ Beton eingebracht" if qty else "Beton eingebracht"
        return CanonicalActivity("beton_eingebracht", text, 86.0, bool(qty))
    if ("aushub" in t or "erdarbeiten" in t) and re.search(r"\b(ausgeführt|durchgeführt|gemacht|erstellt)\b", t):
        return CanonicalActivity("erdarbeiten", "Erdarbeiten durchgeführt", 78.0, False)
    if ("graben" in t or "baugrube" in t or "grube" in t or "gebaggert" in t or "bagger" in t) and re.search(
        r"\b(ausgehoben|erstellt|gezogen|gegraben|gebaggert)\b",
        t,
    ):
        return CanonicalActivity("graben_ausgehoben", "Graben ausgehoben", 79.0, False)
    if ("graben" in t or "gräben" in t or "graeben" in t or "grube" in t or "baugrube" in t) and re.search(
        r"\b(verfüllt|verfuellt|verfüllen|verfuellen|aufgefüllt|aufgefuellt)\b",
        t,
    ):
        return CanonicalActivity("graben_verfuellt", "Graben verfüllt", 77.0, False)
    if ("untergrund" in t or "grube" in t or "baugrube" in t) and re.search(r"\b(verdichtet|verdichtung|verdichten)\b", t):
        return CanonicalActivity("untergrund_verdichtet", "Untergrund verdichtet", 76.5, False)
    if ("drainage" in t or "entwässerung" in t or "entwaesserung" in t) and re.search(r"\b(eingebaut|hergestellt|verlegt)\b", t):
        return CanonicalActivity("drainage_entwaesserung", "Drainage/Entwässerung eingebaut", 75.0, False)
    if ("kanal" in t or "schacht" in t) and re.search(r"\b(angeschlossen|gesetzt|eingebaut|betoniert)\b", t):
        return CanonicalActivity("kanal_schacht", "Kanal-/Schachtarbeiten durchgeführt", 77.0, False)

    catalog_match = match_catalog_activity(t)
    if catalog_match:
        return CanonicalActivity(
            catalog_match.intent,
            catalog_match.text,
            catalog_match.priority,
            _has_any_quantity(t),
        )

    return _fallback_activity_from_chunk(t)


def _is_better(new: CanonicalActivity, old: CanonicalActivity) -> bool:
    n = new.priority + (2.0 if new.has_quantity else 0.0)
    o = old.priority + (2.0 if old.has_quantity else 0.0)
    if n != o:
        return n > o
    return len(new.text) > len(old.text)


def _word_to_number(word: str) -> str | None:
    key = str(word or "").casefold()
    mapping = {
        "ein": "1",
        "eine": "1",
        "eins": "1",
        "zwei": "2",
        "drei": "3",
        "vier": "4",
        "fünf": "5",
        "fuenf": "5",
        "sechs": "6",
        "sieben": "7",
        "acht": "8",
        "neun": "9",
        "zehn": "10",
        "elf": "11",
        "zwölf": "12",
        "zwoelf": "12",
    }
    return mapping.get(key)


def _qty_prefix(raw_text: str) -> str:
    probe = str(raw_text or "").casefold()
    if re.search(r"\b(ca\.?|circa|ungefähr|ungefaehr|etwa|rund)\b", probe, flags=re.IGNORECASE):
        return "ca. "
    return ""


def _fallback_activity_from_chunk(norm_text: str) -> CanonicalActivity | None:
    t = str(norm_text or "").strip()
    if not t:
        return None
    if re.search(r"\b(kundin|kunde)\b.*\b(zufrieden|gesprochen|talk)\b", t):
        return None

    patterns: tuple[tuple[str, str], ...] = (
        (r"\b(.{4,60}?)\s+(verlegt)\b", "verlegt"),
        (r"\b(.{4,60}?)\s+(eingebaut)\b", "eingebaut"),
        (r"\b(.{4,60}?)\s+(montiert)\b", "montiert"),
        (r"\b(.{4,60}?)\s+(gebaut|gemauert|erstellt)\b", "gebaut"),
        (r"\b(.{4,60}?)\s+(entfernt)\b", "entfernt"),
        (r"\b(.{4,60}?)\s+(aufgebracht|aufgetragen)\b", "aufgebracht"),
        (r"\b(.{4,60}?)\s+(verarbeitet)\b", "verarbeitet"),
    )
    for pattern, canon_verb in patterns:
        m = re.search(pattern, t, flags=re.IGNORECASE)
        if not m:
            continue
        obj = re.sub(r"\b(heute|wir|haben|noch|dann|anschließend|anschliessend)\b", " ", m.group(1), flags=re.IGNORECASE)
        obj = re.sub(r"\s+", " ", obj).strip(" ,.;")
        if len(obj) < 4:
            continue
        text = f"{obj[:1].upper()}{obj[1:]} {canon_verb}"
        intent = f"fallback_{re.sub(r'[^a-z0-9]+', '_', text.casefold()).strip('_')}"
        return CanonicalActivity(intent, text, 42.0, bool(re.search(r"\b\d+(?:[.,]\d+)?\b", obj)))
    return None


def _is_fliesen_fuge_context(t: str, *, raw_text: str = "") -> bool:
    if "silikon" in t:
        return False
    if not re.search(r"\b(verfugt|fuge|fugen|zugemacht)\b", t):
        return False
    raw = str(raw_text or "").casefold()
    fliesen_cues = ("fliese", "fliese", "fliesenkleber", "fliesenkleber", "fugenmörtel", "fugenmoertel")
    trockenbau_cues = ("gipskarton", "rigips", "trockenbau", "fugenspachtel", "schnellbauschrauben")
    pflaster_cues = ("pflaster", "splitt", "fuge mit sand", "fugenmaterial")
    if any(c in t for c in trockenbau_cues) or any(c in raw for c in trockenbau_cues):
        return False
    if any(c in t for c in pflaster_cues) or any(c in raw for c in pflaster_cues):
        return False
    return any(c in t for c in fliesen_cues) or any(c in raw for c in fliesen_cues)


def _is_trockenbau_fuge_context(t: str, *, raw_text: str = "") -> bool:
    if not re.search(r"\b(fuge|fugen|gespachtelt|verspachtelt)\b", t):
        return False
    raw = str(raw_text or "").casefold()
    trockenbau_cues = (
        "gipskarton",
        "rigips",
        "trockenbau",
        "fugenspachtel",
        "schnellbauschrauben",
        "decke",
        "ständerwerk",
        "staenderwerk",
        "cw profil",
        "uw profil",
        "dämmung",
        "daemmung",
    )
    return any(c in t for c in trockenbau_cues) or any(c in raw for c in trockenbau_cues)


def _is_pflaster_fuge_context(t: str, *, raw_text: str = "") -> bool:
    if not re.search(r"\b(fuge|fugen|verfugt|verfüllt|verfuellt)\b", t):
        return False
    raw = str(raw_text or "").casefold()
    pflaster_cues = ("pflaster", "splitt", "fugensand")
    return any(c in t for c in pflaster_cues) or any(c in raw for c in pflaster_cues)


def _compact_activity_items(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        t = str(item or "").strip()
        if not t:
            continue
        low = t.casefold()
        if "abgehängte decke montiert" in low and any("decke abgehängt" in x.casefold() for x in out):
            continue
        if low.startswith("decke montiert") and any("decke abgehängt" in x.casefold() for x in out):
            continue
        out.append(t)
    # Wenn für Rand-/Rasenkantensteine sowohl eine generische als auch eine
    # Mengenvariante vorhanden ist, bleibt nur die Mengenvariante.
    has_quantified_edge_stone = any(
        (
            ("randsteine gesetzt" in str(x).casefold() or "rasenkantensteine gesetzt" in str(x).casefold())
            and ("lfm" in str(x).casefold() or "stück" in str(x).casefold() or bool(re.search(r"\b\d+(?:[.,]\d+)?\b", str(x))))
        )
        for x in out
    )
    if not has_quantified_edge_stone:
        return out

    filtered: list[str] = []
    for item in out:
        low = str(item).casefold()
        if "randsteine gesetzt" in low or "rasenkantensteine gesetzt" in low:
            has_qty = "lfm" in low or "stück" in low or bool(re.search(r"\b\d+(?:[.,]\d+)?\b", low))
            if not has_qty:
                continue
        filtered.append(item)
    return filtered

