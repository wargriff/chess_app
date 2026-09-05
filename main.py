"""Point d'entree Chess Pro D4 — logique dans src/app.py."""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_path() -> None:
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> None:
    _ensure_src_path()
    from src.app import run

    raise SystemExit(run())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[Chess Pro] Erreur: {exc}", file=sys.stderr)
        raise
