from __future__ import annotations

import pygame

from config.settings import WINDOW_WIDTH


class MainMenu:
    def __init__(self) -> None:
        self.options = self._build_options()

    def _build_options(self) -> list[tuple[str, pygame.Rect]]:
        center_x = WINDOW_WIDTH // 2
        return [
            ("Joueur vs Joueur", pygame.Rect(center_x - 180, 260, 360, 54)),
            ("Joueur vs IA (Stockfish)", pygame.Rect(center_x - 180, 330, 360, 54)),
            ("Quitter", pygame.Rect(center_x - 180, 400, 360, 54)),
        ]

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        for label, rect in self.options:
            if rect.collidepoint(pos):
                return label
        return None

    def get_options(self) -> list[tuple[str, pygame.Rect]]:
        return self.options


class PauseMenu:
    def __init__(self) -> None:
        center_x = WINDOW_WIDTH // 2
        self.options = [
            ("Reprendre", pygame.Rect(center_x - 150, 300, 300, 50)),
            ("Nouvelle partie", pygame.Rect(center_x - 150, 360, 300, 50)),
            ("Menu principal", pygame.Rect(center_x - 150, 420, 300, 50)),
        ]

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        for label, rect in self.options:
            if rect.collidepoint(pos):
                return label
        return None

    def get_options(self) -> list[tuple[str, pygame.Rect]]:
        return self.options
