from __future__ import annotations

import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BOARD_DIR = os.path.join(ASSETS_DIR, "board")
PIECES_DIR = os.path.join(ASSETS_DIR, "pieces")
ENGINES_DIR = os.path.join(BASE_DIR, "engines")

STOCKFISH_DIR = r"C:\src\stockfish-windows-x86-64-avx2\stockfish"

STOCKFISH_CANDIDATES = [
    os.path.join(STOCKFISH_DIR, "stockfish-windows-x86-64-avx2.exe"),
    os.path.join(STOCKFISH_DIR, "stockfish.exe"),
    os.path.join(STOCKFISH_DIR, "stockfish"),
    os.path.join(ENGINES_DIR, "stockfish.exe"),
    os.path.join(ENGINES_DIR, "stockfish-windows-x86-64-avx2.exe"),
    os.path.join(ENGINES_DIR, "stockfish-windows-x86-64.exe"),
    "stockfish.exe",
    "stockfish",
]


def theme_dir(theme_id: str) -> str:
    return os.path.join(BOARD_DIR, theme_id)


def piece_set_dir(set_id: str) -> str:
    return os.path.join(PIECES_DIR, set_id)
