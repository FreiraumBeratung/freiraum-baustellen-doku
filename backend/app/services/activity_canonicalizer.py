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

    ordered = sorted(
        selected.values(),
        key=lambda x: x.priority + (4.0 if x.has_quantity else 0.0),
        reverse=True,
    )
    return _compact_activity_items([x.text for x in ordered])


def collect_unmatched_chunks(raw_text: str) -> list[str]:
    """Hebel 2 (Diagnose): liefert Chunks aus dem Rohtext, die zu KEINER Taetigkeit
    kanonisiert werden konnten, aber wie ein Arbeitsversuch aussehen.

    Rein lesend — beeinflusst die Strukturierung in keiner Weise. Dient nur dem
    Lernen aus echtem Sprachmaterial (Telemetrie).
    """
    text = str(raw_text or "").strip()
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for chunk in _split_chunks(text):
        c = str(chunk or "").strip()
        if not c:
            continue
        if _canonicalize_chunk(c, raw_text=text) is not None:
            continue
        if not _looks_like_work_attempt(c):
            continue
        key = c.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _looks_like_work_attempt(chunk: str) -> bool:
    words = [w for w in re.split(r"\s+", str(chunk or "").strip()) if w]
    if len(words) < 3:
        return False
    # mind. ein laengeres alphabetisches Wort (kein reines Datum/Zahlengebilde)
    if not any(re.search(r"[a-zäöüß]{4,}", w.lower()) for w in words):
        return False
    # Bias auf verpasste Taetigkeiten: Mengenangabe ODER verbartiges Token vorhanden.
    if re.search(r"\d", chunk):
        return True
    if re.search(r"\b\w{3,}(?:t|en|iert|elt)\b", chunk, flags=re.IGNORECASE):
        return True
    return False


