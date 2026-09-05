"""Ecran de chargement au demarrage (barre de progression)."""

from __future__ import annotations

import threading
from collections.abc import Callable

import pygame

from src.engine.finder import download_stockfish, find_stockfish_binary
from src.models.settings import BOARD_THEMES, DEFAULT_PIECE_SET, PIECE_SETS
from src.ui.renderer import ChessRenderer


class BootstrapLoader:
    def __init__(self, renderer: ChessRenderer) -> None:
        self.renderer = renderer
        self.message = "Demarrage..."
        self.display_progress = 0.0
        self.complete = False
        self._tasks: list[tuple[str, Callable[[], None]]] = []
        self._task_index = 0
        self._target_progress = 0.0
        self._stockfish_thread: threading.Thread | None = None
        self._stockfish_result: str | None = None
        self._build_tasks()

    def _build_tasks(self) -> None:
        self._tasks.append(("Initialisation Pygame...", lambda: pygame.event.pump()))

        preload_pieces = {DEFAULT_PIECE_SET, "cburnett", "merida", "california"}
        for piece_set in PIECE_SETS:
            if piece_set["id"] not in preload_pieces:
                continue
            set_id = piece_set["id"]
            label = piece_set["label"]
            self._tasks.append(
                (
                    f"Pieces : {label}...",
                    lambda sid=set_id: self.renderer.assets.preload_piece_set(sid),
                )
            )

        for theme in BOARD_THEMES:
            theme_id = theme["id"]
            label = theme["label"]
            self._tasks.append(
                (
                    f"Plateau : {label}...",
                    lambda tid=theme_id: self.renderer.assets.preload_theme(tid),
                )
            )

        self._tasks.append(("Verification Stockfish...", self._start_stockfish))
        self._tasks.append(("Finalisation...", lambda: pygame.event.pump()))

    def _start_stockfish(self) -> None:
        if find_stockfish_binary():
            self._stockfish_result = "Stockfish detecte"
            return

        self.message = "Telechargement Stockfish..."
        self._stockfish_result = None

        def worker() -> None:
            downloaded = download_stockfish()
            self._stockfish_result = "Stockfish pret" if downloaded else "Mode minimax (sans Stockfish)"

        self._stockfish_thread = threading.Thread(target=worker, daemon=True)
        self._stockfish_thread.start()

    def _stockfish_pending(self) -> bool:
        return self._stockfish_thread is not None and self._stockfish_thread.is_alive()

    def update(self, dt: float) -> None:
        if self.complete:
            return

        if self._task_index < len(self._tasks):
            message, action = self._tasks[self._task_index]
            self.message = self._stockfish_result or message

            if self._stockfish_pending():
                self._target_progress = min(0.97, (self._task_index + 0.7) / len(self._tasks))
            elif self._stockfish_thread is not None:
                self._task_index += 1
                self._target_progress = self._task_index / len(self._tasks)
            else:
                action()
                pygame.event.pump()
                if self._stockfish_thread is None:
                    self._task_index += 1
                self._target_progress = self._task_index / len(self._tasks)

        self.display_progress += (self._target_progress - self.display_progress) * min(1.0, dt * 10.0)

        if self._task_index >= len(self._tasks) and not self._stockfish_pending():
            if abs(self._target_progress - self.display_progress) < 0.01:
                self.complete = True
                self.display_progress = 1.0
                self.message = "Bienvenue !"


def run_bootstrap(screen: pygame.Surface, renderer: ChessRenderer) -> bool:
    loader = BootstrapLoader(renderer)
    clock = pygame.time.Clock()

    while not loader.complete:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        loader.update(dt)
        renderer.draw_loading_screen(loader.message, loader.display_progress)
        pygame.display.flip()

    renderer.draw_loading_screen(loader.message, 1.0)
    pygame.display.flip()
    pygame.time.wait(350)
    return True
