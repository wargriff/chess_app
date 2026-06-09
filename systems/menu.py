from __future__ import annotations

import pygame

from config.settings import ELO_LEVELS, WINDOW_WIDTH


class MainMenu:
    def __init__(self) -> None:
        self.options = self._build_options()

    def _build_options(self) -> list[tuple[str, pygame.Rect]]:
        center_x = WINDOW_WIDTH // 2
        return [
            ("Joueur vs Joueur", pygame.Rect(center_x - 180, 240, 360, 54)),
            ("Joueur vs IA (Stockfish)", pygame.Rect(center_x - 180, 310, 360, 54)),
            ("Quitter", pygame.Rect(center_x - 180, 380, 360, 54)),
        ]

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        for label, rect in self.options:
            if rect.collidepoint(pos):
                return label
        return None

    def get_options(self) -> list[tuple[str, pygame.Rect]]:
        return self.options


class EloMenu:
    def __init__(self) -> None:
        self.options = self._build_options()

    def _build_options(self) -> list[tuple[str, pygame.Rect]]:
        center_x = WINDOW_WIDTH // 2
        options: list[tuple[str, pygame.Rect]] = []
        start_y = 210
        width = 360
        height = 48
        gap = 12

        for index, level in enumerate(ELO_LEVELS):
            label = f"{level['label']} — {level['elo']} ELO"
            rect = pygame.Rect(center_x - width // 2, start_y + index * (height + gap), width, height)
            options.append((label, rect))
        options.append(("Retour", pygame.Rect(center_x - width // 2, start_y + len(ELO_LEVELS) * (height + gap) + 16, width, height)))
        return options

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        for label, rect in self.options:
            if rect.collidepoint(pos):
                return label
        return None

    def get_level_from_label(self, label: str) -> dict | None:
        for level in ELO_LEVELS:
            expected = f"{level['label']} — {level['elo']} ELO"
            if label == expected:
                return level
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
