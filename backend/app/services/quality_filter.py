from __future__ import annotations

import re
from typing import Any

from app.services.activity_canonicalizer import (
    _raw_has_trockenbau_context,
    canonicalize_activities,
    normalize_for_match,
)
from app.services.customer_talk_builder import refine_customer_talk
from app.services.human_language_engine import humanize_activity, humanize_material
from app.services.summary_builder import build_deterministic_summary
from app.services.trade_phrase_memory import apply_trade_phrase_memory, phrase_priority_boost

_MAIN_WORK_KEYWORDS = (
    "verlegt",
    "montiert",
    "eingebaut",
    "installiert",
    "aufgebracht",
    "aufgetragen",
    "geschlossen",
)

_SECONDARY_WORK_KEYWORDS = (
    "silikonfugen",
    "nachgespachtelt",
    "nacharbeit",
    "kontrolliert",
    "gereinigt",
    "verfugt",
    "spachtel",
)

_ACTIVITY_REWRITE_RULES: tuple[tuple[str, str], ...] = (
    (r"\bdurchführung von verspachtelungsarbeiten\b", "Spachtelarbeiten durchgeführt"),
    (r"\bverspachtelungsarbeiten durchgeführt\b", "Spachtelarbeiten durchgeführt"),
    (r"\bheizungsanschlüsse hergestellt\b", "Heizungsanschlüsse montiert"),
    (r"\bmontage der wasserleitungen\b", "Wasserleitungen montiert"),
    (r"\bwasserleitungen? fertiggestellt\b", "Wasserleitungen montiert"),
    (r"\btrinkwasseranschlüsse hergestellt\b", "Wasserleitungen montiert"),
    (r"\bherstellung von silikonfugen\b", "Silikonfugen hergestellt"),
    (r"\baufbringung von sanierputz\b", "Sanierputz aufgebracht"),
    (r"\beinbau von\s+(\d+(?:[.,]\d+)?\s*m³)\s*schotter\b", r"Einbau von \1 Schotter"),
    (r"\bfliesen von\s*(ca\.\s*)?(\d+(?:[.,]\d+)?)\s*m²\s*durchgeführt\b", r"\1\2 m² Fliesen verlegt"),
    (r"\bfliesenkleber (?:verarbeitet|benutzt|verwendet|gemacht)\b", "Fliesenkleber aufgetragen"),
    (r"\b(?:flex|d(?:ü|ue)nnbett|mittelbett)?kleber (?:verarbeitet|benutzt|verwendet|gemacht|gezogen|aufgebracht)\b", "Fliesenkleber aufgetragen"),
    (r"\bfugenmörtel (?:verarbeitet|benutzt|verwendet)\b", "Fliesen verfugt"),
    (r"\bsilikon (?:verarbeitet|gemacht)\b", "Silikonfugen silikoniert"),
    (r"\brasenkantenstein(?:e|en)? (?:verlegt|gelegt|gebaut)\b", "Rasenkantensteine gesetzt"),
    (r"\brasen gemacht\b", "Rasen gemäht"),
    (r"\brasse gemacht\b", "Rasen gemäht"),
    (r"\b(randstein(?:e|en)?|kantenstein(?:e|en)?|bordstein(?:e|en)?) (?:verlegt|gelegt|benutzt|verbaut|verarbeitet|gebaut)\b", "Randsteine gesetzt"),
    (r"\b(?:den|die|der)\s+(?:neuen|neue|neuer|alten|alte|alter)\s+oberputz\s+(?:aufgetragen|aufgebracht|verarbeitet)\b", "Oberputz aufgetragen"),
    (r"\boberputz\s+(?:aufgetragen|aufgebracht|verarbeitet)\b", "Oberputz aufgetragen"),
    (r"\bgrundputz\s+(?:aufgetragen|aufgebracht|verarbeitet)\b", "Grundputz aufgetragen"),
    (r"\binnenputz\s+(?:aufgetragen|aufgebracht|verarbeitet)\b", "Innenputz aufgetragen"),
    (r"\b(aussenputz|außenputz)\s+(?:aufgetragen|aufgebracht|verarbeitet)\b", "Außenputz aufgetragen"),
    (r"\bein\s+abzweig\s+eingebaut\b", "Abzweig eingebaut"),
    (r"\bein[e]?\s+manschette?\s+montiert\b", "HT-Manschette montiert"),
    (r"\buwe[-\s]*profil\s+montiert\b", "UW-Profil montiert"),
    (r"\bherzk(ö|oe)rper\b", "Heizkörper"),
    (r"\bwc gesetzt\b|\btoilette eingebaut\b", "WC montiert"),
    (r"\bwaschbecken angebaut\b", "Waschbecken montiert"),
    (r"\bdusche angeschlossen\b", "Dusche montiert"),
    (r"\bausgleichsmasse gezogen\b", "Nivelliermasse aufgetragen"),
    (r"\bbodenablauf gesetzt\b", "Bodenablauf eingebaut"),
    (r"\bhausanschluss gemacht\b", "Hausanschluss hergestellt"),
    (r"\basphalt gemacht\b", "Asphalt eingebaut"),
    (r"\basphalt\s+(schneiden|geschnitten|trennen|aufschneiden)\b", "Asphalt schneiden"),
    (r"\basphalt\s+(fräsen|fraesen|abgefräst|abgefraest)\b", "Asphalt fräsen"),
    (r"\b(hochbord|tiefbord)\b.*\b(gesetzt|verlegt|gestellt)\b", "Borde gesetzt"),
    (r"\b(muldenstein|rinnenstein)(?:e|en)?\s+(gesetzt|verlegt)\b", "Rinnensteine gesetzt"),
    (r"\brinnensteine verlegt\b", "Rinnensteine gesetzt"),
    (r"\bgully\s+(gesetzt|montiert)\b", "Straßenabläufe gesetzt"),
    (r"\bfrostschutzschicht\b", "Frostschutzschicht hergestellt"),
    (r"\bschottertragschicht\b", "Schottertragschicht hergestellt"),
    (r"\bplanum\b.*\b(hergestellt|verdichtet)\b", "Planum hergestellt"),
    (r"\bsockelputz gemacht\b", "Sockelputz aufgetragen"),
    (r"\breibputz gemacht\b", "Reibputz aufgetragen"),
    (r"\bkratzputz gemacht\b", "Kratzputz aufgetragen"),
    (r"\bsilikonharzputz\s+(?:aussen|außen\s+)?aufgebracht\b", "Außenputz aufgetragen"),
    (r"\bsilikatputz\s+(?:an der fassade\s+)?aufgetragen\b", "Außenputz aufgetragen"),
    (r"\bwdvs\s+gedübelt\b|\bwdvs\s+geduebelt\b", "WDVS gedübelt"),
    (r"\bwdvs\s+dämmung\s+geklebt\b|\bwdvs\s+daemmung\s+geklebt\b", "WDVS Dämmung geklebt"),
    (r"\bputz\s+geglättet\b|\bputz\s+geglaettet\b", "Putz geglättet"),
    (r"\bputz\s+filziert\b", "Putz filziert"),
    (r"\beckschutzprofile\s+gesetzt\b", "Eckschutzprofile gesetzt"),
    (r"\bapu-leisten\s+montiert\b|\bapu\s+leisten\s+montiert\b", "APU-Leisten montiert"),
    (r"\bleibungsprofile\s+gesetzt\b", "Leibungsprofile gesetzt"),
    (r"\bsockelprofile\s+montiert\b", "Sockelprofile montiert"),
    (r"\btropfkantenprofile\s+gesetzt\b", "Tropfkantenprofile gesetzt"),
)

_MATERIAL_CONFIDENCE_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]], ...] = (
    (r"\bfliesen(?:arbeiten)? verlegt\b|\b\d+(?:[.,]\d+)?\s*m²\s*fliesen verlegt\b", ("Fliesen",), ("Fliesenkleber", "Fugenmörtel"), ()),
    (r"\bfliesen verfugt\b", ("Fugenmörtel",), (), ()),
    (r"\bsilikonfugen (hergestellt|silikoniert)\b", ("Silikon",), (), ()),
    (r"\bgipskarton(?:platten)? montiert\b", ("Gipskartonplatten",), ("Schnellbauschrauben", "Spachtelmasse"), ()),
    (r"\bständerwerk montiert\b", ("CW/UW-Profile",), ("Schnellbauschrauben",), ()),
    (r"\bdecke abgehängt\b", ("CD-Profile",), ("Abhänger",), ()),
    (r"\bfugen verspachtelt\b", ("Fugenspachtel",), (), ()),
    (r"\bsanierputz aufgebracht\b|\bsanierputz aufgetragen\b", ("Sanierputz",), (), ("Grundierung",)),
    (r"\boberputz aufgetragen\b", ("Oberputz",), (), ()),
    (r"\bunterputz aufgetragen\b", ("Unterputz",), (), ()),
    (r"\bgrundputz aufgetragen\b", ("Grundputz",), (), ()),
    (r"\binnenputz aufgetragen\b", ("Innenputz",), (), ()),
    (r"\baußenputz aufgetragen\b|\baussenputz aufgetragen\b", ("Außenputz",), (), ()),
    (r"\bputz aufgebracht\b", ("Putz",), (), ()),
    (r"\bgrundierung aufgetragen\b", ("Grundierung",), (), ()),
    (r"\babdichtung hergestellt\b", ("Abdichtung",), ("Dichtband",), ()),
    (r"\bpflaster(?:arbeiten)? (?:durchgeführt|verlegt|eingebaut)\b|\b\d+(?:[.,]\d+)?\s*m²\s*pflaster (?:verlegt|eingebaut)\b", ("Pflastersteine",), ("Splitt", "Schotter"), ()),
    (r"\bschotter eingebaut\b|\beinbau von\s+\d+(?:[.,]\d+)?\s*m³\s*schotter\b", ("Schotter",), (), ()),
    (r"\bsplitt\b", ("Splitt",), (), ()),
    (r"\b(?:rasenkantensteine|randsteine) gesetzt\b", ("Rasenkantensteine",), (), ()),
    (r"\b(?:\d+(?:[.,]\d+)?\s*lfm\s*)?palisaden gesetzt\b", ("Palisaden",), ("Splitt", "Beton"), ()),
    (r"\b(?:\d+(?:[.,]\d+)?\s*m²\s*)?(?:fläche mit )?mulch eingedeckt\b|\brindenmulch eingedeckt\b", ("Mulch",), ("Rindenmulch", "Geotextil"), ()),
    (r"\b(?:\d+(?:[.,]\d+)?\s*m²\s*)?keramikterrasse verlegt\b", ("Keramikplatten",), ("Stelzlager", "Drainagemörtel", "Einkornmörtel"), ()),
    (r"\bholz-/wpc-terrasse gebaut\b", ("WPC-Dielen",), ("Unterkonstruktion",), ()),
    (r"\brasen vertikutiert\b", (), ("Vertikutierer"), ()),
    (r"\brasen gedüngt\b", ("Dünger",), (), ()),
    (r"\bfläche bewässert\b", (), ("Bewässerungsmaterial"), ()),
    (r"\bwinterdienst durchgeführt\b", ("Streugut",), (), ()),
    (r"\bgeotexti(?:l|el) verlegt\b", ("Geotextil",), (), ()),
    (r"\bhecke geschnitten\b", (), ("Heckenschere"), ()),
    (r"\brasen gemäht\b|\b\d+(?:[.,]\d+)?\s*m²\s*rasen gemäht\b", (), ("Rasenmäher",), ()),
    (r"\brasen getrimmt\b", (), ("Freischneider",), ()),
    (r"\bunkraut entfernt\b", (), ("Handwerkzeug"), ()),
    (r"\bpflanzen gesetzt\b", ("Pflanzen",), ("Pflanzsubstrat"), ()),
    (r"\bgraben ausgehoben\b", (), ("Bodenmaterial",), ()),
    (r"\buntergrund verdichtet\b", (), ("Frostschutzmaterial",), ()),
    (r"\bwasserleitungen montiert\b|\brohrleitungen installiert\b", ("Rohrleitungen",), ("Fittings",), ()),
    (r"\bheizungsanschlüsse montiert\b", (), ("Fittings",), ()),
    (r"\bwc montiert\b", ("WC",), ("Anschlussset",), ()),
    (r"\bwaschbecken montiert\b", ("Waschbecken",), ("Armaturen",), ()),
    (r"\bdusche montiert\b", ("Dusche",), ("Armaturen",), ()),
    (r"\barmaturen montiert\b", ("Armaturen",), (), ()),
    (r"\bdruckprüfung durchgeführt\b|\bdruckpruefung durchgeführt\b", (), ("Prüfset"), ()),
    (r"\bhydraulischer abgleich durchgeführt\b", (), ("Thermostatventile",), ()),
    (r"\b(?:\d+(?:[.,]\d+)?\s*lfm\s*)?kg-rohre verlegt\b", ("KG-Rohre",), ("KG-Bögen", "KG-Abzweige"), ()),
    (r"\b(?:\d+(?:[.,]\d+)?\s*lfm\s*)?ht-rohre verlegt\b", ("HT-Rohre",), ("HT-Bögen", "HT-Abzweige"), ()),
    (r"\bht-manschette montiert\b", ("HT-Manschette",), (), ()),
    (r"\bfassadenarmierung ausgeführt\b|\bfassadenarmierung ausgefuehrt\b", ("Armierungsgewebe",), ("Armierungsmörtel",), ()),
    (r"\barmierung ausgeführt\b|\barmierung ausgefuehrt\b", ("Armierungsgewebe",), ("Armierungsmörtel",), ()),
    (r"\bsockelputz aufgetragen\b", ("Sockelputz",), ("Grundierung",), ()),
    (r"\breibputz aufgetragen\b", ("Reibputz",), (), ()),
    (r"\bkratzputz aufgetragen\b", ("Kratzputz",), (), ()),
    (r"\bwdvs gedübelt\b|\bwdvs geduebelt\b", ("Tellerdübel",), ("Klebe- und Armierungsmörtel",), ()),
    (r"\bwdvs dämmung geklebt\b|\bwdvs daemmung geklebt\b", ("Klebe- und Armierungsmörtel",), ("EPS Dämmplatten", "Mineralwolle Dämmplatten"), ()),
    (r"\bputz geglättet\b|\bputz geglaettet\b", ("Feinputz", "Glättspachtel"), (), ()),
    (r"\bputz filziert\b", ("Feinputz",), (), ()),
    (r"\beckschutzprofile gesetzt\b", ("Eckschutzschiene",), ("Klebeputz", "Spachtelmasse"), ()),
    (r"\bapu-leisten montiert\b|\bapu leisten montiert\b", ("APU-Leiste",), ("Klebeputz",), ()),
    (r"\bleibungsprofile gesetzt\b", ("Leibungsprofil",), ("Klebeputz",), ()),
    (r"\bsockelprofile montiert\b", ("Sockelprofil",), ("Klebeputz",), ()),
    (r"\btropfkantenprofile gesetzt\b", ("Tropfkantenprofil",), ("Klebeputz", "Armierungsmörtel"), ()),
    (r"\bhausanschluss hergestellt\b", ("Hausanschluss",), (), ()),
    (r"\basphalt schneiden\b", ("Asphalt",), (), ("Trennscheibe Asphalt?")),
    (r"\basphalt fräsen\b", ("Asphaltdeckschicht",), (), ("Kaltfräse?")),
    (r"\basphalt verdichten\b", ("Asphaltdeckschicht",), (), ("Walze?")),
    (r"\basphalt eingebaut\b", ("Asphalt",), ("Asphaltmischgut AC", "SMA"), ("Asphaltfertiger?")),
    (r"\bfrostschutzschicht hergestellt\b", ("Frostschutzkies 0/45",), (), ("Walze?")),
    (r"\bschottertragschicht hergestellt\b", ("Schottertragschicht STS 0/32",), (), ("Walze?")),
    (r"\bplanum hergestellt\b", (), (), ("Laser?")),
    (r"\bborde gesetzt\b", ("Hochbord 12x25x100",), ("Beton C12/15",), ()),
    (r"\brinnensteine gesetzt\b", ("Rinnensteine",), ("Bettungsmörtel",), ()),
    (r"\bstraßenabläufe gesetzt\b", ("Straßenablauf Guss",), ("Schachtrahmen",), ()),
    (r"\bschichtenverbund hergestellt\b", ("Bitumenemulsion",), (), ("Bindemittelwagen?")),
    (r"\bnähte hergestellt\b", ("Heißbitumen",), (), ("Nahtspritze?")),
    (r"\bgraben verfüllt\b", ("Kies", "Schotter"), (), ()),
    (r"\bgroßformatfliesen verlegt\b|\bgrossformatfliesen verlegt\b", ("Fliesen",), ("Nivelliersystem"), ()),
    (r"\bnivelliermasse aufgetragen\b", ("Nivelliermasse",), (), ()),
    (r"\bbodenablauf eingebaut\b", ("Bodenablauf",), (), ()),
    (r"\bnaturstein verlegt\b", ("Naturstein",), (), ()),
)

