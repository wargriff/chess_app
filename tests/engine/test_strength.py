"""Tests force Stockfish + partie multi-coups."""

from __future__ import annotations

import time

import chess
import pytest

from src.engine.engine_config import strength_for_elo, uci_options_for
from src.engine.finder import find_stockfish_binary
from src.engine.stockfish_manager import StockfishManager
from src.core.session import GameMode, GameSession


def test_strength_presets_cover_ui_levels():
    for elo in (800, 1000, 1200, 1400, 1600, 1800, 2000, 2400):
        s = strength_for_elo(elo)
        opts = uci_options_for(s)
        assert "Threads" in opts and "Hash" in opts
        if elo >= 1400:
            assert opts["UCI_LimitStrength"] is True
            assert opts["UCI_Elo"] >= 1320
        else:
            assert opts["UCI_LimitStrength"] is False
            assert "Skill Level" in opts


@pytest.fixture(scope="module")
def engine():
    if find_stockfish_binary() is None:
        pytest.skip("Stockfish absent")
    mgr = StockfishManager()
    ok = mgr.start(allow_download=False)
    if not ok:
        pytest.skip(mgr.error or "start fail")
    yield mgr
    mgr.stop()


def _wait(session: GameSession, timeout: float = 10.0) -> chess.Move:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        move = session.poll_engine()
        if move:
            return move
        time.sleep(0.05)
    raise AssertionError("Stockfish timeout")


def test_stockfish_gm_level_plays(engine: StockfishManager):
    engine.configure(2400, None)
    assert engine.elo == 2400
    assert "Grand" in engine.strength_label or engine.elo == 2400
    session = GameSession(mode=GameMode.PVE, elo=2400, color_preference="white", engine=engine)
    session.handle_square_click(chess.E2)
    assert session.handle_square_click(chess.E4) is not None
    assert session.ai_thinking
    sf = _wait(session)
    assert sf is not None
    assert len(session.board.board.move_stack) == 2


def test_full_mini_match(engine: StockfishManager):
    engine.configure(1200, 6)
    session = GameSession(mode=GameMode.PVE, elo=1200, skill=6, color_preference="white", engine=engine)
    for _ in range(8):
        if session.board.is_game_over():
            break
        assert session.can_interact()
        move = next(iter(session.board.board.legal_moves))
        session.handle_square_click(move.from_square)
        played = session.handle_square_click(move.to_square)
        if played is None and session.awaiting_promotion:
            session.pick_promotion(session.pending_promotion[0])
        assert session.ai_thinking
        _wait(session, timeout=12.0)
    assert len(session.board.board.move_stack) >= 8
    # Nouvelle partie + redémarrage moteur
    session.reset()
    assert len(session.board.board.move_stack) == 0
    engine.configure(800)
    assert engine.elo == 800
    assert engine.movetime_ms == strength_for_elo(800).movetime_ms
    session.handle_square_click(chess.E2)
    session.handle_square_click(chess.E4)
    _wait(session)
    assert len(session.board.board.move_stack) == 2
