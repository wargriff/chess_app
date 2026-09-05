"""Tests horloge."""

from src.core.clock import ChessClock


def test_clock_tick_and_flag():
    clock = ChessClock(minutes=0, increment=0)
    assert not clock.enabled
    clock = ChessClock(minutes=1, increment=0)
    clock.start()
    clock.tick(60.0, active_white=True)
    assert clock.flagged_white is True


def test_increment():
    clock = ChessClock(minutes=1, increment=2)
    clock.start()
    before = clock.white_seconds
    clock.on_move(True)
    assert clock.white_seconds == before + 2
