"""Recompute evidence/ab/measurements.csv. Offline, no API key.

Delegates to ``python -m consent_lab measure`` with the evidence directory
next to this file, so the command still works from any working directory.
"""

from __future__ import annotations

from pathlib import Path

from consent_lab.cli import main

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "evidence" / "ab"
    raise SystemExit(main(["measure", "--root", str(root)]))
