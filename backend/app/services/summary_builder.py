from __future__ import annotations

import re


_FORBIDDEN_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bdurchführung von\s+", ""),
    (r"\bverarbeitung von\s+", ""),
    (r"\bherstellung von\s+", ""),
    (r"\bfertigstellung von\s+", ""),
    (r"\bwurden verlegung von\s+", "wurden "),
    (r"\bwurden entfernung von\s+", "wurden "),
)


_PROJECT_CLOSURE_PATTERNS: tuple[str, ...] = (
    r"\bbaustelle\b.{0,24}\b(abgeschlossen|fertig(?:gestellt)?|beendet|erledigt|durch)\b",
    r"\bbauvorhaben\b.{0,24}\b(abgeschlossen|fertig(?:gestellt)?|beendet|erledigt)\b",
    r"\bobjekt\b.{0,24}\b(abgeschlossen|fertig(?:gestellt)?|beendet)\b",
    r"\b(wir\s+sind|wir\s+waren|hier\s+sind\s+wir|hier\s+waren\s+wir)\b.{0,20}\bfertig\b",
    r"\bhier\b.{0,24}\b(nicht\s+mehr\s+hin|nicht\s+mehr\s+hinkommen)\b",
    r"\bnicht\s+mehr\s+(hinkommen|hinfahren|anfahren)\b",
    r"\barbeiten?\b.{0,24}\b(abgeschlossen|beendet|durch|erledigt)\b",
)

_DAY_CLOSURE_PATTERNS: tuple[str, ...] = (
    r"\bfür\s+heute\s+fertig\b",
    r"\bfuer\s+heute\s+fertig\b",
    r"\bheute\s+sind\s+wir\s+fertig\b",
    r"\bheute\s+fertig\b",
    r"\bfeierabend\b",
    r"\barbeitstag\b.{0,18}\b(abgeschlossen|beendet)\b",
    r"\btagesarbeit\b.{0,18}\b(abgeschlossen|beendet)\b",
)


def build_deterministic_summary(
    activities: list[str],
    *,
    raw_text: str = "",
    date: str = "",
    project_name: str = "",
) -> str:
    items = [_clean_fragment(x, raw_text=raw_text) for x in activities if str(x).strip()]
    items = [x for x in items if x]
    items = _prune_redundant_fragments(items)
    closure_sentence = _closure_sentence(raw_text)
    if not items:
        if closure_sentence:
            return _prepend_date(closure_sentence, date)
        return "Keine Angabe"

    main = items[0]
    tail = items[1:]
    second_main: str | None = None
    secondaries: list[str] = []
    hidden_count = 0
    if tail:
        if not _is_secondary_fragment(tail[0]):
            second_main = tail[0]
            secondaries = tail[1:7]
            hidden_count = max(0, len(tail) - 1 - len(secondaries))
        else:
            secondaries = tail[:6]
            hidden_count = max(0, len(tail) - len(secondaries))

    first_sentence = _first_sentence(
        main,
        raw_text=raw_text,
        project_name=project_name,
        second_main=second_main,
    )
    text = first_sentence if not secondaries else f"{first_sentence} {_second_sentence(secondaries, hidden_count=hidden_count)}"
    if closure_sentence:
        text = f"{text} {closure_sentence}".strip()
    return _prepend_date(text, date)