def _split_chunks(text: str) -> list[str]:
    t = str(text or "").strip()
    if not t:
        return []
    # Whisper-Klebung vor dem strukturellen Splitten aufloesen, damit Verb-Uebergaenge
    # (z.B. "ausgeschachtet die KG-Rohre verlegt") sauber getrennt werden.
    t = re.sub(r"\baus\s+geschachtet\b", "ausgeschachtet", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgeotextiel\b", "geotextil", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgeo\s+textil\b", "geotextil", t, flags=re.IGNORECASE)
    t = re.sub(r"\bpflanz\s+k(ü|ue)bel\b", "pflanzkübel", t, flags=re.IGNORECASE)
    t = re.sub(r"\basphalt\s+iert\b", "asphaltiert", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+schnitten\b", "geschnitten", t, flags=re.IGNORECASE)
    t = re.sub(r"\bverti\s+kutiert\b", "vertikutiert", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+d(ü|ue|u)ngt\b", "gedüngt", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(hecke\s+(?:geschnitten|zurückgeschnitten|zurueckgeschnitten|getrimmt))\s+(rindenmulch|mulch)\b",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(rindenmulch|mulch)\s+eingedeckt\s+(?=kunde|problem|offen|bauherr|bauleitung|auftraggeber)",
        r"\1 eingedeckt. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b\d+(?:[.,]\d+)?\s*stunden\s+radlader\s+",
        "radlader. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bradlader\s+(?=mulch|rindenmulch|schotter)\b", "radlader. ", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(wpc\s+terrasse|terrasse)\s+gebaut\s+(?=und\s+)?(?=\d|zwei|drei|ein|pflanz)",
        r"\1 gebaut. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(pflanzkübel\s+mit\s+erde\s+befüllt|pflanzkübel\s+mit\s+erde\s+befuellt)\s+und\s+",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bka\s+ga\s+rohre?\b", "kg rohre", t, flags=re.IGNORECASE)
    t = re.sub(r"\berd\s+aushub\b", "erdaushub", t, flags=re.IGNORECASE)
    t = re.sub(r"\berd\s+arbeiten\b", "erdarbeiten", t, flags=re.IGNORECASE)
    t = re.sub(r"\bbau\s+grube\b", "baugrube", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfrost\s+schutz\b", "frostschutz", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfss\b", "frostschutz", t, flags=re.IGNORECASE)
    t = re.sub(r"\bsts\b", "schottertragschicht", t, flags=re.IGNORECASE)
    t = re.sub(r"\bhoch\s+bord\b", "hochbord", t, flags=re.IGNORECASE)
    t = re.sub(r"\btief\s+bord\b", "tiefbord", t, flags=re.IGNORECASE)
    t = re.sub(r"\brinnen\s+steine\b", "rinnensteine", t, flags=re.IGNORECASE)
    t = re.sub(r"\bschot\s+ter\s+trag\s+schicht\b", "schottertragschicht", t, flags=re.IGNORECASE)
    t = re.sub(r"\bsplit\s+schicht\b", "splittschicht", t, flags=re.IGNORECASE)
    t = re.sub(r"\bhaus\s+anschluss\b", "hausanschluss", t, flags=re.IGNORECASE)
    t = re.sub(r"\bleitung\s+strasse\b", "leitungstrasse", t, flags=re.IGNORECASE)
    t = re.sub(r"\bleitung\s+straße\b", "leitungstrasse", t, flags=re.IGNORECASE)
    t = re.sub(r"\bent\s+w(ä|ae)sserung\b", "entwässerung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+bau\b", "verbau", t, flags=re.IGNORECASE)
    t = re.sub(r"\bdra\s+inage\b", "drainage", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+f(ü|ue|u)llt\b", "verfüllt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+dichtet\b", "verdichtet", t, flags=re.IGNORECASE)
    t = re.sub(r"\baus\s+ge\s+hoben\b", "ausgehoben", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfilter\s+vlies\b", "filtervlies", t, flags=re.IGNORECASE)
    t = re.sub(r"\bka\s+ga\s+b(ö|oe)gen\b", "kg bögen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bka\s+ga\s+abzweig\b", "kg abzweig", t, flags=re.IGNORECASE)
    t = re.sub(r"\bkubik\s+meter\b", "kubikmeter", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(baugrube|graben)\s+ausgehoben\s+verbau\b",
        r"\1 ausgehoben. verbau",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bverbau\s+gesetzt\s+(entw|drainage)\b",
        r"verbau gesetzt. \1",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\berdaushub\s+gemacht\s+(?=\d|ka\s+ga|kg|lauf|zwei|drei|vier|fünf|fuenf|schotter|splittschicht)",
        r"erdaushub gemacht. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b((?:\d+\s+)?(?:laufende\s+meter\s+)?(?:kg\s+rohre|kg-rohre)(?:\s+dn\s+\d+)?)\s+verlegt\s+(splittschicht|splitt|schotter|sand|frostschutz)\b",
        r"\1 verlegt. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bkanal\s+angeschlossen\s+(drainage|entw)",
        r"kanal angeschlossen. \1",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(drainage\s+verlegt)\s+leitungstrasse\b",
        r"\1. leitungstrasse",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bgraben\s+ausgehoben\s+(drainage|frostschutz|sand|hausanschluss)\b",
        r"graben ausgehoben. \1",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\berdarbeiten\s+durchgef(ü|ue|u)hrt\s+baugrube\b",
        r"erdarbeiten durchgeführt. baugrube",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\berdaushub\s+gemacht\s+(schotter|splittschicht)\b",
        r"erdaushub gemacht. \1",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(sand|schotter|splitt|frostschutz)\s+eingebaut\s+und\s+verdichtet\b",
        r"\1 eingebaut. verdichtet",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\ban\s+geschlossen\b", "angeschlossen", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\bgraben\s+gezogen\s+(?=kg|ka\s+ga)",
        r"graben gezogen. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bkg\s+b(ö|oe)gen\s+und\s+(?:einen?\s+)?kg\s+abzweig\b",
        r"kg bögen. kg abzweig",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(kg\s+rohre|kg-rohre)\s+(gelegt|verlegt)\s+(?=(?:zwei|drei|vier|einen?|ein)\s+kg\s+b)",
        r"\1 \2. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bleitungstrasse\s+hergestellt\s+(?=\d|ka\s+ga|kg|lauf|vier|drei|zwei)",
        r"leitungstrasse hergestellt. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(kg\s+rohre|kg-rohre)\s+verlegt\s+graben\b",
        r"\1 verlegt. graben",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bbe\s+wehrungs\s+stahl\b", "bewehrungsstahl", t, flags=re.IGNORECASE)
    t = re.sub(r"\bbe\s+wehrung\b", "bewehrung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bbewehrungs\s+stahl\b", "bewehrungsstahl", t, flags=re.IGNORECASE)
    # Hochbau Whisper-Klebung (vor strukturellen Splits)
    t = re.sub(r"\bschal\s+ung\b", "schalung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfiligran\s+decke\b", "filigrandecke", t, flags=re.IGNORECASE)
    t = re.sub(r"\bbeton\s+decke\b", "betondecke", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfundament\s+platte\b", "fundamentplatte", t, flags=re.IGNORECASE)
    t = re.sub(r"\bquadrat\s+meter\b", "quadratmeter", t, flags=re.IGNORECASE)
    t = re.sub(r"\bkalk\s+sandstein\b", "kalksandstein", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+gossen\b", "gegossen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+baut\b", "verbaut", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+schalt\b", "geschalt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+bunden\b", "gebunden", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b((?:bewehrungs?stahl|bewehrung|armierung)\s+(?:verbaut|eingebaut|verlegt|gestellt|gebunden))\s+(?=(?:\d+|(?:ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwoelf)\s+)?\s*(?:kubik|m³|m3|kubikmeter)\s*beton)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b((?:gebunden|verbaut|eingebaut|verlegt|gestellt))\s+(?=schalung\b)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(schalung\s+(?:aufgestellt|gestellt|erstellt|gebaut|gemacht))\s+(?=betondecke\b)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b((?:\d+|(?:zehn|elf|zwölf|zwoelf|vierzehn|fünfzehn|fuenfzehn|acht|neun|sechs|sieben)\s+)?(?:kubik|kubikmeter|m³|m3)\s*beton\s+(?:gegossen|eingebracht))\s+und\s+(schalung\b)",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(hochgemauert|gemauert|hochgezogen)\s+(?=(?:bewehrungs?stahl|bewehrung|armierung)\b)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(geschalt)\s+(?=\d|(?:\d+[,.]\d+)?er\s+(?:poroton|porit|ytong|kalksandstein))",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    # SHK Whisper-Klebung und Ketten-Splits
    t = re.sub(r"\bfuss\s+boden\s+heizung\b", "fußbodenheizung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+legt\b", "verlegt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bein\s+gebaut\b", "eingebaut", t, flags=re.IGNORECASE)
    t = re.sub(r"\blauf\s+ende\s+meter\b", "laufende meter", t, flags=re.IGNORECASE)
    t = re.sub(r"\bwasser\s+leitungen\b", "wasserleitungen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bwasch\s+becken\b", "waschbecken", t, flags=re.IGNORECASE)
    t = re.sub(r"\bhydraul\s+ischen\b", "hydraulischen", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(wärme|waerme)\s+pumpe\b", "wärmepumpe", t, flags=re.IGNORECASE)
    t = re.sub(r"\bheizungs\s+anschl(ü|ue|u)sse\b", "heizungsanschlüsse", t, flags=re.IGNORECASE)
    t = re.sub(r"\bheiz\s+kreis\s+verteiler\b", "heizkreisverteiler", t, flags=re.IGNORECASE)
    t = re.sub(r"\bmon\s+tiert\b", "montiert", t, flags=re.IGNORECASE)
    t = re.sub(r"\bin\s+stalliert\b", "installiert", t, flags=re.IGNORECASE)
    t = re.sub(r"\bdurch\s+ge\s+f(ü|ue|u)hrt\b", "durchgeführt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bdruckprobe\b", "druckprüfung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bht\s+manschette\b", "ht-manschette", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(kg[\s-]?rohre?(?:\s+dn\s+\d+)?\s+(?:verlegt|gelegt|ver\s+legt))\s+(?=ht[\s-]?rohr)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(verlegt|gelegt|ver\s+legt)\s+(?=ht[\s-]?manschette\b)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(verlegt|gelegt|ver\s+legt)\s+(?=ht[\s-]?b(ö|oe)gen|ht[\s-]?abzweig|kg[\s-]?b(ö|oe)gen|kg[\s-]?abzweig)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(heizkörper|heizkoerper)\s+montiert\s+(?=wc\b)",
        r"\1 montiert. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(wc\s+(?:montiert|gesetzt))\s+(?=wasch[\s-]?becken)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(waschbecken\s+(?:montiert|gesetzt))\s+(?=druck)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(fußbodenheizung|fussbodenheizung)\s+verlegt\s+(?=heizkreisverteiler|heizungs)",
        r"\1 verlegt. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(fußbodenheizung|fussbodenheizung)\s+verlegt\s+(?=hydraul)",
        r"\1 verlegt. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(wärmepumpe|waermepumpe)\s+installiert\s+(?=heizungs)",
        r"\1 installiert. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(dusche\s+montiert)\s+(?=armatur)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(armaturen\s+montiert)\s+(?=druck)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b((?:ht|kg)[\s-]?b(ö|oe)gen\s+(?:eingebaut|ein\s+gebaut|gesetzt))\s+(?=(?:ht|kg)[\s-]?abzweig)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(heizkörper\s+montiert)\s+(?=druck)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bfuss\s+boden\s+heizung\b", "fußbodenheizung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgips\s+karton\s+platten\b", "gipskartonplatten", t, flags=re.IGNORECASE)
    t = re.sub(r"\bnivellier\s+masse\b", "nivelliermasse", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgross\s+format\s+fliesen\b", "großformatfliesen", t, flags=re.IGNORECASE)
    t = re.sub(r"\blauf\s+ende\s+meter\b", "laufende meter", t, flags=re.IGNORECASE)
    t = re.sub(r"\brasen\s+kanten\s+steine\b", "rasenkantensteine", t, flags=re.IGNORECASE)
    t = re.sub(r"\bdruck\s+pr(ü|ue|u)fung\b", "druckprüfung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bsilikon\s+fugen\b", "silikonfugen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bputz\s+runter\b", "putz entfernt", t, flags=re.IGNORECASE)
    t = re.sub(r"\baltputz\s+runter\b", "altputz entfernt", t, flags=re.IGNORECASE)
    t = re.sub(r"\barm\s+ie\s+rung\b", "armierung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bw\s+d\s+v\s+s\b", "wdvs", t, flags=re.IGNORECASE)
    t = re.sub(r"\bschim\s+mel\b", "schimmel", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+schliffen\b", "geschliffen", t, flags=re.IGNORECASE)
    t = re.sub(r"\ban\s+ge\s+schliffen\b", "angeschliffen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bein\s+gebettet\b", "eingebettet", t, flags=re.IGNORECASE)
    t = re.sub(r"\bein\s+gebaut\b", "eingebaut", t, flags=re.IGNORECASE)
    t = re.sub(r"\bauf\s+getragen\b", "aufgetragen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bauf\s+gebracht\b", "aufgebracht", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+daemmt\b", "gedämmt", t, flags=re.IGNORECASE)
    t = re.sub(r"\ban\s+geklebt\b", "angeklebt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfas\s+sade\b", "fassade", t, flags=re.IGNORECASE)
    t = re.sub(r"\bsanier\s+putz\b", "sanierputz", t, flags=re.IGNORECASE)
    t = re.sub(r"\breib\s+putz\b", "reibputz", t, flags=re.IGNORECASE)
    t = re.sub(r"\bkratz\s+putz\b", "kratzputz", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+sims\b", "gesims", t, flags=re.IGNORECASE)
    t = re.sub(r"\bputz\s+ab\s*getragen\b", "putz abgetragen", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(wdvs(?:\s+(?:platten|komplett))?)\s+(angeklebt|montiert|gedämmt|gedaemmt)\s+(armierungs(?:gewebe)?|gewebe|armierung)\b",
        r"\1 \2. \3",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(fassade\s+gedämmt|fassade\s+gedaemmt)\s+(gewebe|armierung|armierungs)\b",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(gewebe\s+reingemacht|gewebe\s+eingebettet|armierungs\s+gewebe\s+eingebettet)\s+(?=außen|aussen|innen|ober|grund|unter|sockel|reib|kratz)",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\breibputz\s+aufgetragen\s+(?=außen|aussen|innen)",
        r"reibputz aufgetragen. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(sockelputz|innenputz|grundputz)\s+(aufgetragen|verarbeitet|gemacht)\s+(?=kunde|problem|offen|bauherr|bauleitung)",
        r"\1 \2. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bkratzputz\s+aufgetragen\s+reibputz\s+nachgearbeitet\b",
        r"kratzputz aufgetragen. reibputz nachgearbeitet",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bputz\s+abgetragen\s+(wand|decke|fassade)\b",
        r"putz abgetragen. \1",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(schimmel\s+weg\s+gemacht|schimmel\s+beseitigt)\s+sanierputz\b",
        r"\1. sanierputz",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(eingebettet)\s+reibputz\b",
        r"\1. reibputz",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(sockelputz\s+aufgetragen|sockelputz\s+gemacht)\s+reibputz\b",
        r"\1. reibputz",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bkratzputz\s+aufgetragen\s+reibputz\b",
        r"kratzputz aufgetragen. reibputz",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(geschliffen|angeschliffen)\s+grundierung\b",
        r"\1. grundierung",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(geschliffen|angeschliffen)\s+grundiert\b",
        r"\1. grundiert",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\becke\s+geschnitten\b", "hecke geschnitten", t, flags=re.IGNORECASE)
    t = re.sub(r"\becke\s+(zurückgeschnitten|zurueckgeschnitten|getrimmt)\b", r"hecke \1", t, flags=re.IGNORECASE)
    t = re.sub(r"\bheiz\s*k(ö|oe)rper\b", "heizkörper", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+fugt\b", "verfugt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+spachtelt\b", "verspachtelt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bschot\s+ter\b", "schotter", t, flags=re.IGNORECASE)
    t = re.sub(r"\bunter\s+grund\b", "untergrund", t, flags=re.IGNORECASE)
    t = re.sub(r"\broll\s+rasen\b", "rollrasen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bstelz\s+lager\b", "stelzlager", t, flags=re.IGNORECASE)
    t = re.sub(r"\bwinter\s+dienst\b", "winterdienst", t, flags=re.IGNORECASE)
    t = re.sub(r"\bent\s+w(ä|ae)sserung\b", "entwässerung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bporo\s+ton\b", "poroton", t, flags=re.IGNORECASE)
    t = re.sub(r"\bka\s+nal\b", "kanal", t, flags=re.IGNORECASE)
    t = re.sub(r"\bpla\s+num\b", "planum", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(verlegt|gelegt)\s+(splittschicht|splitt|sand|frostschutz)\b",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(verlegt|gelegt)\s+(leitungstrasse|leitungs-?trasse|trasse)\b",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bdurch gemacht\s+schalung\b", "durch gemacht. schalung", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(erdarbeiten|erdaushub)\s+gemacht\s+(schalung|bewehrung|beton|fundament)\b",
        r"\1 gemacht. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bverfugt\s+ab\b", "verfugt. ab", t, flags=re.IGNORECASE)
    t = re.sub(r"\bab\s+dichtung\b", "abdichtung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgips\s+karton\b", "gipskarton", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfliesen\s+kleber\b", "fliesenkleber", t, flags=re.IGNORECASE)
    t = re.sub(r"\bflex\s+kleber\b", "flexkleber", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgrund\s+ie\s+rung\b", "grundierung", t, flags=re.IGNORECASE)
    t = re.sub(r"\bboden\s+ablauf\b", "bodenablauf", t, flags=re.IGNORECASE)
    t = re.sub(r"\bdusch\s+rinne\b", "duschrinne", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfein\s+steinzeug\b", "feinsteinzeug", t, flags=re.IGNORECASE)
    t = re.sub(r"\bwand\s+fliesen\b", "wandfliesen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bboden\s+fliesen\b", "bodenfliesen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bmosaik\s+fliesen\b", "mosaikfliesen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+legt\b", "verlegt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+fugt\b", "verfugt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+klebt\b", "geklebt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bauf\s+gezogen\b", "aufgezogen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bauf\s+getragen\b", "aufgetragen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bsilikon\s+iert\b", "silikoniert", t, flags=re.IGNORECASE)
    t = re.sub(r"\bverfugt\s+silikon\b", "verfugt. silikon", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(repariert|ausgetauscht|erneuert)\s+(fuge|fugen)\b",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(ausgetauscht|repariert|erneuert)\s+verfugt\b",
        r"\1. verfugt",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(verlegt|gelegt|gesetzt|geklebt)\s+(?:\w+\s+){0,3}verfugt\b",
        r"\1. verfugt",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bri\s+gips\b", "rigips", t, flags=re.IGNORECASE)
    t = re.sub(r"\bri\s+gips\s+platten\b", "rigips platten", t, flags=re.IGNORECASE)
    t = re.sub(r"\brigipsplatten\b", "rigips platten", t, flags=re.IGNORECASE)
    t = re.sub(r"\bknauf[\s-]?platten\b", "gipskartonplatten", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgk[\s-]?platten\b", "gipskartonplatten", t, flags=re.IGNORECASE)
    t = re.sub(r"\bakustik\s+decke\b", "akustikdecke", t, flags=re.IGNORECASE)
    t = re.sub(r"\brevision\s+sklappe\b", "revisionsklappe", t, flags=re.IGNORECASE)
    t = re.sub(r"\bbrand\s+schutz\s+wand\b", "brandschutzwand", t, flags=re.IGNORECASE)
    t = re.sub(r"\bbrand\s+schutz\s+platten\b", "brandschutzplatten", t, flags=re.IGNORECASE)
    t = re.sub(r"\btrocken\s+bau\s+wand\b", "trockenbauwand", t, flags=re.IGNORECASE)
    t = re.sub(r"\bmineral\s+wolle\b", "mineralwolle", t, flags=re.IGNORECASE)
    t = re.sub(r"\bstein\s+wolle\b", "steinwolle", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+schlossen\b", "geschlossen", t, flags=re.IGNORECASE)
    t = re.sub(r"\bnachzu\s+gemacht\b", "nachgespachtelt", t, flags=re.IGNORECASE)
    t = re.sub(r"\babhangdecke\b", "decke abgehängt", t, flags=re.IGNORECASE)
    t = re.sub(r"\babhang\s+decke\b", "decke abgehängt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bbe\s+plankt\b", "beplankt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfestgemacht\b", "festgeschraubt", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(ständerwerk|staenderwerk)\s+montiert\s+(steinwolle|mineralwolle|dämmung|daemmung)\b",
        r"\1 montiert. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(profile|ständerwerksprofile|staenderwerksprofile)\s+festgeschraubt\s+(mineralwolle|steinwolle|dämmung|daemmung)\b",
        r"\1 festgeschraubt. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(hergestellt|eingebaut|montiert)\s+(akustikdecke|akustik\s+decke|revisionsklappe|revision\s+sklappe)\b",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bverspachtelt\s+brandschutz\b", "verspachtelt. brandschutz", t, flags=re.IGNORECASE)
    t = re.sub(r"\brein\s+fugen\b", "rein. fugen", t, flags=re.IGNORECASE)
    t = re.sub(r"\baufgebaut\s+beide\s+seiten\s+beplankt\b", "aufgebaut. beide seiten beplankt", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(eingebaut|eingesetzt|reingepackt|reingemacht)\s+(trockenbauwand|schallschutz)\b",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bbeplankt\s+(mineralwolle|steinwolle|dämmung|daemmung)\b", r"beplankt. \1", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\bbeide\s+seiten\s+beplankt\s+(mineralwolle|steinwolle|dämmung|daemmung)\b",
        r"beide seiten beplankt. \1",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(geschraubt|montiert|festgeschraubt)\s+(mineralwolle|steinwolle|dämmung|daemmung)\b",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(profilen?|profile)\s+montiert\s+(steinwolle|mineralwolle|dämmung|daemmung)\b",
        r"\1 montiert. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(mineralwolle|steinwolle|dämmung|daemmung)(?:\s+\w+){0,3}\s+(rigips|gipskarton)\s+montiert\b",
        r"\1. \2 montiert",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bfugen\s+zu\s+gemacht\b", ". fugen zu gemacht", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(fugen\s+zu\s+gemacht|fugen\s+verspachtelt|fugen\s+nachgespachtelt|nachgespachtelt)\s+decke\b",
        r"\1. decke",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(fugen\s+(?:zu\s+gemacht|verspachtelt|nachgespachtelt))\s+(revisionsklappe)\b",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(runtergehängt|runtergehaengt|abgehängt|abgehaengt)\s+brandschutz",
        r"\1. brandschutz",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(gesetzt|montiert)\s+(dämmung|daemmung|mineralwolle|steinwolle)\s+eingebaut\b",
        r"\1. \2 eingebaut",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\beingebaut\s+beidseitig\s+(rigips|gipskarton)\s+montiert\b",
        r"eingebaut. \1 montiert",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bfugen\s+zu\s+gemacht\s+brandschutz\b", "fugen zu gemacht. brandschutz", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(verspachtelt|nachgespachtelt)\s+spachtelarbeiten\b",
        r"\1. spachtelarbeiten",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bplatten\s+raus\b", "platten raus.", t, flags=re.IGNORECASE)
    t = re.sub(r"\bstaender\s+werk\b", "staenderwerk", t, flags=re.IGNORECASE)
    t = re.sub(r"\bstein\s+wolle\b", "steinwolle", t, flags=re.IGNORECASE)
    t = re.sub(r"\babge\s+haengt\b", "abgehängt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+schraubt\b", "verschraubt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bver\s+legt\b", "verlegt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bge\s+schraubt\b", "geschraubt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfugen\s+spachtel\b", "fugenspachtel", t, flags=re.IGNORECASE)
    t = re.sub(r"\bpro\s+file\b", "profile", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfestfest\s+gemacht\b", "festgeschraubt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bfest\s+gemacht\b", "geschraubt", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(\d+)\s+meter\s+kg\b(?!\s*rohr)", r"\1 meter kg rohre", t, flags=re.IGNORECASE)
    t = re.sub(r"\babdichtung im duschbereich\b", "abdichtung im duschbereich. ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bnach dem kundengespr(ä|ae)ch\b", ". nach dem kundengespräch", t, flags=re.IGNORECASE)
    t = re.sub(r"\boffen bleibt\b", ". offen bleibt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bproblem war\b", ". problem war", t, flags=re.IGNORECASE)
    t = re.sub(r"\btelefoniert\b", ". telefoniert", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(wand|decke|fassade)\s+(angeschliffen|geschliffen)\b",
        r"\1 \2. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bgrundierung\s+drauf\b", "grundierung drauf. ", t, flags=re.IGNORECASE)
    t = re.sub(r"\beingebettet\b", "eingebettet. ", t, flags=re.IGNORECASE)
    t = re.sub(r"\berdaushub\s+gemacht\b", "erdaushub gemacht. ", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(unter|ober|grund|sanier|alt|innen|sockel|reib|kratz)\s+putz\b",
        r"\1putz",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"(\bunterputz\b[^.]{0,80})\b(oberputz\s+(?:aufgetragen|aufgebracht|verarbeitet|gemacht|gezogen|aufgezogen|glatt))\b",
        r"\1. \2",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"[;!?]", ".", t)
    t = re.sub(r"\bwir haben\b", ".", t, flags=re.IGNORECASE)
    t = re.sub(r"\bhaben wir\b", ".", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(?:dann noch|dann|denn|danach|anschließend|anschliessend|sowie|und dann|zwischendurch)\b",
        ".",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bdabei\b", ".", t, flags=re.IGNORECASE)
    # Whisper-Verhoerer: "um" steht haeufig faelschlich fuer "und" direkt vor
    # einer Mengenangabe (z.B. "verlegt um 4 Kubik Beton eingebracht").
    t = re.sub(
        r"\bum\s+(?=\d+(?:[.,]\d+)?\s*(?:kubik|kubikmeter|m³|m3|m²|m2|qm|tonnen?|kg|liter|stück|st))",
        ". ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bfür den untergrund\b", ".", t, flags=re.IGNORECASE)
    t = re.sub(r"\bden graben\b", ". den graben", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(asphaltiert|eingebracht|eingebaut)\s+mit\b",
        r"\1. mit",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bleitungstrasse hergestellt\s+hausanschluss",
        r"leitungstrasse hergestellt. hausanschluss",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(frostschutz|fss)\s+und\s+(schottertragschicht|sts)\s+hergestellt\b",
        r"frostschutz hergestellt. schottertragschicht hergestellt",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\basphaltfräse\b", "asphalt fräse", t, flags=re.IGNORECASE)
    t = re.sub(r"\bbaustelle\s+mix\s*:\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgehweg\s+saniert\s*:\s*", "gehweg saniert. ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bdrainage\s+verlegt\s+", "drainage verlegt. ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bgehweg\s+asphaltiert\b", "gehweg asphaltiert. ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bstra(ß|ss)e\s+asphaltiert\b", r"straße asphaltiert. ", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(schneiden|geschnitten)\s+(?:und\s+)?(?:\d+(?:[.,]\d+)?\s*(?:m²|m2|qm|meter)?\s+)?asphaltiert\b",
        r"\1. asphaltiert",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(\d+(?:[.,]\d+)?\s*(?:m²|m2|qm)\s+)?asphaltiert\s+(?=randstein|rasenkantenstein|kantenstein|bordstein|hochbord|borde|rinnenstein|pflasterstein)",
        r"\1asphaltiert. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\basphalt\s+gefräst\b", "asphalt gefräst. ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bneue\s+deckschicht\s+", "neue deckschicht. ", t, flags=re.IGNORECASE)
    t = re.sub(
        r"\bplanum\s+verdichtet\s+(?=asphalt)",
        "planum verdichtet. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(asphalt)\s+(\d+(?:[.,]\d+)?\s*quadrat(?:e|en)?)\s+und\s+",
        r"asphalt \2. und ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bleitungstrasse hergestellt\s+stra(ß|ss)e\s+asphaltiert",
        r"leitungstrasse hergestellt. straße asphaltiert",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(ausgehoben|ausgeschachtet)\s+(?=(?:\d+(?:[.,]\d+)?\s*)?(?:lfm|meter|m\s*)?(?:kg|ht|ka\s+ga))",
        r"\1. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(\d+(?:[.,]\d+)?\s*(?:m²|m2|qm)\s+)?asphaltiert\s+(?=pflasterstein)",
        r"\1asphaltiert. ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\basphaltiert\s+(\d+(?:[.,]\d+)?\s*(?:m²|m2|qm)\s+)?unkraut",
        r"asphaltiert. \1unkraut",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\bhochbord und (rinnenstein|muldenstein)",
        r"hochbord gesetzt. \1",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b(hochbord|tiefbord)\s+gesetzt\s+(rinnenstein|muldenstein)",
        r"\1 gesetzt. \2",
        t,
        flags=re.IGNORECASE,
    )
    # Geteiltes Schluss-Verb ueber "und"-Aufzaehlungen verteilen, BEVOR "und" zum
    # Trenner wird. So wird aus "50 m² Unterputz und 50 m² Oberputz aufgebracht"
    # -> "... Unterputz aufgebracht und ... Oberputz aufgebracht". Rein additiv:
    # verbslose Vorglieder bekommen das Schlussverb, sonst aendert sich nichts.
    _clause_pieces = [p.strip() for p in re.split(r"[.]", t) if p.strip()]
    if _clause_pieces:
        t = ". ".join(_propagate_trailing_verb(p) for p in _clause_pieces)
    t = re.sub(r"\bund\b", ".", t, flags=re.IGNORECASE)
    parts = [p.strip(" ,.;") for p in re.split(r"[.]", t) if p.strip(" ,.;")]
    out: list[str] = []
    for part in parts:
        first = _split_by_verb_transition(part)
        for inner in first:
            out.extend(_split_by_semantic_comma(inner))
    return [x for x in out if x]


def _propagate_trailing_verb(clause: str) -> str:
    """Verteilt ein gemeinsames Schluss-Verb auf verbslose Vorglieder einer
    "und"-Aufzaehlung.

    Beispiel: "50 m² Unterputz und 50 m² Oberputz aufgebracht"
    -> "50 m² Unterputz aufgebracht und 50 m² Oberputz aufgebracht".

    Sicherheits-Invarianten (rein additiv):
    - Nur aktiv, wenn die Klausel ein "und" enthaelt UND auf ein bekanntes
      Taetigkeitsverb endet.
    - Nur verbslose Vorglieder, die wie ein Objekt aussehen (alphabetischer
      Wortstamm), bekommen das Verb. Das letzte Glied bleibt unveraendert.
    - Glieder, die bereits ein Taetigkeitsverb tragen, bleiben unveraendert.
    """
    s = str(clause or "").strip()
    if not s or not re.search(r"\bund\b", s, flags=re.IGNORECASE):
        return s
    # Auch generische "fertig"-Verben aus gebrochenem Deutsch (gemacht/gearbeitet/
    # machen/macht/fertig) zaehlen als Verb-Quelle, damit verbslose Glieder in
    # "ich hab gemacht X und Y" das Verb erben (fuehrendes Verb). Zusaetzlich
    # domaenenspezifische Partizipien (gedüngt, eingedeckt, ...), damit solche
    # Glieder NICHT faelschlich als verblos gelten und ueberschrieben werden.
    all_verbs = tuple(_TRANSITION_VERBS) + _GENERIC_DONE_VERBS + _EXTRA_VERB_TOKENS
    verbs_pattern = "|".join(sorted(all_verbs, key=len, reverse=True))
    segments = [seg.strip() for seg in re.split(r"\bund\b", s, flags=re.IGNORECASE) if seg.strip()]
    if len(segments) < 2:
        return s

    def _last_verb_in(segment: str) -> str | None:
        hits = re.findall(rf"\b({verbs_pattern})\b", segment, flags=re.IGNORECASE)
        # Erstes Verb im Glied — verhindert, dass ein fernes Schlussverb
        # (z.B. "beplankt") auf kurze Vorglieder wie "CW-Profil" durchgereicht wird.
        return hits[0] if hits else None

    verbs_per = [_last_verb_in(seg) for seg in segments]
    if not any(verbs_per):
        return s

    rebuilt: list[str] = []
    for idx, seg in enumerate(segments):
        looks_like_object = re.search(r"[a-zäöüß]{4,}", seg.lower()) is not None
        if verbs_per[idx] is None and looks_like_object:
            # Verb vom naechsten Glied rechts uebernehmen (z.B. "Grundierung und
            # Fliesenkleber aufgetragen ..."), sonst vom naechsten Glied links
            # (fuehrendes Verb in "ich hab gemacht X und Y").
            chosen = None
            for j in range(idx + 1, len(segments)):
                if verbs_per[j]:
                    chosen = verbs_per[j]
                    break
            if chosen is None:
                for j in range(idx - 1, -1, -1):
                    if verbs_per[j]:
                        chosen = verbs_per[j]
                        break
            if chosen:
                if re.search(r"\basphalt\b", seg, flags=re.IGNORECASE) and re.search(
                    r"gemacht|verf[uü]ll|gesetzt", chosen, flags=re.IGNORECASE
                ):
                    pass
                elif re.search(r"\b(schneiden|schneide|geschnitten)\b", seg, flags=re.IGNORECASE) and re.search(
                    r"gesetzt", chosen, flags=re.IGNORECASE
                ):
                    pass
                else:
                    seg = f"{seg} {chosen}"
        rebuilt.append(seg)
    return " und ".join(rebuilt)


_GENERIC_DONE_VERBS = ("gemacht", "gearbeitet", "machen", "macht", "mache", "fertig")

# Nur fuer die "hat dieses Glied ein eigenes Verb?"-Erkennung der Aufzaehlungs-
# Propagation. Verhindert, dass domaenenspezifische Partizipien (die nicht in
# _TRANSITION_VERBS stehen) als verblos gelten und ein fremdes Verb erben.
_EXTRA_VERB_TOKENS = (
    "eingedeckt",
    "gedüngt",
    "geduengt",
    "vertikutiert",
    "bewässert",
    "bewaessert",
    "gestreut",
    "gegraben",
    "gepflanzt",
    "abgerieben",
    "silikoniert",
    "gezogen",
    "grundiert",
    "geschliffen",
    "asphaltiert",
)


_TRANSITION_VERBS = (
    "angebracht",
    "montiert",
    "verlegt",
    "abgehangen",
    "abgehängt",
    "abgehaengt",
    "verspachtelt",
    "verfugt",
    "aufgetragen",
    "aufgebracht",
    "verarbeitet",
    "benutzt",
    "verwendet",
    "nachgearbeitet",
    "eingebaut",
    "gebaut",
    "gesetzt",
    "gestellt",
    "aufgestellt",
    "aufgebaut",
    "hochgezogen",
    "aufgemauert",
    "gemauert",
    "geschnitten",
    "befüllt",
    "befuellt",
    "verfüllt",
    "verfuellt",
    "ausgehoben",
    "ausgeschachtet",
    "abgetragen",
    "geschliffen",
    "grundiert",
    "reingepackt",
    "eingepackt",
    "beplankt",
    "verdichtet",
    "entfernt",
    "beseitigt",
    "gedämmt",
    "gedaemmt",
    "vertikutiert",
    "gedüngt",
    "geduengt",
    "bewässert",
    "bewaessert",
    "saniert",
    "angeschlossen",
    "installiert",
    "geschlossen",
    "hergestellt",
    "ausgeführt",
    "ausgefuehrt",
    "durchgeführt",
    "durchgefuehrt",
    "eingebracht",
    "eingedeckt",
    "erstellt",
    "gegossen",
    "betoniert",
    "fertiggestellt",
    "gemäht",
    "gemaeht",
    "getrimmt",
    "verschraubt",
    "eingesetzt",
    "gebunden",
    "geschalt",
    "ausgelegt",
    "verteilt",
    "gezogen",
    "aufgezogen",
    "angeschliffen",
    "eingebettet",
    "geschraubt",
    "festgeschraubt",
    "angebaut",
    "angeklebt",
    "geklebt",
    "hochgemauert",
    "gespachtelt",
    "reingemacht",
    "runtergehängt",
    "runtergehaengt",
    "stuckiert",
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
    "rigipsplatten",
    "splittschicht",
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
    "bodenfliesen",
    "wandfliesen",
    "rohre",
    "kg-rohre",
    "ht-rohre",
    "filtervlies",
    "trennvlies",
    "geotextil",
    "vlies",
    "rasenkanten",
    "rasenkantensteine",
    "pflanzen",
    "pflanzkübel",
    "pflanzkuebel",
    "schotter",
    "splitt",
    "sand",
    "boden",
    "fläche",
    "flaeche",
    "frostschutz",
    "planum",
    "abgleich",
    "hydraulischen",
    "sanierputz",
    "altputz",
    "schimmel",
    "unterputz",
    "oberputz",
    "grundputz",
    "innenputz",
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
    "bewährung",
    "bewahrung",
    "bewehrungsstahl",
    "armierung",
    "bewährungsstahl",
    "schalung",
    "fundament",
    "wasserleitungen",
    "heizung",
    "heizkörper",
    "heiz",
    "herzkörper",
    "heizkoerper",
    "thermostatventil",
    "thermostatventile",
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
    "rindenmulch",
    "palisaden",
    "palisade",
    "keramikplatten",
    "keramikplatte",
    "wpc",
    "holzdeck",
    "vertikutieren",
    "vertikutiert",
    "gedüngt",
    "geduengt",
    "bewässert",
    "bewaessert",
    "winterdienst",
    "stelzlager",
    "splittschicht",
    "erdaushub",
    "baugrube",
    "fundamentplatte",
    "fundament",
    "leitungstrasse",
    "leitungs",
    "randsteine",
    "rücklaufverschraubung",
    "ruecklaufverschraubung",
    "rücklauf",
    "ruecklauf",
    "lüftung",
    "lueftung",
    "betondecke",
    "dämmmatte",
    "daemm",
    "daemmatte",
    "geotextil",
    "trennvlies",
    "wc",
    "toilette",
    "waschbecken",
    "waschtisch",
    "dusche",
    "duschwanne",
    "armatur",
    "armaturen",
    "druckprüfung",
    "druckpruefung",
    "nivelliermasse",
    "ausgleichsmasse",
    "bodenablauf",
    "duschrinne",
    "naturstein",
    "sockelputz",
    "reibputz",
    "kratzputz",
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
    "erdarbeiten",
    "gewebe",
    "armierungsgewebe",
    "flexkleber",
    "großformatfliesen",
    "grossformatfliesen",
    "profile",
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
    # Baustellensprache: "Fuenfer/Achter/Zehner" als Steinformat- oder
    # Durchmesserangabe. Erlaubt Split nach Verb, wenn solch ein Format folgt.
    "fünfer",
    "fuenfer",
    "achter",
    "zehner",
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
    follow_pattern = "|".join(
        "(?<!roll)rasen" if w == "rasen" else re.escape(w) for w in _FOLLOW_NOUNS
    )
    number_words_pattern = "|".join(_NUMBER_WORDS)
    pattern = (
        rf"\b({verbs_pattern})\b\s+"
        rf"(?=(?:{follow_pattern}|{number_words_pattern}|\d)\b|\d)"
    )
    marked = re.sub(pattern, r"\1. ", t, flags=re.IGNORECASE)
    verb_chain = "|".join(
        v for v in _TRANSITION_VERBS if v not in ("eingebaut", "eingebracht", "verlegt", "montiert", "gesetzt")
    )
    marked = re.sub(
        rf"\b({verbs_pattern})\b\s+(?=\b({verb_chain})\b)",
        r"\1. ",
        marked,
        flags=re.IGNORECASE,
    )
    splits = [p.strip(" ,.;") for p in re.split(r"[.]", marked) if p.strip(" ,.;")]
    return splits if splits else [t]


def _split_by_semantic_comma(part: str) -> list[str]:
    t = str(part or "").strip()
    if not t:
        return []
    pattern = r",\s+"
    splits = [p.strip(" ,.;") for p in re.split(pattern, t, flags=re.IGNORECASE) if p.strip(" ,.;")]
    return splits if splits else [t]


def normalize_for_match(text: str) -> str:
    """Public alias of the internal normalization helper.

    Useful for downstream modules that want to apply the same Whisper/
    spelling fixes before running their own pattern matching, ohne dass dort
    eigene Duplikate gepflegt werden muessen.
    """
    return _normalize_for_match(text)


def _normalize_for_match(text: str) -> str:
    out = text.casefold()
    out = re.sub(r"\bas\s+fault\b", "asphalt", out)
    out = re.sub(r"\bfss\b", "frostschutz", out)
    out = re.sub(r"\bsts\b", "schottertragschicht", out)
    out = re.sub(r"\basphaltfräse\b", "asphalt fräse", out)
    out = re.sub(r"\brinnen\s+steine\b", "rinnensteine", out)
    out = re.sub(r"\bhoch\s+bord\b", "hochbord", out)
    out = re.sub(r"\btief\s+bord\b", "tiefbord", out)
    out = re.sub(r"\bver\s+legt\b", "verlegt", out)
    out = re.sub(r"\bfrä\s+sen\b", "fräsen", out)
    out = re.sub(r"\basphalt\s+iert\b", "asphaltiert", out)
    out = re.sub(r"\bfrost\s+schutz\b", "frostschutz", out)
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
    out = re.sub(r"\bfrostschutz\s+reingemacht\b", "frostschutz eingebaut", out)
    out = re.sub(r"\bfss\s+reingemacht\b", "frostschutz eingebaut", out)
    out = re.sub(r"\bmeter quadrat\b", "m²", out)
    # Gebrochenes Deutsch / Whisper: verkuerzte Flaecheneinheit "30 quadrat"
    # -> m². Nur wenn nicht bereits "quadratmeter" (oben schon ersetzt).
    out = re.sub(r"\bquadrat(?:e|en)?\b", "m²", out)
    out = re.sub(r"\bkubikmeter\b|\bkubik\b", "m³", out)
    out = re.sub(r"\blaufende meter\b|\blfd\.?\s*meter\b|\blfm\b", "lfm", out)
    out = re.sub(r"\bkg-?\s*rohre\b", "kg rohre", out)
    out = re.sub(r"\bht-?\s*rohre\b", "ht rohre", out)
    # Gebrochenes Deutsch / Nicht-Muttersprachler: generische Taetigkeitsverben
    # auf das Token "gemacht" vereinheitlichen (NUR fuers Matching, nicht fuer die
    # Anzeige). So greifen die Fachregeln auch bei "ich hab gearbeitet ...",
    # "ich machen ...", "... fertig". Display-Text kommt weiterhin aus den Regeln.
    out = re.sub(r"\bgearbeitet\b", "gemacht", out)
    out = re.sub(r"\bfertig\s*gemacht\b", "gemacht", out)
    out = re.sub(r"\b(mache|machen|macht)\b", "gemacht", out)
    if not (
        re.search(r"\basphalt\b", out)
        and re.search(
            r"\b(schneiden|schneide|geschnitten|aufgeschnitten|trennen|aufschneiden|fräsen|fraesen|abgefräst|abgefraest)\b",
            out,
        )
    ):
        out = re.sub(r"\bfertig\b(?!\s*gestellt)", "gemacht", out)
    # Häufige Whisper-Verhörer bei Trockenbau-Profilen.
    out = re.sub(r"\buwe\b(?=\s*[-]?\s*profil)", "uw", out)
    out = re.sub(r"\bcwe\b(?=\s*[-]?\s*profil)", "cw", out)
    out = re.sub(r"\buae\b(?=\s*[-]?\s*profil)", "ua", out)
    out = re.sub(r"\bkg\s*dn\s*\d+\b", "kg rohre", out)
    out = re.sub(r"\bht\s*dn\s*\d+\b", "ht rohre", out)
    out = re.sub(r"\brasen[\s-]*kanten[\s-]*steine?\b", "rasenkantensteine", out)
    out = re.sub(r"\brasen[\s-]*kanten\b", "rasenkanten", out)
    # Whisper-Verhoerer GaLaBau-Pflege: "Rasse" statt "Rasen", "gemacht" statt "gemäht".
    out = re.sub(
        r"\brasse\b(?=\s+(?:gemacht|gemäht|gemaeht|mähen|maehen|getrimmt|geschnitten|verlegt|gelegt))",
        "rasen",
        out,
    )
    out = re.sub(r"\brasen gemacht\b", "rasen gemäht", out)
    out = re.sub(r"\brasse gemacht\b", "rasen gemäht", out)
    out = re.sub(r"\bfliesen gemacht\b", "fliesen verlegt", out)
    out = re.sub(r"\bschotter reingemacht\b", "schotter eingebaut", out)
    out = re.sub(r"\bunkraut weg gemacht\b", "unkraut entfernt", out)
    out = re.sub(r"\bunkraut weg\b", "unkraut entfernt", out)
    out = re.sub(r"\bgarten freigeschnitten\b", "rasen getrimmt", out)
    out = re.sub(r"\bganzen garten freigeschnitten\b", "rasen getrimmt", out)
    out = re.sub(r"\bvertikuliert\b|\bvertikulieren\b", "vertikutiert", out)
    out = re.sub(r"\bgedungt\b|\bgeduenght\b", "gedüngt", out)
    out = re.sub(r"\bbewassert\b|\bbewessert\b|\bbewassert\b", "bewässert", out)
    out = re.sub(r"\bstelllager\b|\bstelzlagern\b", "stelzlager", out)
    out = re.sub(r"\bgeotextiel\b", "geotextil", out)
    out = re.sub(r"\bgeo\s+textil\b", "geotextil", out)
    out = re.sub(r"\bka\s+ga\s+rohre?\b", "kg rohre", out)
    out = re.sub(r"\berd\s+aushub\b", "erdaushub", out)
    out = re.sub(r"\berd\s+arbeiten\b", "erdarbeiten", out)
    out = re.sub(r"\bbau\s+grube\b", "baugrube", out)
    out = re.sub(r"\bfrost\s+schutz\b", "frostschutz", out)
    out = re.sub(r"\bsplit\s+schicht\b", "splittschicht", out)
    out = re.sub(r"\bhaus\s+anschluss\b", "hausanschluss", out)
    out = re.sub(r"\bleitung\s+strasse\b", "leitungstrasse", out)
    out = re.sub(r"\bent\s+w(ä|ae)sserung\b", "entwässerung", out)
    out = re.sub(r"\bver\s+bau\b", "verbau", out)
    out = re.sub(r"\bdra\s+inage\b", "drainage", out)
    out = re.sub(r"\bver\s+f(ü|ue|u)llt\b", "verfüllt", out)
    out = re.sub(r"\bver\s+dichtet\b", "verdichtet", out)
    out = re.sub(r"\baus\s+ge\s+hoben\b", "ausgehoben", out)
    out = re.sub(r"\bfilter\s+vlies\b", "filtervlies", out)
    out = re.sub(r"\bka\s+ga\s+b(ö|oe)gen\b", "kg bögen", out)
    out = re.sub(r"\bka\s+ga\s+abzweig\b", "kg abzweig", out)
    out = re.sub(r"\bpla\s+num\b", "planum", out)
    out = re.sub(r"\bpflanz\s+k(ü|ue)bel\b", "pflanzkübel", out)
    out = re.sub(r"\bge\s+schnitten\b", "geschnitten", out)
    out = re.sub(r"\bverti\s+kutiert\b", "vertikutiert", out)
    out = re.sub(r"\bge\s+d(ü|ue|u)ngt\b", "gedüngt", out)
    out = re.sub(r"\ban\s+geschlossen\b", "angeschlossen", out)
    out = re.sub(r"\bbe\s+wehrungs\s+stahl\b", "bewehrungsstahl", out)
    out = re.sub(r"\bbe\s+wehrung\b", "bewehrung", out)
    out = re.sub(r"\bbewehrungs\s+stahl\b", "bewehrungsstahl", out)
    out = re.sub(r"\bschal\s+ung\b", "schalung", out)
    out = re.sub(r"\bfiligran\s+decke\b", "filigrandecke", out)
    out = re.sub(r"\bbeton\s+decke\b", "betondecke", out)
    out = re.sub(r"\bfundament\s+platte\b", "fundamentplatte", out)
    out = re.sub(r"\bquadrat\s+meter\b", "quadratmeter", out)
    out = re.sub(r"\bkalk\s+sandstein\b", "kalksandstein", out)
    out = re.sub(r"\bge\s+gossen\b", "gegossen", out)
    out = re.sub(r"\bver\s+baut\b", "verbaut", out)
    out = re.sub(r"\bge\s+schalt\b", "geschalt", out)
    out = re.sub(r"\bge\s+bunden\b", "gebunden", out)
    out = re.sub(r"\bwasser\s+leitungen\b", "wasserleitungen", out)
    out = re.sub(r"\bwasch\s+becken\b", "waschbecken", out)
    out = re.sub(r"\bhydraul\s+ischen\b", "hydraulischen", out)
    out = re.sub(r"\b(wärme|waerme)\s+pumpe\b", "wärmepumpe", out)
    out = re.sub(r"\bheizungs\s+anschl(ü|ue|u)sse\b", "heizungsanschlüsse", out)
    out = re.sub(r"\bheiz\s+kreis\s+verteiler\b", "heizkreisverteiler", out)
    out = re.sub(r"\bmon\s+tiert\b", "montiert", out)
    out = re.sub(r"\bin\s+stalliert\b", "installiert", out)
    out = re.sub(r"\bdurch\s+ge\s+f(ü|ue|u)hrt\b", "durchgeführt", out)
    out = re.sub(r"\bdruckprobe\b", "druckprüfung", out)
    out = re.sub(r"\bht\s+manschette\b", "ht-manschette", out)
    out = re.sub(r"\bfuss\s+boden\s+heizung\b", "fußbodenheizung", out)
    out = re.sub(r"\bgips\s+karton\s+platten\b", "gipskartonplatten", out)
    out = re.sub(r"\bfliesen\s+kleber\b", "fliesenkleber", out)
    out = re.sub(r"\bflex\s+kleber\b", "flexkleber", out)
    out = re.sub(r"\bab\s+dichtung\b", "abdichtung", out)
    out = re.sub(r"\bboden\s+ablauf\b", "bodenablauf", out)
    out = re.sub(r"\bdusch\s+rinne\b", "duschrinne", out)
    out = re.sub(r"\bfein\s+steinzeug\b", "feinsteinzeug", out)
    out = re.sub(r"\bwand\s+fliesen\b", "wandfliesen", out)
    out = re.sub(r"\bboden\s+fliesen\b", "bodenfliesen", out)
    out = re.sub(r"\bmosaik\s+fliesen\b", "mosaikfliesen", out)
    out = re.sub(r"\bgross\s+format\b", "großformat", out)
    out = re.sub(r"\bver\s+legt\b", "verlegt", out)
    out = re.sub(r"\bver\s+fugt\b", "verfugt", out)
    out = re.sub(r"\bge\s+klebt\b", "geklebt", out)
    out = re.sub(r"\bauf\s+gezogen\b", "aufgezogen", out)
    out = re.sub(r"\bauf\s+getragen\b", "aufgetragen", out)
    out = re.sub(r"\bauf\s+gebracht\b", "aufgebracht", out)
    out = re.sub(r"\bge\s+schliffen\b", "geschliffen", out)
    out = re.sub(r"\ban\s+ge\s+schliffen\b", "angeschliffen", out)
    out = re.sub(r"\bein\s+gebettet\b", "eingebettet", out)
    out = re.sub(r"\bein\s+gebaut\b", "eingebaut", out)
    out = re.sub(r"\barm\s+ie\s+rung\b", "armierung", out)
    out = re.sub(r"\bw\s+d\s+v\s+s\b", "wdvs", out)
    out = re.sub(r"\bschim\s+mel\b", "schimmel", out)
    out = re.sub(r"\bge\s+daemmt\b", "gedämmt", out)
    out = re.sub(r"\ban\s+geklebt\b", "angeklebt", out)
    out = re.sub(r"\bfas\s+sade\b", "fassade", out)
    out = re.sub(r"\bsanier\s+putz\b", "sanierputz", out)
    out = re.sub(r"\bputz\s+ab\s*getragen\b", "putz abgetragen", out)
    out = re.sub(r"\bge\s+sims\b", "gesims", out)
    out = re.sub(r"\bsilikon\s+iert\b", "silikoniert", out)
    out = re.sub(r"\bri\s+gips\b", "rigips", out)
    out = re.sub(r"\bri\s+gips\s+platten\b", "rigips platten", out)
    out = re.sub(r"\bknauf[\s-]?platten\b", "gipskartonplatten", out)
    out = re.sub(r"\bakustik\s+decke\b", "akustikdecke", out)
    out = re.sub(r"\brevision\s+sklappe\b", "revisionsklappe", out)
    out = re.sub(r"\bbrand\s+schutz\s+wand\b", "brandschutzwand", out)
    out = re.sub(r"\bbrand\s+schutz\s+platten\b", "brandschutzplatten", out)
    out = re.sub(r"\btrocken\s+bau\s+wand\b", "trockenbauwand", out)
    out = re.sub(r"\bstein\s+wolle\b", "steinwolle", out)
    out = re.sub(r"\babhangdecke\b", "decke abgehängt", out)
    out = re.sub(r"\babhang\s+decke\b", "decke abgehängt", out)
    out = re.sub(r"\bbe\s+plankt\b", "beplankt", out)
    out = re.sub(r"\bfestgemacht\b", "festgeschraubt", out)
    out = re.sub(r"\bprofi\b", "profile", out)
    out = re.sub(r"\bstaender\s+werk\b", "staenderwerk", out)
    out = re.sub(r"\bstein\s+wolle\b", "steinwolle", out)
    out = re.sub(r"\babge\s+haengt\b", "abgehängt", out)
    out = re.sub(r"\bver\s+schraubt\b", "verschraubt", out)
    out = re.sub(r"\bge\s+schraubt\b", "geschraubt", out)
    out = re.sub(r"\bfugen\s+spachtel\b", "fugenspachtel", out)
    out = re.sub(r"\bstaender\s+werks\s+profile\b", "ständerwerk profile", out)
    out = re.sub(r"\bpro\s+file\b", "profile", out)
    out = re.sub(r"\bfestfest\s+gemacht\b", "festgeschraubt", out)
    out = re.sub(r"\bfest\s+gemacht\b", "geschraubt", out)
    out = re.sub(r"\bfugen?\s+zu\s+gemacht\b", "fugen zugemacht", out)
    out = re.sub(r"\b(trockenbau)?wand\s+zu\s+gemacht\b", r"\1wand zugemacht", out)
    out = re.sub(r"\b(\d+)\s+meter\s+kg\b(?!\s*rohr)", r"\1 meter kg rohre", out)
    out = re.sub(r"\bnivellier\s+masse\b", "nivelliermasse", out)
    out = re.sub(r"\bgross\s+format\s+fliesen\b", "großformatfliesen", out)
    out = re.sub(r"\blauf\s+ende\s+meter\b", "laufende meter", out)
    out = re.sub(r"\brasen\s+kanten\s+steine\b", "rasenkantensteine", out)
    out = re.sub(r"\bdruck\s+pr(ü|ue|u)fung\b", "druckprüfung", out)
    out = re.sub(r"\bsilikon\s+fugen\b", "silikonfugen", out)
    out = re.sub(r"\bschimel\b", "schimmel", out)
    out = re.sub(r"\bdruckprufung\b", "druckprüfung", out)
    # Whisper-Trennung von Putz-Komposita: "unter putz" -> "unterputz" usw.
    out = re.sub(r"\baus\s+geschachtet\b", "ausgeschachtet", out)
    out = re.sub(r"\bunter\s+putz\b", "unterputz", out)
    out = re.sub(
        r"\b(unter|ober|grund|sanier|alt|innen|sockel|reib|kratz)\s+putz\b",
        r"\1putz",
        out,
    )
    out = re.sub(r"\b(au(?:ß|ss)en)\s+putz\b", r"\1putz", out)
    out = re.sub(r"\becke geschnitten\b", "hecke geschnitten", out)
    out = re.sub(r"\becke zurückgeschnitten\b|\becke zurueckgeschnitten\b", "hecke zurückgeschnitten", out)
    out = re.sub(r"\becke getrimmt\b", "hecke getrimmt", out)
    out = re.sub(r"\becke schneiden\b|\becke schneide\b", "hecke schneiden", out)
    # Whisper-Verhoerer: "Bewaehrung/Bewahrung/Bewährung(sstahl)" auf
    # "Bewehrung(sstahl)" vereinheitlichen. Wichtig: auch das Wortbestandteil
    # "bewährungsstahl" wird erfasst, damit Dedupe spaeter greift.
    out = re.sub(r"\bbew(?:ä|ae)hrungsstahl\b|\bbewahrungsstahl\b", "bewehrungsstahl", out)
    out = re.sub(r"\bbew(?:ä|ae)hrung\b|\bbewahrung\b", "bewehrung", out)
    # Whisper-Verhoerer: "Duennbettmoertel" wird haeufig zu "den Bettmoertel".
    # Wir fangen "den bettmoertel" zentral als "duennbettmoertel" ab, bevor andere Patterns laufen.
    out = re.sub(r"\bden\s+bettm(ö|oe)rtel\b", "dünnbettmörtel", out)
    out = re.sub(r"\bd(ü|ue)nn[\s-]?bettm(ö|oe)rtel\b", "dünnbettmörtel", out)
    # Familien-Normalisierung Hochbau: Poroton (Ziegel) vs Porit (Porenbeton).
    # Wichtig: porit/purit gehoeren zur Porenbeton-Familie und duerfen NICHT zu poroton gemappt werden.
    out = re.sub(r"\b(puroton|porroton|poriton|porotn|porothon)\b", "poroton", out)
    out = re.sub(r"\b(purit|poriht|porriht|porith)\b", "porit", out)
    out = re.sub(r"\b(yetong|yton|y-tong|y tong)\b", "ytong", out)
    out = re.sub(r"\bporen\s*beton\b", "porenbeton", out)
    out = re.sub(r"\bkalk\s*sandstein(e)?\b", "kalksandstein", out)
    out = re.sub(r"\bherz\s*k(ö|oe)rper\b|\bherzk(ö|oe)rper\b", "heizkörper", out)
    out = re.sub(r"\bheiz\s*k(ö|oe)rper\b", "heizkörper", out)
    out = re.sub(r"\bver\s+fugt\b", "verfugt", out)
    out = re.sub(r"\bver\s+spachtelt\b", "verspachtelt", out)
    out = re.sub(r"\bschot\s+ter\b", "schotter", out)
    out = re.sub(r"\bunter\s+grund\b", "untergrund", out)
    out = re.sub(r"\broll\s+rasen\b", "rollrasen", out)
    out = re.sub(r"\bstelz\s+lager\b", "stelzlager", out)
    out = re.sub(r"\bwinter\s+dienst\b", "winterdienst", out)
    out = re.sub(r"\bent\s+w(ä|ae)sserung\b", "entwässerung", out)
    out = re.sub(r"\bka\s+nal\b", "kanal", out)
    out = re.sub(r"\bab\s+dichtung\b", "abdichtung", out)
    out = re.sub(r"\bmanschete\b", "manschette", out)
    out = re.sub(r"\bbeton gemacht\b", "beton eingebracht", out)
    out = _normalize_masonry_size_notation(out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


_STONE_WORD_PATTERN = r"(poroton|porit|porenbeton|ytong|kalksandstein|ks(?:[-\s]*stein(?:e)?)?|ziegel)"


def _normalize_masonry_size_notation(text: str) -> str:
    """Repariert Whisper-Fragmente bei Steinformaten (Poroton/Porit/KS).

    Wichtige Invarianten:
    - 15er bleibt 15er, 11,5er bleibt 11,5er, 17,5er bleibt 17,5er.
    - Nur der Spezialfall "l5"/"el5" (Whisper-Verhoerer) wird zu 11,5er.
    - "aporoton/aporit/aytong/aks" werden als " a poroton" entklebt.
    - Format-Glue: "17 5 a poroton" -> "17,5er Poroton",
      "15 a poroton" -> "15er Poroton" (NICHT 11,5er!).
    """

    t = str(text or "")

    # Whisper-Klebung: "aporoton/aporit/aytong/akalksandstein/aziegel" zuerst aufloesen,
    # damit der Wachhund-Check unten die Steinwoerter findet. Wir splitten an der
    # Wortgrenze vor "a" + Steinwort -> "a <stein>".
    t = re.sub(
        r"\ba(poroton|porit|porenbeton|ytong|kalksandstein|ziegel)\b",
        r"a \1",
        t,
        flags=re.IGNORECASE,
    )

    if not re.search(rf"\b{_STONE_WORD_PATTERN}\b|\bmauerwerk\b|\bstein(?:e|en)?\b", t, flags=re.IGNORECASE):
        return t

    # Halbzahlige Formate mit getrenntem "5" oder "fuenfer" + optionalem "a" + Steinwort.
    # Beispiele: "17 5 a poroton" -> "17,5er Poroton", "11 5 porit" -> "11,5er Porit".
    t = re.sub(
        rf"\b(\d{{1,2}})\s+(?:5|fünfer|fuenfer)\s+(?:a\s+)?{_STONE_WORD_PATTERN}\b",
        lambda m: f"{m.group(1)},5er {m.group(2)}",
        t,
        flags=re.IGNORECASE,
    )

    # Ganzzahlige Formate mit optionalem "a"-Glue + Steinwort.
    # Beispiele: "15 a poroton" -> "15er Poroton", "24 poroton" -> "24er Poroton".
    t = re.sub(
        rf"\b(\d{{1,2}})\s+(?:a\s+)?{_STONE_WORD_PATTERN}\b",
        lambda m: f"{m.group(1)}er {m.group(2)}",
        t,
        flags=re.IGNORECASE,
    )

    # Baustellensprache ohne explizites Steinwort: "11 fuenfer" -> "11,5er".
    t = re.sub(r"\b(\d{1,2})\s*(fünfer|fuenfer)\b", lambda m: f"{m.group(1)},5er", t, flags=re.IGNORECASE)

    # Whisper-Verhoerer "l5/l5er/el5/el5er" -> Spezialfall fuer 11,5er.
    t = re.sub(r"\b(?:l|el)\s*5(?:er)?\b", "11,5er", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(?:l|el)\s*(fünfer|fuenfer)\b", "11,5er", t, flags=re.IGNORECASE)

    t = re.sub(r"\s+", " ", t).strip()
    return t


def _extract_qty_m2(text: str) -> str | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(m²|m2|qm|quadratmeter)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    w = re.search(
        r"\b(eins|eine|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwoelf|"
        r"zwanzig|dreißig|dreissig|vierzig|fünfzig|fuenfzig|sechzig|siebzig|achtzig|neunzig|hundert|"
        r"fünfundzwanzig|funfundzwanzig|vierundzwanzig|dreiunddreißig|dreiunddreissig)\s*"
        r"(m²|m2|qm|quadratmeter)\b",
        text,
        flags=re.IGNORECASE,
    )
    if w:
        return _word_to_number(w.group(1)) or w.group(1)
    w_any = re.search(r"\b([a-zäöüß]+)\s*(m²|m2|qm|quadratmeter)\b", text, flags=re.IGNORECASE)
    if w_any:
        return _word_to_number(w_any.group(1))
    return None


def _is_keramikterrasse_context(t: str, *, raw_text: str = "") -> bool:
    probe = f"{t} {raw_text}".casefold()
    if re.search(r"\bkeramikterrasse\b", probe):
        return True
    if re.search(r"\bterrasse\b", probe) and re.search(
        r"\b(keramik(?:platte(?:n)?)?|keramikplatte|feinsteinzeug(?:platten?)?|platten)\b",
        probe,
    ):
        return True
    return False


def _extract_qty_m3(text: str) -> str | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(m³|m3|kubikmeter|kubik)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    w = re.search(
        r"\b(eins|eine|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwoelf|"
        r"zwanzig|dreißig|dreissig|vierzig|fünfzig|fuenfzig|sechzig|siebzig|achtzig|neunzig|hundert)\s*"
        r"(m³|m3|kubikmeter|kubik)\b",
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
    if m:
        return m.group(1)
    w = re.search(
        r"\b("
        r"eins|eine|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwoelf|"
        r"zwanzig|dreißig|dreissig|vierzig|fünfzig|fuenfzig|sechzig|siebzig|achtzig|neunzig|"
        r"fünfundzwanzig|funfundzwanzig|dreiunddreißig|dreiunddreissig|vierundzwanzig"
        r")\s*(lfm|laufende meter)\b",
        text,
        flags=re.IGNORECASE,
    )
    return _word_to_number(w.group(1)) if w else None


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

    # GaLaBau Keramikterrasse vor generischem Fliesen-Match (Terrasse + Keramikplatten).
    # Wichtig: der Chunk selbst muss einen Keramik-/Terrassen-Hinweis tragen, damit
    # fremde Chunks (z.B. "geotextil verlegt") nicht ueber den raw_text-Kontext
    # faelschlich als Keramikterrasse eingeordnet werden.
    if ("keramik" in t or "terrasse" in t or "platten" in t or "feinsteinzeug" in t) and _is_keramikterrasse_context(
        t, raw_text=raw_text
    ) and re.search(
        r"\b(verlegt|gelegt|gebaut|hergestellt|gemacht|drauf)\b",
        t,
    ):
        qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text)
        text = f"{_qty_prefix(raw_text)}{qty} m² Keramikterrasse verlegt" if qty else "Keramikterrasse verlegt"
        return CanonicalActivity("keramikterrasse_verlegt", text, 103.0, bool(qty))

    # Fliesenleger
    if "grundierung" in t and re.search(
        r"\b(aufgetragen|aufgebracht|benutzt|verwendet|verarbeitet|gemacht|drauf|draufgezogen)\b",
        t,
    ) and not re.search(r"\b(unterputz|oberputz|altputz|putz runter|sanierputz)\b", t):
        return CanonicalActivity("grundierung_aufgetragen", "Grundierung aufgetragen", 67.0, False)
    if re.search(r"\bgrundiert\b", t) and (
        "wand" in t
        or "decke" in t
        or "untergrund" in t
        or re.search(r"\b(wand|decke|untergrund|fassade)\b", (raw_text or "").casefold())
    ):
        return CanonicalActivity("grundierung_aufgetragen", "Grundierung aufgetragen", 67.0, False)
    if "abdichtung" in t and (
        re.search(r"\b(hergestellt|aufgebracht|eingebaut|gemacht)\b", t)
        or re.search(r"\b(dusch|duschbereich|bad|fliesen)\b", t)
        or re.search(r"\b(dusch|duschbereich|bad)\b", (raw_text or "").casefold())
    ) and "nivelliermasse" not in t:
        return CanonicalActivity("abdichtung_hergestellt", "Abdichtung hergestellt", 71.0, False)
    if re.search(r"\b(nivelliermasse|ausgleichsmasse|nivellierspachtel)\b", t) and re.search(
        r"\b(aufgetragen|aufgebracht|gezogen|verteilt|gemacht)\b",
        t,
    ):
        return CanonicalActivity("nivelliermasse_aufgetragen", "Nivelliermasse aufgetragen", 70.0, False)
    fliesen_kleber_hit = re.search(
        r"\b(fliesenkleber|flexkleber|mittelbettm(?:ö|oe)rtel)\b",
        t,
    )
    duennbett_fliesen_context = (
        re.search(r"\bd(?:ü|ue)nnbettm(?:ö|oe)rtel\b", t)
        and re.search(r"\bfliesen\b", t)
    )
    if (fliesen_kleber_hit or duennbett_fliesen_context) and re.search(
        r"\b(gezogen|aufgezogen|aufgetragen|aufgebracht|benutzt|verwendet|verarbeitet|gemacht|drauf)\b",
        t,
    ):
        return CanonicalActivity("fliesenkleber", "Fliesenkleber aufgetragen", 68.0, False)
    if re.search(r"\b(wand)?fliese(n)?\b", t) and re.search(r"\b(repariert|ausgetauscht|erneuert)\b", t):
        return CanonicalActivity("fliesen_reparatur", "Fliesen repariert", 63.0, False)
    if re.search(r"\b(gro(ß|ss)format(?:fliesen?)?|gro(ß|ss)format)\b", t) and re.search(
        r"\b(verlegt|gelegt|gesetzt|gemacht)\b",
        t,
    ):
        qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text)
        text = f"{_qty_prefix(raw_text)}{qty} m² Großformatfliesen verlegt" if qty else "Großformatfliesen verlegt"
        return CanonicalActivity("grossformatfliesen_verlegt", text, 101.0, bool(qty))
    if re.search(r"\bfliesen\b", t) and not re.search(r"\bfliesenkleber\b", t) and not re.search(
        r"\bverfugt\b",
        t,
    ) and re.search(
        r"\b(verlegt|gelegt|gemacht|geklebt|gesetzt)\b",
        t,
    ):
        qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text)
        text = f"{_qty_prefix(raw_text)}{qty} m² Fliesen verlegt" if qty else "Fliesen verlegt"
        return CanonicalActivity("fliesen_verlegt", text, 100.0, bool(qty))
    if re.search(
        r"\b(platten|mosaik|feinsteinzeug|mosaikfliesen|wandfliesen|bodenfliesen)\b",
        t,
    ) and re.search(r"\b(verlegt|gelegt|gesetzt|geklebt)\b", t):
        if _is_keramikterrasse_context(t, raw_text=raw_text):
            qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text)
            text = f"{_qty_prefix(raw_text)}{qty} m² Keramikterrasse verlegt" if qty else "Keramikterrasse verlegt"
            return CanonicalActivity("keramikterrasse_verlegt", text, 103.0, bool(qty))
        qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text)
        text = f"{_qty_prefix(raw_text)}{qty} m² Fliesen verlegt" if qty else "Fliesen verlegt"
        return CanonicalActivity("fliesen_verlegt", text, 100.0, bool(qty))
    if re.search(r"\b(bodenablauf|ablaufrinne|duschrinne)\b", t) and re.search(r"\b(eingebaut|montiert|gesetzt)\b", t):
        return CanonicalActivity("bodenablauf_eingebaut", "Bodenablauf eingebaut", 71.0, False)
    if re.search(r"\bnaturstein(?:platte(n)?)?\b", t) and re.search(r"\b(verlegt|gelegt|gesetzt|gemacht)\b", t):
        qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text)
        text = f"{_qty_prefix(raw_text)}{qty} m² Naturstein verlegt" if qty else "Naturstein verlegt"
        return CanonicalActivity("naturstein_verlegt", text, 70.0, bool(qty))
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
    if ("hecke" in t or "hecken" in t) and re.search(
        r"\b(geschnitten|zurückgeschnitten|zurueckgeschnitten|getrimmt|schneiden|schneide)\b",
        t,
    ):
        return CanonicalActivity("hecke_geschnitten", "Hecke geschnitten", 76.0, False)
    if re.search(r"\bgarten\b", t) and re.search(r"\b(freigeschnitten|freischneiden|getrimmt)\b", t):
        return CanonicalActivity("rasen_getrimmt", "Rasen getrimmt", 77.0, False)
    # Rand-/Rasenkantensteine MUSS vor "rasen" geprüft werden, damit
    # "Rasenkantensteine" nicht versehentlich als "Rasen verlegt" interpretiert wird.
    if re.search(
        r"\b(rasenkantenstein(e|en)?|rasenkanten|randstein(e|en)?|kantenstein(e|en)?|bordstein(e|en)?)\b",
        t,
    ) and re.search(r"\b(gesetzt|gestellt|verlegt|gelegt|benutzt|verbaut|verarbeitet|montiert|eingebaut|gebaut|gemacht)\b", t):
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
    # Spezifischere Rasen-Verben (vertikutiert/gedüngt) duerfen nicht vom
    # schwachen "gemacht"-Signal der Maeh-Regel ueberstimmt werden.
    _rasen_specific = re.search(r"\b(vertikutiert|vertikutieren|gedüngt|geduengt)\b", t)
    if ("rasen" in t or "rollrasen" in t) and not re.search(r"\brasenkanten", t):
        if re.search(r"\b(verlegt|gelegt|eingebracht|ausgelegt)\b", t):
            qty = _extract_qty_m2(t)
            text = f"{_qty_prefix(raw_text)}{qty} m² Rasen verlegt" if qty else "Rasen verlegt"
            return CanonicalActivity("rasen_verlegt", text, 73.0, bool(qty))
        if not _rasen_specific and re.search(r"\b(gemäht|gemaeht|gemacht|mähen|maehen|geschnitten)\b", t):
            qty = _extract_qty_m2(t)
            text = f"{_qty_prefix(raw_text)}{qty} m² Rasen gemäht" if qty else "Rasen gemäht"
            return CanonicalActivity("rasen_gemaeht", text, 78.0, bool(qty))
        if re.search(r"\b(getrimmt|freigeschnitten|freischneiden|nachgeschnitten)\b", t):
            return CanonicalActivity("rasen_getrimmt", "Rasen getrimmt", 77.0, False)
    if re.search(r"\b(rasen|rasenkanten)\b", t) and re.search(
        r"\b(getrimmt|freigeschnitten|freischneiden|nachgeschnitten)\b",
        t,
    ):
        return CanonicalActivity("rasen_getrimmt", "Rasen getrimmt", 77.0, False)
    if ("pflanzen" in t or "bäume" in t or "baeume" in t or "sträucher" in t or "straeucher" in t) and re.search(
        r"\b(gesetzt|gepflanzt|eingepflanzt|bepflanzt)\b",
        t,
    ):
        return CanonicalActivity("pflanzen_gepflanzt", "Pflanzen gesetzt", 74.0, False)
    if "unkraut" in t and re.search(
        r"\b(entfernt|gejätet|gejaetet|gezupft|beseitigt|gehackt|gemacht|weg gemacht|weg|durchgeführt|durchgefuehrt|gerupft)\b",
        t,
    ):
        return CanonicalActivity("unkraut_entfernt", "Unkraut entfernt", 74.0, False)
    if "laub" in t and re.search(r"\b(entfernt|gefegt|geräumt|geraeumt|beseitigt|gemacht|aufgesammelt)\b", t):
        return CanonicalActivity("laub_entfernt", "Laub entfernt", 72.0, False)
    if re.search(r"\bpalisad(?:e|en)\b", t) and re.search(
        r"\b(gesetzt|gestellt|montiert|eingebaut|verlegt|gebaut|gemacht|eingesetzt)\b",
        t,
    ):
        qty_lfm = _extract_qty_lfm(t)
        if qty_lfm:
            text = f"{qty_lfm} lfm Palisaden gesetzt"
            return CanonicalActivity("palisaden_gesetzt", text, 83.0, True)
        return CanonicalActivity("palisaden_gesetzt", "Palisaden gesetzt", 83.0, False)
    if re.search(r"\b(terrasse|deck|holzdeck|diele|dielen)\b", t) and re.search(r"\b(holz|wpc|diele)\b", t) and re.search(
        r"\b(gebaut|verlegt|montiert|hergestellt)\b",
        t,
    ):
        qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text)
        text = f"{_qty_prefix(raw_text)}{qty} m² Holz-/WPC-Terrasse gebaut" if qty else "Holz-/WPC-Terrasse gebaut"
        return CanonicalActivity("holz_wpc_terrasse_gebaut", text, 74.0, bool(qty))
    if re.search(r"\brasen\b", t) and re.search(r"\b(vertikutiert|vertikutieren)\b", t):
        return CanonicalActivity("rasen_vertikutiert", "Rasen vertikutiert", 75.0, False)
    # Subjekt-Fallback fuer Komma-Ketten wie "Rasen gemäht, vertikutiert, gedüngt":
    # "vertikutiert" ist eindeutig eine Rasen-Taetigkeit. Greift nur, wenn im Chunk
    # KEIN konkurrierendes Rasen-Verb (gedüngt/gemäht) steht, damit deren eigene
    # Fallbacks (gleiche Subjekt-Logik) nicht ueberschrieben werden.
    if (
        re.search(r"\b(vertikutiert|vertikutieren)\b", t)
        and not re.search(r"\b(gedüngt|geduengt|gemäht|gemaeht|gemaht)\b", t)
        and re.search(r"\brasen\b", str(raw_text or ""), flags=re.IGNORECASE)
    ):
        return CanonicalActivity("rasen_vertikutiert", "Rasen vertikutiert", 75.0, False)
    if re.search(r"\brasen\b", t) and re.search(r"\b(gedüngt|geduengt|gedüngen|geduengen)\b", t):
        return CanonicalActivity("rasen_geduengt", "Rasen gedüngt", 74.0, False)
    if re.search(r"\b(gedüngt|geduengt|gedüngen|geduengen)\b", t) and re.search(
        r"\brasen\b",
        str(raw_text or ""),
        flags=re.IGNORECASE,
    ):
        return CanonicalActivity("rasen_geduengt", "Rasen gedüngt", 74.0, False)
    if re.search(r"\b(fläche|flaeche|rasen|beet)\b", t) and re.search(
        r"\b(bewässert|bewaessert|gegossen|gewässert|gewaessert)\b",
        t,
    ):
        return CanonicalActivity("flaeche_bewaessert", "Fläche bewässert", 69.0, False)
    if re.search(r"\b(bewässert|bewaessert|gegossen|gewässert|gewaessert)\b", t) and re.search(
        r"\brasen\b",
        str(raw_text or ""),
        flags=re.IGNORECASE,
    ):
        return CanonicalActivity("flaeche_bewaessert", "Fläche bewässert", 69.0, False)
    if re.search(r"\b(winterdienst|schnee|eis|streugut|salz)\b", t) and re.search(
        r"\b(geräumt|geraeumt|gestreut|durchgeführt|durchgefuehrt|gemacht|verteilt)\b",
        t,
    ):
        return CanonicalActivity("winterdienst_ausgefuehrt", "Winterdienst durchgeführt", 73.0, False)
    if re.search(r"\b(geotextil|trennvlies|filtervlies|vlies)\b", t) and re.search(r"\b(verlegt|eingebaut|eingebracht)\b", t):
        return CanonicalActivity("geotextil_verlegt", "Geotextil verlegt", 68.0, False)
    if re.search(r"\bgemulcht\b", t) and not re.search(r"\b(entfernt|weg|beseitigt)\b", t):
        qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text)
        label = "Rindenmulch eingedeckt" if "rindenmulch" in t or "rindenmulch" in raw_text.casefold() else "Fläche mit Mulch eingedeckt"
        text = f"{_qty_prefix(raw_text)}{qty} m² {label}" if qty else label
        return CanonicalActivity("mulch_eingedeckt", text, 73.0, bool(qty))
    if re.search(r"\b(rindenmulch|mulch)\b", t) and re.search(
        r"\b(eingedeckt|eingebracht|gelegt|verteilt|gestreut|bestreut|eingestreut|aufgebracht|reingemacht|gemacht)\b",
        t,
    ) and not re.search(r"\b(entfernt|weg|beseitigt|geräumt|geraeumt)\b", t):
        qty = _extract_qty_m2(t)
        label = "Rindenmulch eingedeckt" if "rindenmulch" in t else "Fläche mit Mulch eingedeckt"
        text = f"{_qty_prefix(raw_text)}{qty} m² {label}" if qty else label
        return CanonicalActivity("mulch_eingedeckt", text, 73.0, bool(qty))
    if ("unkraut" in t or "laub" in t or "mulch" in t) and re.search(
        r"\b(entfernt|durchgeführt|durchgefuehrt|geräumt|geraeumt)\b",
        t,
    ):
        return CanonicalActivity("pflegearbeiten", "Pflegearbeiten durchgeführt", 55.0, False)
    if ("unkraut" in t or "laub" in t) and re.search(
        r"\b(gemacht|verteilt|gestreut)\b",
        t,
    ):
        return CanonicalActivity("pflegearbeiten", "Pflegearbeiten durchgeführt", 55.0, False)
    if "pflaster" in t and re.search(r"\b(verlegt|gelegt|gemacht)\b", t):
        qty = _extract_qty_m2(t)
        text = f"{_qty_prefix(raw_text)}{qty} m² Pflaster verlegt" if qty else "Pflaster verlegt"
        return CanonicalActivity("pflaster_verlegt", text, 102.0, bool(qty))
    if ("gartenmauer" in t or ("mauer" in t and re.search(r"\b(garten|beet|aussenanlage|außenanlage|hof|terrasse)\b", t))) and re.search(
        r"\b(gebaut|erstellt|hochgezogen|gemauert|gemacht)\b",
        t,
    ):
        qty = _extract_qty_m2(t)
        text = f"{_qty_prefix(raw_text)}{qty} m² Gartenmauer gebaut" if qty else "Gartenmauer gebaut"
        return CanonicalActivity("gartenmauer_gebaut", text, 95.0, bool(qty))
    if "schotter" in t and re.search(
        r"\b(eingebaut|verarbeitet|eingebracht|verdichtet|reingemacht|rein gemacht|rein|verwendet|verteilt)\b",
        t,
    ):
        qty = _extract_qty_m3(t)
        text = f"{qty} m³ Schotter eingebaut" if qty else "Schotter eingebaut"
        return CanonicalActivity("schotter_eingebaut", text, 82.0, bool(qty))
    if "splitt" in t or "split" in t or "splittschicht" in t:
        # Liefer-/Mangelkontext ("Splitt zu spät geliefert", "Splitt fehlt") ist
        # KEINE Einbau-Taetigkeit. Nur ueberspringen, wenn kein Einbau-Verb vorliegt.
        _splitt_delivery = re.search(
            r"\b(geliefert|liefer\w*|bestellt|fehlt|fehlen|fehlte|gefehlt|nachbestell\w*)\b",
            t,
        )
        _splitt_install = re.search(
            r"\b(eingebaut|verteilt|verdichtet|eingebracht|abgezogen|verarbeitet|aufgebracht|reingemacht|rein gemacht|verwendet|verlegt|gesetzt)\b",
            t,
        )
        if _splitt_delivery and not _splitt_install:
            return None
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

    if re.search(r"\bstelzlager\b", t) and re.search(r"\b(gesetzt|montiert|verlegt|eingebaut)\b", t):
        return CanonicalActivity("stelzlager_gesetzt", "Stelzlager gesetzt", 71.0, False)
    if re.search(r"\b(zaun|sichtschutz)\b", t) and re.search(
        r"\b(gesetzt|montiert|gestellt|aufgebaut|eingebaut|verlegt)\b",
        t,
    ):
        return CanonicalActivity("zaun_gesetzt", "Zaun gesetzt", 69.0, False)

    # Trockenbau — Spezialregeln vor dem allgemeinen Dämmblock
    if re.search(r"\bdoppelständerwand\b", t) and re.search(r"\b(aufgebaut|montiert|gebaut|errichtet)\b", t):
        return CanonicalActivity("staenderwerk_montiert", "Ständerwerk montiert", 79.0, False)
    if re.search(r"\b(revisionsklappe|revisionsklappen)\b", t) and re.search(
        r"\b(eingebaut|montiert|gesetzt|angebracht)\b",
        t,
    ):
        return CanonicalActivity("revisionsklappe_eingebaut", "Revisionsklappe eingebaut", 66.0, False)
    if re.search(r"\b(dämmung|daemmung|dämmmatte|daemmatte|steinwolle|mineralwolle)\b", t) and re.search(
        r"\b(eingebaut|verlegt|angebracht|eingebracht|eingesetzt|reingepackt|reingemacht|ein\s+gemacht)\b",
        t,
    ):
        return CanonicalActivity("daemmung_eingebaut", "Dämmung eingebaut", 71.0, False)
    if re.search(r"\b(dämmung|daemmung|steinwolle|mineralwolle)\s+gemacht\b", t) and re.search(
        r"\b(dämmung|daemmung|steinwolle|mineralwolle)\s+eingebaut\b",
        str(raw_text or ""),
        flags=re.IGNORECASE,
    ):
        return CanonicalActivity("daemmung_eingebaut", "Dämmung eingebaut", 71.0, False)
    if re.fullmatch(r"(dämmung|daemmung|steinwolle|mineralwolle)", t) and _raw_has_trockenbau_context(raw_text):
        if re.search(r"\b(eingebaut|eingesetzt|reingepackt|reingemacht)\b", str(raw_text or ""), flags=re.IGNORECASE):
            return CanonicalActivity("daemmung_eingebaut", "Dämmung eingebaut", 71.0, False)
    if re.search(r"\bbrandschutzwand\b", t) and re.search(
        r"\b(hergestellt|gebaut|montiert|beplankt|errichtet)\b",
        t,
    ):
        return CanonicalActivity("brandschutzwand_hergestellt", "Brandschutzwand hergestellt", 72.0, False)
    if (
        re.search(r"\bbrandschutz\b", t)
        and re.search(r"\b(hergestellt|gebaut|errichtet)\b", t)
        and not re.search(r"\bfugen?\b", t)
    ):
        return CanonicalActivity("brandschutzwand_hergestellt", "Brandschutzwand hergestellt", 72.0, False)
    if re.search(r"\bakustikdecke\b", t) and re.search(r"\b(eingebaut|montiert)\b", t):
        return CanonicalActivity("akustikdecke_eingebaut", "Akustikdecke eingebaut", 70.0, False)
    if (
        "ständerwerk" in t
        or "staenderwerk" in t
        or "ständerwerksprofile" in t
        or "staenderwerksprofile" in t
        or "cw profil" in t
        or "uw profil" in t
        or "profile" in t
    ) and re.search(
        r"\b(gebaut|montiert|gestellt|eingebaut|gemacht|geschraubt|festgeschraubt|angebaut|gesetzt|eingesetzt)\b",
        t,
    ):
        return CanonicalActivity("staenderwerk_montiert", "Ständerwerk montiert", 79.0, False)
    if "trockenbauwand" in t or "schließen einer trockenbauwand" in t or re.search(r"\brigipswand\b", t):
        if re.search(r"\b(geschlossen|fertiggestellt|fertig|gemacht|zugemacht)\b", t):
            return CanonicalActivity("trockenbauwand_geschlossen", "Trockenbauwand geschlossen", 96.0, False)
    if re.search(r"\bwand\b", t) and re.search(r"\b(geschlossen|zugemacht)\b", t) and _raw_has_trockenbau_context(raw_text):
        return CanonicalActivity("trockenbauwand_geschlossen", "Trockenbauwand geschlossen", 96.0, False)
    if _is_trockenbau_fuge_context(t, raw_text=raw_text):
        return CanonicalActivity("trockenbau_fugen_verspachtelt", "Fugen verspachtelt", 62.0, False)
    if "decke" in t and re.search(r"\b(abgehängt|abgehaengt|abgehangen|runtergehängt|runtergehaengt)\b", t):
        return CanonicalActivity("decke_abgehaengt", "Decke abgehängt", 74.0, False)
    if re.search(r"\bakustikdecke\b", t) and re.search(r"\b(runtergehängt|runtergehaengt|abgehängt|abgehaengt|montiert)\b", t):
        return CanonicalActivity("decke_abgehaengt", "Decke abgehängt", 74.0, False)
    if "decke" in t and re.search(r"\b(montiert|angebracht)\b", t):
        if _raw_has_trockenbau_context(raw_text):
            return CanonicalActivity("decke_abgehaengt", "Decke abgehängt", 74.0, False)
    if "gipskarton" in t or "rigips" in t or "gk platten" in t or "knauf" in t:
        if re.search(r"\b(montiert|angebracht|dran gemacht|aufgebaut|beplankt|gemacht|verschraubt|geschraubt|festgeschraubt|rein)\b", t):
            return CanonicalActivity("gipskarton_montiert", "Gipskartonplatten montiert", 90.0, False)
    raw_probe_tb = str(raw_text or "").casefold()
    if re.search(r"\bplatten\b", t) and re.search(r"\b(rein|reingemacht|verschraubt|montiert|beplankt)\b", t) and any(
        c in f"{t} {raw_probe_tb}" for c in ("gipskarton", "rigips", "gk platten", "trockenbau", "knauf")
    ):
        return CanonicalActivity("gipskarton_montiert", "Gipskartonplatten montiert", 90.0, False)
    if re.search(r"\bbeide seiten beplankt\b", t) or (
        re.search(r"\bbeplankt\b", t) and re.search(r"\bbrandschutzplatten\b", f"{t} {raw_probe_tb}")
    ):
        return CanonicalActivity("gipskarton_montiert", "Gipskartonplatten montiert", 90.0, False)
    if re.search(r"\bbeplankt\b", t) and any(
        c in f"{t} {raw_probe_tb}"
        for c in ("gipskarton", "rigips", "gk platten", "trockenbau", "ständerwerk", "staenderwerk", "seiten", "platten")
    ):
        return CanonicalActivity("gipskarton_montiert", "Gipskartonplatten montiert", 90.0, False)
    if re.search(r"\bbrandschutz(?:platten)?\b", t) and re.search(r"\bbeplankt\b", t):
        return CanonicalActivity("gipskarton_montiert", "Gipskartonplatten montiert", 90.0, False)
    if (
        re.search(r"\bspachtel(?:arbeiten|masse)?\b", t)
        and not re.search(r"\b(verspachtelt|fugenspachtel|nachgespachtelt|zu\s+gemacht)\b", t)
    ) or re.search(r"\bzugespachtelt\b", t):
        return CanonicalActivity("spachtelarbeiten", "Spachtelarbeiten durchgeführt", 60.0, False)
    if re.search(r"\b(graben|gräben|graeben|baugrube)\b", t) and re.search(
        r"\b(verfüllt|verfuellt|verfüllen|verfuellen|aufgefüllt|aufgefuellt)\b",
        t,
    ):
        return CanonicalActivity("graben_verfuellt", "Graben verfüllt", 77.0, False)
    if _is_pflaster_fuge_context(t, raw_text=raw_text):
        return CanonicalActivity("pflasterfugen_verfugt", "Pflasterfugen verfugt", 57.0, False)

    # SHK / Tiefbau-Rohre — KG/HT vor generischem "Rohre gelegt" (sonst SHK-Fehlmatch).
    raw_probe = _normalize_for_match(str(raw_text or ""))
    if "erdaushub" in t and re.search(r"\b(gemacht|durchgeführt|durchgefuehrt)\b", t) and "putz" not in t:
        return CanonicalActivity("graben_ausgehoben", "Graben ausgehoben", 79.0, False)
    if re.search(r"\bkg\b", t) and re.search(r"\b(verlegt|gelegt|eingebaut|montiert)\b", t) and not re.search(
        r"\bkg[\s-]?rohr",
        t,
    ):
        if re.search(r"\b(?:meter|m|lfm|dn|rohr|kanal|entwässerung|entwaesserung)\b", t) or re.search(
            r"\b\d+\s*(?:meter|m|lfm)?\s*kg\b",
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
    if re.search(r"\bheizkreisverteiler\b", t) and re.search(
        r"\b(angeschlossen|montiert|installiert|eingebaut)\b",
        t,
    ):
        return CanonicalActivity("heizungsanschluesse_montiert", "Heizungsanschlüsse montiert", 88.0, False)
    if "heizungsanschl" in t or ("heizung" in t and "ansch" in t):
        return CanonicalActivity("heizungsanschluesse_montiert", "Heizungsanschlüsse montiert", 88.0, False)
    if "wasserleitung" in t or "trinkwasser" in t or "rohrleitung" in t:
        if re.search(r"\b(verlegt|gelegt|montiert|angeschlossen|eingebaut|gemacht)\b", t):
            return CanonicalActivity("wasserleitungen_verlegt", "Wasserleitungen verlegt", 87.0, False)
    if re.search(r"\brohre gelegt\b", t) and not re.search(r"\b(kg|kanal|ht|abwasser)\b", f"{t} {raw_probe}"):
        return CanonicalActivity("wasserleitungen_verlegt", "Wasserleitungen verlegt", 87.0, False)
    if re.search(r"\babzweig(e)?\b", t) and (
        re.search(r"\b(eingebaut|gesetzt|montiert|verbaut|gemacht)\b", t)
        or re.search(r"\babzweig(e)?\b.{0,24}\b(eingebaut|gesetzt|montiert|verbaut|gemacht)\b", raw_probe)
        or (
            re.search(r"\bkg\s+abzweig\b", t)
            and re.search(r"\bgemacht\b", raw_probe)
            and not re.search(r"\bdurch\s+gemacht\b", raw_probe)
        )
    ):
        context_probe = f"{t} | {raw_probe}"
        if "kg" in context_probe or "kanal" in context_probe:
            return CanonicalActivity("kg_abzweig_eingebaut", "KG-Abzweig eingebaut", 63.0, False)
        if "ht" in context_probe or "abwasser" in context_probe:
            return CanonicalActivity("ht_abzweig_eingebaut", "HT-Abzweig eingebaut", 62.0, False)
        return CanonicalActivity("abzweig_eingebaut", "Abzweig eingebaut", 58.0, False)
    if re.search(r"\bb(ö|oe)gen?\b|\bbogen\b", t) and not re.search(
        r"\b(fehlt|fehlte|fehlen|gefehlt|nachleg|nachbestell)\b",
        f"{t} {raw_probe}",
    ) and (
        re.search(r"\b(eingebaut|gesetzt|montiert|verbaut)\b", t)
        or (
            re.search(r"\bgemacht\b", t)
            and not re.search(r"\bdurch\s+gemacht\b", t)
        )
        or re.search(
            r"\bb(ö|oe)gen?\b.{0,24}\b(eingebaut|gesetzt|montiert|verbaut)\b",
            raw_probe,
        )
        or (
            re.search(r"\bkg\s+b(ö|oe)gen\b", t)
            and re.search(r"\b(eingebaut|gesetzt|montiert|verbaut)\b", raw_probe)
        )
    ):
        context_probe = f"{t} | {raw_probe}"
        if "kg" in context_probe or "kanal" in context_probe:
            return CanonicalActivity("kg_boegen_eingebaut", "KG-Bögen eingebaut", 62.5, False)
        if "ht" in context_probe or "abwasser" in context_probe:
            return CanonicalActivity("ht_boegen_eingebaut", "HT-Bögen eingebaut", 61.5, False)
        return CanonicalActivity("boegen_eingebaut", "Bögen eingebaut", 57.5, False)
    if re.search(r"\bmanschette\b", t) and (
        re.search(r"\b(eingebaut|gesetzt|montiert|verbaut)\b", t)
        or re.search(r"\bmanschette\b.{0,24}\b(eingebaut|gesetzt|montiert|verbaut)\b", raw_probe)
    ):
        context_probe = f"{t} | {raw_probe}"
        if "ht" in context_probe or "abwasser" in context_probe:
            return CanonicalActivity("ht_manschette_montiert", "HT-Manschette montiert", 61.0, False)
        return CanonicalActivity("manschette_montiert", "Manschette montiert", 56.0, False)
    if "fußbodenheizung" in t or "fussbodenheizung" in t:
        if re.search(r"\b(verlegt|eingebaut|installiert)\b", t):
            return CanonicalActivity("fussbodenheizung_verlegt", "Fußbodenheizung verlegt", 81.0, False)
    if ("lüftung" in t or "lueftung" in t or "klima" in t) and re.search(r"\b(installiert|eingebaut|montiert)\b", t):
        return CanonicalActivity("lueftung_klima_installiert", "Lüftungs-/Klimatechnik installiert", 69.0, False)
    if re.search(r"\br(ü|ue)cklaufverschraubung(en)?\b", t) and re.search(r"\b(montiert|eingebaut|gesetzt|verschraubt)\b", t):
        return CanonicalActivity("ruecklaufverschraubung_montiert", "Rücklaufverschraubung montiert", 57.0, False)
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
    if ("heizkörper" in t or "heizkoerper" in t) and re.search(r"\b(montiert|angebracht|eingebaut|gemacht)\b", t):
        return CanonicalActivity("heizkoerper_montiert", "Heizkörper montiert", 80.0, False)
    if re.search(r"\b(wc|toilette|wand-wc|stand-wc)\b", t) and re.search(r"\b(montiert|gesetzt|eingebaut|angeschlossen|gemacht)\b", t):
        return CanonicalActivity("wc_montiert", "WC montiert", 80.0, False)
    if re.search(r"\b(waschbecken|waschtisch)\b", t) and re.search(r"\b(montiert|gesetzt|eingebaut|angeschlossen|gemacht)\b", t):
        return CanonicalActivity("waschbecken_montiert", "Waschbecken montiert", 79.0, False)
    if re.search(r"\b(dusche|duschwanne|duschkabine)\b", t) and re.search(r"\b(montiert|gesetzt|eingebaut|angeschlossen|gemacht)\b", t):
        return CanonicalActivity("dusche_montiert", "Dusche montiert", 79.0, False)
    if re.search(r"\b(armatur(en)?|mischer|wasserhahn)\b", t) and re.search(r"\b(montiert|gesetzt|eingebaut|angeschlossen|gemacht)\b", t):
        return CanonicalActivity("armaturen_montiert", "Armaturen montiert", 78.0, False)
    if re.search(r"\b(druckprüfung|druckpruefung|druckprobe|dichtheitsprüfung|dichtheitspruefung)\b", t) and re.search(
        r"\b(durchgeführt|durchgefuehrt|durch\s+gemacht|abgeschlossen|gemacht)\b",
        t,
    ):
        return CanonicalActivity("druckpruefung_durchgefuehrt", "Druckprüfung durchgeführt", 78.0, False)
    if re.search(r"\b(hydraulischer abgleich|abgleich)\b", t) and re.search(
        r"\b(durchgeführt|durchgefuehrt|gemacht)\b",
        t,
    ):
        return CanonicalActivity("hydraulischer_abgleich", "Hydraulischer Abgleich durchgeführt", 77.0, False)

    # Sanierung
    if (
        "altputz" in t
        or "putz runter" in t
        or re.search(r"\b(alten?\s+putz|putz\s+abgetragen|putz\s+ab\s*getragen|altputz)\b", t)
    ):
        return CanonicalActivity("altputz_entfernt", "Altputz entfernt", 91.0, False)
    if re.search(r"\b(geschliffen|angeschliffen)\b", t) and (
        "wand" in t
        or "decke" in t
        or "fassade" in t
        or re.search(r"\b(wand|decke|fassade)\b", (raw_text or "").casefold())
    ):
        return CanonicalActivity("wand_geschliffen", "Wand geschliffen", 72.0, False)
    if "schimmel" in t:
        return CanonicalActivity("schimmel_beseitigt", "Schimmel beseitigt", 85.0, False)
    if "sanierputz" in t:
        return CanonicalActivity("sanierputz_aufgebracht", "Sanierputz aufgebracht", 92.0, False)
    if re.search(r"\bputz\b", t) and re.search(r"\b(drauf|draufgezogen)\b", t) and re.search(
        r"\b(sanier|schimmel)\b",
        f"{t} {str(raw_text or '').casefold()}",
    ):
        return CanonicalActivity("sanierputz_aufgebracht", "Sanierputz aufgebracht", 92.0, False)
    if "grundputz" in t and re.search(r"\b(aufgetragen|aufgebracht|verarbeitet|gemacht)\b", t):
        return CanonicalActivity("grundputz_aufgetragen", "Grundputz aufgetragen", 77.0, False)
    if "unterputz" in t and re.search(
        r"\b(aufgetragen|aufgebracht|verarbeitet|nachgearbeitet|gemacht|aufgezogen|gezogen)\b",
        t,
    ):
        return CanonicalActivity("unterputz_aufgetragen", "Unterputz aufgetragen", 77.0, False)
    if "fassade" in t and re.search(r"\b(gedämmt|gedaemmt)\b", t):
        return CanonicalActivity("wdvs_ausgefuehrt", "WDVS ausgeführt", 73.0, False)
    if ("armierung" in t or "gewebe" in t) and re.search(
        r"\b(hergestellt|aufgebracht|eingebettet|eingebaut|montiert|ausgeführt|ausgefuehrt|gemacht|reingemacht|reingepackt)\b",
        t,
    ):
        raw_probe = _normalize_for_match(str(raw_text or ""))
        if "fassade" in t or re.search(r"\bfassade|fassaden|fas\s+sade\b", raw_probe):
            return CanonicalActivity("fassadenarmierung", "Fassadenarmierung ausgeführt", 72.0, False)
        return CanonicalActivity("armierung_ausgefuehrt", "Armierung ausgeführt", 71.5, False)
    if "reibputz" in t and re.search(
        r"\b(aufgetragen|aufgebracht|verarbeitet|abgerieben|gemacht|geschliffen|angeschliffen|nachgearbeitet)\b",
        t,
    ):
        return CanonicalActivity("reibputz_aufgetragen", "Reibputz aufgetragen", 73.0, False)
    if ("innenputz" in t or "aussenputz" in t or "außenputz" in t) and re.search(
        r"\b(aufgetragen|aufgebracht|verarbeitet|gemacht|strukturiert|gezogen|aufgezogen)\b",
        t,
    ):
        if "innenputz" in t:
            return CanonicalActivity("innenputz_aufgetragen", "Innenputz aufgetragen", 76.0, False)
        return CanonicalActivity("aussenputz_aufgetragen", "Außenputz aufgetragen", 76.0, False)
    if "sockelputz" in t and re.search(r"\b(aufgetragen|aufgebracht|verarbeitet|gemacht)\b", t):
        return CanonicalActivity("sockelputz_aufgetragen", "Sockelputz aufgetragen", 73.0, False)
    if "kratzputz" in t and re.search(r"\b(aufgetragen|aufgebracht|verarbeitet|gemacht)\b", t):
        return CanonicalActivity("kratzputz_aufgetragen", "Kratzputz aufgetragen", 73.0, False)
    if "oberputz" in t and re.search(
        r"\b(aufgetragen|aufgebracht|verarbeitet|gemacht|gezogen|aufgezogen|glatt)\b",
        t,
    ) and not (
        re.search(r"\boffen\b[^.]{0,50}\boberputz\b", t)
        and not re.search(
            r"\boberputz\b[^.]{0,25}\b(aufgetragen|aufgebracht|verarbeitet|gemacht|gezogen|aufgezogen|glatt)\b",
            t,
        )
        and not re.search(
            r"\b(aufgetragen|aufgebracht|verarbeitet|gemacht|gezogen|aufgezogen|glatt)\b[^.]{0,25}\boberputz\b",
            t,
        )
    ):
        return CanonicalActivity("oberputz_aufgetragen", "Oberputz aufgetragen", 78.0, False)
    if re.search(r"\bputz\b", t) and re.search(r"\b(aufgebracht|aufgetragen|verarbeitet)\b", t):
        return CanonicalActivity("putz_aufgebracht", "Putz aufgebracht", 76.0, False)
    if "wdvs" in t and re.search(
        r"\b(gedämmt|gedaemmt|angebracht|montiert|ausgeführt|ausgefuehrt|gemacht|angeklebt)\b",
        t,
    ):
        return CanonicalActivity("wdvs_ausgefuehrt", "WDVS ausgeführt", 73.0, False)
    if "fassade" in t and re.search(r"\b(hergestellt|aufgebracht|eingebettet)\b", t):
        return CanonicalActivity("fassadenarmierung", "Fassadenarmierung ausgeführt", 72.0, False)
    if re.search(r"\bstuckarbeiten\b", t) and re.search(r"\b(gemacht|durchgeführt|durchgefuehrt)\b", t):
        return CanonicalActivity("stuckarbeiten", "Stuckarbeiten durchgeführt", 62.0, False)
    if "stuck" in t and re.search(r"\b(montiert|hergestellt|angebracht|stuckiert|gemacht)\b", t):
        return CanonicalActivity("stuckarbeiten", "Stuckarbeiten durchgeführt", 62.0, False)

    # Hochbau / Tiefbau (breiter Kern)
    if (
        re.search(r"\b(bewehrung|bewehrungsstahl|armierung)\b", t)
        and re.search(r"\b(eingebaut|verlegt|gestellt|verarbeitet|verbaut|gebunden)\b", t)
    ):
        return CanonicalActivity("bewehrung_eingebaut", "Bewehrung eingebaut", 84.0, False)
    if (
        re.search(r"\b(mauerwerk|poroton|porit|porenbeton|ytong|kalksandstein|ks(?:-stein)?|ziegel|stein)\b", t)
        and re.search(r"\b(gemauert|gebaut|erstellt|gesetzt|verarbeitet|hochgezogen|aufgemauert|hochgemauert|gemacht)\b", t)
        and "gartenmauer" not in t
    ):
        qty = _extract_qty_m2(t)
        text = f"{_qty_prefix(raw_text)}{qty} m² Mauerwerk erstellt" if qty else "Mauerwerk erstellt"
        return CanonicalActivity("mauerwerk_erstellt", text, 84.0, bool(qty))
    if re.search(r"\bfundamentplatte\b", t) and re.search(r"\bbetoniert\b", t):
        qty = _extract_qty_m3(t)
        text = f"{_qty_prefix(raw_text)}{qty} m³ Beton eingebracht" if qty else "Beton eingebracht"
        return CanonicalActivity("beton_eingebracht", text, 86.0, bool(qty))
    if re.search(r"\bfundamentplatte\b", t) and re.search(
        r"\b(geschalt|erstellt|gebaut|gestellt)\b",
        t,
    ):
        return CanonicalActivity("schalung_erstellt", "Schalung erstellt", 83.0, False)
    if "schalung" in t and re.search(
        r"\b(erstellt|gestellt|gebaut|aufgebaut|aufgestellt|montiert|gesetzt|aufgeschlagen|gemacht|gelassen|stehen\s*gelassen)\b",
        t,
    ):
        return CanonicalActivity("schalung_erstellt", "Schalung erstellt", 83.0, False)
    if re.search(r"\b(stra(ß|ss)enabl(ä|ae)uf|gully)\b", t) and re.search(
        r"\b(gesetzt|montiert|eingebaut)\b",
        t,
    ):
        return CanonicalActivity("strassenablauf_gesetzt", "Straßenabläufe gesetzt", 82.0, False)
    if "beton" in t and "betonfundament" not in t and re.search(r"\b(gegossen|eingebracht|verarbeitet|gemacht)\b", t):
        qty = _extract_qty_m3(t)
        text = f"{qty} m³ Beton eingebracht" if qty else "Beton eingebracht"
        return CanonicalActivity("beton_eingebracht", text, 86.0, bool(qty))
    if re.search(r"\b(betondecke|decke)\b", t) and re.search(r"\b(gegossen|eingebracht)\b", t) and "beton" in str(
        raw_text or ""
    ).casefold():
        return CanonicalActivity("beton_eingebracht", "Beton eingebracht", 86.0, False)
    if ("erdaushub" in t or "baugrube" in t) and re.search(
        r"\b(gemacht|durchgeführt|durchgefuehrt|erstellt|ausgeführt|ausgefuehrt)\b",
        t,
    ):
        return CanonicalActivity("graben_ausgehoben", "Graben ausgehoben", 79.0, False)
    if ("aushub" in t or "erdarbeiten" in t) and (
        re.search(
            r"\b(ausgeführt|ausgefuehrt|durchgeführt|durchgefuehrt|durch\s+gemacht|gemacht|erstellt)\b",
            t,
        )
        or (t.strip().startswith("erdarbeiten") and "durch" in t)
    ):
        return CanonicalActivity("erdarbeiten", "Erdarbeiten durchgeführt", 78.0, False)
    if ("graben" in t or "baugrube" in t or "grube" in t or "gebaggert" in t or "bagger" in t) and re.search(
        r"\b(ausgehoben|ausgeschachtet|erstellt|gezogen|gegraben|gebaggert|gemacht)\b",
        t,
    ):
        return CanonicalActivity("graben_ausgehoben", "Graben ausgehoben", 79.0, False)
    if "boden" in t and re.search(r"\b(ausgeschachtet|ausgehoben)\b", t) and "putz" not in t:
        return CanonicalActivity("boden_ausgeschachtet", "Boden ausgeschachtet", 80.0, False)
    if (
        re.search(r"\b(ausgeschachtet|ausgehoben)\b", t)
        and "putz" not in t
        and re.search(r"\bboden\b", (raw_text or "").casefold())
        and (len(t.split()) <= 3 or "boden" in t)
    ):
        return CanonicalActivity("boden_ausgeschachtet", "Boden ausgeschachtet", 80.0, False)
    if re.search(r"\bsand\b", t) and re.search(
        r"\b(eingebaut|eingebracht|reingepackt|reingemacht|rein gemacht|eingepackt|verfüllt|verfuellt|rein)\b",
        t,
    ):
        return CanonicalActivity("sand_eingebaut", "Sand eingebaut", 74.0, False)
    if re.search(
        r"\b(verfüllt|verfuellt|verfüllen|verfuellen|aufgefüllt|aufgefuellt)\b",
        t,
    ) and (
        ("graben" in t or "gräben" in t or "graeben" in t or "grube" in t or "baugrube" in t)
        # Subjekt-Fallback fuer Aufzaehlungen wie "Graben ausgehoben und verfüllt":
        # nur wenn der Chunk kein konkurrierendes Subjekt (Fuge/Pflaster/Beton) traegt.
        or (
            not re.search(r"\b(fuge|fugen|silikon|pflaster|beton)\b", t)
            and re.search(r"\b(graben|gräben|graeben|baugrube|grube)\b", (raw_text or "").casefold())
        )
    ):
        return CanonicalActivity("graben_verfuellt", "Graben verfüllt", 77.0, False)
    if "frostschutz" in t and re.search(r"\b(eingebaut|eingebracht|verlegt|reingepackt|reingemacht)\b", t):
        return CanonicalActivity("frostschutz_eingebaut", "Frostschutz eingebaut", 78.5, False)
    if "planum" in t and re.search(r"\b(hergestellt|erstellt|gemacht)\b", t):
        return CanonicalActivity("planum_hergestellt", "Planum hergestellt", 79.5, False)
    if "planum" in t and re.search(r"\bverdichtet\b", t):
        tiefbau_ctx = re.search(
            r"\b(schotter|splitt|kg|graben|frostschutz|sand|erdaushub|erdarbeiten|bagger)\b",
            t,
        ) or re.search(
            r"\b(schotter|splitt|kg\s*rohr|graben|frostschutz|erdaushub|bagger)\b",
            (raw_text or "").casefold(),
        )
        if not tiefbau_ctx:
            return CanonicalActivity("planum_hergestellt", "Planum hergestellt", 79.5, False)
    if re.search(r"\b(verdichtet|verdichtung|verdichten)\b", t) and (
        ("untergrund" in t or "grube" in t or "baugrube" in t or "sand" in t or "planum" in t)
        or (
            not re.search(r"\b(beton|estrich|fuge|fugen|pflaster)\b", t)
            and re.search(
                r"\b(untergrund|grube|baugrube|graben|gräben|graeben|planum|schotter|frostschutz|sand)\b",
                (raw_text or "").casefold(),
            )
        )
    ):
        return CanonicalActivity("untergrund_verdichtet", "Untergrund verdichtet", 76.5, False)
    if ("drainage" in t or "entwässerung" in t or "entwaesserung" in t) and re.search(
        r"\b(eingebaut|hergestellt|verlegt|gelegt)\b",
        t,
    ):
        return CanonicalActivity("drainage_entwaesserung", "Drainage/Entwässerung eingebaut", 75.0, False)
    if ("kanal" in t or "schacht" in t) and re.search(r"\b(angeschlossen|gesetzt|eingebaut|betoniert)\b", t):
        return CanonicalActivity("kanal_schacht", "Kanal-/Schachtarbeiten durchgeführt", 77.0, False)
    if re.search(r"\b(leitungstrasse|leitungs-?trasse|trasse)\b", t) and re.search(
        r"\b(hergestellt|erstellt|gebaut|angelegt|gemacht)\b",
        t,
    ):
        return CanonicalActivity("leitungstrasse_hergestellt", "Leitungstrasse hergestellt", 76.0, False)
    if re.search(r"\b(hausanschluss|hausanschlüsse|hausanschluesse)\b", t) and re.search(
        r"\b(hergestellt|angeschlossen|eingebaut|gemacht)\b",
        t,
    ):
        return CanonicalActivity("hausanschluss_hergestellt", "Hausanschluss hergestellt", 78.0, False)
    if "asphalt" in t and re.search(r"\b(quadrat|quadrate|quadraten|m²|m2|qm)\b", t):
        qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text or "")
        text = f"{_qty_prefix(raw_text)}{qty} m² Asphalt eingebaut" if qty else "Asphalt eingebaut"
        return CanonicalActivity("asphalt_eingebaut", text, 77.5, bool(qty))
    if "asphalt" in t and re.search(
        r"\b(schneiden|schneide|geschnitten|aufgeschnitten|trennen|aufschneiden)\b",
        t,
    ):
        qty = _extract_qty_lfm(t) or _extract_qty_lfm(raw_text or "")
        text = f"{qty} m Asphalt schneiden" if qty else "Asphalt schneiden"
        return CanonicalActivity("asphalt_schneiden", text, 84.0, bool(qty))
    if re.search(r"\b(asphalt|deckschicht)\b", t) and re.search(r"\b(fräsen|fraesen|gefräst|gefraest|abgefräst|abgefraest|abfräsen|abfraesen)\b", t):
        return CanonicalActivity("asphalt_fraesen", "Asphalt fräsen", 84.0, False)
    if re.search(r"\basphalt\s*fräse\b", t):
        return CanonicalActivity("asphalt_fraesen", "Asphalt fräsen", 84.0, False)
    if "asphalt" in t and re.search(r"\b(eingebaut|eingebracht|asphaltiert|verteilt)\b", t):
        qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text or "")
        text = f"{_qty_prefix(raw_text)}{qty} m² Asphalt eingebaut" if qty else "Asphalt eingebaut"
        return CanonicalActivity("asphalt_eingebaut", text, 77.0, bool(qty))
    if "asphalt" in t and re.search(r"\b(walzen|verdichten|verdichtet)\b", t):
        qty = _extract_qty_m2(t) or _extract_qty_m2(raw_text or "")
        text = f"{_qty_prefix(raw_text)}{qty} m² Asphalt verdichten" if qty else "Asphalt verdichten"
        return CanonicalActivity("asphalt_verdichten", text, 81.0, bool(qty))
    if re.search(r"\bfrostschutz(?:schicht)?\b", t) and re.search(
        r"\b(hergestellt|eingebaut|eingebracht|erstellt|verlegt)\b",
        t,
    ):
        return CanonicalActivity("frostschutzschicht_hergestellt", "Frostschutzschicht hergestellt", 81.5, False)
    if re.search(r"\b(schottertragschicht|sts)\b", t) and re.search(
        r"\b(hergestellt|eingebaut|eingebracht|erstellt)\b",
        t,
    ):
        return CanonicalActivity("schottertragschicht_hergestellt", "Schottertragschicht hergestellt", 81.0, False)
    if re.search(r"\b(hochbord|tiefbord|borde)\b", t) and re.search(
        r"\b(gesetzt|verlegt|gestellt|montiert)\b",
        t,
    ):
        return CanonicalActivity("borde_gesetzt", "Borde gesetzt", 83.5, False)
    if re.search(r"\b(rinnenstein(?:e|en)?|muldenstein(?:e|en)?)\b", t) and re.search(
        r"\b(gesetzt|verlegt|gestellt)\b",
        t,
    ):
        return CanonicalActivity("rinnensteine_gesetzt", "Rinnensteine gesetzt", 82.5, False)
    if re.search(r"\b(stra(ß|ss)enabl(ä|ae)uf|gully)\b", t) and re.search(
        r"\b(gesetzt|montiert|eingebaut)\b",
        t,
    ):
        return CanonicalActivity("strassenablauf_gesetzt", "Straßenabläufe gesetzt", 82.0, False)
    if re.search(r"\b(schichtenverbund|haftbr(ü|ue)cke)\b", t) and re.search(
        r"\b(hergestellt|aufgetragen|eingebracht)\b",
        t,
    ):
        return CanonicalActivity("schichtenverbund_hergestellt", "Schichtenverbund hergestellt", 79.0, False)
    if re.search(r"\b(naht|nähte|asphaltnaht)\b", t) and re.search(
        r"\b(hergestellt|erstellt|verschlossen)\b",
        t,
    ):
        return CanonicalActivity("naehte_hergestellt", "Nähte hergestellt", 78.5, False)

    catalog_match = match_catalog_activity(t)
    if catalog_match and not (
        catalog_match.intent == "strassenbau_ausgefuehrt" and "asphalt" in t
    ):
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
        "zwanzig": "20",
        "dreißig": "30",
        "dreissig": "30",
        "vierzig": "40",
        "fünfzig": "50",
        "fuenfzig": "50",
        "sechzig": "60",
        "siebzig": "70",
        "achtzig": "80",
        "neunzig": "90",
        "fünfundzwanzig": "25",
        "funfundzwanzig": "25",
        "vierundzwanzig": "24",
        "dreiunddreißig": "33",
        "dreiunddreissig": "33",
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
        (r"\b(.{4,60}?)\s+(gemäht|gemaeht)\b", "gemäht"),
        (r"\b(.{4,60}?)\s+(getrimmt)\b", "getrimmt"),
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
    if not re.search(r"\b(verfugt|fuge|fugen|fugenmörtel|fugenmoertel|zugemacht|nachgezogen)\b", t):
        return False
    raw = str(raw_text or "").casefold()
    fliesen_cues = (
        "fliese",
        "fliesen",
        "wandfliesen",
        "bodenfliesen",
        "mosaikfliesen",
        "mosaik",
        "feinsteinzeug",
        "naturstein",
        "fliesenkleber",
        "flexkleber",
        "fugenmörtel",
        "fugenmoertel",
        "bodenablauf",
        "duschrinne",
        "ablaufrinne",
    )
    trockenbau_cues = ("gipskarton", "rigips", "trockenbau", "fugenspachtel", "schnellbauschrauben")
    pflaster_cues = ("pflaster", "splitt", "fuge mit sand", "fugenmaterial")
    if any(c in t for c in trockenbau_cues) or any(c in raw for c in trockenbau_cues):
        return False
    if any(c in t for c in pflaster_cues) or any(c in raw for c in pflaster_cues):
        return False
    return any(c in t for c in fliesen_cues) or any(c in raw for c in fliesen_cues)


def _raw_has_trockenbau_context(raw_text: str) -> bool:
    raw_cf = str(raw_text or "").casefold()
    return bool(
        re.search(
            r"gips\s*karton|rigips|ri\s+gips|gk[\s-]?platten|knauf|trocken\s*bau|"
            r"ständerwerk|staender\s*werk|cw\s*profil|uw\s*profil|akustik\s*decke|"
            r"schnell\s*bau\s*schrauben|doppelständerwand|beide\s+seiten\s+beplankt",
            raw_cf,
        )
    )


def _is_trockenbau_fuge_context(t: str, *, raw_text: str = "") -> bool:
    if not re.search(
        r"\b(fuge|fugen|fugenspachtel|gespachtelt|verspachtelt|nachgespachtelt|zugemacht|zu\s+gemacht|nachzu\s+gemacht)\b",
        t,
    ):
        return False
    if _raw_has_trockenbau_context(raw_text):
        return True
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
    return any(c in t for c in trockenbau_cues)


def _is_pflaster_fuge_context(t: str, *, raw_text: str = "") -> bool:
    if not re.search(r"\b(fuge|fugen|verfugt|verfüllt|verfuellt)\b", t):
        return False
    if re.search(r"\b(graben|gräben|graeben|baugrube)\b", t) and re.search(
        r"\b(verfüllt|verfuellt|verfüllen|verfuellen)\b",
        t,
    ):
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
    if has_quantified_edge_stone:
        filtered: list[str] = []
        for item in out:
            low = str(item).casefold()
            if "randsteine gesetzt" in low or "rasenkantensteine gesetzt" in low:
                has_qty = "lfm" in low or "stück" in low or bool(re.search(r"\b\d+(?:[.,]\d+)?\b", low))
                if not has_qty:
                    continue
            filtered.append(item)
        out = filtered

    # Generische Formteile durch gewerkspezifische Varianten ersetzen.
    has_kg_bogen = any("kg-bögen eingebaut" in str(x).casefold() for x in out)
    has_ht_bogen = any("ht-bögen eingebaut" in str(x).casefold() for x in out)
    has_kg_abzweig = any("kg-abzweig eingebaut" in str(x).casefold() for x in out)
    has_ht_abzweig = any("ht-abzweig eingebaut" in str(x).casefold() for x in out)
    # Bewehrungs-Dedupe: "Bewehrung eingebaut" (kanonisch) schlaegt jede
    # Variante mit "Bewehrungsstahl/Bewährungsstahl" - es ist dieselbe Sache.
    has_bewehrung = any(
        re.match(r"^bewehrung\s+(eingebaut|verlegt|gestellt)$", str(x).casefold())
        for x in out
    )
    cleaned: list[str] = []
    for item in out:
        low = str(item).casefold()
        if (has_kg_bogen or has_ht_bogen) and low == "bögen eingebaut":
            continue
        if (has_kg_abzweig or has_ht_abzweig) and low == "abzweig eingebaut":
            continue
        if has_bewehrung and re.search(r"\bbew(?:e|ä|ae)hrungsstahl\b", low):
            continue
        cleaned.append(item)
    return cleaned

