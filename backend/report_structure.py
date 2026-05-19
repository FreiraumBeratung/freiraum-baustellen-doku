"""
Regelbasierte Strukturierung von Tagesbericht-Rohtext (Sprint 8).

Keine LLM-Anbindung — rein lokale Schlagwort-/Satz-Muster für DEV/V1.

Manuelle Checks (ohne pytest):
    cd backend
    py -3.13 -m report_structure
"""

from __future__ import annotations

import re
from typing import Any

# ── Tätigkeit: häufige Partizipformen und Arbeitsschrift ─────────────────────
ACTIVITY_MARKERS = (
    "gemacht",
    "gebaut",
    "gelegt",
    "gepflastert",
    "vorbereitet",
    "eingebaut",
    "montiert",
    "installiert",
    "angeschlossen",
    "gestrichen",
    "gespachtelt",
    "verlegt",
    "abgerissen",
    "gereinigt",
    "verdichtet",
    "gesetzt",
    "repariert",
    "ausgetauscht",
    "geprüft",
    # bewährt aus V1:
    "betoniert",
    "verputzt",
    "gebohrt",
    "demontiert",
    "transportiert",
    "verfugt",
    "ausgeführt",
    "gearbeitet",
    "geschraubt",
)

# ── Material: nur mit explizitem Materialbezug („Pflaster“ allein ohne Hinweis = nicht automatisch Material) ─
MATERIAL_HINTS = (
    "material",
    "verbaut",
    "verwendet",
    "gebraucht",
    "geliefert",
    "bestellt",
    "nachbestell",
    "fehlt an material",
    "material fehlt",
    "materialfehlt",
    "material mangel",
    "lieferung fehlt",
    "schotter",
    "splitt",
    "pflastersteine",
    "pflaster steine",
    "randstein",
    "zement",
    "beton",
    "rohr",
    "kabel",
    "farbe",
    "platte",
    "dämmung",
    "daemmung",
    "holz",
    "schraub",
    "palette",
    "paletten",
    "mörtel",
    "mortel",
)

PROBLEM_TRIGGERS = (
    "problem",
    "schwierig",
    "kaputt",
    "defekt",
    "nicht funktion",
    "funktioniert nicht",
    "verzög",
    "verzoeg",
    "kunde nicht da",
    "auftraggeber nicht da",
    "material fehlt",
    "lieferung fehlt",
    "konnte nicht",
    "konnten nicht",
)

OPEN_HINT_PHRASES = (
    "fehlt noch",
    "fehlen noch",
    "muss noch",
    "musste noch",
    "mussten noch",
    "muss ich noch",
    "müssen wir noch",
    "muessen wir noch",
    " morgen",
    "übermorgen",
    "uebermorgen",
    " nächste woche",
    " naechste woche",
    "offen bleib",
    "nachliefer",
    "nachzuliefer",
    " noch zu bestellen",
    " nachbestell",
    " noch zu klären",
    " noch zu klaer",
    "warten auf",
)


def _open_hint_match(lower_sentence: str) -> bool:
    """„offen“ nur als eigenes Wort; Phrasen substrings gegen normalisierten Text."""
    sl = lower_sentence.strip()
    padded = f" {sl} "
    for p in OPEN_HINT_PHRASES:
        needle = p.strip()
        if needle in padded or needle in sl:
            return True
    if re.search(r"\boffen\b", sl):
        return True
    if re.match(r"^morgen\b", sl):
        return True
    return False


CUSTOMER_HINTS = (
    " kunde ",
    "kunden",
    "kundin",
    "bauherr",
    "auftraggeber",
    "gesprochen",
    "informiert",
    "abgesprochen",
    "war zufrieden",
    "freigegeben",
    "rücksprache",
    "ruecksprache",
)


def _lw(text: str) -> str:
    return f" {text.strip().lower()} "


def _strip_clause(s: str) -> str:
    t = (s or "").strip()
    return re.sub(r"[.!?,:;]+$", "", t).strip()


def _fragment_has_activity(lw: str) -> bool:
    return any(marker in lw for marker in ACTIVITY_MARKERS)


