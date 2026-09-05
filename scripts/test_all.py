#!/usr/bin/env python
"""Lance toute la suite de tests Chess Pro D4."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    print("=== Chess Pro D4 — tests automatiques ===")
    cmd = [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"]
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode == 0:
        print("Tous les tests ont réussi.")
    else:
        print("Des tests ont échoué.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
