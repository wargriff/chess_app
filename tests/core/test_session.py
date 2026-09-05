"""Tests navigation historique / undo."""

import chess

from src.core.session import GameMode, GameSession


def test_goto_ply():
    s = GameSession(mode=GameMode.PVP)
    s.handle_square_click(chess.E2)
    s.handle_square_click(chess.E4)
    s.handle_square_click(chess.E7)
    s.handle_square_click(chess.E5)
    assert len(s.board.board.move_stack) == 2
    s.goto_ply(1)
    assert len(s.board.board.move_stack) == 1
    assert s.board.board.peek().uci() == "e2e4"
    s.goto_ply(0)
    assert len(s.board.board.move_stack) == 0