_EXPLICIT_MATERIAL_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bschotter\b", "Schotter"),
    (r"\bsplitt\b", "Splitt"),
    (r"\bpflastersteine?\b", "Pflastersteine"),
    (r"\brasen[\s-]*kanten[\s-]*stein(?:e|en)?\b|\brasen[\s-]*kanten\b", "Rasenkantensteine"),
    (r"\brandstein(?:e|en)?\b|\bkantenstein(?:e|en)?\b|\bbordstein(?:e|en)?\b", "Rasenkantensteine"),
    (r"\bfliesen\b", "Fliesen"),
    (r"\bsilikon\b", "Silikon"),
    (r"\bgipskartonplatten?\b", "Gipskartonplatten"),
    (r"\bsanierputz\b", "Sanierputz"),
    (r"\boberputz\b", "Oberputz"),
    (r"\bunterputz\b", "Unterputz"),
    (r"\bgrundierung\b|\bhaftgrund\b|\btiefgrund\b|\bbetonkontakt\b", "Grundierung"),
    (r"\bgrundputz\b", "Grundputz"),
    (r"\binnenputz\b", "Innenputz"),
    (r"\baussenputz\b|\baußenputz\b", "Außenputz"),
    (r"\bputz\b", "Putz"),
    (r"\brohrleitungen?\b|\bwasserleitungen?\b", "Rohrleitungen"),
    (r"\bkg-?\s*rohre?\b", "KG-Rohre"),
    (r"\bht-?\s*rohre?\b", "HT-Rohre"),
    (r"\bkg\s*dn\s*\d+\b", "KG-Rohre"),
    (r"\bht\s*dn\s*\d+\b", "HT-Rohre"),
    (r"\bkg[-\s]*bögen?\b|\bkg[-\s]*bogen\b", "KG-Bögen"),
    (r"\bht[-\s]*bögen?\b|\bht[-\s]*bogen\b", "HT-Bögen"),
    (r"\bkg[-\s]*abzweige?\b", "KG-Abzweige"),
    (r"\bht[-\s]*abzweige?\b", "HT-Abzweige"),
    (r"\bht[-\s]*manschette\b|\bmanschette\b", "HT-Manschette"),
    (r"\bfittings\b", "Fittings"),
    (r"\bheizk(ö|oe)rper\b", "Heizkörper"),
    (r"\bthermostatventile?\b", "Thermostatventile"),
    (r"\br(ü|ue)cklaufverschraubung(en)?\b", "Rücklaufverschraubung"),
    (r"\bpflanzsubstrat\b", "Pflanzsubstrat"),
    (r"\bpflanzkübel\b|\bpflanzkuebel\b", "Pflanzkübel"),
    (r"\bpalisad(?:e|en)\b", "Palisaden"),
    (r"\brindenmulch\b", "Rindenmulch"),
    (r"\bmulch\b", "Mulch"),
    (r"\bkeramikplatte(?:n)?\b", "Keramikplatten"),
    (r"\bstelzlag(?:er|ern)?\b", "Stelzlager"),
    (r"\bdrainagem(?:ö|oe)rtel\b", "Drainagemörtel"),
    (r"\beinkorn(?:m(?:ö|oe)rtel)?\b", "Einkornmörtel"),
    (r"\bwpc[-\s]*dielen?\b|\bwpc\b", "WPC-Dielen"),
    (r"\bunterkonstruktion\b", "Unterkonstruktion"),
    (r"\bd(ü|ue)nger\b", "Dünger"),
    (r"\bstreugut\b|\bsalz\b", "Streugut"),
    (r"\bgeotextil\b|\btrennvlies\b|\bfiltervlies\b|\bvlies\b", "Geotextil"),
    (r"\bwc\b|\btoilette\b", "WC"),
    (r"\bwaschbecken\b|\bwaschtisch\b", "Waschbecken"),
    (r"\bdusche\b|\bduschwanne\b|\bduschkabine\b", "Dusche"),
    (r"\barmatur(en)?\b|\bwasserhahn\b|\bmischer\b", "Armaturen"),
    (r"\bdruckpr(ü|ue)fung\b", "Prüfset"),
    (r"\bhausanschluss\b", "Hausanschluss"),
    (r"\bhochbord\b", "Hochbord"),
    (r"\btiefbord\b", "Tiefbord"),
    (r"\brinnenstein(?:e|en)?\b", "Rinnensteine"),
    (r"\bmuldenstein(?:e|en)?\b", "Muldensteine"),
    (r"\bfrostschutzkies\b", "Frostschutzkies"),
    (r"\bbitumenemulsion\b", "Bitumenemulsion"),
    (r"\bsma\b", "SMA"),
    (r"\basphalt\b", "Asphalt"),
    (r"\bnivelliermasse\b|\bausgleichsmasse\b|\bnivellierspachtel\b", "Nivelliermasse"),
    (r"\bbodenablauf\b|\bduschrinne\b|\bablaufrinne\b", "Bodenablauf"),
    (r"\bnaturstein\b", "Naturstein"),
    (r"\bsockelputz\b", "Sockelputz"),
    (r"\breibputz\b", "Reibputz"),
    (r"\bkratzputz\b", "Kratzputz"),
    (r"\bfliesenkleber\b", "Fliesenkleber"),
    (r"\bfugenspachtel\b", "Fugenspachtel"),
    (r"\bmineralwolle\b(?:\s+\w+){0,8}\s+d(ä|ae)mmplatten\b|\bd(ä|ae)mmplatten\b(?:\s+\w+){0,8}\s+mineralwolle\b", "Mineralwolle Dämmplatten"),
    (r"\beps\s+d(ä|ae)mmplatten\b", "EPS Dämmplatten"),
    (r"\bsteinwolle\b", "Steinwolle"),
    (r"\bmineralwolle\b", "Mineralwolle"),
    (r"\barmierungsgewebe\b", "Armierungsgewebe"),
    (r"\barmierungsm(ö|oe)rtel\b", "Armierungsmörtel"),
    (r"\bhaftgrund\b|\btiefgrund\b|\bbetonkontakt\b", "Haftgrund"),
    (r"\bporoton(?:[-\s]*ziegel)?\b", "Poroton-Ziegel"),
    (r"\b(?:porit|porenbeton|ytong)\b", "Porenbetonsteine"),
    (r"\bkalksandstein\b|\bks[-\s]*steine?\b|\bks\b", "Kalksandsteine"),
    (r"\bschalung\b", "Schalung"),
    (r"\bbewehrung(?:sstahl)?\b|\bbst\s*500\b", "Bewehrungsstahl"),
    (r"\bd(ü|ue)nnbettm(ö|oe)rtel\b", "Dünnbettmörtel"),
    (r"\bmauerm(ö|oe)rtel\b", "Mauermörtel"),
    (r"\bbaukleber\b", "Baukleber"),
    (r"\bbeton\b", "Beton"),
    (r"\bgipsputz\b", "Gipsputz"),
    (r"\bkalkputz\b", "Kalkputz"),
    (r"\bkalkzementputz\b", "Kalkzementputz"),
    (r"\blehmputz\b", "Lehmputz"),
    (r"\bsilikonharzputz\b", "Silikonharzputz"),
    (r"\bsilikatputz\b", "Silikatputz"),
    (r"\bfeinputz\b", "Feinputz"),
    (r"\bgl(ä|ae)ttspachtel\b", "Glättspachtel"),
    (r"\btellerd(ü|ue)bel\b", "Tellerdübel"),
    (r"\beps\b", "EPS Dämmplatten"),
    (r"\bklebe- und armierungsm(ö|oe)rtel\b|\bklebe und armierungsm(ö|oe)rtel\b", "Klebe- und Armierungsmörtel"),
    (r"\bholzfaserplatten\b", "Holzfaserplatten"),
    (r"\bpu-stuckprofil\b", "PU-Stuckprofil"),
    (r"\bgips-stuckprofil\b", "Gips-Stuckprofil"),
    (r"\bstuckkleber\b", "Stuckkleber"),
    (r"\barmierungsmörtel\b|\barmierungsmoertel\b|\barmierungs\s+m(?:ö|oe)rtel\b", "Armierungsmörtel"),
    (r"\bd(ä|ae)mmplatten\b", "Dämmplatten"),
    (r"\bklebeputz\b", "Klebeputz"),
    (r"\bspachtelmasse\b", "Spachtelmasse"),
    (r"\beckschutzprofile\b", "Eckschutzschiene"),
    (r"\bapu(?:-|\s)?leiste\b", "APU-Leiste"),
    (r"\banputzleiste\b", "APU-Leiste"),
    (r"\bleibungsprofil\b", "Leibungsprofil"),
    (r"\blaibungsprofil\b", "Leibungsprofil"),
    (r"\bsockelprofil\b", "Sockelprofil"),
    (r"\btropfkantenprofil\b", "Tropfkantenprofil"),
    (r"\btropfkante\b", "Tropfkantenprofil"),
)

