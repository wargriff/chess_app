"""Client UCI Stockfish — utilisé uniquement dans le thread worker."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import chess
import chess.engine

logger = logging.getLogger("chesspro.uci")


@dataclass
class AnalysisInfo:
    fen: str
    depth: int = 0
    score_cp: int | None = None
    mate: int | None = None
    nodes: int = 0
    nps: int = 0
    time_ms: int = 0
    pv: list[chess.Move] = field(default_factory=list)
    best_move: chess.Move | None = None

    @property
    def eval_text(self) -> str:
        if self.mate is not None:
            sign = "+" if self.mate > 0 else "-"
            return f"{sign}M{abs(self.mate)}"
        if self.score_cp is None:
            return "—"
        return f"{self.score_cp / 100:+.2f}"

    @property
    def white_advantage(self) -> float | None:
        if self.mate is not None:
            return 1.0 if self.mate > 0 else -1.0
        if self.score_cp is None:
            return None
        import math

        return math.tanh(self.score_cp / 400.0)


class UCIClient:
    """SimpleEngine encapsulé. Ne pas appeler depuis le thread UI."""

    def __init__(self) -> None:
        self._engine: chess.engine.SimpleEngine | None = None
        self.binary: Path | None = None
        self.error: str | None = None

    @property
    def available(self) -> bool:
        return self._engine is not None

    def start(self, binary: Path) -> bool:
        self.stop()
        binary = Path(binary)
        if not binary.is_file():
            self.error = f"Fichier introuvable: {binary}"
            logger.error(self.error)
            return False
        try:
            logger.info("UCI popen %s", binary)
            self._engine = chess.engine.SimpleEngine.popen_uci(str(binary))
            # Handshake explicite
            self._engine.configure({})
            self.binary = binary
            self.error = None
            id_name = None
            if isinstance(getattr(self._engine, "id", None), dict):
                id_name = self._engine.id.get("name")
            logger.info("UCI pret: %s (%s)", binary.name, id_name or "Stockfish")
            return True
        except (chess.engine.EngineError, subprocess.SubprocessError, OSError) as exc:
            self.error = str(exc)
            self._engine = None
            self.binary = None
            logger.exception("Echec demarrage UCI")
            return False

    def stop(self) -> None:
        if self._engine is not None:
            try:
                logger.info("UCI quit")
                self._engine.quit()
            except Exception:
                logger.exception("Erreur UCI quit")
            self._engine = None

    def configure_strength(self, elo: int, skill: int | None = None) -> None:
        if self._engine is None:
            return
        if elo >= 1320:
            opts = {
                "UCI_LimitStrength": True,
                "UCI_Elo": min(max(int(elo), 1320), 3190),
            }
        else:
            level = skill if skill is not None else max(0, min(20, int(elo) // 60))
            opts = {"UCI_LimitStrength": False, "Skill Level": int(level)}
        logger.info("UCI configure strength elo=%s opts=%s", elo, opts)
        self._engine.configure(opts)

    def play(
        self,
        board: chess.Board,
        *,
        depth: int | None = None,
        movetime_ms: int | None = None,
        time_s: float | None = None,
    ) -> chess.Move | None:
        if self._engine is None:
            logger.error("play() sans moteur")
            return None
        if board.is_game_over():
            logger.warning("play() ignore: partie terminee (%s)", board.result())
            return None

        if depth is not None:
            limit = chess.engine.Limit(depth=int(depth))
        elif movetime_ms is not None:
            limit = chess.engine.Limit(time=max(0.05, movetime_ms / 1000.0))
        elif time_s is not None:
            limit = chess.engine.Limit(time=max(0.05, float(time_s)))
        else:
            limit = chess.engine.Limit(time=0.8)

        # Log position + historique UCI (startpos moves ...)
        moves_uci = " ".join(m.uci() for m in board.move_stack)
        logger.info(
            "UCI position startpos moves %s | fen=%s | go %s",
            moves_uci or "(none)",
            board.fen(),
            limit,
        )
        result = self._engine.play(board, limit)
        move = result.move
        logger.info("UCI bestmove %s (ponder=%s)", move.uci() if move else None, result.ponder)
        if move is None:
            self.error = "Stockfish n'a pas renvoye de bestmove"
            return None
        if move not in board.legal_moves:
            self.error = f"bestmove illegal: {move.uci()}"
            logger.error(self.error)
            return None
        return move

    def analyse(
        self,
        board: chess.Board,
        *,
        depth: int = 18,
        movetime_ms: int | None = None,
        multipv: int = 1,
    ) -> AnalysisInfo:
        info = AnalysisInfo(fen=board.fen())
        if self._engine is None:
            return info
        limit = (
            chess.engine.Limit(time=movetime_ms / 1000.0)
            if movetime_ms
            else chess.engine.Limit(depth=depth)
        )
        logger.info("UCI analyse fen=%s limit=%s", board.fen(), limit)
        raw = self._engine.analyse(board, limit, multipv=multipv)
        if isinstance(raw, list):
            raw = raw[0] if raw else {}
        score = raw.get("score")
        if score is not None:
            pov = score.white()
            if pov.is_mate():
                info.mate = pov.mate()
            else:
                info.score_cp = pov.score()
        info.depth = int(raw.get("depth") or 0)
        info.nodes = int(raw.get("nodes") or 0)
        info.nps = int(raw.get("nps") or 0)
        info.time_ms = int((raw.get("time") or 0) * 1000)
        pv = list(raw.get("pv") or [])
        info.pv = pv
        info.best_move = pv[0] if pv else None
        logger.info(
            "UCI info score=%s depth=%s best=%s",
            info.eval_text,
            info.depth,
            info.best_move.uci() if info.best_move else None,
        )
        return info
