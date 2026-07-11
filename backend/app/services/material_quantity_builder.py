"""Material mit Mengen/Einheiten aus Rohtext — PANZEK-tauglich (additiv).

Erkennt u. a.:
- Standardmengen: t, m³, m², m, St., Sack, Rolle
- LKW-Ladungen: „6 LKW HT Bodenaushub“
- Entsorgung: „22 t Boden entsorgt“, „9,3 t Asphalt entsorgt“
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MaterialLine:
    quantity: str
    unit: str
    description: str

    def display(self) -> str:
        q = self.quantity.strip()
        u = self.unit.strip()
        d = self.description.strip()
        if q and u:
            return f"{q} {u} {d}".strip()
        return d


_UNIT_ALIASES: dict[str, str] = {
    "ton": "t",
    "tonnen": "t",
    "to": "t",
    "m3": "m³",
    "kubikmeter": "m³",
    "kubik": "m³",
    "qm": "m²",
    "m2": "m²",
    "quadratmeter": "m²",
    "met": "m",
    "meter": "m",
    "lfm": "lfm",
    "st": "St.",
    "stk": "St.",
    "stück": "St.",
    "stueck": "St.",
    "sa": "Sack",
    "sak": "Sack",
    "sack": "Sack",
    "säcke": "Sack",
    "saeck": "Sack",
    "rol": "Rolle",
    "rolle": "Rolle",
    "rollen": "Rolle",
    "lkw": "LKW",
}

_ENTSORG_SUBSTANCE = (
    r"(?:boden|bauschutt|asphalt|erdaushub|aushub|beton(?:aushub)?|schotter|mischgut)"
)

_DISPOSAL_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        rf"(?P<qty>\d+(?:[.,]\d+)?)\s*(?:t|ton|tonnen|to)\s+(?P<sub>{_ENTSORG_SUBSTANCE})\s+entsorg",
        rf"(?P<qty>\d+(?:[.,]\d+)?)\s*(?:t|ton|tonnen|to)\s+entsorg(?:ung|t|en)?\s+(?:von\s+)?(?P<sub>{_ENTSORG_SUBSTANCE})",
        rf"(?P<sub>{_ENTSORG_SUBSTANCE})\s+entsorg(?:t|en|ung)\s+(?P<qty>\d+(?:[.,]\d+)?)\s*(?:t|ton|tonnen|to)",
        rf"entsorg(?:ung|t|en)?\s+(?:von\s+)?(?P<sub>{_ENTSORG_SUBSTANCE})\s+(?P<qty>\d+(?:[.,]\d+)?)\s*(?:t|ton|tonnen|to)",
    )
)

_LKW_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"(?P<qty>\d+)\s*(?:x\s*)?lkw\s+(?:(?P<prefix>ht|up)\s+)?(?P<desc>[a-zäöüß][a-zäöüß0-9/.\- ]{0,40}?)(?=\s+sowie|\s+und|\s+\d|\s*\.|,|$)",
        r"(?P<qty>\d+)\s*(?:x\s*)?lkw(?:\s*ladung(?:en)?)?\s+(?:mit\s+)?(?P<desc>[a-zäöüß][a-zäöüß0-9/.\- ]{0,40}?)(?=\s+sowie|\s+und|\s+\d|\s*\.|,|$)",
    )
)

_QTY_UNIT_DESC = re.compile(
    r"(?P<qty>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>t|ton|tonnen|to|m³|m3|kubikmeter|kubik|qm|m²|m2|quadratmeter|"
    r"met|meter|m(?![²³23])|lfm|st\.?|stk|stück|stueck|sa\.?|sak|sack|säcke|saeck|rolle?|rollen)\s+"
    r"(?P<desc>[a-zäöüß0-9/.\-° ]{2,48})"
    r"(?=\s+(?:eingebaut|eingebracht|verarbeitet|verlegt|gelegt|aufgetragen|danach|und dann|sowie|dann)\b|[,.!?]|$)",
    re.IGNORECASE,
)

_WORD_NUM = (
    r"(?:ein|eine|eins|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|"
    r"\d+(?:[.,]\d+)?)"
)
_WORD_KUBIK_MAT = re.compile(
    rf"(?P<qty>{_WORD_NUM})\s+kubik(?:meter)?\s+"
    r"(?P<mat>split|splitt|schotter|beton|sand|kies)\b"
    r"(?:\s+(?P<frac>zwei\s+fünfer|zwei\s+fuenfer|\d+\s*/\s*\d+|null\s+\d+))?",
    re.IGNORECASE,
)

_DESC_STOP = re.compile(
    r"\b(?:eingebaut|eingebracht|verarbeitet|verlegt|gelegt|aufgetragen|danach|und dann|sowie|dann)\b",
    re.IGNORECASE,
)

# Mengen + Oberflächenarbeit (z. B. „50 m² Pflaster gelegt“) sind Tätigkeiten, keine Materialzeilen.
_WORK_SURFACE_MAT_SKIP = re.compile(
    r"\b(?:"
    r"pflaster|rasen|rasenkante|borde|randstein|hecke|unkraut|laub|terrasse|"
    r"oberputz|unterputz|innenputz|außenputz|aussenputz|grundputz|sockelputz|reibputz|kratzputz"
    r")\b.*\b(?:"
    r"gelegt|verlegt|gesetzt|gemäht|gemaeht|getrimmt|geschnitten|entfernt|"
    r"aufgetragen|aufgebracht|verarbeitet|geglättet|geglaettet|filziert|eingedeckt|"
    r"eingebaut|eingebracht"
    r")\b",
    re.IGNORECASE,
)

_TOK_BAND = re.compile(
    r"(?P<qty>\d+(?:[.,]\d+)?)\s*(?:m|met|meter)\s+tok[\s-]?band",
    re.IGNORECASE,
)

_ASPHALT_MIX = re.compile(
    r"(?P<qty>\d+(?:[.,]\d+)?)\s*(?:t|ton|tonnen|to)\s+asphalt\s+0\s*/\s*\d+",
    re.IGNORECASE,
)


def _norm_qty(value: str) -> str:
    return str(value or "").strip().replace(".", ",")


def _norm_unit(raw: str) -> str:
    key = str(raw or "").strip().casefold().rstrip(".")
    if key == "m":
        return "m"
    return _UNIT_ALIASES.get(key, raw.strip())


def _norm_key(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().casefold())


def _disposal_label(substance: str) -> str:
    sub = str(substance or "").strip().casefold()
    mapping = {
        "boden": "Boden entsorgt",
        "bauschutt": "Bauschutt entsorgt",
        "asphalt": "Asphalt entsorgt",
        "erdaushub": "Erdaushub entsorgt",
        "aushub": "Aushub entsorgt",
        "beton": "Beton entsorgt",
        "betonaushub": "Beton entsorgt",
        "schotter": "Schotter entsorgt",
        "mischgut": "Mischgut entsorgt",
    }
    for needle, label in mapping.items():
        if needle in sub:
            return label
    return f"{substance.strip().title()} entsorgt"


def _clean_desc(text: str) -> str:
    t = re.sub(r"\s+", " ", str(text or "").strip(" .,;:-"))
    t = re.sub(r"\b(und|sowie|dann|danach|außerdem|ausserdem)\b$", "", t, flags=re.IGNORECASE).strip()
    t = re.sub(
        r"\s+(?:verdichtet|verarbeitet|eingebaut|eingebracht|verlegt|gelegt)$",
        "",
        t,
        flags=re.IGNORECASE,
    )
    if not t:
        return ""
    return t[0].upper() + t[1:] if t[0].islower() else t


def _line_key(line: MaterialLine) -> str:
    return _norm_key(f"{line.quantity}|{line.unit}|{line.description}")


def _material_key_from_display(text: str) -> str:
    low = _norm_key(text)
    low = re.sub(r"^\d+(?:,\d+)?\s+\S+\s+", "", low)
    return low


def _normalize_material_probe(text: str) -> str:
    t = re.sub(r"\s+", " ", str(text or "").strip())
    t = re.sub(r"\bbau\s+schutt\b", "bauschutt", t, flags=re.IGNORECASE)
    t = re.sub(r"\bboden\s+aushub\b", "bodenaushub", t, flags=re.IGNORECASE)
    return t


def _word_to_qty(word: str) -> str:
    key = str(word or "").strip().casefold()
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
    }
    if key in mapping:
        return mapping[key]
    val = key.replace(",", ".")
    return val if re.fullmatch(r"\d+(?:\.\d+)?", val) else word.strip()


def _normalize_fraction_token(frac: str | None) -> str:
    raw = str(frac or "").strip()
    if not raw:
        return ""
    low = raw.casefold()
    if re.search(r"zwei\s+fünfer|zwei\s+fuenfer", low):
        return "2/5"
    m = re.search(r"null\s+(\d+)", low)
    if m:
        return f"0/{m.group(1)}"
    m = re.search(r"(\d+)\s*/\s*(\d+)", raw)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return raw


def _material_label_from_match(mat: str, frac: str | None = None) -> str:
    name = "Splitt" if str(mat or "").casefold() in {"split", "splitt"} else str(mat or "").strip().title()
    frac_norm = _normalize_fraction_token(frac)
    if frac_norm:
        return f"{name} {frac_norm}"
    return name


def _trim_material_desc(desc: str) -> str:
    t = re.sub(r"\s+", " ", str(desc or "").strip(" .,;:-"))
    m = _DESC_STOP.search(t)
    if m:
        t = t[: m.start()].strip(" .,;:-")
    t = re.sub(r"\bnull\s+(\d+)\b", r"0/\1", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(zwei\s+fünfer|zwei\s+fuenfer)\b", "2/5", t, flags=re.IGNORECASE)
    return _clean_desc(t)


def extract_quantified_materials(raw_text: str) -> list[str]:
    """Extrahiert Materialzeilen mit Menge/Einheit/Bezeichnung aus Rohtext."""
    probe = _normalize_material_probe(raw_text)
    if not probe:
        return []

    found: list[MaterialLine] = []
    seen_spans: list[tuple[int, int]] = []

    def _overlap(start: int, end: int) -> bool:
        return any(not (end <= s or start >= e) for s, e in seen_spans)

    def _add(line: MaterialLine, start: int, end: int) -> None:
        if not line.description:
            return
        if _overlap(start, end):
            return
        key = _line_key(line)
        if any(_line_key(x) == key for x in found):
            return
        seen_spans.append((start, end))
        found.append(line)

    for pat in _DISPOSAL_PATTERNS:
        for m in pat.finditer(probe):
            sub = m.group("sub")
            qty = m.group("qty")
            if not sub or not qty:
                continue
            _add(
                MaterialLine(_norm_qty(qty), "t", _disposal_label(sub)),
                m.start(),
                m.end(),
            )

    for pat in _LKW_PATTERNS:
        for m in pat.finditer(probe):
            qty = m.group("qty")
            desc = m.group("desc") or ""
            prefix = (m.groupdict().get("prefix") or "").strip().upper()
            desc = _clean_desc(desc)
            if prefix and not desc.upper().startswith(prefix):
                desc = f"{prefix} {desc}".strip()
            if not qty or not desc:
                continue
            _add(MaterialLine(_norm_qty(qty), "LKW", desc), m.start(), m.end())

    for m in _TOK_BAND.finditer(probe):
        _add(MaterialLine(_norm_qty(m.group("qty") or ""), "m", "TOK-Band"), m.start(), m.end())

    for m in _ASPHALT_MIX.finditer(probe):
        desc = "Asphalt 0/11"
        mmix = re.search(r"0\s*/\s*(\d+)", m.group(0))
        if mmix:
            desc = f"Asphalt 0/{mmix.group(1)}"
        _add(MaterialLine(_norm_qty(m.group("qty") or ""), "t", desc), m.start(), m.end())

    for m in _WORD_KUBIK_MAT.finditer(probe):
        qty = _word_to_qty(m.group("qty") or "")
        label = _material_label_from_match(m.group("mat") or "", m.group("frac"))
        if qty and label:
            _add(MaterialLine(_norm_qty(qty), "m³", label), m.start(), m.end())

    for m in _QTY_UNIT_DESC.finditer(probe):
        desc = _trim_material_desc(m.group("desc") or "")
        if not desc or len(desc) > 48:
            continue
        low_desc = desc.casefold()
        if re.search(r"\bentsorg", low_desc):
            continue
        if re.search(r"\b(lkw|stunden|std|uhr|bis)\b", low_desc):
            continue
        if re.search(r"^(bagger|radlader|walze|kran|stampfer|dumper)\b", low_desc):
            continue
        if _WORK_SURFACE_MAT_SKIP.search(low_desc):
            continue
        unit = _norm_unit(m.group("unit") or "")
        if unit in {"m²", "m2", "qm", "quadratmeter"} and re.fullmatch(
            r"pflaster(?:steine)?", low_desc.strip()
        ):
            continue
        if re.search(
            r"\b(?:legen|verlegen|schneiden|auftragen|montieren|fertigstellen|"
            r"abschließen|abschliessen|betonieren|asphaltieren|einbauen)\s*$",
            low_desc,
        ):
            continue
        _add(
            MaterialLine(_norm_qty(m.group("qty") or ""), unit, desc),
            m.start(),
            m.end(),
        )

    return [x.display() for x in found]


def _attach_quantity_if_missing(material: str, raw_text: str) -> str:
    """Versucht, einer bestehenden Materialzeile eine Menge aus dem Rohtext zuzuordnen."""
    mat = str(material or "").strip()
    if not mat:
        return mat
    if re.match(r"^\d", mat):
        return mat

    mat_key = _material_key_from_display(mat)
    probe = re.sub(r"\s+", " ", str(raw_text or ""))
    if not probe:
        return mat

    # Entsorgung: Substanz im Material, Menge im Text
    if "entsorg" in mat_key:
        for pat in _DISPOSAL_PATTERNS:
            m = pat.search(probe)
            if m and mat_key in _disposal_label(m.group("sub") or "").casefold():
                return MaterialLine(_norm_qty(m.group("qty") or ""), "t", mat).display()

    escaped = re.escape(mat_key)
    m = re.search(
        rf"(?P<qty>\d+(?:[.,]\d+)?)\s*"
        rf"(?P<unit>t|ton|tonnen|to|m³|m3|kubikmeter|qm|m²|m2|quadratmeter|met|meter|m|lfm|st\.?|stk|sack|sa\.?|rolle?|lkw)\s+"
        rf"(?P<desc>[^.!?]{{0,80}}{escaped}[^.!?]{{0,40}})",
        probe,
        flags=re.IGNORECASE,
    )
    if m:
        unit = _norm_unit(m.group("unit") or "")
        desc = mat if mat_key in _norm_key(m.group("desc") or "") else _clean_desc(m.group("desc") or mat)
        return MaterialLine(_norm_qty(m.group("qty") or ""), unit, desc).display()

    if mat_key in {"splitt", "split"}:
        wm = _WORD_KUBIK_MAT.search(probe)
        if wm:
            qty = _word_to_qty(wm.group("qty") or "")
            label = _material_label_from_match(wm.group("mat") or "", wm.group("frac"))
            if qty and label:
                return MaterialLine(_norm_qty(qty), "m³", label).display()

    return mat


def enrich_materials_list(materials: Iterable[str], raw_text: str) -> list[str]:
    """Reichert Materialien an: Mengen formatieren, LKW/Entsorgung aus Text ergänzen."""
    base = [str(x).strip() for x in materials if str(x).strip()]
    extracted = extract_quantified_materials(raw_text)

    out: list[str] = []
    seen: set[str] = set()

    def _push(item: str) -> None:
        val = str(item or "").strip()
        if not val:
            return
        key = _material_key_from_display(val)
        if key in seen:
            return
        seen.add(key)
        out.append(val)

    for mat in base:
        _push(_attach_quantity_if_missing(mat, raw_text))

    for item in extracted:
        _push(item)

    return out
