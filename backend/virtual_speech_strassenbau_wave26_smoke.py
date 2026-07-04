"""Welle 26: Straßenbau Herz-Nieren — Tätigkeiten, Material, ASR, gebrochenes Deutsch.

Deckt Dimensionen der Wellen 2–16 für Straßenbau/Tiefbau-Straße. Rein additiv.
"""

from __future__ import annotations

from strassenbau_wave_scenarios import core_scenarios
from virtual_speech_strassenbau_shared import build_cases, run_smoke


def main() -> int:
    cases = build_cases(core_scenarios(), prefix="Strassenbau")
    return run_smoke(cases, "VIRTUAL-SPEECH-STRASSENBAU-WAVE26-SMOKE")


if __name__ == "__main__":
    raise SystemExit(main())
