"""Tests sauvegarde JSON / PGN / FEN."""

from pathlib import Path

import chess

from src.core.board import ChessBoard
from src.core.session import GameMode, GameSession
from src.services.save_manager import GameSaveData, SaveManager


def test_save_and_load_fen(tmp_path: Path):
    mgr = SaveManager(tmp_path)
    board = ChessBoard()
    board.push(board.board.parse_san("e4"))
    path = mgr.save_fen(board.fen(), "t.fen")
    fen = mgr.load_fen(path)
    assert fen.startswith("rnbqkbnr/pppppppp/8/8/4P3")


def test_save_pgn(tmp_path: Path):
    mgr = SaveManager(tmp_path)
    board = ChessBoard()
    board.push(board.board.parse_san("d4"))
    path = mgr.save_pgn(board.export_pgn(), "t.pgn")
    assert path.is_file()
    loaded, _ = mgr.load_pgn(path)
    assert len(loaded.board.move_stack) == 1


def test_json_save_and_restore(tmp_path: Path):
    mgr = SaveManager(tmp_path)
    session = GameSession(mode=GameMode.PVP, time_minutes=5, time_increment=2, player_name="Alice")
    session.handle_square_click(chess.E2)
    session.handle_square_click(chess.E4)
    session.handle_square_click(chess.E7)
    session.handle_square_click(chess.E5)
    white_before = session.clock.white_seconds
    black_before = session.clock.black_seconds

    data = session.to_save_data()
    path = mgr.save_game(data, "match.json")
    assert path.is_file()

    loaded = mgr.load_game(path)
    assert loaded.mode == "PVP"
    assert loaded.moves == ["e2e4", "e7e5"]
    assert abs(loaded.white_seconds - white_before) < 0.01

    restored = GameSession(mode=GameMode.PVP, time_minutes=5, time_increment=2, player_name="Alice")
    restored.restore_from_save(loaded, resume_engine=False)
    assert [m.uci() for m in restored.board.board.move_stack] == ["e2e4", "e7e5"]
    assert abs(restored.clock.white_seconds - white_before) < 0.5
    assert abs(restored.clock.black_seconds - black_before) < 0.5


def test_list_empty_saves(tmp_path: Path):
    mgr = SaveManager(tmp_path)
    assert mgr.list_json_saves() == []