def _closure_sentence(raw_text: str) -> str:
    raw = str(raw_text or "").casefold()
    if not raw.strip():
        return ""

    if _matches_any(raw, _PROJECT_CLOSURE_PATTERNS):
        if "bauvorhaben" in raw:
            return "Das Bauvorhaben wurde abgeschlossen."
        if "objekt" in raw:
            return "Das Objekt wurde abgeschlossen."
        return "Die Baustelle wurde abgeschlossen."

    if _matches_any(raw, _DAY_CLOSURE_PATTERNS):
        return "Der Arbeitstag wurde abgeschlossen."

    return ""


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _clean_fragment(value: str, *, raw_text: str = "") -> str:
    out = str(value or "").strip()
    out = re.sub(r"\s+", " ", out)
    out = re.sub(r"^(wir haben heute|wir haben|heute haben wir)\s+", "", out, flags=re.IGNORECASE)
    out = re.sub(r"^heute\s+", "", out, flags=re.IGNORECASE)
    out = re.sub(r"^(danach|anschließend|anschliessend|zum schluss|zum schluß)\s+", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\bim bad\b$", "", out, flags=re.IGNORECASE).strip()
    for pattern, repl in _FORBIDDEN_PATTERNS:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    # Schutz vor rohen Dictatfragmenten wie
    # "den neuen oberputz aufgetragen" -> "Oberputz aufgetragen".
    out = re.sub(
        r"^(den|die|der)\s+(?:neuen|neue|neuer|alten|alte|alter)\s+"
        r"(oberputz|grundputz|innenputz|aussenputz|außenputz|putz)\s+"
        r"(aufgetragen|aufgebracht|verarbeitet)\b",
        lambda m: f"{m.group(2).capitalize()} aufgetragen",
        out,
        flags=re.IGNORECASE,
    )
    out = _apply_quantity_certainty(out, raw_text=raw_text)
    out = _humanize_quantity_phrases(out, raw_text=raw_text)
    out = _inject_putz_qty_from_raw(out, raw_text=raw_text)
    out = re.sub(r"\bherzk(ö|oe)rper\b", "Heizkörper", out, flags=re.IGNORECASE)
    out = re.sub(r"\bmanschete\b", "Manschette", out, flags=re.IGNORECASE)
    # Wiederholte Fragmente aus Whisper-Ketten glätten.
    out = re.sub(
        r"\b(Thermostatventile eingebaut)\s+\1\b",
        r"\1",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(r"\s+", " ", out).strip(" ,.;")
    return out


def _prune_redundant_fragments(items: list[str]) -> list[str]:
    vals = [str(x).strip() for x in items if str(x).strip()]
    if len(vals) < 2:
        return vals
    out: list[str] = []
    lower_vals = [v.casefold() for v in vals]
    for idx, value in enumerate(vals):
        low = lower_vals[idx]
        # Entfernt überlange Mischfragmente, wenn deren Teilaussagen bereits
        # als eigene saubere Tätigkeiten vorhanden sind.
        covered_by_two = 0
        for jdx, other in enumerate(lower_vals):
            if idx == jdx:
                continue
            if other and other in low and other != low:
                covered_by_two += 1
        if covered_by_two >= 2:
            continue
        out.append(value)
    return out


def _first_sentence(main: str, *, raw_text: str, project_name: str, second_main: str | None = None) -> str:
    if second_main and main.casefold() == "trockenbauwand geschlossen":
        prefix = _location_prefix(main, raw_text=raw_text, project_name=project_name).replace("wurden", "wurde")
        return f"{prefix} die Trockenbauwand geschlossen und {second_main}.".replace("  ", " ")

    main_phrase = _normalize_secondary_phrase(main, single_mode=True)
    prefix = _location_prefix(main, raw_text=raw_text, project_name=project_name)
    main_is_singular = _is_singular_secondary(main_phrase)

    if second_main:
        second_phrase = _normalize_secondary_phrase(second_main, single_mode=True)
        second_is_singular = _is_singular_secondary(second_phrase)
        # "und" wirkt natürlicher, wenn ein Singular-Subjekt im Spiel ist.
        connector = "und" if (main_is_singular or second_is_singular) else "sowie"
        if main_is_singular and second_is_singular:
            if main_phrase.casefold().startswith(("der ", "die ", "das ")) and second_phrase.casefold().startswith(
                ("der ", "die ", "das ")
            ):
                prefix = prefix.replace("wurden", "wurde")
        # Bei zwei Subjekten bleibt das Hilfsverb in der Regel im Plural ("wurden").
        return f"{prefix} {main_phrase} {connector} {second_phrase}.".replace("  ", " ")

    if main_is_singular:
        prefix = prefix.replace("wurden", "wurde")
    return f"{prefix} {main_phrase}.".replace("  ", " ")


def _second_sentence(secondaries: list[str], *, hidden_count: int = 0) -> str:
    if not secondaries:
        return ""
    raw_parts = [str(x).strip() for x in secondaries if str(x).strip()]
    parts = [_normalize_secondary_phrase(p) for p in raw_parts]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    style_probe = " | ".join(parts).casefold()
    list_style_terms = (
        "putz",
        "haftgrund",
        "armierung",
        "wdvs",
        "thermostatventil",
        "rücklaufverschraubung",
        "ruecklaufverschraubung",
        "manschette",
        "abzweig",
        "bögen",
        "boegen",
    )
    prefer_list_style = any(term in style_probe for term in list_style_terms)
    # Hochbau-/Rohbau-Kontext: Bei klassischen Rohbau-Begriffen wirkt der
    # gleichfoermige "Zusaetzlich"-Auftakt redundant. "Ausserdem" klingt
    # natuerlicher und vermeidet den Listen-Eindruck.
    rohbau_terms = (
        "schalung",
        "bewehrung",
        "fundament",
        "mauerwerk",
        "beton ",
        "beton.",
        "filigrandecke",
    )
    is_rohbau_context = any(term in style_probe for term in rohbau_terms)
    secondary_intro_one = "Außerdem" if is_rohbau_context else "Zusätzlich"
    secondary_intro_pair = "Außerdem" if is_rohbau_context else "Zusätzlich"
    if len(parts) == 1:
        one = _normalize_secondary_phrase(parts[0], single_mode=True)
        if prefer_list_style:
            sentence = f"Ergänzend: {one}."
            if hidden_count > 0:
                sentence += " Weitere Arbeiten sind in den Tätigkeiten dokumentiert."
            return sentence
        verb = "wurde" if _is_singular_secondary(one) else "wurden"
        sentence = f"{secondary_intro_one} {verb} {one}."
        if hidden_count > 0:
            sentence += " Weitere Arbeiten sind in den Tätigkeiten dokumentiert."
        return sentence
    if prefer_list_style:
        listed = _join_with_und(parts)
        sentence = f"Ergänzend: {listed}."
        if hidden_count > 0:
            sentence += " Weitere Arbeiten sind in den Tätigkeiten dokumentiert."
        return sentence
    if len(parts) == 2:
        sentence = f"{secondary_intro_pair} wurden {parts[0]} und {parts[1]}."
        if hidden_count > 0:
            sentence += " Weitere Arbeiten sind in den Tätigkeiten dokumentiert."
        return sentence

    # Bei drei oder mehr Sekundärarbeiten vermeiden wir die harte Form
    # "wurden Schotter eingebaut, ...". Mit dieser Form klingt es natürlicher.
    listed = _join_with_und(parts)
    sentence = f"Außerdem wurden folgende Arbeiten ausgeführt: {listed}."
    if hidden_count > 0:
        sentence += " Weitere Arbeiten sind in den Tätigkeiten dokumentiert."
    return sentence


def _location_prefix(main: str, *, raw_text: str, project_name: str) -> str:
    probe = f"{raw_text} {main}".casefold()
    if "fliesen" in probe and re.search(r"\b(bad|badezimmer|nasszelle|duschbad|gäste-?wc|gaeste-?wc)\b", probe):
        return "Im Bad wurden"
    return "Auf der Baustelle wurden"


def _prepend_date(summary: str, date: str) -> str:
    d = _format_date_de(date)
    if not d or not summary.strip():
        return summary.strip()
    return f"{d}: {summary.strip()}"


def _format_date_de(value: str) -> str:
    s = str(value or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if not m:
        return s
    return f"{m.group(3)}.{m.group(2)}.{m.group(1)}"


def _inject_putz_qty_from_raw(fragment: str, *, raw_text: str) -> str:
    """Ergänzt fehlende m²-Angaben bei Putzschicht-Tätigkeiten aus dem Rohtext."""
    out = str(fragment or "").strip()
    if not out or re.search(r"\b\d+(?:[.,]\d+)?\s*(?:m²|m2|qm)\b", out, flags=re.IGNORECASE):
        return out
    layer_re = (
        r"(oberputz|unterputz|innenputz|außenputz|aussenputz|grundputz|"
        r"sockelputz|reibputz|kratzputz)"
    )
    if not re.search(layer_re, out, flags=re.IGNORECASE):
        return out
    if not re.search(
        r"\b(aufgetragen|aufgebracht|verarbeitet|geglättet|geglaettet|filziert)\b",
        out,
        flags=re.IGNORECASE,
    ):
        return out
    raw = str(raw_text or "")
    if not raw.strip():
        return out
    m = re.search(
        rf"(\d+(?:[.,]\d+)?)\s*(?:qm)?(?:m²|m2|quadratmeter)\s+{layer_re}\b",
        raw,
        flags=re.IGNORECASE,
    )
    if not m:
        m = re.search(
            rf"(\d+(?:[.,]\d+)?)\s+quadratmeter\s+{layer_re}\b",
            raw,
            flags=re.IGNORECASE,
        )
    if not m:
        return out
    qty = m.group(1)
    prefix = "ca. " if _should_use_approx(raw) else ""

    def _repl(match: re.Match[str]) -> str:
        layer = match.group(1)
        return f"{prefix}{qty} m² {layer[:1].upper()}{layer[1:]}"

    return re.sub(rf"\b({layer_re})\b", _repl, out, count=1, flags=re.IGNORECASE)


def _humanize_quantity_phrases(text: str, *, raw_text: str = "") -> str:
    out = str(text or "")
    if _should_use_approx(raw_text) and not re.search(
        r"\bca\.\s*\d+(?:[.,]\d+)?\s*(m²|m2|qm)\s*fliesen verlegt",
        out,
        flags=re.IGNORECASE,
    ):
        out = re.sub(
            r"(\d+(?:[.,]\d+)?)\s*(m²|m2|qm)\s*fliesen verlegt",
            r"ca. \1 m² Fliesen verlegt",
            out,
            flags=re.IGNORECASE,
        )
    if _should_use_approx(raw_text) and not re.search(
        r"\bca\.\s*\d+(?:[.,]\d+)?\s*(m²|m2|qm)\s*pflaster verlegt",
        out,
        flags=re.IGNORECASE,
    ):
        out = re.sub(
            r"(\d+(?:[.,]\d+)?)\s*(m²|m2|qm)\s*pflaster verlegt",
            r"ca. \1 m² Pflaster verlegt",
            out,
            flags=re.IGNORECASE,
        )
    out = re.sub(
        r"(\d+(?:[.,]\d+)?)\s*(m³|m3)\s*schotter eingebaut",
        r"\1 m³ Schotter eingebaut",
        out,
        flags=re.IGNORECASE,
    )
    return out


def _is_secondary_fragment(fragment: str) -> bool:
    f = str(fragment or "").casefold()
    secondary_terms = ("silikon", "spachtel", "fittings", "splitt", "verfugt")
    return any(t in f for t in secondary_terms)


def _apply_quantity_certainty(text: str, *, raw_text: str) -> str:
    out = str(text or "")
    if _should_use_approx(raw_text):
        return out
    return re.sub(r"\bca\.\s*(?=\d)", "", out, flags=re.IGNORECASE)


def _should_use_approx(raw_text: str) -> bool:
    probe = str(raw_text or "").casefold()
    return bool(
        re.search(
            r"\b(ca\.?|circa|ungefähr|ungefaehr|etwa|rund)\b",
            probe,
            flags=re.IGNORECASE,
        )
    )


_ARTICLE_FOR_SINGLE_MODE: tuple[tuple[str, str], ...] = (
    ("untergrund verdichtet", "der Untergrund verdichtet"),
    ("hecke geschnitten", "die Hecke geschnitten"),
    ("rasen gemäht", "der Rasen gemäht"),
    ("rasen getrimmt", "der Rasen getrimmt"),
    ("rasen verlegt", "der Rasen verlegt"),
    ("unkraut entfernt", "Unkraut entfernt"),
    ("laub entfernt", "Laub entfernt"),
    ("decke abgehängt", "die Decke abgehängt"),
    ("trockenbauwand geschlossen", "die Trockenbauwand geschlossen"),
    ("gartenmauer gebaut", "die Gartenmauer gebaut"),
    ("pergola aufgestellt", "die Pergola aufgestellt"),
    ("pergola/carport aufgestellt", "die Pergola aufgestellt"),
    ("carport aufgestellt", "der Carport aufgestellt"),
    ("terrasse gebaut", "die Terrasse gebaut"),
    ("keramikterrasse verlegt", "die Keramikterrasse verlegt"),
    ("holz-/wpc-terrasse gebaut", "die Holz-/WPC-Terrasse gebaut"),
    ("palisaden gesetzt", "die Palisaden gesetzt"),
    ("fläche mit mulch eingedeckt", "die Fläche mit Mulch eingedeckt"),
    ("rindenmulch eingedeckt", "der Rindenmulch eingedeckt"),
    ("rasen vertikutiert", "der Rasen vertikutiert"),
    ("rasen gedüngt", "der Rasen gedüngt"),
    ("fläche bewässert", "die Fläche bewässert"),
    ("winterdienst durchgeführt", "der Winterdienst durchgeführt"),
    ("geotextil verlegt", "das Geotextil verlegt"),
    ("wc montiert", "das WC montiert"),
    ("waschbecken montiert", "das Waschbecken montiert"),
    ("dusche montiert", "die Dusche montiert"),
    ("armaturen montiert", "die Armaturen montiert"),
    ("druckprüfung durchgeführt", "die Druckprüfung durchgeführt"),
    ("hydraulischer abgleich durchgeführt", "der hydraulische Abgleich durchgeführt"),
    ("nivelliermasse aufgetragen", "die Nivelliermasse aufgetragen"),
    ("bodenablauf eingebaut", "der Bodenablauf eingebaut"),
    ("naturstein verlegt", "der Naturstein verlegt"),
    ("sockelputz aufgetragen", "der Sockelputz aufgetragen"),
    ("reibputz aufgetragen", "der Reibputz aufgetragen"),
    ("kratzputz aufgetragen", "der Kratzputz aufgetragen"),
    ("hausanschluss hergestellt", "der Hausanschluss hergestellt"),
    ("asphalt eingebaut", "der Asphalt eingebaut"),
    ("zaun montiert", "der Zaun montiert"),
    ("zaun/sichtschutz montiert", "der Zaun montiert"),
    ("graben ausgehoben", "der Graben ausgehoben"),
    ("graben verfüllt", "der Graben verfüllt"),
    ("fundament erstellt", "das Fundament erstellt"),
    ("akustikdecke eingebaut", "die Akustikdecke eingebaut"),
    ("brandschutzwand hergestellt", "die Brandschutzwand hergestellt"),
    ("revisionsklappe eingebaut", "die Revisionsklappe eingebaut"),
    ("schalung erstellt", "die Schalung erstellt"),
    ("filigrandecke montiert", "die Filigrandecke montiert"),
    ("fußbodenheizung verlegt", "die Fußbodenheizung verlegt"),
    ("fussbodenheizung verlegt", "die Fußbodenheizung verlegt"),
    ("wärmepumpe installiert", "die Wärmepumpe installiert"),
    ("waermepumpe installiert", "die Wärmepumpe installiert"),
    ("ständerwerk montiert", "das Ständerwerk montiert"),
    ("staenderwerk montiert", "das Ständerwerk montiert"),
    ("dämmung eingebaut", "die Dämmung eingebaut"),
    ("daemmung eingebaut", "die Dämmung eingebaut"),
    ("drainage/entwässerung eingebaut", "die Drainage eingebaut"),
)


def _normalize_secondary_phrase(text: str, *, single_mode: bool = False) -> str:
    out = str(text or "").strip()
    if not out:
        return ""
    low = out.casefold()
    for needle, replacement in _ARTICLE_FOR_SINGLE_MODE:
        if low == needle:
            return replacement
    return out


_SINGULAR_FIRST_WORDS: tuple[str, ...] = (
    "splitt",
    "schotter",
    "untergrund",
    "aushub",
    "sanierputz",
    "beton",
    "hecke",
    "fliesenkleber",
    "silikon",
    "grundierung",
    "abdichtung",
    "putz",
    "innenputz",
    "aussenputz",
    "außenputz",
    "oberputz",
    "grundputz",
    "wdvs",
    "fassadenarmierung",
    "gartenmauer",
    "rasen",
    "mauerwerk",
    "schalung",
    "bewehrung",
    "fundament",
    "filigrandecke",
    "altputz",
    "schimmel",
    "decke",
    "akustikdecke",
    "brandschutzwand",
    "revisionsklappe",
    "trockenbauwand",
    "fußbodenheizung",
    "fussbodenheizung",
    "wärmepumpe",
    "waermepumpe",
    "gastherme",
    "heizkessel",
    "graben",
    "verbau",
    "spundwand",
    "pergola",
    "carport",
    "gartenhaus",
    "terrasse",
    "keramikterrasse",
    "holz-/wpc-terrasse",
    "palisaden",
    "mulch",
    "rindenmulch",
    "vertikutieren",
    "vertikutiert",
    "dünger",
    "duenger",
    "bewässerung",
    "winterdienst",
    "geotextil",
    "wc",
    "waschbecken",
    "dusche",
    "armaturen",
    "druckprüfung",
    "druckpruefung",
    "hydraulischer",
    "abgleich",
    "nivelliermasse",
    "bodenablauf",
    "naturstein",
    "sockelputz",
    "reibputz",
    "kratzputz",
    "hausanschluss",
    "zaun",
    "sichtschutz",
    "teich",
    "bachlauf",
    "wasserspiel",
    "drainage",
    "entwässerung",
    "entwaesserung",
    "kanal",
    "schacht",
    "asphalt",
    "fläche",
    "flaeche",
    "gelände",
    "gelaende",
    "ständerwerk",
    "staenderwerk",
    "dämmung",
    "daemmung",
)


def _is_singular_secondary(fragment: str) -> bool:
    f = str(fragment or "").casefold().strip()
    if not f:
        return False
    # Mengenangaben (z.B. "50 m² Pflaster verlegt", "3 m³ Schotter eingebaut") ->
    # Plural-Hilfsverb ("wurden"), weil die Mengenangabe als Plural-Subjekt fungiert.
    if re.search(r"\b\d+(?:[.,]\d+)?\s*(m²|m2|qm|m³|m3|lfm|stück|stk|kg|t)\b", f):
        return False
    # Artikel-Anfang (z.B. "die Hecke ...", "der Untergrund ...") -> Singular,
    # außer es handelt sich um klar plurale Substantive ("die Fliesen", "die Pflanzen").
    if re.match(r"^(der|die|das)\s+", f):
        plural_after_article = ("die fliesen", "die pflanzen", "die rohre", "die anschlüsse", "die anschluesse", "die platten")
        if not any(f.startswith(p) for p in plural_after_article):
            return True
    first_word = f.split(" ", 1)[0] if " " in f else f
    if first_word in _SINGULAR_FIRST_WORDS:
        return True
    return False


def _join_with_und(parts: list[str]) -> str:
    vals = [str(x).strip() for x in parts if str(x).strip()]
    if not vals:
        return ""
    if len(vals) == 1:
        return vals[0]
    if len(vals) == 2:
        return f"{vals[0]} und {vals[1]}"
    return f"{', '.join(vals[:-1])} und {vals[-1]}"
