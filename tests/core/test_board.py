"""Tests des regles d'echecs (python-chess via ChessBoard)."""

from __future__ import annotations

import chess

from src.core.board import ChessBoard


def test_starting_legal_moves():
    board = ChessBoard()
    assert len(list(board.board.legal_moves)) == 20


def test_scholars_mate_checkmate():
    board = ChessBoard()
    for san in ["e4", "e5", "Qh5", "Nc6", "Bc4", "Nf6", "Qxf7"]:
        board.push(board.board.parse_san(san))
    assert board.is_checkmate()


def test_castling_kingside():
    board = ChessBoard()
    board.set_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    move = chess.Move.from_uci("e1g1")
    assert board.is_legal(move)
    board.push(move)
    assert board.piece_at(chess.G1).piece_type == chess.KING


def test_en_passant():
    board = ChessBoard()
    for san in ["e4", "a6", "e5", "d5"]:
        board.push(board.board.parse_san(san))
    move = board.board.parse_san("exd6")
    assert board.is_legal(move)


def test_stalemate():
    board = ChessBoard()
    board.set_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert board.is_stalemate()


def test_insufficient_material():
    board = ChessBoard()
    board.set_fen("8/8/8/4k3/8/8/8/4K3 w - - 0 1")
    assert board.board.is_insufficient_material()


def test_fen_roundtrip():
    board = ChessBoard()
    fen = board.fen()
    other = ChessBoard(fen)
    assert other.fen() == fen


def test_pgn_export_contains_moves():
    board = ChessBoard()
    board.push(board.board.parse_san("e4"))
    board.push(board.board.parse_san("e5"))
    pgn = board.export_pgn()
    assert "e4" in pgn and "e5" in pgn


def test_undo():
    board = ChessBoard()
    board.push(board.board.parse_san("e4"))
    assert board.undo()
    assert len(board.board.move_stack) == 0
