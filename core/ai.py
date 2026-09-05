"""Compat AI — utilise StockfishManager via session; minimax conserve pour tests."""

from __future__ import annotations

import chess

from src.engine.stockfish_manager import StockfishManager
from src.models.settings import AI_DEPTH

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20_000,
}


def evaluate(board: chess.Board) -> int:
    if board.is_checkmate():
        return -50_000 if board.turn else 50_000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    score = 0
    for _, piece in board.piece_map().items():
        value = PIECE_VALUES[piece.piece_type]
        score += value if piece.color == chess.WHITE else -value
    return score


class MinimaxAI:
    def __init__(self, depth: int = AI_DEPTH) -> None:
        self.depth = depth

    def choose_move(self, board: chess.Board) -> chess.Move | None:
        moves = list(board.legal_moves)
        return moves[0] if moves else None


class ChessAI:
    def __init__(self, elo: int = 1200, skill: int | None = 8) -> None:
        self.elo = elo
        self.skill = skill
        self.engine = StockfishManager()
        self.engine.configure(elo, skill)
        self.engine.start(allow_download=False)
        self.fallback = MinimaxAI()
        self.engine_label = self.engine.engine_label

    def set_elo(self, elo: int, skill: int | None = None) -> None:
        self.elo = elo
        self.skill = skill
        self.engine.configure(elo, skill)

    def choose_move(self, board: chess.Board) -> chess.Move | None:
        if self.engine.available:
            # synchrone via client direct pour compat
            return self.engine._client.play(board, movetime_ms=400)
        return self.fallback.choose_move(board)

    def close(self) -> None:
        self.engine.stop()