def _fragment_has_material_hint(lw: str) -> bool:
    return any(h in lw for h in MATERIAL_HINTS)


def _sentence_has_problem(lower_sentence: str) -> bool:
    """Probleme: Phrasen + Wortgrenzen wo nötig (Regen/Wetter …)."""
    s = lower_sentence.strip().lower()
    if any(ph in s for ph in PROBLEM_TRIGGERS):
        return True
    if re.search(r"\bfehl", s):  # fehlt/fehlen/fehlend …
        return True
    if re.search(r"\bregen\b", s):
        return True
    if re.search(r"\bknapp\b", s):
        return True
    return False


def _sentence_has_customer(lw: str) -> bool:
    return any(h in lw for h in CUSTOMER_HINTS)


def _dedupe_preserve(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        t = x.strip()
        if not t:
            continue
        key = t.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def _split_sentence_for_activities(sentence: str) -> list[str]:
    """Teilt Aufzählungen mit „und“ nur, wenn mehrere Arbeitssignaturen gemeint sind."""
    s = sentence.strip()
    low = sentence.lower()
    if " und " not in low and " sowie " not in low:
        return [s]

    splitter = r"\s+und\s+" if " und " in low else r"\s+sowie\s+"
    raw_parts = [p.strip() for p in re.split(splitter, s, flags=re.IGNORECASE) if p.strip()]
    if len(raw_parts) < 2:
        return [s]
    flagged = [_fragment_has_activity(_lw(p)) for p in raw_parts]
    if all(flagged):
        return raw_parts
    return [s]


def _fmt_clock(hour: str, minute: str | None) -> str:
    mi = minute if minute and str(minute).isdigit() else "00"
    return f"{int(hour):02d}:{int(mi):02d}"


def _extract_work_times_from_text(text_plain: str) -> tuple[str | None, str | None]:
    t_start: str | None = None
    t_end: str | None = None
    lw_block = text_plain

    patterns: tuple[tuple[str, str], ...] = (
        (
            r"arbeitszeit\s+(?:war\s+)?von\s+(\d{1,2})(?::(\d{2}))?\s*(?:uhr\b)?\s*(?:bis|-|–)\s+(\d{1,2})(?::(\d{2}))?(?:\s*uhr)?",
            "von-bis-generic",
        ),
        (
            r"\bvon\s+(\d{1,2})(?::(\d{2}))?\s*(?:uhr\b)?\s+(?:bis|-|–)\s+(\d{1,2})(?::(\d{2}))?(?:\s*uhr)?",
            "von-bis-compact",
        ),
        (
            r"start\s+(\d{1,2})[:.](\d{2})\s+ende\s+(\d{1,2})[:.](\d{2})",
            "start-ende-dotted",
        ),
        (
            r"\bstart\s+(\d{1,2})(?::(\d{2}))?\s+ende\s+(\d{1,2})(?::(\d{2}))?",
            "start-ende-space",
        ),
    )

    for tp, _kid in patterns:
        m = re.search(tp, lw_block, re.IGNORECASE)
        if not m:
            continue
        try:
            if _kid == "start-ende-dotted" or _kid == "start-ende-space":
                t_start = _fmt_clock(m.group(1), m.group(2))
                t_end = _fmt_clock(m.group(3), m.group(4))
            else:
                t_start = _fmt_clock(m.group(1), m.group(2))
                t_end = _fmt_clock(m.group(3), m.group(4))
            break
        except (IndexError, ValueError, TypeError):
            continue

    if not (t_start and t_end):
        time_m_legacy = re.search(
            r"(\d{1,2}[.:]\d{2})\s*(?:bis|–|-|uhr\s+bis)\s*(\d{1,2}[.:]\d{2})",
            lw_block,
            re.I,
        )
        if time_m_legacy:
            aa = time_m_legacy.group(1).replace(".", ":")
            bb = time_m_legacy.group(2).replace(".", ":")
            t_start, t_end = aa, bb

    return t_start, t_end


def structure_report_fields(
    raw: str,
    employee_names: list[str],
    start_time: str,
    end_time: str,
    date_str: str,
    *,
    project_name: str | None = None,
    customer_name: str | None = None,
) -> dict[str, Any]:
    strip_raw = raw.strip()
    placeholder_raw = ""
    text = strip_raw if strip_raw else ""
    sentences = (
        [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()] if text else []
    )

    activities: list[str] = []
    materials: list[str] = []
    problems: list[str] = []
    open_items: list[str] = []
    customer_bits: list[str] = []

    for sentence in sentences:
        lw_sent = _lw(sentence)

        units = _split_sentence_for_activities(sentence)

        for unit in units:
            u = _strip_clause(unit)
            if not u:
                continue
            lu = _lw(u)
            if _fragment_has_activity(lu):
                activities.append(u)
            # Material nur bei explizitem Hinweis
            if _fragment_has_material_hint(lu):
                materials.append(u)

        if _sentence_has_problem(lw_sent.strip().lower()):
            problems.append(sentence.strip())

        if _open_hint_match(sentence.strip().lower()):
            open_items.append(sentence.strip())

        if _sentence_has_customer(lw_sent):
            customer_bits.append(sentence.strip())

    activities = _dedupe_preserve(activities)
    materials = _dedupe_preserve(materials)
    problems = _dedupe_preserve(problems)
    open_items = _dedupe_preserve(open_items)

    placeholder_raw = "Keine Angabe" if not strip_raw else strip_raw

    t_from_text_start, t_from_text_end = _extract_work_times_from_text(text)

    work_time_line = f"{start_time} – {end_time} Uhr (erfasst)"
    if t_from_text_start and t_from_text_end:
        work_time_line = (
            f"{t_from_text_start} – {t_from_text_end} Uhr (aus Text)"
            f" · erfasst: {start_time} – {end_time}"
        )

    emp_line = ", ".join(employee_names) if employee_names else ""
    proj = (project_name or "").strip()
    proj_display = proj if proj else ""

    summary_open = ""
    if open_items:
        summary_open = (
            " Offene Punkte: " + "; ".join(x[:140] + ("…" if len(x) > 140 else "") for x in open_items[:3])
            + ("…" if len(open_items) > 3 else "")
        )

    summary_acts_part = ""
    if activities:
        pick = activities[:2]
        summary_acts_part = "; ".join(pick)
        if len(activities) > 2:
            summary_acts_part += " …"
    elif text:
        summary_acts_part = "siehe Rohtext / feingliedrige Zuordnung nötig"
    else:
        summary_acts_part = "nicht strukturierbar — kein Rohtext"

    if proj_display and emp_line:
        summary = (
            f"Am {date_str} wurden auf der Baustelle „{proj_display}“ durch {emp_line} "
            f"folgende Arbeiten durchgeführt: {summary_acts_part}.{summary_open}"
        )
    elif proj_display:
        summary = (
            f"Am {date_str} wurden auf der Baustelle „{proj_display}“ folgende Arbeiten durchgeführt: "
            f"{summary_acts_part}.{summary_open}"
        )
    elif emp_line:
        summary = (
            f"Am {date_str} haben {emp_line} folgende Arbeiten durchgeführt: {summary_acts_part}.{summary_open}"
        )
    else:
        summary = (
            f"Am {date_str} wurden folgende Arbeiten durchgeführt: {summary_acts_part}.{summary_open}"
        )
    summary = re.sub(r"\s+", " ", summary).strip()

    customer_talk_joined = " ".join(customer_bits).strip()

    cust_name = (customer_name or "").strip()
    cust_tail = ""
    if cust_name and cust_name.lower() not in summary.lower():
        cust_tail = f" Kunde ({cust_name})"
        summary = summary + cust_tail if summary else cust_tail.strip()

    return {
        "summary": summary,
        "activities": activities,
        "materials": materials,
        "problems": problems,
        "openItems": open_items,
        "customerTalk": customer_talk_joined,
        "workTime": work_time_line,
        "participants": list(employee_names),
        "rawText": placeholder_raw,
        "date": date_str,
        "startTime": start_time,
        "endTime": end_time,
    }


# ── eingebaute Beispiele (Sprint-Doku / Smoke) ────────────────────────────────

def _builtin_case_checks() -> list[str]:
    errors: list[str] = []

    def run(
        name: str,
        raw: str,
        *,
        emp: list[str] | None = None,
        proj: str = "Mustergarten",
        expect_act_phrases: tuple[str, ...] = (),
        material_must_not_anchor: tuple[str, ...] = (),
        expect_any_material: tuple[str, ...] = (),
        problems_needle: tuple[str, ...] = (),
        open_needle: tuple[str, ...] = (),
        customer_needle: tuple[str, ...] = (),
    ) -> None:
        r = structure_report_fields(
            raw,
            emp or [],
            "08:00",
            "16:30",
            "2026-05-01",
            project_name=proj,
            customer_name="",
        )
        act = [a.lower() for a in r["activities"]]
        mat = [m.lower() for m in r["materials"]]
        mats_joined = " ".join(mat)
        for ph in expect_act_phrases:
            if not any(ph.lower() in a for a in act):
                errors.append(f"{name}: erwartete Tätigkeits-Phrase nicht gefunden ({ph!r}); got={act!r}")

        if material_must_not_anchor:
            combo = mats_joined
            for forbid in material_must_not_anchor:
                problem = forbid.lower().strip().replace('"', '').replace("`", "")
                if combo and problem in combo:
                    errors.append(f"{name}: Material soll ohne {forbid!r} bleiben, war {mat!r}")

        if expect_any_material:
            if not any(any(n.lower() in m for n in expect_any_material) for m in mat):
                errors.append(f"{name}: Material erwartete Marke nicht in {mat!r}")

        for pn in problems_needle:
            pl = [p.lower() for p in r["problems"]]
            if not any(pn.lower() in p for p in pl):
                errors.append(f"{name}: Problem erwartete {pn!r} nicht in {pl!r}")
        for on in open_needle:
            ol = [o.lower() for o in r["openItems"]]
            if not any(on.lower() in o for o in ol):
                errors.append(f"{name}: Offene erwartete {on!r} nicht in {ol!r}")

        ct = str(r["customerTalk"] or "").lower()
        for cn in customer_needle:
            if cn.lower() not in ct:
                errors.append(f"{name}: Kunde erwartete {cn!r} nicht in customerTalk")

    run(
        "Test1-Pflaster-gelegt",
        "Ich habe heute mit Marcel und Matthias 200 Quadratmeter Pflaster gelegt.",
        emp=["Marcel", "Matthias"],
        proj="Haus Musterstraße",
        expect_act_phrases=("gelegt",),
        material_must_not_anchor=tuple(),
    )
    mats1 = structure_report_fields(
        "Ich habe heute mit Marcel und Matthias 200 Quadratmeter Pflaster gelegt.",
        ["Marcel", "Matthias"],
        "08:00",
        "16:30",
        "2026-05-01",
        project_name="Haus Musterstraße",
    )["materials"]
    if mats1:
        errors.append(f"Test1: Material-Liste soll leer sein, war {mats1!r}")

    run(
        "Test2-Schotter-Randsteine-Pallets",
        "Wir haben Schotter eingebaut und Randsteine gesetzt. Es fehlen noch zwei Paletten Pflastersteine.",
        emp=["Anna", "Ben"],
        expect_act_phrases=("schotter", "randstein"),
        expect_any_material=("schotter",),
        problems_needle=("pflasterstein",),
        open_needle=("fehlen",),
    )

    run(
        "Test3-Kundengespräch",
        "Mit dem Kunden wurde gesprochen, er war zufrieden.",
        customer_needle=("kunden",),
    )

    return errors


if __name__ == "__main__":
    fails = _builtin_case_checks()
    if fails:
        print("report_structure Builtin-Checks: FEHLGESCHLAGEN")
        for f in fails:
            print(" - ", f)
        raise SystemExit(1)
    print("report_structure Builtin-Checks: OK (3 Hauptfälle + Randbedingungen)")
