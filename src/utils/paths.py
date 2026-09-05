"""Chemins robustes (dev, frozen PyInstaller, data utilisateur)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """Racine du projet (assets, stockfish) ou dossier de l'exe."""
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    # src/utils/paths.py -> src/utils -> src -> project root
    return Path(__file__).resolve().parents[2]


def bundle_dir() -> Path:
    """Ressources embarquées (MEIPASS en frozen, sinon racine projet)."""
    if _is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return project_root()


def runtime_dir() -> Path:
    return Path(sys.executable).resolve().parent if _is_frozen() else project_root()


def user_data_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        path = base / "ChessPro"
    else:
        path = Path.home() / ".chesspro"
    path.mkdir(parents=True, exist_ok=True)
    return path


ROOT = project_root()
BUNDLE = bundle_dir()
RUNTIME = runtime_dir()

ASSETS = BUNDLE / "assets"
BOARD_ASSETS = ASSETS / "board"
PIECE_ASSETS = ASSETS / "pieces"
SOUND_ASSETS = ASSETS / "sounds"
ICON_ASSETS = ASSETS / "icons"
FONT_ASSETS = ASSETS / "fonts"
BG_ASSETS = ASSETS / "backgrounds"

DATA = RUNTIME / "data"
SAVES = DATA / "saves"
SETTINGS_DIR = DATA / "settings"
CACHE = DATA / "cache"
LOGS = DATA / "logs"

STOCKFISH_DIR = RUNTIME / "stockfish"
ENGINES_DIR = RUNTIME / "engines"  # legacy fallback


def ensure_data_dirs() -> None:
    for folder in (SAVES, SETTINGS_DIR, CACHE, LOGS, STOCKFISH_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def theme_dir(theme_id: str) -> Path:
    return BOARD_ASSETS / theme_id


def piece_set_dir(set_id: str) -> Path:
    return PIECE_ASSETS / set_id


def settings_file() -> Path:
    ensure_data_dirs()
    return SETTINGS_DIR / "settings.json"


def stockfish_candidates(custom: str | None = None) -> list[Path]:
    candidates: list[Path] = []
    env = (os.environ.get("STOCKFISH_PATH") or "").strip()
    if custom:
        candidates.append(Path(custom))
    if env:
        candidates.append(Path(env))
    for folder in (STOCKFISH_DIR, ENGINES_DIR):
        candidates.extend(
            [
                folder / "stockfish.exe",
                folder / "stockfish-windows-x86-64-avx2.exe",
                folder / "stockfish-windows-x86-64.exe",
                folder / "stockfish",
            ]
        )
    return candidates
