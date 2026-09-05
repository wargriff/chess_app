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
    multipv_lines: list[dict] = field(default_factory=list)

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
        from src.engine.engine_config import strength_for_elo, uci_options_for

        strength = strength_for_elo(elo)
        # skill override uniquement pour niveaux non limit-strength
        if not strength.limit_strength and skill is not None:
            from dataclasses import replace

            strength = replace(strength, skill=skill)
        opts = uci_options_for(strength)
        logger.info("UCI configure strength elo=%s label=%s opts=%s", elo, strength.label, opts)
        self._engine.configure(opts)
        # isready pour valider
        self._engine.ping()

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
        multipv = max(1, min(int(multipv), 5))
        limit = (
            chess.engine.Limit(time=movetime_ms / 1000.0)
            if movetime_ms
            else chess.engine.Limit(depth=depth)
        )
        logger.info("UCI analyse fen=%s limit=%s multipv=%s", board.fen(), limit, multipv)
        try:
            self._engine.configure({"MultiPV": multipv})
        except Exception:
            pass
        raw = self._engine.analyse(board, limit, multipv=multipv)
        rows = raw if isinstance(raw, list) else [raw]
        lines: list[dict] = []
        for i, row in enumerate(rows):
            if not row:
                continue
            score = row.get("score")
            mate = None
            cp = None
            if score is not None:
                pov = score.white()
                if pov.is_mate():
                    mate = pov.mate()
                else:
                    cp = pov.score()
            pv_moves = list(row.get("pv") or [])
            eval_txt = f"{'+' if (mate or 0) > 0 else '-'}M{abs(mate)}" if mate is not None else (
                f"{(cp or 0) / 100:+.2f}" if cp is not None else "—"
            )
            lines.append(
                {
                    "multipv": i + 1,
                    "eval": eval_txt,
                    "score_cp": cp,
                    "mate": mate,
                    "depth": int(row.get("depth") or 0),
                    "pv_uci": [m.uci() for m in pv_moves],
                    "best_move": pv_moves[0].uci() if pv_moves else None,
                }
            )
        info.multipv_lines = lines
        primary = rows[0] if rows else {}
        score = primary.get("score")
        if score is not None:
            pov = score.white()
            if pov.is_mate():
                info.mate = pov.mate()
            else:
                info.score_cp = pov.score()
        info.depth = int(primary.get("depth") or 0)
        info.nodes = int(primary.get("nodes") or 0)
        info.nps = int(primary.get("nps") or 0)
        info.time_ms = int((primary.get("time") or 0) * 1000)
        pv = list(primary.get("pv") or [])
        info.pv = pv
        info.best_move = pv[0] if pv else None
        logger.info(
            "UCI info score=%s depth=%s best=%s lines=%s",
            info.eval_text,
            info.depth,
            info.best_move.uci() if info.best_move else None,
            len(lines),
        )
        return info
