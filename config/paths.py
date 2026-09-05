"""Compat: chemins legacy + src.utils.paths."""

from __future__ import annotations

import os

from src.utils.paths import (
    ASSETS as ASSETS_DIR,
    BOARD_ASSETS as BOARD_DIR,
    ENGINES_DIR,
    PIECE_ASSETS as PIECES_DIR,
    ROOT as BASE_DIR,
    RUNTIME as RUNTIME_DIR,
    STOCKFISH_DIR,
    piece_set_dir as _piece_set_dir,
    theme_dir as _theme_dir,
    user_data_dir,
)

# str paths for anciens scripts
ASSETS_DIR = str(ASSETS_DIR)
BOARD_DIR = str(BOARD_DIR)
PIECES_DIR = str(PIECES_DIR)
ENGINES_DIR = str(ENGINES_DIR)
BASE_DIR = str(BASE_DIR)
RUNTIME_DIR = str(RUNTIME_DIR)

STOCKFISH_CANDIDATES = [
    os.environ.get("STOCKFISH_PATH", "").strip(),
    os.path.join(str(STOCKFISH_DIR), "stockfish.exe"),
    os.path.join(ENGINES_DIR, "stockfish.exe"),
    "stockfish.exe",
    "stockfish",
]


def theme_dir(theme_id: str) -> str:
    return str(_theme_dir(theme_id))


def piece_set_dir(set_id: str) -> str:
    return str(_piece_set_dir(set_id))
