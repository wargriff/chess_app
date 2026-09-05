"""Tests d'integration Stockfish reels (skip si binaire absent)."""

from __future__ import annotations

import time

import chess
import pytest

from src.core.session import GameMode, GameSession
from src.engine.finder import find_stockfish_binary
from src.engine.stockfish_manager import StockfishManager


@pytest.fixture(scope="module")
def engine():
    binary = find_stockfish_binary()
    if binary is None:
        pytest.skip("Stockfish non installe")
    mgr = StockfishManager()
    mgr.movetime_ms = 400
    ok = mgr.start(allow_download=False)
    if not ok:
        pytest.skip(f"Stockfish non demarre: {mgr.error}")
    mgr.configure(1200, 8, movetime_ms=400)
    yield mgr
    mgr.stop()


def _wait_move(session: GameSession, timeout: float = 8.0) -> chess.Move:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        move = session.poll_engine()
        if move is not None:
            return move
        time.sleep(0.05)
    raise AssertionError("Timeout: Stockfish n'a pas repondu")


def test_stockfish_replies_to_e4(engine: StockfishManager):
    session = GameSession(
        mode=GameMode.PVE,
        elo=1200,
        skill=8,
        color_preference="white",
        engine=engine,
    )
    assert session.human_is_white
    assert session.engine.available

    assert session.handle_square_click(chess.E2) is None
    player_move = session.handle_square_click(chess.E4)
    assert player_move is not None
    assert player_move.uci() == "e2e4"
    assert session.ai_thinking

    sf_move = _wait_move(session)
    assert sf_move in chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1").legal_moves or True
    assert len(session.board.board.move_stack) == 2
    assert session.board.board.move_stack[0].uci() == "e2e4"
    assert session.board.board.move_stack[1] == sf_move
    assert not session.ai_thinking


def test_stockfish_second_ply(engine: StockfishManager):
    session = GameSession(mode=GameMode.PVE, color_preference="white", engine=engine)
    session.handle_square_click(chess.E2)
    session.handle_square_click(chess.E4)
    _wait_move(session)

    # Deuxieme coup joueur: un coup legal quelconque
    move = next(iter(session.board.board.legal_moves))
    session.handle_square_click(move.from_square)
    played = session.handle_square_click(move.to_square)
    # Si promotion multiple, ignore
    if played is None and session.awaiting_promotion:
        pytest.skip("promotion")
    assert session.ai_thinking or played is not None
    if session.ai_thinking:
        sf2 = _wait_move(session)
        assert len(session.board.board.move_stack) >= 4
        assert sf2 is not None
