"""Sauvegardes JSON de partie (+ PGN/FEN en export secondaire)."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.board import ChessBoard
from src.utils.paths import SAVES, ensure_data_dirs

logger = logging.getLogger("chesspro.save")

SAVE_VERSION = 1


@dataclass
class GameSaveMeta:
    path: Path
    saved_at: str
    mode: str
    white: str
    black: str
    elo: int | None
    result: str
    ply: int
    label: str


@dataclass
class GameSaveData:
    version: int = SAVE_VERSION
    saved_at: str = ""
    mode: str = "PVP"
    moves: list[str] = field(default_factory=list)
    fen_start: str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    white_name: str = "Joueur"
    black_name: str = "Joueur"
    human_is_white: bool = True
    elo: int = 1200
    skill: int | None = 8
    time_minutes: int = 10
    time_increment: int = 0
    white_seconds: float = 600.0
    black_seconds: float = 600.0
    clock_enabled: bool = True
    result: str = "*"
    message: str = ""
    board_theme: str = ""
    piece_set: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameSaveData:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


class SaveManager:
    def __init__(self, folder: Path | None = None) -> None:
        ensure_data_dirs()
        self.folder = folder or SAVES
        self.folder.mkdir(parents=True, exist_ok=True)

    def list_json_saves(self) -> list[GameSaveMeta]:
        metas: list[GameSaveMeta] = []
        for path in sorted(self.folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = self.load_game(path)
            except Exception as exc:
                logger.warning("Sauvegarde illisible %s: %s", path.name, exc)
                continue
            result = data.result or "*"
            label = f"{data.white_name} vs {data.black_name}"
            metas.append(
                GameSaveMeta(
                    path=path,
                    saved_at=data.saved_at or path.stem,
                    mode=data.mode,
                    white=data.white_name,
                    black=data.black_name,
                    elo=data.elo if data.mode != "PVP" else None,
                    result=result,
                    ply=len(data.moves),
                    label=label,
                )
            )
        return metas

    def list_saves(self) -> list[Path]:
        """Compat : chemins JSON puis PGN."""
        json_paths = [m.path for m in self.list_json_saves()]
        pgn_paths = sorted(self.folder.glob("*.pgn"), key=lambda p: p.stat().st_mtime, reverse=True)
        return json_paths + pgn_paths

    def save_game(self, data: GameSaveData, name: str | None = None) -> Path:
        if not data.saved_at:
            data.saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = name or f"{stamp}.json"
        if not filename.endswith(".json"):
            filename += ".json"
        path = self.folder / filename
        path.write_text(json.dumps(data.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Partie sauvegardée: %s", path)
        return path

    def load_game(self, path: Path) -> GameSaveData:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Format de sauvegarde invalide")
        return GameSaveData.from_dict(raw)

    def save_pgn(self, pgn_text: str, name: str | None = None) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = name or f"partie_{stamp}.pgn"
        if not filename.endswith(".pgn"):
            filename += ".pgn"
        path = self.folder / filename
        path.write_text(pgn_text, encoding="utf-8")
        logger.info("PGN sauvegardé: %s", path)
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
