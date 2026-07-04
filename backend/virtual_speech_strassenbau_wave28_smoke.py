"""Welle 28: Straßenbau Cross-Monster — GaLaBau + Tiefbau + Straßenbau gemischt.

Deckt Dimension der Welle 25 für Pilot-Realität (öffentlicher Bereich). Rein additiv.
"""

from __future__ import annotations

from strassenbau_wave_scenarios import cross_trade_scenarios
from virtual_speech_strassenbau_shared import build_cases, run_smoke


def main() -> int:
    cases = build_cases(cross_trade_scenarios(), prefix="StrassenbauX")
    return run_smoke(cases, "VIRTUAL-SPEECH-STRASSENBAU-WAVE28-SMOKE")


if __name__ == "__main__":
    raise SystemExit(main())
