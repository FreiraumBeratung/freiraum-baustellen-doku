"""Generator Putz & Stuck Welle 17 — Profil-Cluster (JSON-Katalog).

Fokus: APU, Leibung, Eckschutz, Sockelprofil, Tropfkante.
Rein additiv; Welle 15/16 bleiben Regression.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "putz_stuck_wave17_scenarios.py"


def s(raw: str, acts: tuple[str, ...], **kw) -> dict:
    d = dict(
        raw=raw,
        acts=acts,
        mats=(),
        forbid_acts=(),
        problem=False,
        open_=False,
        customer=False,
        min_act=None,
    )
    d.update(kw)
    return d


SCENARIOS: list[dict] = [
    # ── APU-Leisten ──
    s(
        "APU-Leiste 6mm montiert am Fensteranschluss mit Klebeputz.",
        ("APU-Leisten montiert",),
        mats=("APU-Leiste", "Klebeputz"),
    ),
    s(
        "Anputzleiste 9mm gesetzt Fensteranschlussprofil montiert.",
        ("APU-Leisten montiert",),
        mats=("APU-Leiste",),
        min_act=1,
    ),
    s(
        "APU-Leiste mit Gewebe montiert Problem Material knapp Offen Rest morgen.",
        ("APU-Leisten montiert",),
        problem=True,
        open_=True,
    ),
    s(
        "hamma APU-Leiste montiert fertig.",
        ("APU-Leisten montiert",),
        min_act=1,
    ),
    # ── Eckschutz ──
    s(
        "Eckschutzschiene Alu gesetzt an allen Außenecken.",
        ("Eckschutzprofile gesetzt",),
        mats=("Eckschutzschiene",),
    ),
    s(
        "Eckprofil PVC montiert Kantenschutz verarbeitet.",
        ("Eckschutzprofile gesetzt",),
    ),
    s(
        "Eckschutzprofile gesetzt mit Klebeputz und Spachtelmasse.",
        ("Eckschutzprofile gesetzt",),
        mats=("Eckschutzschiene", "Klebeputz"),
    ),
    # ── Leibungsprofile ──
    s(
        "Leibungsprofil PVC am Fenster gesetzt.",
        ("Leibungsprofile gesetzt",),
        mats=("Leibungsprofil",),
    ),
    s(
        "Laibungsprofil Alu montiert Fensterleibung fertig.",
        ("Leibungsprofile gesetzt",),
        mats=("Leibungsprofil",),
    ),
    s(
        "Leibungsprofile gesetzt Dichtlippe montiert Kunde informiert.",
        ("Leibungsprofile gesetzt",),
        customer=True,
    ),
    # ── Sockelprofile ──
    s(
        "Sockelprofil 8mm montiert mit Tropfkante.",
        ("Sockelprofile montiert",),
        mats=("Sockelprofil",),
    ),
    s(
        "Startprofil 10mm gesetzt Sockelschiene angebracht.",
        ("Sockelprofile montiert",),
        mats=("Sockelprofil",),
    ),
    s(
        "Sockelprofile montiert Sockeldämmung und Noppenbahn verarbeitet.",
        ("Sockelprofile montiert",),
    ),
    # ── Tropfkanten ──
    s(
        "Tropfkantenprofil Alu gesetzt unter Fensterbank.",
        ("Tropfkantenprofile gesetzt",),
        mats=("Tropfkantenprofil",),
    ),
    s(
        "Abtropfkante PVC montiert Tropfkante mit Gewebe.",
        ("Tropfkantenprofile gesetzt",),
        mats=("Tropfkantenprofil",),
    ),
    s(
        "Tropfkantenprofile gesetzt Klebeputz und Armierungsmörtel benutzt.",
        ("Tropfkantenprofile gesetzt",),
        mats=("Klebeputz", "Armierungsmörtel"),
    ),
    # ── Ketten / WDVS + Profile ──
    s(
        "WDVS Dämmung geklebt. Sockelprofil montiert. APU-Leiste montiert.",
        ("WDVS Dämmung geklebt", "Sockelprofile montiert", "APU-Leisten montiert"),
    ),
    s(
        "Sockelprofil montiert APU-Leiste montiert Leibungsprofil gesetzt Eckschutz gesetzt.",
        (
            "Sockelprofile montiert",
            "APU-Leisten montiert",
            "Leibungsprofile gesetzt",
            "Eckschutzprofile gesetzt",
        ),
        min_act=3,
    ),
    s(
        "Eckschutzprofile gesetzt. Tropfkantenprofile gesetzt. Reibputz aufgetragen.",
        ("Eckschutzprofile gesetzt", "Tropfkantenprofile gesetzt", "Reibputz aufgetragen"),
    ),
    s(
        (
            "An der Fassade WDVS gedübelt Armierungsgewebe eingebettet "
            "Sockelprofil montiert APU-Leisten montiert Leibungsprofile gesetzt "
            "Bauherr zufrieden Problem Wind Offen letzte Ecke Montag."
        ),
        (
            "WDVS gedübelt",
            "Armierung ausgeführt",
            "Sockelprofile montiert",
            "APU-Leisten montiert",
            "Leibungsprofile gesetzt",
        ),
        problem=True,
        open_=True,
        customer=True,
        min_act=4,
    ),
    s(
        "Leibungsprofil gesetzt. Eckschutzschiene gesetzt. Außenputz aufgetragen.",
        ("Leibungsprofile gesetzt", "Eckschutzprofile gesetzt", "Außenputz aufgetragen"),
    ),
    # ── Regression-Schutz (Sockelputz / Stuck bleiben) ──
    s(
        "Sockelputz aufgetragen und verarbeitet.",
        ("Sockelputz aufgetragen",),
        forbid_acts=("Sockelprofile montiert",),
    ),
    s(
        "Sockelleiste stuckiert Gesims angebracht.",
        ("Stuckarbeiten durchgeführt",),
        forbid_acts=("Sockelprofile montiert",),
    ),
    # ── Kurz / Umgangssprache ──
    s(
        "heute APU montiert und Eckschutz gemacht.",
        ("APU-Leisten montiert", "Eckschutzprofile gesetzt"),
        min_act=1,
    ),
    s(
        "ich hab Leibung und Tropfkante gesetzt.",
        ("Leibungsprofile gesetzt", "Tropfkantenprofile gesetzt"),
        min_act=1,
    ),
    s(
        "40 Meter Eckschutzschiene gesetzt fertig.",
        ("Eckschutzprofile gesetzt",),
        min_act=1,
    ),
    s(
        "Kundengespräch Profile abgestimmt Problem Lieferung spät Offen APU nächste Woche.",
        (),
        problem=True,
        open_=True,
        customer=True,
        min_act=0,
    ),
]


def _emit() -> str:
    lines = [
        '"""Putz & Stuck Welle 17 — generierte Basisszenarien (Profil-Cluster)."""',
        "",
        "from __future__ import annotations",
        "",
        "",
        "def all_base_scenarios() -> list[dict]:",
        "    return [",
    ]
    for spec in SCENARIOS:
        lines.append("        {")
        lines.append(f'            "raw": {spec["raw"]!r},')
        lines.append(f'            "acts": {spec["acts"]!r},')
        if spec.get("mats"):
            lines.append(f'            "mats": {spec["mats"]!r},')
        if spec.get("forbid_acts"):
            lines.append(f'            "forbid_acts": {spec["forbid_acts"]!r},')
        if spec.get("problem"):
            lines.append('            "problem": True,')
        if spec.get("open_"):
            lines.append('            "open_": True,')
        if spec.get("customer"):
            lines.append('            "customer": True,')
        if spec.get("min_act") is not None:
            lines.append(f'            "min_act": {spec["min_act"]!r},')
        lines.append("        },")
    lines.append("    ]")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUT.write_text(_emit(), encoding="utf-8")
    print(f"Wrote {len(SCENARIOS)} scenarios -> {OUT}")


if __name__ == "__main__":
    main()
