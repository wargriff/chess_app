"""Compat Stockfish."""

from src.engine.finder import download_stockfish, find_stockfish_binary, resolve_stockfish
from src.engine.stockfish_manager import StockfishManager as StockfishEngine

__all__ = ["StockfishEngine", "download_stockfish", "find_stockfish_binary", "resolve_stockfish"]
