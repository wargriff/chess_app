"""Tests moteur — detection (sans bloquer si absent)."""

from src.engine.finder import find_stockfish_binary
from src.engine.uci_client import AnalysisInfo


def test_analysis_eval_text_mate():
    info = AnalysisInfo(fen="8/8/8/8/8/8/8/K6k w - - 0 1", mate=3)
    assert "M3" in info.eval_text


def test_analysis_eval_cp():
    info = AnalysisInfo(fen="start", score_cp=125)
    assert info.eval_text == "+1.25"


def test_find_stockfish_does_not_crash():
    # Peut retourner None — ne doit pas lever
    find_stockfish_binary()