_SUGGESTION_RULES: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    (
        r"\b\d+(?:[.,]\d+)?\s*m²\s*fliesen verlegt\b|\bfliesen verlegt\b",
        (
            ("Fliesenkleber benutzt?", r"\b(flex|fliesen|fliesen)?kleber\b|\bmittelbettm(ö|oe)rtel\b|\bd(ü|ue)nnbettm(ö|oe)rtel\b"),
            ("Grundierung benutzt?", r"\b(grundierung|haftgrund|tiefgrund|primer|voranstrich)\b"),
            ("Fugenmörtel benutzt?", r"\b(fugenm(ö|oe)rtel|verfugt|fugen(?:arbeiten)?)\b"),
        ),
    ),
    (
        r"\bdecke abgehängt\b",
        (
            ("CD-Profile benutzt?", r"\bcd[-\s]*profile?\b"),
            ("UD-Profile benutzt?", r"\bud[-\s]*profile?\b"),
            ("Abhänger benutzt?", r"\b(direktabh(ä|ae)nger|noniusabh(ä|ae)nger|abh(ä|ae)nger)\b"),
        ),
    ),
    (
        r"\bständerwerk montiert\b",
        (
            ("CW/UW-Profile benutzt?", r"\b(?:cw|uw)[-\s]*profile?n?\b"),
            ("UA-Profile benutzt?", r"\bua[-\s]*profile?\b|\bt(ü|ue)r(?:sturz|verst(ä|ae)rkung)\b"),
            ("Schnellbauschrauben benutzt?", r"\bschnellbauschrauben?\b"),
        ),
    ),
    (
        r"\bgipskartonplatten montiert\b",
        (
            ("Schnellbauschrauben benutzt?", r"\bschnellbauschrauben?\b"),
            ("Fugenspachtel benutzt?", r"\bfugenspachtel\b|\bspachtelmasse\b"),
        ),
    ),
    (
        r"\b\d+(?:[.,]\d+)?\s*m²\s*pflaster verlegt\b|\bpflaster verlegt\b",
        (
            ("Splitt benutzt?", r"\bsplitt\b|\bsplit\b"),
            ("Schotter benutzt?", r"\bschotter\b|frostschutz"),
            ("Fugensand benutzt?", r"\bfugensand\b|\bfugenmaterial\b"),
        ),
    ),
    (
        r"\b(?:rasenkantensteine|randsteine) gesetzt\b",
        (
            ("Beton benutzt?", r"\bbeton\b|\bm(ö|oe)rtel\b"),
            ("Splitt benutzt?", r"\bsplitt\b"),
        ),
    ),
    (
        r"\bdrainage/entwässerung eingebaut\b|\bentwässerung eingebaut\b|\bentwaesserung eingebaut\b",
        (
            ("Drainagerohr benutzt?", r"\bdrainage(?:rohr)?\b|\bdr(ä|ae)n(?:rohr)?\b"),
            ("Filtervlies benutzt?", r"\bfiltervlies\b|\btrennvlies\b"),
            ("Sickerschacht benutzt?", r"\bsickerschacht\b|\bschacht\b"),
        ),
    ),
    (
        r"\b(?:\d+(?:[.,]\d+)?\s*lfm\s*)?kg-rohre verlegt\b",
        (
            ("KG-Bögen benutzt?", r"\bkg[-\s]*b(ö|oe)gen?\b|\bbogen\b"),
            ("KG-Abzweige benutzt?", r"\bkg[-\s]*abzweig"),
            ("Reinigungsrohr benutzt?", r"\breinigungsrohr\b"),
        ),
    ),
    (
        r"\b(?:\d+(?:[.,]\d+)?\s*lfm\s*)?ht-rohre verlegt\b",
        (
            ("HT-Bögen benutzt?", r"\bht[-\s]*b(ö|oe)gen?\b|\bbogen\b"),
            ("HT-Abzweige benutzt?", r"\bht[-\s]*abzweig"),
            ("HT-Manschette benutzt?", r"\bht[-\s]*manschette\b"),
        ),
    ),
    (
        r"\bwasserleitungen verlegt\b|\bwasserleitungen montiert\b",
        (
            ("Pressfittings benutzt?", r"\bpressfittings?\b|\bfittings?\b"),
            ("Mehrschichtverbundrohr benutzt?", r"\bmehrschicht|verbundrohr|aluverbund"),
        ),
    ),
    (
        r"\bheizkörper montiert\b|\bheizkoerper montiert\b",
        (
            ("Thermostatventil benutzt?", r"\bthermostatventil\b"),
            ("Rücklaufverschraubung benutzt?", r"\br(ü|ue)cklaufverschraubung\b"),
        ),
    ),
    (
        r"\bfußbodenheizung verlegt\b|\bfussbodenheizung verlegt\b",
        (
            ("FBH-Verteiler benutzt?", r"\bverteiler\b"),
            ("Randdämmstreifen benutzt?", r"\brandd(ä|ae)mmstreifen\b"),
            ("Tackersystem benutzt?", r"\btacker(system|nadeln?)\b"),
        ),
    ),
    (
        r"\binnenputz aufgetragen\b|\baussenputz aufgetragen\b|\baußenputz aufgetragen\b|\bsanierputz aufgebracht\b",
        (
            ("Putzmaschine benutzt?", r"\bputzmaschine\b"),
            ("Kartätsche benutzt?", r"\bkartätsche\b|\bkartaetsche\b"),
            ("Haftgrund benutzt?", r"\bhaftgrund\b|\btiefgrund\b|\bbetonkontakt\b"),
            ("Armierungsgewebe benutzt?", r"\barmierungsgewebe\b"),
        ),
    ),
    (
        r"\b(aussenputz aufgetragen|außenputz aufgetragen)\b",
        (
            ("Haftbrücke benutzt?", r"\bhaftbr(ü|ue)cke\b"),
            ("Gewebeeinlage benutzt?", r"\bgewebeeinlage\b"),
        ),
    ),
    (
        r"\boberputz aufgetragen\b",
        (
            ("Grundierung benutzt?", r"\b(grundierung|haftgrund|tiefgrund|betonkontakt)\b"),
            ("Haftgrund benutzt?", r"\b(grundierung|haftgrund|tiefgrund|betonkontakt)\b"),
            ("Unterputz aufgetragen?", r"\b(unterputz|grundputz)\b"),
        ),
    ),
    (
        r"\bsockelputz aufgetragen\b|\bsockelputz gemacht\b",
        (
            ("Grundierung benutzt?", r"\b(grundierung|haftgrund|tiefgrund|betonkontakt)\b"),
        ),
    ),
    (
        r"\bschimmel beseitigt\b",
        (
            ("Schimmelentferner benutzt?", r"\bschimmelentferner\b"),
        ),
    ),
    (
        r"\baltputz entfernt\b",
        (
            ("Entsorgungssäcke benutzt?", r"\b(entsorgungss(ä|ae)cke|baus(ä|ae)cke|m(ü|ue)lls(ä|ae)cke)\b"),
            ("Container benutzt?", r"\b(container|mulde)\b"),
        ),
    ),
    (
        r"\bwdvs ausgeführt\b|\bwdvs ausgefuehrt\b",
        (
            ("Klebemörtel benutzt?", r"\bklebem(ö|oe)rtel\b"),
            ("Tellerdübel benutzt?", r"\btellerd(ü|ue)bel\b"),
            ("Armierungsgewebe benutzt?", r"\barmierungsgewebe\b"),
        ),
    ),
    (
        r"\bfassadenarmierung ausgeführt\b|\bfassadenarmierung ausgefuehrt\b",
        (
            ("Armierungsmörtel benutzt?", r"\barmierungsm(ö|oe)rtel\b"),
            ("Armierungsgewebe benutzt?", r"\barmierungsgewebe\b"),
        ),
    ),
    (
        r"\barmierung ausgeführt\b|\barmierung ausgefuehrt\b",
        (
            ("Armierungsmörtel benutzt?", r"\barmierungsm(ö|oe)rtel\b"),
            ("Armierungsgewebe benutzt?", r"\barmierungsgewebe\b"),
        ),
    ),
    (
        r"\bwdvs gedübelt\b|\bwdvs geduebelt\b",
        (
            ("Tellerdübel benutzt?", r"\btellerd(ü|ue)bel\b"),
            ("Schraubdübel benutzt?", r"\bschraubd(ü|ue)bel\b"),
            ("Schlagdübel benutzt?", r"\bschlagd(ü|ue)bel\b"),
        ),
    ),
    (
        r"\bwdvs dämmung geklebt\b|\bwdvs daemmung geklebt\b",
        (
            ("Zahntraufel benutzt?", r"\bzahntraufel\b"),
            ("Klebe- und Armierungsmörtel benutzt?", r"\bklebe"),
            ("Gewebe benutzt?", r"\bgewebe\b"),
        ),
    ),
    (
        r"\bputz geglättet\b|\bputz geglaettet\b",
        (
            ("Glättkelle benutzt?", r"\bgl(ä|ae)ttkelle\b"),
            ("Schwammbrett benutzt?", r"\bschwammbrett\b"),
            ("Feinputz benutzt?", r"\bfeinputz\b"),
        ),
    ),
    (
        r"\bputz filziert\b",
        (
            ("Filzbrett benutzt?", r"\bfilzbrett\b"),
            ("Schwammbrett benutzt?", r"\bschwammbrett\b"),
        ),
    ),
    (
        r"\beckschutzprofile gesetzt\b",
        (
            ("Klebeputz benutzt?", r"\bklebeputz\b"),
            ("Spachtelmasse benutzt?", r"\bspachtelmasse\b"),
        ),
    ),
    (
        r"\bapu-leisten montiert\b|\bapu leisten montiert\b",
        (
            ("PVC-APU benutzt?", r"\bapu\s+pvc\b|\bpvc[-\s]*apu\b"),
            ("Alu-APU benutzt?", r"\bapu\s+alu\b|\balu[-\s]*apu\b"),
            ("Dichtlippe benutzt?", r"\bdichtlippe\b"),
            ("Klebeputz benutzt?", r"\bklebeputz\b"),
        ),
    ),
    (
        r"\bleibungsprofile gesetzt\b",
        (
            ("Dichtlippe benutzt?", r"\bdichtlippe\b"),
            ("Klebeputz benutzt?", r"\bklebeputz\b"),
        ),
    ),
    (
        r"\bsockelprofile montiert\b",
        (
            ("Sockeldämmung benutzt?", r"\bsockeld(ä|ae)mmung\b"),
            ("Noppenbahn benutzt?", r"\bnoppenbahn\b"),
        ),
    ),
    (
        r"\btropfkantenprofile gesetzt\b",
        (
            ("Klebeputz benutzt?", r"\bklebeputz\b"),
            ("Armierung benutzt?", r"\barmierungs(?:gewebe|mörtel)\b"),
        ),
    ),
    (
        r"\bstuckarbeiten durchgeführt\b",
        (
            ("Montagekleber benutzt?", r"\b(stuckkleber|montagekleber)\b"),
            ("Feinspachtel benutzt?", r"\bfeinspachtel\b"),
        ),
    ),
    (
        r"\bschalung erstellt\b",
        (
            ("Schalöl benutzt?", r"\bschal(ö|oe)l\b"),
            ("Spannstäbe benutzt?", r"\bspannst(ä|ae)be?\b"),
        ),
    ),
    (
        r"\bbewehrung eingebaut\b",
        (
            ("Bindedraht benutzt?", r"\bbindedraht\b"),
            ("Abstandhalter benutzt?", r"\babstandhalter\b|\bdistanz"),
        ),
    ),
    (
        r"\bfundament erstellt\b",
        (
            ("Schalung benutzt?", r"\bschalung\b"),
            ("Bewehrung benutzt?", r"\bbewehrung|armierung\b"),
            ("Beton benutzt?", r"\bbeton\b"),
        ),
    ),
    (
        r"\bmauerwerk erstellt\b",
        (
            ("Dünnbettmörtel benutzt?", r"\bd(ü|ue)nnbettm(ö|oe)rtel\b"),
            ("Mauermörtel benutzt?", r"\bmauerm(ö|oe)rtel\b"),
            ("Baukleber benutzt?", r"\bbaukleber\b"),
            ("Mauerwerksanker benutzt?", r"\bmauerwerksanker\b"),
        ),
    ),
    (
        r"\bbewehrung eingebaut\b|\bschalung erstellt\b|\bfundament erstellt\b",
        (
            ("Bewehrungsstahl benutzt?", r"\bbewehrungs?stahl\b|\bbst\s*500\b"),
            ("Mattenstahl benutzt?", r"\bmattenstahl\b|\bbst[-\s]*matten\b"),
            ("Rödeldraht benutzt?", r"\br(ö|oe)deldraht\b"),
        ),
    ),
    (
        r"\b(?:\d+(?:[.,]\d+)?\s*lfm\s*)?palisaden gesetzt\b",
        (
            ("Splitt benutzt?", r"\bsplitt\b|\bsplit\b"),
            ("Beton benutzt?", r"\bbeton\b|\bm(ö|oe)rtel\b"),
        ),
    ),
    (
        r"\b(?:\d+(?:[.,]\d+)?\s*m²\s*)?(?:fläche mit )?mulch eingedeckt\b|\brindenmulch eingedeckt\b",
        (
            ("Rindenmulch benutzt?", r"\brindenmulch\b"),
            ("Geotextil benutzt?", r"\bgeotextil\b|\btrennvlies\b|\bvlies\b"),
        ),
    ),
    (
        r"\b(?:\d+(?:[.,]\d+)?\s*m²\s*)?keramikterrasse verlegt\b",
        (
            ("Stelzlager benutzt?", r"\bstelzlag"),
            ("Drainagemörtel benutzt?", r"\bdrainage(?:m(ö|oe)rtel)?\b"),
            ("Einkornmörtel benutzt?", r"\beinkorn(?:m(ö|oe)rtel)?\b"),
        ),
    ),
    (
        r"\bholz-/wpc-terrasse gebaut\b",
        (
            ("Unterkonstruktion benutzt?", r"\bunterkonstruktion\b"),
            ("WPC-Dielen benutzt?", r"\bwpc[-\s]*dielen?\b|\bwpc\b"),
        ),
    ),
    (
        r"\brasen vertikutiert\b",
        (
            ("Vertikutierer benutzt?", r"\bvertikutierer\b"),
        ),
    ),
    (
        r"\brasen gedüngt\b",
        (
            ("Dünger benutzt?", r"\bd(ü|ue)nger\b"),
        ),
    ),
    (
        r"\bfläche bewässert\b|\bflaeche bewaessert\b",
        (
            ("Bewässerungsmaterial benutzt?", r"\bbew(ä|ae)sser"),
        ),
    ),
    (
        r"\bwinterdienst durchgeführt\b|\bwinterdienst durchgefuehrt\b",
        (
            ("Streugut benutzt?", r"\bstreugut\b|\bsalz\b"),
        ),
    ),
    (
        r"\bwc montiert\b",
        (
            ("Anschlussset benutzt?", r"\banschlussset\b"),
        ),
    ),
    (
        r"\bwaschbecken montiert\b|\bdusche montiert\b",
        (
            ("Armaturen benutzt?", r"\barmatur(en)?\b|\bwasserhahn\b|\bmischer\b"),
        ),
    ),
    (
        r"\bdruckprüfung durchgeführt\b|\bdruckpruefung durchgeführt\b",
        (
            ("Prüfset benutzt?", r"\bprüfset\b|\bdruckpr(ü|ue)f"),
        ),
    ),
    (
        r"\bgroßformatfliesen verlegt\b|\bgrossformatfliesen verlegt\b",
        (
            ("Nivelliersystem benutzt?", r"\bnivelliersystem\b|\bleveling\b"),
        ),
    ),
    (
        r"\bnivelliermasse aufgetragen\b",
        (
            ("Nivelliermasse benutzt?", r"\bnivelliermasse\b|\bausgleichsmasse\b"),
        ),
    ),
    (
        r"\bbodenablauf eingebaut\b",
        (
            ("Ablaufset benutzt?", r"\bablauf(set)?\b|\bduschrinne\b"),
        ),
    ),
    (
        r"\bhausanschluss hergestellt\b",
        (
            ("Dichteinsatz benutzt?", r"\bdichteinsatz\b"),
        ),
    ),
    (
        r"\bfiligrandecke montiert\b",
        (
            ("Aufbeton benutzt?", r"\baufbeton\b"),
            ("Gitterträger benutzt?", r"\bgittertr(ä|ae)ger\b"),
        ),
    ),
)

