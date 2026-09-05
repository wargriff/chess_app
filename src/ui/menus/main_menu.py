"""Menu principal epure Chess Pro."""

from __future__ import annotations

import pygame

from src.ui.layout import UILayout


class MainMenu:
    LABELS = [
        "JOUER CONTRE STOCKFISH",
        "JOUER EN LOCAL",
        "STOCKFISH VS STOCKFISH",
        "ANALYSE",
        "PARTIES SAUVEGARDEES",
        "QUITTER",
    ]

    def __init__(self, layout: UILayout) -> None:
        self.layout = layout
        self.options: list[tuple[str, pygame.Rect]] = []
        self.rebuild()

    def rebuild(self) -> None:
        center_x = self.layout.width // 2
        w = self.layout.s(420)
        h = self.layout.s(48)
        gap = self.layout.s(10)
        block_h = len(self.LABELS) * h + (len(self.LABELS) - 1) * gap
        y0 = max(self.layout.s(200), (self.layout.height - block_h) // 2)
        self.options = [
            (label, pygame.Rect(center_x - w // 2, y0 + i * (h + gap), w, h))
            for i, label in enumerate(self.LABELS)
        ]

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        for label, rect in self.options:
            if rect.collidepoint(pos):
                return label
        return None

    def get_options(self) -> list[tuple[str, pygame.Rect]]:
        return self.options


class PauseMenu:
    def __init__(self, layout: UILayout) -> None:
        self.layout = layout
        self.options: list[tuple[str, pygame.Rect]] = []
        self.rebuild()

    def rebuild(self) -> None:
        center_x = self.layout.width // 2
        w = self.layout.s(300)
        h = self.layout.s(48)
        gap = self.layout.s(12)
        y0 = self.layout.height // 2 - self.layout.s(80)
        labels = ["Reprendre", "Nouvelle partie", "Sauver PGN", "Menu principal"]
        self.options = [
            (label, pygame.Rect(center_x - w // 2, y0 + i * (h + gap), w, h))
            for i, label in enumerate(labels)
        ]

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        for label, rect in self.options:
            if rect.collidepoint(pos):
                return label
        return None

    def get_options(self) -> list[tuple[str, pygame.Rect]]:
        return self.options
