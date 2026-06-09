from __future__ import annotations

import threading

import chess

from core.ai import ChessAI
from core.board import ChessBoard


class GameSession:
    """Gère sélection, coups, IA Stockfish et annulation."""

    def __init__(self, vs_ai: bool = False, elo: int = 1200, skill: int | None = 8) -> None:
        self.board = ChessBoard()
        self.vs_ai = vs_ai
        self.elo = elo
        self.skill = skill
        self.ai = ChessAI(elo=elo, skill=skill) if vs_ai else None
        self.selected: chess.Square | None = None
        self.legal_targets: list[chess.Square] = []
        self.last_move: chess.Move | None = None
        self.message = ""
        self.ai_thinking = False
        self._ai_thread: threading.Thread | None = None

    @property
    def engine_label(self) -> str:
        if self.ai is None:
            return "Humain vs Humain"
        return self.ai.engine_label

    def reset(self, vs_ai: bool | None = None, elo: int | None = None, skill: int | None = None) -> None:
        if self.ai is not None:
            self.ai.close()

        if vs_ai is not None:
            self.vs_ai = vs_ai
        if elo is not None:
            self.elo = elo
        if skill is not None:
            self.skill = skill

        if self.vs_ai:
            self.ai = ChessAI(elo=self.elo, skill=self.skill)
        else:
            self.ai = None

        self.board.reset()
        self.clear_selection()
        self.last_move = None
        self.message = ""
        self.ai_thinking = False
        self._ai_thread = None

    def close(self) -> None:
        if self.ai is not None:
            self.ai.close()
            self.ai = None

    def clear_selection(self) -> None:
        self.selected = None
        self.legal_targets = []

    def square_from_pixel(self, row: int, col: int) -> chess.Square:
        return chess.square(col, 7 - row)

    def can_interact(self) -> bool:
        return not self.ai_thinking and not self.board.is_game_over()

    def handle_square_click(self, square: chess.Square) -> bool:
        if not self.can_interact():
            return False

        if self.vs_ai and self.board.turn() == chess.BLACK:
            return False

        if self.selected is None:
            moves = self.board.legal_moves_from(square)
            if not moves:
                return False
            self.selected = square
            self.legal_targets = [move.to_square for move in moves]
            return False

        if square == self.selected:
            self.clear_selection()
            return False

        candidate_moves = [
            move for move in self.board.legal_moves_from(self.selected) if move.to_square == square
        ]
        if not candidate_moves:
            moves = self.board.legal_moves_from(square)
            if moves:
                self.selected = square
                self.legal_targets = [candidate.to_square for candidate in moves]
            else:
                self.clear_selection()
            return False

        chosen = candidate_moves[0]
        if len(candidate_moves) > 1:
            chosen = next(
                (move for move in candidate_moves if move.promotion == chess.QUEEN),
                candidate_moves[0],
            )

        self.board.push(chosen)
        self.last_move = chosen
        self.clear_selection()
        self.message = self.board.status_text()

        if self.vs_ai and not self.board.is_game_over():
            self.start_ai_move()
        return True

    def start_ai_move(self) -> None:
        if self.ai is None or self.board.is_game_over() or self.ai_thinking:
            return
        if self.board.turn() != chess.BLACK:
            return

        self.ai_thinking = True
        self.message = "L'IA réfléchit..."

        def worker() -> None:
            move = self.ai.choose_move(self.board.board) if self.ai else None
            if move is not None and not self.board.is_game_over():
                self.board.push(move)
                self.last_move = move
                self.message = self.board.status_text()
            self.ai_thinking = False

        self._ai_thread = threading.Thread(target=worker, daemon=True)
        self._ai_thread.start()

    def undo_move(self) -> None:
        if self.ai_thinking:
            return
        if self.vs_ai:
            self.board.undo()
        self.board.undo()
        self.clear_selection()
        self.message = self.board.status_text()

    def set_elo_level(self, elo: int, skill: int | None) -> None:
        if not self.vs_ai or self.ai is None:
            return
        self.elo = elo
        self.skill = skill
        self.ai.set_elo(elo, skill)
        self.message = f"Niveau IA : {elo} ELO"