_MACHINE_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("bagger", r"\b(?:mini\s*)?bagger(?:arbeiten)?\b|\bgebaggert\b", "Baggerarbeiten durchgeführt", "Baggerstunden erfassen?"),
    ("dumper", r"\bdumper\b", "Dumper eingesetzt", "Dumperstunden erfassen?"),
    (
        "ruettelplatte",
        r"\br(ü|ue)ttelplatte\b|\br(ü|ue)ttler\b",
        "Rüttelplatte eingesetzt",
        "Rüttelplattenstunden erfassen?",
    ),
    ("stampfer", r"\bstampfer\b", "Stampfer eingesetzt", "Stampferstunden erfassen?"),
    ("radlader", r"\bradlader\b", "Radlader eingesetzt", "Radladerstunden erfassen?"),
    (
        "walze",
        r"\b(?:walze(?:nzug)?|grabenwalze)\b",
        "Walzenarbeiten durchgeführt",
        "Walzenstunden erfassen?",
    ),
    (
        "kaltfraese",
        r"\bkaltfr(ä|ae)se\b",
        "Asphalt fräsen",
        "Kaltfräse?",
    ),
    (
        "asphaltfertiger",
        r"\basphaltfertiger\b",
        "Asphalt eingebaut",
        "Asphaltfertiger?",
    ),
    (
        "grader",
        r"\bgrader\b",
        "Planum hergestellt",
        "Grader?",
    ),
    ("kran", r"\b(autokran|turmdrehkran|kran)\b", "Kranarbeiten durchgeführt", "Kranstunden erfassen?"),
)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        v = str(raw or "").strip()
        if not v:
            continue
        key = v.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


