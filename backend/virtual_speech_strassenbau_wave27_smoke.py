"""Welle 27: Straßenbau P2/P3 — Kundengespräch, Problem, Offen (implizit + explizit).

Deckt Dimensionen der Wellen 20–24 für Straßenbau. Rein additiv.
"""

from __future__ import annotations

from strassenbau_wave_scenarios import problem_customer_scenarios
from virtual_speech_strassenbau_shared import build_cases, run_smoke


def main() -> int:
    cases = build_cases(problem_customer_scenarios(), prefix="StrassenbauPC")
    return run_smoke(cases, "VIRTUAL-SPEECH-STRASSENBAU-WAVE27-SMOKE")


if __name__ == "__main__":
    raise SystemExit(main())
