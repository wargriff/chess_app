from __future__ import annotations

import chess


class ChessBoard:
    """Encapsule python-chess pour la logique de partie."""

    def __init__(self) -> None:
        self.board = chess.Board()
        self.history: list[chess.Move] = []

    def reset(self) -> None:
        self.board.reset()
        self.history.clear()

    def piece_at(self, square: chess.Square) -> chess.Piece | None:
        return self.board.piece_at(square)

    def legal_moves_from(self, square: chess.Square) -> list[chess.Move]:
        if self.board.is_game_over():
            return []

        piece = self.board.piece_at(square)
        if piece is None or piece.color != self.board.turn:
            return []

        return [move for move in self.board.legal_moves if move.from_square == square]

    def is_legal(self, move: chess.Move) -> bool:
        return move in self.board.legal_moves

    def push(self, move: chess.Move) -> None:
        self.board.push(move)
        self.history.append(move)

    def undo(self) -> bool:
        if not self.history:
            return False
        self.board.pop()
        self.history.pop()
        return True

    def turn(self) -> bool:
        return self.board.turn

    def is_check(self) -> bool:
        return self.board.is_check()

    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    def result_text(self) -> str:
        if self.board.is_checkmate():
            winner = "Noirs" if self.board.turn else "Blancs"
            return f"Échec et mat — {winner} gagnent"
        if self.board.is_stalemate():
            return "Pat — match nul"
        if self.board.is_insufficient_material():
            return "Matériel insuffisant — match nul"
        if self.board.is_seventyfive_moves():
            return "Règle des 75 coups — match nul"
        if self.board.is_fivefold_repetition():
            return "Répétition — match nul"
        return "Partie terminée"

    def status_text(self) -> str:
        if self.is_game_over():
            return self.result_text()
        side = "Blancs" if self.board.turn else "Noirs"
        suffix = " (échec)" if self.is_check() else ""
        return f"Trait aux {side}{suffix}"