def _format_date_de(value: str) -> str:
    s = str(value or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if not m:
        return s
    return f"{m.group(3)}.{m.group(2)}.{m.group(1)}"


def _clean_activity(text: str) -> str:
    t = str(text or "").strip()
    if not t:
        return ""
    t = re.sub(r"^(wir haben heute|wir haben|heute haben wir)\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^(danach|anschließend|anschliessend|zum schluss|zum schluß)\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\bund anschließend\b|\bund anschliessend\b", ", ", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip(" ,.;")
    return t


def _rewrite_activity(text: str, *, raw_text: str = "") -> str:
    out = _clean_activity(text)
    for pattern, repl in _ACTIVITY_REWRITE_RULES:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    out = apply_trade_phrase_memory(out, raw_text=raw_text)
    out = humanize_activity(out)
    out = re.sub(r"\s+", " ", out).strip(" ,.;")
    return out


def _activity_signature(activity: str, *, raw_text: str = "") -> str:
    t = _rewrite_activity(activity, raw_text=raw_text).casefold()
    t = re.sub(r"\b\d+(?:[.,]\d+)?\s*(m²|m2|qm|m³|m3|kg|t|mm|cm)\b", " ", t)
    t = re.sub(r"\b\d+(?:[.,]\d+)?\b", " ", t)
    t = re.sub(r"\b(verlegung von|durchführung von|herstellung von|montage von|einbau von)\b", " ", t)
    t = re.sub(r"[^a-z0-9äöüß/\s-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _has_quantity(text: str) -> bool:
    return bool(re.search(r"\b\d+(?:[.,]\d+)?\s*(m²|m2|qm|m³|m3|kg|t|mm|cm)\b", text.casefold()))


def _priority(activity: str, *, raw_text: str = "") -> float:
    a = activity.casefold()
    score = 0.0
    if _has_quantity(activity):
        score += 8.0
    if any(k in a for k in _MAIN_WORK_KEYWORDS):
        score += 4.0
    if _is_secondary_activity(activity):
        score -= 3.0
    if "splitt" in a or "silikonfugen" in a:
        score -= 1.5
    if "pflaster verlegt" in a or "fliesen verlegt" in a or "trockenbauwand geschlossen" in a:
        score += 2.0
    if "," in activity:
        score -= 1.5
    score += phrase_priority_boost(activity, raw_text=raw_text)
    score += min(len(activity), 120) / 200.0
    return score


def _is_secondary_activity(activity: str) -> bool:
    a = activity.casefold()
    if any(k in a for k in _SECONDARY_WORK_KEYWORDS):
        return True
    return False


def _pick_better(a: str, b: str, *, raw_text: str = "") -> str:
    pa = _priority(a, raw_text=raw_text)
    pb = _priority(b, raw_text=raw_text)
    if pb > pa:
        return b
    if pb == pa and len(b) > len(a):
        return b
    return a


def _semantic_dedupe_activities(activities: list[str], *, raw_text: str = "") -> list[str]:
    merged: list[str] = []
    for raw in activities:
        candidate = _rewrite_activity(raw, raw_text=raw_text)
        if not candidate:
            continue
        c_sig = _activity_signature(candidate, raw_text=raw_text)
        if not c_sig:
            continue
        found = False
        for idx, existing in enumerate(merged):
            e_sig = _activity_signature(existing, raw_text=raw_text)
            if not e_sig:
                continue
            if c_sig == e_sig or c_sig in e_sig or e_sig in c_sig:
                merged[idx] = _pick_better(existing, candidate, raw_text=raw_text)
                found = True
                break
        if not found:
            merged.append(candidate)
    merged = _dedupe(merged)
    merged.sort(key=lambda x: _priority(x, raw_text=raw_text), reverse=True)
    return merged


def _split_compound_activities(activities: list[str]) -> list[str]:
    out: list[str] = []
    for raw in activities:
        t = _clean_activity(raw)
        if not t:
            continue
        parts = [p.strip(" ,.;") for p in re.split(r"\s*,\s*|\s+sowie\s+|\s+und\s+", t, flags=re.IGNORECASE)]
        if len(parts) <= 1:
            chunks = re.findall(
                r"[^,.;]*?\b(?:verlegt|eingebaut|montiert|installiert|aufgebracht|geschlossen|verfugt|silikoniert|durchgeführt)\b",
                t,
                flags=re.IGNORECASE,
            )
            clean_chunks = [c.strip(" ,.;") for c in chunks if c.strip(" ,.;")]
            if len(clean_chunks) >= 2:
                parts = clean_chunks
        good: list[str] = []
        for p in parts:
            if not p:
                continue
            lp = p.casefold()
            if _has_quantity(p) or any(k in lp for k in _MAIN_WORK_KEYWORDS) or "silikonfugen" in lp:
                good.append(p)
        out.extend(good if good else [t])
    return out


_ACTIVITY_VERB_TOKENS = (
    "verlegt",
    "montiert",
    "eingebaut",
    "installiert",
    "aufgebracht",
    "aufgetragen",
    "geschnitten",
    "gesetzt",
    "gebaut",
    "verspachtelt",
    "verfugt",
    "abgehängt",
    "abgehaengt",
    "angeschlossen",
    "verdichtet",
    "ausgehoben",
    "entfernt",
    "beseitigt",
    "saniert",
    "geschlossen",
    "hergestellt",
    "betoniert",
    "gegossen",
    "gemauert",
    "befüllt",
    "befuellt",
    "fertiggestellt",
    "silikoniert",
)


def _looks_like_activity_phrase(text: str) -> bool:
    low = str(text or "").casefold().strip()
    if not low:
        return False
    # "Schotter" allein -> Material; "Schotter eingebaut" -> Aktivitätsphrase.
    return any(re.search(rf"\b{re.escape(tok)}\b", low) for tok in _ACTIVITY_VERB_TOKENS)


def _clean_material(text: str) -> str:
    t = str(text or "").strip()
    if not t:
        return ""
    if re.search(r"\b(wir haben|heute|danach)\b", t.casefold()):
        return ""
    if _looks_like_activity_phrase(t):
        # Aktivitätsphrasen ("Dämmung eingebaut", "Pflaster verlegt") gehören
        # nicht in die Materialliste.
        return ""
    t = re.sub(r"\s+", " ", t).strip(" ,.;")
    return humanize_material(t)


def _material_confidence_buckets(
    activities: list[str],
    raw_text: str,
    ai_materials: list[str],
) -> dict[str, list[str]]:
    high: list[str] = []
    medium: list[str] = []
    low: list[str] = []
    acts_join = " | ".join(activities).casefold()
    raw_probe = str(raw_text or "").casefold()
    # Zweiter Probe-Text mit Whisper-/Schreibfehler-Reparatur, damit Patterns
    # auch bei Varianten wie "Bewährung", "Aporoton", "11 5 a poroton" greifen.
    raw_probe_norm = normalize_for_match(str(raw_text or ""))

    for pattern, value in _EXPLICIT_MATERIAL_PATTERNS:
        if (
            re.search(pattern, acts_join, flags=re.IGNORECASE)
            or re.search(pattern, raw_probe, flags=re.IGNORECASE)
            or re.search(pattern, raw_probe_norm, flags=re.IGNORECASE)
        ):
            high.append(value)

    if re.search(r"\bmorgen\b.*\bpflaster\s+(?:legen|verlegen)\b", raw_probe, flags=re.IGNORECASE):
        high.append("Pflastersteine")

    # Sonderfall "Bettmoertel" ohne klares Praefix: Whisper macht aus
    # "Duennbettmoertel" gelegentlich "den Bettmoertel" (zentral schon repariert),
    # in anderen Faellen bleibt nur "Bettmoertel" stehen. Kontextabhaengig aufloesen:
    # - im KS/Kalksandstein-Kontext -> "Mauermoertel"
    # - im Porit/Ytong/Porenbeton-Kontext -> "Duennbettmoertel"
    # - sonst (z.B. Poroton, neutral) -> "Duennbettmoertel" als haeufigste Lesart.
    if re.search(r"\bbettm(ö|oe)rtel\b", raw_probe_norm, flags=re.IGNORECASE) and not re.search(
        r"\bd(ü|ue)nnbettm(ö|oe)rtel\b|\bmittelbettm(ö|oe)rtel\b|\bdickbettm(ö|oe)rtel\b",
        raw_probe_norm,
        flags=re.IGNORECASE,
    ):
        if re.search(r"\bkalksandstein\b|\bks[-\s]*stein\b|\bks\b", raw_probe_norm, flags=re.IGNORECASE):
            high.append("Mauermörtel")
        else:
            high.append("Dünnbettmörtel")

    for pattern, high_vals, med_vals, low_vals in _MATERIAL_CONFIDENCE_RULES:
        if re.search(pattern, acts_join, flags=re.IGNORECASE):
            high.extend(high_vals)
            medium.extend(med_vals)
            low.extend(low_vals)

    for dn in _extract_dn_values(raw_probe, kind="kg"):
        high.append(f"KG-Rohre DN {dn}")
    for dn in _extract_dn_values(raw_probe, kind="ht"):
        high.append(f"HT-Rohre DN {dn}")

    # Deterministische Extraktion spezifischer Steinformate aus dem
    # normalisierten Rohtext - greift unabhaengig von der AI-Strukturierung
    # und sorgt fuer Konsistenz zwischen den Steinfamilien (Poroton/Porit/KS).
    for fmt in _extract_stone_formats(raw_probe_norm):
        high.append(fmt)

    for item in ai_materials:
        clean = _clean_material(item)
        if not clean:
            continue
        c = clean.casefold()
        if c in (x.casefold() for x in high):
            continue
        if c in raw_probe:
            high.append(clean)
        elif c in acts_join:
            medium.append(clean)

    if "Mineralwolle" in high and "Dämmplatten" in high:
        high = [v for v in high if v not in ("Mineralwolle", "Dämmplatten")]
        high.append("Mineralwolle Dämmplatten")

    return {
        "high": _dedupe([x for x in high if x]),
        "medium": _dedupe([x for x in medium if x]),
        "low": _dedupe([x for x in low if x]),
    }


def _extract_stone_formats(text: str) -> list[str]:
    """Extrahiert spezifische Steinformate aus dem (normalisierten) Rohtext.

    Liefert Materialien wie "15er Poroton", "17,5er KS", "11,5er Porit".
    Wird in der HIGH-Konfidenz-Liste hinzugefuegt; der spaetere
    `_prefer_specific_material_labels`-Schritt entfernt dann die generischen
    Familieneintraege.
    """
    out: list[str] = []
    t = str(text or "")
    if not t:
        return out

    # Poroton-Familie (Ziegel)
    for m in re.finditer(r"\b(\d{1,2})(?:[.,](5))?er\s+poroton\b", t, flags=re.IGNORECASE):
        size = m.group(1)
        if m.group(2):
            size = f"{size},5"
        out.append(f"{size}er Poroton")

    # Porit/Ytong/Porenbeton-Familie
    for m in re.finditer(
        r"\b(\d{1,2})(?:[.,](5))?er\s+(porit|ytong|porenbeton)\b",
        t,
        flags=re.IGNORECASE,
    ):
        size = m.group(1)
        if m.group(2):
            size = f"{size},5"
        family = m.group(3).capitalize()
        out.append(f"{size}er {family}")

    # Kalksandstein-Familie (KS)
    for m in re.finditer(
        r"\b(\d{1,2})(?:[.,](5))?er\s+(?:ks|kalksandstein|ks[-\s]*stein)\b",
        t,
        flags=re.IGNORECASE,
    ):
        size = m.group(1)
        if m.group(2):
            size = f"{size},5"
        out.append(f"{size}er KS")

    return out


def _extract_dn_values(text: str, *, kind: str) -> list[str]:
    out: list[str] = []
    t = str(text or "")
    if kind == "kg":
        for m in re.finditer(r"\b(?:dn|den|de\s*en|d\s*n)\s*(\d{2,3})\s*[-\s]?(?:kg|kanal)\b", t, flags=re.IGNORECASE):
            out.append(m.group(1))
        for m in re.finditer(
            r"\b(?:kg|kanal)\s*[-\s]?(?:rohre?|rohr)?\s*(?:dn|den|de\s*en|d\s*n)\s*(\d{2,3})\b",
            t,
            flags=re.IGNORECASE,
        ):
            out.append(m.group(1))
        # Umgangssprache:
        # "100er/Hunderter KG-Rohr" => DN 110
        # "150er/Hundertfuffziger KG-Rohr" => DN 160
        if re.search(
            r"\b(100er|hunderter|hundert(?:er)?)\b.{0,24}\b(kg|kanal|kg[-\s]?rohr(?:e)?)\b",
            t,
            flags=re.IGNORECASE,
        ):
            out.append("110")
        if re.search(
            r"\b(150er|hundertf(ü|ue|u)nfzig(?:er)?|hundertfuffzig(?:er)?)\b.{0,24}\b(kg|kanal|kg[-\s]?rohr(?:e)?)\b",
            t,
            flags=re.IGNORECASE,
        ):
            out.append("160")
    elif kind == "ht":
        for m in re.finditer(r"\b(?:dn|den|de\s*en|d\s*n)\s*(\d{2,3})\s*[-\s]?ht\b", t, flags=re.IGNORECASE):
            out.append(m.group(1))
        for m in re.finditer(
            r"\bht\s*[-\s]?(?:rohre?|rohr)?\s*(?:dn|den|de\s*en|d\s*n)\s*(\d{2,3})\b",
            t,
            flags=re.IGNORECASE,
        ):
            out.append(m.group(1))
    return _dedupe(out)


_MATERIAL_ECHO_VERBS = re.compile(
    r"\b(?:verarbeitet|verbaut|verwendet|eingesetzt|eingebaut|reingemacht|reingepackt)\b|zum\s+einsatz\b",
    flags=re.IGNORECASE,
)


def _implied_materials_from_activities(activities: list[str]) -> set[str]:
    implied: set[str] = set()
    probe = " | ".join(str(x or "") for x in activities)
    for pattern, high_mats, _, _ in _MATERIAL_CONFIDENCE_RULES:
        if re.search(pattern, probe, flags=re.IGNORECASE):
            implied.update(m for m in high_mats if m)
    return implied


def _is_pure_material_echo(activity: str, known_materials: set[str]) -> bool:
    low = str(activity or "").casefold().strip()
    if not low or not known_materials:
        return False
    if not _MATERIAL_ECHO_VERBS.search(low):
        return False
    act_key = _material_key(low)
    if not act_key:
        return False
    for mat in known_materials:
        mat_key = _material_key(mat)
        if not mat_key:
            continue
        if mat_key not in act_key and act_key not in mat_key:
            continue
        remainder = _MATERIAL_ECHO_VERBS.sub(" ", low)
        remainder = re.sub(r"\b(dafür|dafuer|kamen|kam|zu|dem|der|die|das|es|sie)\b", " ", remainder)
        remainder = re.sub(r"\s+", " ", remainder).strip()
        rem_key = _material_key(remainder)
        if rem_key == mat_key or (mat_key and mat_key in rem_key):
            return True
    return False


def _drop_material_echo_activities(activities: list[str], materials: list[str]) -> list[str]:
    vals = [str(x).strip() for x in activities if str(x).strip()]
    if len(vals) < 2:
        return vals
    primary_implied = _implied_materials_from_activities([vals[0]])
    if not primary_implied:
        return vals
    out = [vals[0]]
    for act in vals[1:]:
        if re.search(
            r"\b\d+(?:[.,]\d+)?\s*(m²|m2|qm|m³|m3|lfm|stück|stk|kg|t)\b",
            act,
            flags=re.IGNORECASE,
        ):
            out.append(act)
            continue
        if _is_pure_material_echo(act, primary_implied):
            continue
        out.append(act)
    return _dedupe(out)


def _build_summary(input_data: dict[str, Any], activities: list[str]) -> str:
    if not activities:
        return "Keine Angabe"

    raw_text = str(input_data.get("rawText") or "")
    # Aktivitäten sind bereits priorisiert; erste Position = Hauptarbeit.
    parts = [_summary_fragment(x, raw_text=raw_text) for x in activities]
    parts = [p for p in parts if p]
    if not parts:
        return "Keine Angabe"

    main = parts[0]
    secondaries = parts[1:3]
    first_sentence = _build_main_sentence(raw_text, main)

    if not secondaries:
        return first_sentence

    secondary_sentence = f"Zusätzlich wurden {_join_activities(secondaries)}."
    return f"{first_sentence} {secondary_sentence}"


def _ensure_activity_material_consistency(activities: list[str], materials: list[str], raw_text: str) -> list[str]:
    out = list(activities)
    acts_probe = " | ".join(activities).casefold()
    mats_probe = " | ".join(materials).casefold()
    raw_probe = str(raw_text or "").casefold()

    if "pflanzkübel" in mats_probe and "pflanzkübel" not in acts_probe and re.search(r"\bpflanzk(ü|ue)bel\b", raw_probe):
        if re.search(r"\b(fertiggestellt|befüllt|befuellt|gesetzt|gestellt)\b", raw_probe):
            out.append("Pflanzkübel fertiggestellt")
    if "schotter" in mats_probe and "schotter" not in acts_probe and re.search(r"\bschotter\b", raw_probe):
        if re.search(r"\b(eingebaut|eingebracht|verarbeitet|verwendet|reingemacht|rein gemacht|rein)\b", raw_probe):
            out.append("Schotter eingebaut")
        elif re.search(
            r"\b(kubik|kubikmeter|m³|m3)\b.{0,30}?\bschotter\b|\bschotter\b.{0,30}?\b(kubik|kubikmeter|m³|m3)\b",
            raw_probe,
        ):
            out.append("Schotter eingebaut")
    if "splitt" in mats_probe and "splitt" not in acts_probe and re.search(r"\bsplitt|split\b", raw_probe):
        if re.search(r"\b(eingebaut|verarbeitet|eingebracht|verwendet)\b", raw_probe):
            out.append("Splitt eingebaut")
    if ("steinwolle" in mats_probe or "mineralwolle" in mats_probe) and "dämmung eingebaut" not in acts_probe:
        if re.search(r"\b(dämmung|daemmung|steinwolle|mineralwolle|dämmmatte|daemmatte)\b", raw_probe) and re.search(
            r"\b(eingebaut|verlegt|angebracht|montiert|eingebracht|reingepackt|reingemacht|eingesetzt)\b",
            raw_probe,
        ):
            out.append("Dämmung eingebaut")
    return _dedupe(out)


def _enforce_explicit_optional_materials(materials: list[str], raw_text: str) -> list[str]:
    raw_probe = str(raw_text or "").casefold()
    optional_only_when_explicit: tuple[tuple[str, str], ...] = (
        ("CD-Profile", r"\bcd[-\s]*profile?\b"),
        ("CW/UW-Profile", r"\b(?:cw|uw)[-\s]*profile?n?\b"),
        ("Abhänger", r"\babh(ä|ae)nger\b"),
        ("Heckenschere", r"\bheckenschere\b"),
        ("Frostschutzmaterial", r"\bfrostschutz\b"),
        ("Bodenmaterial", r"\bbodenmaterial\b"),
    )
    out: list[str] = []
    for mat in materials:
        value = str(mat or "").strip()
        if not value:
            continue
        keep = True
        for label, pattern in optional_only_when_explicit:
            if value.casefold() == label.casefold() and not re.search(pattern, raw_probe, flags=re.IGNORECASE):
                keep = False
                break
        if keep:
            out.append(value)
    return _dedupe(out)


def _build_material_suggestions(activities: list[str], materials: list[str], raw_text: str) -> list[str]:
    acts_probe = " | ".join(str(x or "") for x in activities).casefold()
    mats_probe = " | ".join(str(x or "") for x in materials).casefold()
    raw_probe = str(raw_text or "").casefold()
    material_keys = {_material_key(m) for m in materials if _material_key(m)}

    suggestions: list[str] = []
    for activity_pattern, candidates in _SUGGESTION_RULES:
        if not re.search(activity_pattern, acts_probe, flags=re.IGNORECASE):
            continue
        for label, explicit_pattern in candidates:
            normalized = str(label or "").strip()
            if not normalized:
                continue
            core = re.sub(r"\s*\?\s*$", "", normalized).casefold()
            key = _material_key(normalized)
            # Bereits im finalen Material oder im Rohtext/Activities erwähnt -> kein Vorschlag.
            if core and (core in mats_probe or core in raw_probe or core in acts_probe):
                continue
            # Werkzeug/Maschine bereits im Rohtext → kein Vorschlag (auch Teilwörter).
            if re.search(r"\bputzmaschine\b", raw_probe) and "putzmaschine" in core:
                continue
            if re.search(r"\bschwammbrett\b", raw_probe) and "filzbrett" in core:
                continue
            if re.search(r"\bfilzbrett\b", raw_probe) and "filzbrett" in core:
                continue
            if re.search(r"\bfilzbrett\b", raw_probe) and "schwammbrett" in core:
                continue
            if "schimmelentferner" in core and re.search(r"\bschimmel\s+beseitigt\b", raw_probe) and re.search(
                r"\bsanierputz\b", raw_probe
            ) and re.search(r"\b(unterputz|oberputz|haftgrund)\b", raw_probe):
                continue
            if re.search(r"\bglättkelle\b|\bglaettkelle\b", raw_probe) and ("glättkelle" in core or "glaettkelle" in core):
                continue
            if re.search(r"\bzahntraufel\b", raw_probe) and "zahntraufel" in core:
                continue
            if re.search(r"\btellerd(ü|ue)bel\b", raw_probe) and "tellerd" in core:
                continue
            if re.search(r"\bschlagd(ü|ue)bel\b", raw_probe) and "schlagd" in core:
                continue
            if re.search(r"\bschraubd(ü|ue)bel\b", raw_probe) and "schraubd" in core:
                continue
            if re.search(r"\bklebeputz\b", raw_probe) and "klebeputz" in core:
                continue
            if re.search(r"\b(teller|schraub|schlag)d(ü|ue)bel\b", raw_probe) and re.search(
                r"d(ü|ue)bel", core
            ):
                continue
            if re.search(r"\bkartätsche\b|\bkartaetsche\b", raw_probe) and (
                "kartätsche" in core or "kartaetsche" in core or "putzmaschine" in core
            ):
                continue
            if re.search(r"\b(stuckkleber|montagekleber)\b", raw_probe) and ("kleber" in core or "montagekleber" in core):
                continue
            if key and key in material_keys:
                continue
            if re.search(explicit_pattern, raw_probe, flags=re.IGNORECASE):
                continue
            if re.search(explicit_pattern, mats_probe, flags=re.IGNORECASE):
                continue
            suggestions.append(normalized)

    kg_dns = _extract_dn_values(raw_probe, kind="kg")
    if re.search(r"\bkg-rohre\b", acts_probe, flags=re.IGNORECASE) and kg_dns:
        suggestions = [
            s
            for s in suggestions
            if not re.match(r"^KG-(Bögen|Abzweige)\s+benutzt\?$", str(s), flags=re.IGNORECASE)
        ]
        for dn in kg_dns:
            for label in (
                f"KG-Bögen DN {dn} benutzt?",
                f"KG-Abzweige DN {dn} benutzt?",
                f"Reinigungsrohr DN {dn} benutzt?",
            ):
                key = _material_key(label)
                if key and key in material_keys:
                    continue
                suggestions.append(label)

    ht_dns = _extract_dn_values(raw_probe, kind="ht")
    if re.search(r"\bht-rohre\b", acts_probe, flags=re.IGNORECASE) and ht_dns:
        suggestions = [
            s
            for s in suggestions
            if not re.match(r"^HT-(Bögen|Abzweige|Manschette)\s+benutzt\?$", str(s), flags=re.IGNORECASE)
        ]
        for dn in ht_dns:
            for label in (
                f"HT-Bögen DN {dn} benutzt?",
                f"HT-Abzweige DN {dn} benutzt?",
                f"HT-Manschette DN {dn} benutzt?",
            ):
                key = _material_key(label)
                if key and key in material_keys:
                    continue
                suggestions.append(label)

    suggestions = _append_keramikterrasse_thickness_suggestions(
        suggestions,
        acts_probe=acts_probe,
        mats_probe=mats_probe,
        raw_probe=raw_probe,
        material_keys=material_keys,
    )

    return _dedupe(suggestions)


def _append_keramikterrasse_thickness_suggestions(
    suggestions: list[str],
    *,
    acts_probe: str,
    mats_probe: str,
    raw_probe: str,
    material_keys: set[str],
) -> list[str]:
    if not re.search(r"\bkeramikterrasse\b", acts_probe, flags=re.IGNORECASE):
        return suggestions

    thin = bool(
        re.search(
            r"\b(?:keramik(?:platte(?:n)?)?|platte(?:n)?)\s*(?:zwei|2)\s*(?:cm|zentimeter)\b|"
            r"\b(?:zwei|2)\s*(?:cm|zentimeter)\s*(?:dick(?:e|r|es)?|keramik|platte(?:n)?)\b",
            raw_probe,
            flags=re.IGNORECASE,
        )
    )
    thick = bool(
        re.search(
            r"\b(?:keramik(?:platte(?:n)?)?|platte(?:n)?)\s*(?:drei|vier|fünf|funf|3|4|5)\s*(?:cm|zentimeter)\b|"
            r"\b(?:drei|vier|fünf|funf|3|4|5)\s*(?:cm|zentimeter)\s*(?:dick(?:e|r|es)?|keramik|platte(?:n)?)\b",
            raw_probe,
            flags=re.IGNORECASE,
        )
    )

    def _maybe_add(label: str, explicit_pattern: str) -> None:
        normalized = str(label or "").strip()
        if not normalized:
            return
        core = re.sub(r"\s*\?\s*$", "", normalized).casefold()
        key = _material_key(normalized)
        if core and (core in mats_probe or core in raw_probe or core in acts_probe):
            return
        if key and key in material_keys:
            return
        if re.search(explicit_pattern, raw_probe, flags=re.IGNORECASE):
            return
        if re.search(explicit_pattern, mats_probe, flags=re.IGNORECASE):
            return
        suggestions.append(normalized)

    # Dünne Platten (2 cm): typisch auf Stelzlager.
    if thin:
        suggestions = [
            s
            for s in suggestions
            if not re.search(r"^(Drainagemörtel|Einkornmörtel)\s+benutzt\?$", str(s), flags=re.IGNORECASE)
        ]
        _maybe_add("Stelzlager benutzt?", r"\bstelzlag")
        return suggestions

    # Dickere Platten (3 cm+): Bettung statt Stelzlager.
    if thick:
        suggestions = [
            s
            for s in suggestions
            if not re.search(r"^Stelzlager\s+benutzt\?$", str(s), flags=re.IGNORECASE)
        ]
        _maybe_add("Einkornmörtel benutzt?", r"\beinkorn(?:m(ö|oe)rtel)?\b")
        _maybe_add("Drainagemörtel benutzt?", r"\bdrainage(?:m(ö|oe)rtel)?\b")
        return suggestions

    return suggestions


def _material_key(value: str) -> str:
    t = str(value or "").casefold().strip()
    if not t:
        return ""
    t = re.sub(r"\?$", "", t).strip()
    t = re.sub(
        r"\b(benutzt|verwendet|verarbeitet|eingebaut|aufgetragen|aufgebracht|montiert|gesetzt|verlegt)\b",
        " ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bdn\s*\d{2,3}\b", " ", t, flags=re.IGNORECASE)
    # Singular/Plural-Harmonisierung für robustes Dedupe.
    t = re.sub(r"\bthermostatventile\b", "thermostatventil", t)
    t = re.sub(r"\brücklaufverschraubungen\b|\bruecklaufverschraubungen\b", "rücklaufverschraubung", t)
    t = re.sub(r"\babzweige\b", "abzweig", t)
    t = re.sub(r"\bb(ö|oe)gen\b", "bogen", t)
    t = re.sub(r"\bfittings\b", "fitting", t)
    t = re.sub(r"\bboegen\b", "bogen", t)
    t = re.sub(r"[^a-z0-9äöüß/\s-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\bpflaster\s+steine?\b", "pflastersteine", t)
    t = re.sub(r"\bfliesen\s+kleber\b", "fliesenkleber", t)
    return t


def _enforce_pipe_family_consistency(materials: list[str], activities: list[str], raw_text: str) -> list[str]:
    acts_probe = " | ".join(str(x or "") for x in activities).casefold()
    raw_probe = str(raw_text or "").casefold()
    context = f"{acts_probe} | {raw_probe}"
    has_kg_context = bool(re.search(r"\bkg\b|\bkanal\b", context, flags=re.IGNORECASE))
    has_ht_context = bool(re.search(r"\bht\b|\babwasser\b", context, flags=re.IGNORECASE))

    out: list[str] = []
    for mat in materials:
        value = str(mat or "").strip()
        if not value:
            continue
        low = value.casefold()
        if has_ht_context and not has_kg_context and re.search(r"\bkg\b", low, flags=re.IGNORECASE):
            continue
        if has_kg_context and not has_ht_context and re.search(r"\bht\b", low, flags=re.IGNORECASE):
            continue
        out.append(value)
    return _dedupe(out)


def _prefer_dn_specific_materials(materials: list[str]) -> list[str]:
    vals = [str(x).strip() for x in materials if str(x).strip()]
    has_kg_dn = any(re.search(r"\bkg-rohre\s*dn\s*\d{2,3}\b", v, flags=re.IGNORECASE) for v in vals)
    has_ht_dn = any(re.search(r"\bht-rohre\s*dn\s*\d{2,3}\b", v, flags=re.IGNORECASE) for v in vals)
    out: list[str] = []
    for value in vals:
        low = value.casefold()
        if has_kg_dn and low == "kg-rohre":
            continue
        if has_ht_dn and low == "ht-rohre":
            continue
        out.append(value)
    return _dedupe(out)


def _resolve_bettmoertel_conflicts(materials: list[str]) -> list[str]:
    """Entfernt einen isolierten "Bettmoertel"-Eintrag, wenn bereits eine
    spezifischere Moertel-Variante (Duenn-/Mittel-/Dickbett-/Mauermoertel) im
    Material steht. Hintergrund: Whisper macht aus "Duennbettmoertel" oft
    "den Bettmoertel"; die zentrale Normalisierung repariert das, aber AI-
    Material-Extraktion liefert zusaetzlich rohes "Bettmoertel" - das ist eine
    Dopplung.
    """
    vals = [str(x).strip() for x in materials if str(x).strip()]
    if not vals:
        return []
    probe = " | ".join(v.casefold() for v in vals)
    has_specific_mortar = bool(
        re.search(r"\b(d(ü|ue)nnbett|mittelbett|dickbett)m(ö|oe)rtel\b", probe, flags=re.IGNORECASE)
    ) or bool(re.search(r"\bmauerm(ö|oe)rtel\b", probe, flags=re.IGNORECASE))
    if not has_specific_mortar:
        return vals
    out: list[str] = []
    for v in vals:
        if v.casefold().strip() in ("bettmörtel", "bettmoertel"):
            continue
        out.append(v)
    return out


def _prefer_specific_material_labels(materials: list[str]) -> list[str]:
    vals = [str(x).strip() for x in materials if str(x).strip()]
    probe = " | ".join(v.casefold() for v in vals)

    has_kg_bogen = "kg-bögen" in probe or "kg-boegen" in probe
    has_ht_bogen = "ht-bögen" in probe or "ht-boegen" in probe
    has_kg_abzweig = "kg-abzweige" in probe or "kg-abzweig" in probe
    has_ht_abzweig = "ht-abzweige" in probe or "ht-abzweig" in probe
    has_specific_putz = any(
        key in probe
        for key in ("oberputz", "unterputz", "innenputz", "außenputz", "aussenputz", "grundputz", "sanierputz")
    )
    # Spezifische Stein-Formate (z.B. "24er Poroton", "17,5er Poroton")
    # ueberschreiben den generischen Familieneintrag ("Poroton-Ziegel").
    has_specific_poroton = bool(
        re.search(r"\b\d{1,2}(?:[.,]5)?er\s*poroton\b", probe, flags=re.IGNORECASE)
    )
    has_specific_porenbeton = bool(
        re.search(r"\b\d{1,2}(?:[.,]5)?er\s*(?:porit|porenbeton|ytong)\b", probe, flags=re.IGNORECASE)
    )
    has_specific_ks = bool(
        re.search(r"\b\d{1,2}(?:[.,]5)?er\s*(?:ks|kalksandstein)\b", probe, flags=re.IGNORECASE)
    )
    has_armierungsmoertel = "armierungsmörtel" in probe or "armierungsmoertel" in probe

    out: list[str] = []
    for value in vals:
        low = value.casefold()
        if (has_kg_bogen or has_ht_bogen) and low in ("bögen", "bogen", "boegen"):
            continue
        if (has_kg_abzweig or has_ht_abzweig) and low in ("abzweige", "abzweig"):
            continue
        if has_specific_putz and low == "putz":
            continue
        if has_specific_poroton and low in ("poroton-ziegel", "poroton ziegel", "poroton"):
            continue
        if has_specific_porenbeton and low in ("porenbetonsteine", "porenbeton", "porit", "ytong"):
            continue
        if has_specific_ks and low in ("kalksandsteine", "kalksandstein", "ks", "ks-steine", "ks-stein"):
            continue
        if has_armierungsmoertel and low in ("mörtel", "moertel"):
            continue
        out.append(value)
    return _dedupe(out)


def _apply_dn_to_pipe_fittings(materials: list[str], activities: list[str], raw_text: str) -> list[str]:
    vals = [str(x).strip() for x in materials if str(x).strip()]
    if not vals:
        return []
    acts_probe = " | ".join(str(x or "") for x in activities).casefold()
    raw_probe = str(raw_text or "").casefold()
    has_kg_context = bool(re.search(r"\bkg\b|\bkanal\b", f"{acts_probe} | {raw_probe}", flags=re.IGNORECASE))
    has_ht_context = bool(re.search(r"\bht\b|\babwasser\b", f"{acts_probe} | {raw_probe}", flags=re.IGNORECASE))
    kg_dns = _extract_dn_values(raw_text, kind="kg")
    ht_dns = _extract_dn_values(raw_text, kind="ht")
    kg_dn = kg_dns[0] if len(kg_dns) == 1 else None
    ht_dn = ht_dns[0] if len(ht_dns) == 1 else None

    out: list[str] = []
    for value in vals:
        low = value.casefold()
        if kg_dn and (low in ("kg-bögen", "kg-boegen") or (has_kg_context and low in ("bögen", "bogen", "boegen"))):
            out.append(f"KG-Bögen DN {kg_dn}")
            continue
        if kg_dn and (low in ("kg-abzweige", "kg-abzweig") or (has_kg_context and low in ("abzweige", "abzweig"))):
            out.append(f"KG-Abzweige DN {kg_dn}")
            continue
        if ht_dn and (low in ("ht-bögen", "ht-boegen") or (has_ht_context and low in ("bögen", "bogen", "boegen"))):
            out.append(f"HT-Bögen DN {ht_dn}")
            continue
        if ht_dn and (low in ("ht-abzweige", "ht-abzweig") or (has_ht_context and low in ("abzweige", "abzweig"))):
            out.append(f"HT-Abzweige DN {ht_dn}")
            continue
        if ht_dn and low in ("manschette", "ht-manschette"):
            out.append(f"HT-Manschette DN {ht_dn}")
            continue
        out.append(value)
    return _dedupe(out)


def _machine_hours_present(raw_text: str, *, machine_key: str) -> bool:
    raw = str(raw_text or "").casefold()
    machine_patterns: dict[str, str] = {
        "bagger": r"\b(?:mini\s*)?bagger\b",
        "dumper": r"\bdumper\b",
        "ruettelplatte": r"\br(ü|ue)ttelplatte\b|\br(ü|ue)ttler\b",
        "stampfer": r"\bstampfer\b",
        "radlader": r"\bradlader\b",
        "walze": r"\bwalze(nzug)?\b|\bgrabenwalze\b",
        "kran": r"\b(autokran|turmdrehkran|kran)\b",
        "lkw": r"\blkw\b",
        "putzmaschine": r"\bputzmaschine\b",
    }
    machine_pattern = machine_patterns.get(machine_key, "")
    if not machine_pattern:
        return False
    if not re.search(machine_pattern, raw, flags=re.IGNORECASE):
        return False
    # Stundenangaben im Kontext der Maschine (direkt danach oder wenige Wörter davor).
    gap = r"(?:\s+\S+){0,8}\s+"
    return bool(
        re.search(
            machine_pattern + r"\s+(\d+(?:[.,]\d+)?)\s*(h|std|stunden)\b",
            raw,
            flags=re.IGNORECASE,
        )
        or re.search(
            r"\b(\d+(?:[.,]\d+)?)\s*(h|std|stunden)\b" + gap + machine_pattern,
            raw,
            flags=re.IGNORECASE,
        )
    )


def _extract_machine_hours(raw_text: str) -> list[str]:
    raw = str(raw_text or "").casefold()
    out: list[str] = []
    machine_patterns: tuple[tuple[str, str], ...] = (
        ("Bagger", r"\b(?:mini\s*)?bagger\b"),
        ("Dumper", r"\bdumper\b"),
        ("Rüttelplatte", r"\br(ü|ue)ttelplatte\b|\br(ü|ue)ttler\b"),
        ("Stampfer", r"\bstampfer\b"),
        ("Radlader", r"\bradlader\b"),
        ("Walze", r"\b(?:walze(?:nzug)?|grabenwalze)\b"),
        ("Kran", r"\b(?:autokran|turmdrehkran|kran)\b"),
        ("LKW", r"\blkw\b"),
        ("Putzmaschine", r"\bputzmaschine\b"),
    )
    gap = r"(?:\s+\S+){0,8}\s+"
    for label, pattern in machine_patterns:
        m_after = re.search(
            pattern + r"\s+(\d+(?:[.,]\d+)?)\s*(h|std|stunden)\b",
            raw,
            flags=re.IGNORECASE,
        )
        if m_after and m_after.group(1):
            hours = m_after.group(1).replace(".", ",")
            out.append(f"{label}: {hours} h")
            continue
        m_before = re.search(
            r"\b(\d+(?:[.,]\d+)?)\s*(h|std|stunden)\b" + gap + pattern,
            raw,
            flags=re.IGNORECASE,
        )
        if m_before and m_before.group(1):
            hours = m_before.group(1).replace(".", ",")
            out.append(f"{label}: {hours} h")
    return _dedupe(out)


def _apply_machine_assistance(
    activities: list[str],
    raw_text: str,
) -> tuple[list[str], list[str], list[str]]:
    acts = list(activities)
    raw_probe = str(raw_text or "").casefold()
    machine_suggestions: list[str] = []

    existing_probe = " | ".join(acts).casefold()
    for machine_key, detect_pattern, activity_text, suggestion_label in _MACHINE_RULES:
        if not re.search(detect_pattern, raw_probe, flags=re.IGNORECASE):
            continue
        if activity_text.casefold() not in existing_probe:
            acts.append(activity_text)
            existing_probe = " | ".join(acts).casefold()
        if not _machine_hours_present(raw_text, machine_key=machine_key):
            machine_suggestions.append(suggestion_label)

    machine_hours = _extract_machine_hours(raw_text)
    return _dedupe(acts), _dedupe(machine_suggestions), machine_hours


def _context_gate_activities(activities: list[str], raw_text: str) -> list[str]:
    probe = str(raw_text or "").casefold()
    has_fliesen_context = bool(re.search(r"\b(fliesen?|fliesenkleber|fugenmörtel|fugenmoertel)\b", probe))
    has_trockenbau_context = _raw_has_trockenbau_context(probe)
    out: list[str] = []
    for act in activities:
        low = str(act or "").casefold()
        if has_trockenbau_context and not has_fliesen_context:
            if any(token in low for token in ("fliesen", "fliesenkleber", "fugenmörtel", "fugenmoertel")):
                continue
        if "fliesen verfugt" in low and not has_fliesen_context and has_trockenbau_context:
            continue
        out.append(str(act))
    return _dedupe(out)


def _evidence_gate_activities(activities: list[str], raw_text: str) -> list[str]:
    raw = normalize_for_match(str(raw_text or ""))
    if not raw.strip():
        return _dedupe(activities)

    acts = [str(a or "").strip() for a in activities if str(a or "").strip()]
    kept: list[str] = []
    for act in acts:
        if _activity_is_supported_by_raw(act, raw, acts):
            kept.append(act)
    return _dedupe(kept)


def _activity_is_supported_by_raw(activity: str, raw: str, all_activities: list[str]) -> bool:
    low = str(activity or "").casefold()
    if not low:
        return False

    if "gipskartonplatten montiert" in low:
        return bool(
            re.search(
                r"gips\s*karton|rigips|ri\s+gips|gk[\s-]?platten|knauf|"
                r"beide\s+seiten\s+beplankt|doppelständerwand",
                raw,
            )
            or (
                re.search(r"\bbeplankt\b", raw)
                and re.search(
                    r"trocken\s*bau|ständerwerk|staender\s*werk|gips\s*karton|rigips|ri\s+gips",
                    raw,
                )
            )
        )
    if "decke abgehängt" in low:
        return bool(
            re.search(r"decke|akustik\s*decke|abhang\s*decke", raw)
            and re.search(
                r"abgeh(ä|ae|a)ng|abgehaengt|abgehangen|runtergeh(ä|ae|a)ng|runtergehaengt",
                raw,
            )
            or (
                _raw_has_trockenbau_context(raw)
                and re.search(r"decke", raw)
                and re.search(r"montiert|angebracht", raw)
            )
        )
    if "fugen verspachtelt" in low:
        return bool(
            re.search(r"\bfugen?\b|\bfugenspachtel\b|\btrockenbaufugen\b", raw)
            and re.search(r"(spacht|fugenspachtel|verspacht|zugemacht|zu\s+gemacht|nachzu\s+gemacht|gezogen)", raw)
        )
    if "fliesen verfugt" in low:
        if not re.search(r"\bfugen?\b|\bfugenm(ö|oe)rtel\b|\bverfugt\b|\bnachgezogen\b", raw):
            return False
        if re.search(r"fliesen|fliese|naturstein|mosaik|feinsteinzeug", raw):
            return True
        if re.search(r"\b(bodenablauf|duschrinne|ablaufrinne)\b", raw):
            return True
        return any("fliesen verlegt" in x.casefold() or "naturstein verlegt" in x.casefold() for x in all_activities)
    if "bodenablauf eingebaut" in low:
        return bool(re.search(r"boden\s*ablauf|duschrinne|ablaufrinne", raw))
    if "fliesenkleber aufgetragen" in low:
        has_verb = re.search(
            r"(gezogen|aufgezogen|aufgetragen|aufgebracht|auf\s+getragen|auf\s+gezogen|benutzt|verwendet|verarbeitet|gemacht|drauf)",
            raw,
        )
        if not has_verb:
            return False
        if re.search(r"\bfliesenkleber\b|\bflexkleber\b|\bmittelbettm(ö|oe)rtel\b", raw):
            return True
        if re.search(r"fliesen\s*kleber|flex\s*kleber", raw):
            return True
        # Generischer "Kleber" zaehlt nur, wenn auch Fliesen-Kontext da ist.
        if re.search(r"\b\w*kleber\b", raw) and re.search(r"\bfliesen?\b", raw):
            return True
        # Duennbettmoertel ist nur im Fliesen-Kontext eindeutig Fliesenkleber;
        # im Mauerwerks-Kontext (Poroton/Porit/Ytong/KS) NICHT.
        if re.search(r"\bd(ü|ue)nnbettm(ö|oe)rtel\b", raw) and re.search(r"\bfliesen?\b", raw):
            return True
        return False
    if "pflanzen gesetzt" in low:
        return bool(re.search(r"\bpflanz", raw) and re.search(r"(gesetzt|gepflanzt|bepflanzt|eingepflanzt)", raw))
    if "hecke geschnitten" in low:
        return bool(
            re.search(r"\b(hecken?|str(ä|ae)ucher)\b", raw, flags=re.IGNORECASE)
            and re.search(
                r"(geschnitten|getrimmt|zurückgeschnitten|zurueckgeschnitten|schneiden|schneide)",
                raw,
                flags=re.IGNORECASE,
            )
        )
    if "rasen gemäht" in low:
        return bool(
            re.search(r"\brasen\b", raw)
            and re.search(r"(gemäht|gemaeht|gemacht|mähen|maehen|geschnitten)", raw, flags=re.IGNORECASE)
        )
    if "rasen getrimmt" in low:
        return bool(
            re.search(r"\brasen\b", raw)
            and re.search(r"(getrimmt|freigeschnitten|freischneiden|nachgeschnitten)", raw, flags=re.IGNORECASE)
        )
    if "unkraut entfernt" in low:
        return bool(
            re.search(r"\bunkraut\b", raw, flags=re.IGNORECASE)
            and re.search(
                r"(entfernt|gejätet|gejaetet|gezupft|zupfen|weg gemacht|weg|gemacht|gehackt|gerupft|beseitigt)",
                raw,
                flags=re.IGNORECASE,
            )
        )
    if "laub entfernt" in low:
        return bool(re.search(r"\blaub\b", raw, flags=re.IGNORECASE))
    if "pflasterfugen" in low:
        before = raw.split("morgen", 1)[0] if re.search(r"\bmorgen\b", raw, flags=re.IGNORECASE) else raw
        if re.search(r"\bfugensand\b", raw, flags=re.IGNORECASE) and re.search(
            r"\bf(?:ü|ue|u)llen\b",
            raw,
            flags=re.IGNORECASE,
        ):
            return bool(re.search(r"\bverfugt\b|\bverfüllt\b|\bverfuellt\b", before, flags=re.IGNORECASE))
        return bool(re.search(r"\bverfugt\b|\bverfüllt\b|\bverfuellt\b", raw, flags=re.IGNORECASE))

    return True


def _location_prefix(raw_text: str, main_fragment: str) -> str:
    raw = str(raw_text or "").casefold()
    main = str(main_fragment or "").casefold()
    if "fliesen" in main and re.search(r"\b(bad|badezimmer|nasszelle|duschbad|gäste-?wc|gaeste-?wc)\b", raw):
        return "Im Bad wurden "
    return "Auf der Baustelle wurden "


def _build_main_sentence(raw_text: str, main_fragment: str) -> str:
    main = str(main_fragment or "").strip()
    if not main:
        return "Keine Angabe"
    if re.match(r"^(die|der|das)\s+", main.casefold()):
        prefix = _location_prefix(raw_text, main).replace("wurden ", "wurde ")
        return f"{prefix}{main}."
    return f"{_location_prefix(raw_text, main)}{main}."


def _join_activities(items: list[str]) -> str:
    vals = [str(x).strip() for x in items if str(x).strip()]
    if not vals:
        return "zusätzliche Arbeiten durchgeführt"
    if len(vals) == 1:
        return vals[0]
    if len(vals) == 2:
        return f"{vals[0]} und {vals[1]}"
    return f"{vals[0]}, {vals[1]} und {vals[2]}"


def _summary_fragment(activity: str, *, raw_text: str = "") -> str:
    a = _rewrite_activity(activity, raw_text=raw_text)
    low = a.casefold()
    m_fliesen = re.search(r"(\d+(?:[.,]\d+)?)\s*m²\s*fliesen verlegt", low)
    if m_fliesen:
        return f"ca. {m_fliesen.group(1)} m² Fliesen verlegt"
    m_pfl = re.search(r"(\d+(?:[.,]\d+)?)\s*m²\s*pflaster verlegt", low)
    if m_pfl:
        return f"{m_pfl.group(1)} m² Pflaster verlegt"
    m_schot = re.search(r"(\d+(?:[.,]\d+)?)\s*m³\s*schotter eingebaut", low)
    if m_schot:
        return f"{m_schot.group(1)} m³ Schotter eingebaut"
    m_rasen = re.search(r"(\d+(?:[.,]\d+)?)\s*m²\s*rasen gemäht", low)
    if m_rasen:
        return f"{m_rasen.group(1)} m² Rasen gemäht"
    if low == "spachtelarbeiten durchgeführt":
        return "Spachtelarbeiten durchgeführt"
    if low == "trockenbauwand geschlossen":
        return "die Trockenbauwand geschlossen"
    if low == "wasserleitungen montiert":
        return "Wasserleitungen montiert"
    if low == "heizungsanschlüsse montiert":
        return "Heizungsanschlüsse montiert"
    return a


def _drop_conflicting_pipe_activities(activities: list[str], raw_text: str = "") -> list[str]:
    probe = " | ".join(str(a or "") for a in activities).casefold()
    raw = str(raw_text or "").casefold()
    if "kg-rohre" in probe or "ht-rohre" in probe:
        if re.search(r"\bwasserleit", raw):
            return list(activities)
        return [a for a in activities if "wasserleitungen" not in str(a or "").casefold()]
    return list(activities)


def _drop_customer_sentiment_activities(activities: list[str]) -> list[str]:
    out: list[str] = []
    for act in activities:
        low = str(act or "").strip().casefold()
        if not low:
            continue
        if re.search(
            r"\b(?:freut\s+sich|weitere\s+auftrag|weiterempfehl|kontaktkreis|"
            r"sehr\s+zufrieden|mit\s+unserer\s+arbeit|empfiehlt\s+uns)\b",
            low,
        ):
            continue
        if re.search(r"\b(?:kundin|kunde|bauherr|auftraggeber)\b", low) and not re.search(
            r"\b(?:verlegt|gelegt|gebaut|montiert|eingebaut|geschnitten|aufgetragen|"
            r"geschlossen|betoniert|gegossen|grundiert)\b",
            low,
        ):
            continue
        out.append(str(act))
    return out


def _drop_runon_noise_activities(activities: list[str]) -> list[str]:
    out: list[str] = []
    for act in activities:
        low = str(act or "").strip().casefold()
        if not low:
            continue
        if re.match(r"^(also|genau)\s+\w+", low):
            continue
        if low.startswith("ich hab gemacht "):
            continue
        if low.startswith("ja also vom tag her "):
            continue
        if re.search(r"\bfeierabend\b", low):
            continue
        out.append(str(act))
    return out


def _raw_future_segment(raw_text: str) -> str:
    m = re.search(r"\b(?:und\s+)?morgen\b", str(raw_text or ""), flags=re.IGNORECASE)
    if not m:
        return ""
    return str(raw_text or "")[m.start() :]


def _raw_paving_aborted(raw_text: str) -> bool:
    raw = str(raw_text or "").casefold()
    planned = bool(
        re.search(
            r"\b(wollten|wollen|wollte)\b.{0,140}\b(?:mit\s+dem\s+)?pflaster\w*\b.{0,80}\banfangen\b"
            r"|\bpflaster\w*\b.{0,80}\banfangen\b",
            raw,
        )
    )
    aborted = bool(
        re.search(
            r"\b(abbrechen|unterbrochen|angefangen\s+(?:hat\s+)?zu\s+regnen|"
            r"strich\s+durch\s+die\s+rechnung)\b",
            raw,
        )
    )
    return planned and aborted


def _drop_aborted_paving_activities(activities: list[str], raw_text: str) -> list[str]:
    if not _raw_paving_aborted(raw_text):
        return activities
    out: list[str] = []
    for act in activities:
        low = str(act or "").casefold()
        if re.search(r"\bpflaster\b", low) and re.search(r"\b(verlegt|eingebaut|gelegt)\b", low):
            continue
        if re.search(r"\bwollten\b", low):
            continue
        out.append(str(act))
    return out


def _drop_graben_unterbau_false_positive(activities: list[str], raw_text: str) -> list[str]:
    raw = str(raw_text or "").casefold()
    if not re.search(r"\bunterbau\b", raw):
        return activities
    if re.search(r"\bgraben\s+(?:ausgehoben|ausgeschachtet|gezogen)\b", raw):
        return activities
    return [a for a in activities if "graben ausgehoben" not in str(a or "").casefold()]


def _is_future_only_pflaster_activity(activity: str, raw_text: str) -> bool:
    low_act = str(activity or "").casefold()
    raw = str(raw_text or "").casefold()
    if not re.search(r"\bpflaster\b", low_act):
        return False
    if not re.search(r"\b(?:verlegt|gelegt|eingebaut)\b", low_act):
        return False
    future = _raw_future_segment(raw_text).casefold()
    if not future or not re.search(r"\bpflaster\s+(?:legen|verlegen)\b", future):
        return False
    before = raw.split("morgen", 1)[0]
    return not re.search(r"\bpflaster\s+(?:verlegt|gelegt|eingebaut)\b", before)


def _drop_future_work_activities(activities: list[str], raw_text: str) -> list[str]:
    """Entfernt Zukunfts-/Plan-Arbeiten aus der Tätigkeitsliste (z. B. morgen Pflaster legen)."""
    out: list[str] = []
    for act in activities:
        low = str(act or "").strip().casefold()
        if not low:
            continue
        if re.match(r"^morgen\s+m(?:ü|ue)ssen\b", low):
            continue
        if re.match(
            r"^(?:morgen|montag|dienstag|mittwoch|donnerstag|freitag|samstag|"
            r"nächste\s+woche|naechste\s+woche)\b",
            low,
        ):
            continue
        if _is_future_only_pflaster_activity(act, raw_text):
            continue
        if "pflasterfugen" in low:
            # raw_text → lokale Variable (wie in den anderen Filtern); sonst NameError → 500
            raw = str(raw_text or "").casefold()
            before = raw.split("morgen", 1)[0] if re.search(r"\bmorgen\b", raw) else raw
            if re.search(r"\bfugensand\b", raw) and re.search(
                r"\bf(?:ü|ue|u)llen\b",
                raw,
                flags=re.IGNORECASE,
            ) and not re.search(r"\bverfugt\b|\bverfüllt\b|\bverfuellt\b", before, flags=re.IGNORECASE):
                continue
        out.append(str(act))
    return out


def _drop_garbage_material_lines(materials: list[str]) -> list[str]:
    """Entfernt Satzfragmente und Tätigkeits-Echos aus der Materialliste."""
    out: list[str] = []
    for mat in materials:
        low = str(mat or "").strip().casefold()
        if not low:
            continue
        if len(low) > 55:
            continue
        if re.search(r"\b(danach|und dann|eingebaut und|eingebaut danach)\b", low):
            continue
        if re.search(r"\beingebaut\b", low) and re.search(r"\b(pflaster|schotter|splitt|split)\b", low):
            continue
        if re.search(r"\b(?:legen|verlegen)\b", low):
            continue
        if re.search(r"\b(morgen|muessen|müssen|fertig\s+gestellt|fertiggestellt|wollten|wollen)\b", low):
            continue
        if re.search(r"\bm³\b", mat, flags=re.IGNORECASE) and re.search(r"\bpflaster\b", low):
            continue
        if re.search(r"\b(reingepackt|reingemacht)\b", low):
            continue
        if re.search(r"\brein\b", low) and re.search(r"\b(split|splitt|schotter|frostschutz)\b", low):
            continue
        out.append(str(mat))
    return _dedupe(out)


def _prefer_quantified_materials(materials: list[str]) -> list[str]:
    """Bare Materialzeilen und doppelte Mengenzeilen bereinigen."""
    vals = [str(x).strip() for x in materials if str(x).strip()]
    has_pflastersteine = any(_material_key(x) == "pflastersteine" for x in vals)

    quant_by_base: dict[str, list[str]] = {}
    bare_or_other: list[str] = []
    for mat in vals:
        if re.match(r"^\d", mat):
            core = re.sub(r"^\d+(?:[.,]\d+)?\s+\S+\s+", "", mat.casefold()).strip()
            base = core.split()[0] if core else _material_key(mat)
            if base == "split":
                base = "splitt"
            quant_by_base.setdefault(base, []).append(mat)
        else:
            bare_or_other.append(mat)

    quant_keys: set[str] = set()
    out: list[str] = []
    for base, lines in quant_by_base.items():
        best = max(lines, key=lambda x: len(x))
        if base in {"splitt", "schotter", "pflastersteine"}:
            quant_keys.add(base)
        if has_pflastersteine and re.search(r"\bm²\b", best, flags=re.IGNORECASE):
            if re.search(r"\bpflaster\b", best, flags=re.IGNORECASE):
                continue
        out.append(best)

    for mat in bare_or_other:
        key = _material_key(mat)
        if key in quant_keys:
            continue
        out.append(mat)

    return _dedupe(out)


def _drop_putz_layer_material_echo(materials: list[str], activities: list[str]) -> list[str]:
    """Entfernt Tätigkeits-Echos aus Materialien (z. B. „50 m² Pflaster gelegt“), behält Produktnamen."""
    acts_probe = " | ".join(str(a or "") for a in activities).casefold()
    out: list[str] = []
    for mat in materials:
        low = str(mat or "").strip().casefold()
        if not low:
            continue
        # Vollständige Tätigkeitszeilen mit Arbeitsverb — kein Material.
        if re.search(
            r"\b(aufgetragen|auf\s*getragen|aufgebracht|auf\s*gebracht|verarbeitet|geglättet|geglaettet|filziert|gelegt|verlegt|gesetzt|gemäht|gemaeht|geschnitten|eingebaut|eingebracht)\b",
            low,
        ):
            continue
        low_core = re.sub(r"^\d+(?:[.,]\d+)?\s*(?:m²|m2|qm²|qm2|quadratmeter)\s+", "", low)
        low_core = re.sub(r"\s+auf\s*getragen\s*$", "", low_core).strip()
        drop = False
        # Kratzputz nur als Material, wenn Außenputz-Tätigkeit den Kontext schon trägt.
        if re.search(r"\b(außenputz|aussenputz)\b.*\b(aufgetragen|aufgebracht|verarbeitet)\b", acts_probe):
            if low_core == "kratzputz" or low_core.startswith("kratzputz "):
                drop = True
        # Oberputz/Unterputz etc. als kurze Produktnamen bleiben erhalten (gewünscht im Bericht).
        if not drop:
            out.append(str(mat))
    return _dedupe(out)


def apply_quality_filter(input_data: dict[str, Any], structured: dict[str, Any]) -> dict[str, Any]:
    result = dict(structured)
    activities_raw = [str(x) for x in (result.get("activities") or [])]
    materials_raw = [str(x) for x in (result.get("materials") or [])]
    machine_hours_raw = [str(x).strip() for x in (result.get("machineHours") or []) if str(x).strip()]
    problems_raw = [str(x).strip() for x in (result.get("problems") or []) if str(x).strip()]
    open_raw = [str(x).strip() for x in (result.get("openItems") or []) if str(x).strip()]

    raw_text = str(input_data.get("rawText") or "")
    activities = canonicalize_activities(activities_raw, raw_text=raw_text)
    activities = _drop_conflicting_pipe_activities(activities, raw_text)
    activities = _context_gate_activities(activities, raw_text)
    activities = _evidence_gate_activities(activities, raw_text)
    activities = _drop_runon_noise_activities(activities)
    activities = _drop_future_work_activities(activities, raw_text)
    activities = _drop_aborted_paving_activities(activities, raw_text)
    activities = _drop_graben_unterbau_false_positive(activities, raw_text)
    activities = _drop_customer_sentiment_activities(activities)
    activities, machine_suggestions, machine_hours_auto = _apply_machine_assistance(activities, raw_text)
    confidence = _material_confidence_buckets(
        activities,
        raw_text,
        materials_raw,
    )
    # Nur HIGH-Confidence-Materialien sind im finalen Bericht sichtbar.
    materials = _enforce_explicit_optional_materials(confidence["high"], raw_text)
    materials = _prefer_dn_specific_materials(materials)
    materials = _apply_dn_to_pipe_fittings(materials, activities, raw_text)
    materials = _resolve_bettmoertel_conflicts(materials)
    materials = _prefer_specific_material_labels(materials)
    materials = _enforce_pipe_family_consistency(materials, activities, raw_text)
    from app.services.material_quantity_builder import enrich_materials_list

    materials = enrich_materials_list(materials, raw_text)
    materials = _drop_garbage_material_lines(materials)
    materials = _prefer_quantified_materials(materials)
    materials = _drop_putz_layer_material_echo(materials, activities)
    activities = _ensure_activity_material_consistency(activities, materials, raw_text)
    activities = _drop_material_echo_activities(activities, materials)
    material_suggestions = _build_material_suggestions(activities, materials, raw_text)
    summary = build_deterministic_summary(
        activities,
        raw_text=raw_text,
        date=str(input_data.get("date") or ""),
        project_name=str(input_data.get("projectName") or ""),
    )

    result["activities"] = activities
    result["materials"] = materials
    result["materialSuggestions"] = material_suggestions
    result["machineSuggestions"] = machine_suggestions
    result["machineHours"] = _dedupe(machine_hours_raw + machine_hours_auto)
    result["summary"] = summary
    from app.services.summary_material_guard import strip_material_echo_from_summary

    result["summary"] = strip_material_echo_from_summary(
        str(result.get("summary") or summary),
        materials,
        activities,
    )
    result["problems"] = _dedupe(problems_raw)
    result["openItems"] = _dedupe(open_raw)
    from app.services.problem_open_builder import refine_open_items_list, refine_problems_list

    result["problems"] = refine_problems_list(result["problems"], raw_text)
    result["openItems"] = refine_open_items_list(result["openItems"], raw_text)
    result["customerTalk"] = refine_customer_talk(
        raw_text,
        str(result.get("customerTalk") or ""),
        summary=str(result.get("summary") or summary),
    )
    if not str(result.get("customerTalk") or "").strip():
        result["customerTalk"] = "Keine Angabe"
    return result
