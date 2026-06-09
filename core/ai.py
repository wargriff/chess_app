from __future__ import annotations

import chess

from config.settings import AI_DEPTH
from core.stockfish_engine import StockfishEngine


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


def order_moves(board: chess.Board, moves: list[chess.Move]) -> list[chess.Move]:
    def key(move: chess.Move) -> int:
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                return PIECE_VALUES[victim.piece_type] - PIECE_VALUES[attacker.piece_type]
            return 100
        if board.gives_check(move):
            return 50
        return 0

    return sorted(moves, key=key, reverse=True)


def minimax(board: chess.Board, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
    if depth == 0 or board.is_game_over():
        return evaluate(board)

    moves = order_moves(board, list(board.legal_moves))

    if maximizing:
        best = -999_999
        for move in moves:
            board.push(move)
            best = max(best, minimax(board, depth - 1, alpha, beta, False))
            board.pop()
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best

    best = 999_999
    for move in moves:
        board.push(move)
        best = min(best, minimax(board, depth - 1, alpha, beta, True))
        board.pop()
        beta = min(beta, best)
        if beta <= alpha:
            break
    return best


class MinimaxAI:
    def __init__(self, depth: int = AI_DEPTH) -> None:
        self.depth = depth

    def choose_move(self, board: chess.Board) -> chess.Move | None:
        if board.is_game_over():
            return None

        is_white = board.turn == chess.WHITE
        best_move: chess.Move | None = None
        best_score = -999_999 if is_white else 999_999

        for move in order_moves(board, list(board.legal_moves)):
            board.push(move)
            score = minimax(board, self.depth - 1, -999_999, 999_999, not is_white)
            board.pop()

            if is_white and score > best_score:
                best_score = score
                best_move = move
            elif not is_white and score < best_score:
                best_score = score
                best_move = move

        return best_move


class ChessAI:
    """IA Stockfish avec repli minimax si le moteur est absent."""

    def __init__(self, elo: int = 1200, skill: int | None = 8) -> None:
        self.elo = elo
        self.skill = skill
        self.stockfish = StockfishEngine(elo=elo, skill=skill)
        self.fallback = MinimaxAI()
        self.engine_label = self.stockfish.engine_label if self.stockfish.available else "Minimax (fallback)"

    def set_elo(self, elo: int, skill: int | None = None) -> None:
        self.elo = elo
        self.skill = skill
        self.stockfish.set_elo(elo, skill)
        self.engine_label = self.stockfish.engine_label if self.stockfish.available else "Minimax (fallback)"

    def choose_move(self, board: chess.Board) -> chess.Move | None:
        if board.is_game_over():
            return None
        if self.stockfish.available:
            move = self.stockfish.choose_move(board)
            if move is not None:
                return move
        return self.fallback.choose_move(board)

    def close(self) -> None:
        self.stockfish.close()
