"""Met a jour Chess Pro : dependances, assets, Stockfish, exe."""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS = os.path.join(ROOT, "tools")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _run(label: str, script: str) -> None:
    path = os.path.join(TOOLS, script)
    print(f"\n[{label}] {script}")
    subprocess.check_call([sys.executable, path], cwd=ROOT)


def main() -> int:
    os.chdir(ROOT)
    print("=" * 55)
    print("  Chess Pro - Mise a jour")
    print(f"  {ROOT}")
    print("=" * 55)

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    _run("assets plateau", "generate_assets.py")

    pieces = os.path.join(ROOT, "assets", "pieces", "california", "wK.png")
    if not os.path.isfile(pieces):
        _run("pieces Lichess", "download_pieces.py")

    from core.stockfish_engine import download_stockfish, find_stockfish_binary

    if not find_stockfish_binary():
        print("\n[Stockfish] telechargement...")
        download_stockfish()

    _run("compilation exe", "build_exe.py")

    app = os.path.join(ROOT, "dist", "ChessPro", "ChessPro.exe")
    if os.path.isfile(app):
        print(f"\nOK — jeu pret : {app}")
        print("Lancez : dist\\ChessPro\\JOUEZ-ICI.bat ou ChessPro.exe")
        return 0

    print("\nEchec : exe introuvable apres build.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
