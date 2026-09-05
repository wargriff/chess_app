"""Tests sauvegarde PGN/FEN."""

from pathlib import Path

from src.core.board import ChessBoard
from src.services.save_manager import SaveManager


def test_save_and_load_fen(tmp_path: Path):
    mgr = SaveManager(tmp_path)
    board = ChessBoard()
    board.push(board.board.parse_san("e4"))
    path = mgr.save_fen(board.fen(), "t.fen")
    fen = mgr.load_fen(path)
    assert "e2e4" in fen or fen.startswith("rnbqkbnr/pppppppp/8/8/4P3")


def test_save_pgn(tmp_path: Path):
    mgr = SaveManager(tmp_path)
    board = ChessBoard()
    board.push(board.board.parse_san("d4"))
    path = mgr.save_pgn(board.export_pgn(), "t.pgn")
    assert path.is_file()
    loaded, _ = mgr.load_pgn(path)
    assert len(loaded.board.move_stack) == 1
