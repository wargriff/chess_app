"""Plateau d'échecs — wrapper python-chess (règles séparées de l'UI)."""

from __future__ import annotations

import chess
import chess.pgn
from io import StringIO


class ChessBoard:
    """Encapsule python-chess pour la logique de partie."""

    def __init__(self, fen: str | None = None) -> None:
        self.board = chess.Board(fen) if fen else chess.Board()
        self.history: list[chess.Move] = list(self.board.move_stack)

    def reset(self) -> None:
        self.board.reset()
        self.history.clear()

    def set_fen(self, fen: str) -> None:
        self.board.set_fen(fen)
        self.history = list(self.board.move_stack)

    def fen(self) -> str:
        return self.board.fen()

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
        if not self.board.move_stack:
            return False
        self.board.pop()
        if self.history:
            self.history.pop()
        return True

    def turn(self) -> bool:
        return self.board.turn

    def is_check(self) -> bool:
        return self.board.is_check()

    def is_checkmate(self) -> bool:
        return self.board.is_checkmate()

    def is_stalemate(self) -> bool:
        return self.board.is_stalemate()

    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    def can_claim_draw(self) -> bool:
        return self.board.can_claim_draw()

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
        if self.board.can_claim_fifty_moves():
            return "Règle des 50 coups — nulle possible"
        if self.board.can_claim_threefold_repetition():
            return "Répétition triple — nulle possible"
        return "Partie terminée"

    def status_text(self) -> str:
        if self.is_game_over():
            return self.result_text()
        side = "Blancs" if self.board.turn else "Noirs"
        suffix = " (échec)" if self.is_check() else ""
        return f"Trait aux {side}{suffix}"

    def san_history(self) -> list[str]:
        board = self.board.copy()
        # Rebuild from start for SAN
        moves = list(board.move_stack)
        temp = chess.Board()
        sans: list[str] = []
        for move in moves:
            sans.append(temp.san(move))
            temp.push(move)
        return sans

    def export_pgn(
        self,
        *,
        white: str = "White",
        black: str = "Black",
        result: str = "*",
        event: str = "Chess Pro D4",
    ) -> str:
        game = chess.pgn.Game()
        game.headers["Event"] = event
        game.headers["White"] = white
        game.headers["Black"] = black
        game.headers["Result"] = result if result != "*" else self.board.result(claim_draw=True)
        node = game
        temp = chess.Board()
        for move in self.board.move_stack:
            node = node.add_variation(move)
            temp.push(move)
        exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=False)
        return game.accept(exporter)

    @staticmethod
    def load_pgn(text: str) -> tuple[ChessBoard, chess.pgn.Game]:
        game = chess.pgn.read_game(StringIO(text))
        if game is None:
            raise ValueError("PGN invalide")
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
        wrapper = ChessBoard()
        wrapper.board = board
        wrapper.history = list(board.move_stack)
        return wrapper, game
