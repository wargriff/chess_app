from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import chess
import chess.engine

from config.paths import ENGINES_DIR, STOCKFISH_CANDIDATES

STOCKFISH_RELEASE_URL = (
    "https://github.com/official-stockfish/Stockfish/releases/download/"
    "sf_17.1/stockfish-windows-x86-64-avx2.zip"
)


def find_stockfish_binary() -> str | None:
    for candidate in STOCKFISH_CANDIDATES:
        if os.path.isabs(candidate):
            if os.path.isfile(candidate):
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    return None


def download_stockfish() -> str | None:
    os.makedirs(ENGINES_DIR, exist_ok=True)
    zip_path = os.path.join(ENGINES_DIR, "stockfish.zip")
    extract_dir = os.path.join(ENGINES_DIR, "_extract")

    try:
        print("Téléchargement de Stockfish...")
        urlretrieve(STOCKFISH_RELEASE_URL, zip_path)
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(extract_dir)

        for root, _, files in os.walk(extract_dir):
            for name in files:
                if name.lower().startswith("stockfish") and name.lower().endswith(".exe"):
                    source = os.path.join(root, name)
                    target = os.path.join(ENGINES_DIR, "stockfish.exe")
                    shutil.copy2(source, target)
                    return target
    except OSError as error:
        print(f"Impossible de télécharger Stockfish : {error}")
    finally:
        if os.path.isfile(zip_path):
            os.remove(zip_path)
        if os.path.isdir(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)
    return None


class StockfishEngine:
    """Moteur Stockfish avec réglage ELO via UCI."""

    def __init__(self, elo: int, skill: int | None = None) -> None:
        self.elo = elo
        self.skill = skill
        self._engine: chess.engine.SimpleEngine | None = None
        self.available = False
        self.engine_label = "Minimax (fallback)"
        self._open()

    def _open(self) -> None:
        binary = find_stockfish_binary()
        if binary is None:
            binary = download_stockfish()

        if binary is None:
            return

        try:
            self._engine = chess.engine.SimpleEngine.popen_uci(binary)
            self._apply_strength()
            self.available = True
            self.engine_label = f"Stockfish ({self.elo} ELO)"
            print(f"Stockfish chargé : {binary}")
        except (chess.engine.EngineError, subprocess.SubprocessError, OSError) as error:
            print(f"Stockfish indisponible ({binary}) : {error}")
            self._engine = None

    def _apply_strength(self) -> None:
        if self._engine is None:
            return

        if self.elo >= 1320:
            self._engine.configure(
                {
                    "UCI_LimitStrength": True,
                    "UCI_Elo": min(max(self.elo, 1320), 3190),
                }
            )
        else:
            skill = self.skill if self.skill is not None else max(0, min(20, self.elo // 60))
            self._engine.configure(
                {
                    "UCI_LimitStrength": False,
                    "Skill Level": skill,
                }
            )

    def set_elo(self, elo: int, skill: int | None = None) -> None:
        self.elo = elo
        self.skill = skill
        if self._engine is not None:
            self._apply_strength()
            self.engine_label = f"Stockfish ({self.elo} ELO)"

    def choose_move(self, board: chess.Board, limit: chess.engine.Limit | None = None) -> chess.Move | None:
        if self._engine is None or board.is_game_over():
            return None

        search_limit = limit or chess.engine.Limit(time=0.4)
        result = self._engine.play(board, search_limit)
        return result.move

    def close(self) -> None:
        if self._engine is not None:
            self._engine.quit()
            self._engine = None
