"""Lance le backend API Chess Pro D4 (port 3848)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.main import main

if __name__ == "__main__":
    main()
