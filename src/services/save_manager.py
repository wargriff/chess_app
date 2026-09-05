"""Sauvegardes PGN / FEN."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from src.core.board import ChessBoard
from src.utils.paths import SAVES, ensure_data_dirs

logger = logging.getLogger("chesspro.save")


class SaveManager:
    def __init__(self, folder: Path | None = None) -> None:
        ensure_data_dirs()
        self.folder = folder or SAVES

    def list_saves(self) -> list[Path]:
        return sorted(self.folder.glob("*.pgn"), key=lambda p: p.stat().st_mtime, reverse=True)

    def save_pgn(self, pgn_text: str, name: str | None = None) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = name or f"partie_{stamp}.pgn"
        if not filename.endswith(".pgn"):
            filename += ".pgn"
        path = self.folder / filename
        path.write_text(pgn_text, encoding="utf-8")
        logger.info("PGN sauvegarde: %s", path)
        return path

    def load_pgn(self, path: Path) -> tuple[ChessBoard, object]:
        text = path.read_text(encoding="utf-8")
        return ChessBoard.load_pgn(text)

    def save_fen(self, fen: str, name: str | None = None) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = name or f"position_{stamp}.fen"
        if not filename.endswith(".fen"):
            filename += ".fen"
        path = self.folder / filename
        path.write_text(fen.strip() + "\n", encoding="utf-8")
        return path

    def load_fen(self, path: Path) -> str:
        return path.read_text(encoding="utf-8").strip().splitlines()[0]
