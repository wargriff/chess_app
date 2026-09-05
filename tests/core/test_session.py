"""Tests navigation historique / undo / redo / horloge."""

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


def test_undo_restores_clock_and_invalidates_redo_after_new_move():
    s = GameSession(mode=GameMode.PVP, time_minutes=5, time_increment=3)
    s.clock.white_seconds = 290.0
    s.clock.black_seconds = 300.0
    s.handle_square_click(chess.E2)
    s.handle_square_click(chess.E4)
    assert abs(s.clock.white_seconds - 293.0) < 0.01
    s.undo_move()
    assert len(s.board.board.move_stack) == 0
    assert abs(s.clock.white_seconds - 290.0) < 0.01
    assert s.can_redo()
    s.redo_move()
    assert len(s.board.board.move_stack) == 1
    assert abs(s.clock.white_seconds - 293.0) < 0.01
    s.undo_move()
    s.handle_square_click(chess.D2)
    s.handle_square_click(chess.D4)
    assert not s.can_redo()
