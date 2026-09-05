"""Menus principal et pause — présentation premium épurée."""

from __future__ import annotations

import pygame

from src.ui.layout import UILayout


class MainMenu:
    """Accueil : 4 actions principales seulement."""

    PRIMARY = [
        ("JOUER CONTRE STOCKFISH", "Jouer contre Stockfish"),
        ("JOUER EN LOCAL", "Jouer en local"),
        ("STOCKFISH VS STOCKFISH", "Stockfish vs Stockfish"),
        ("ANALYSE", "Analyse"),
    ]
    SECONDARY = [
        ("PARTIES SAUVEGARDEES", "Sauvegardes"),
        ("QUITTER", "Quitter"),
    ]

    def __init__(self, layout: UILayout) -> None:
        self.layout = layout
        self.options: list[tuple[str, pygame.Rect]] = []
        self.rebuild()

    def rebuild(self) -> None:
        center_x = self.layout.width // 2
        w = min(self.layout.s(420), self.layout.width - self.layout.s(48))
        h = self.layout.s(50)
        gap = self.layout.s(12)
        # Position sous le titre
        y0 = self.layout.height // 2 - self.layout.s(40)
        self.options = []
        for i, (key, _) in enumerate(self.PRIMARY):
            self.options.append((key, pygame.Rect(center_x - w // 2, y0 + i * (h + gap), w, h)))
        y1 = y0 + len(self.PRIMARY) * (h + gap) + self.layout.s(16)
        sw = w // 2 - self.layout.s(6)
        for i, (key, _) in enumerate(self.SECONDARY):
            self.options.append(
                (key, pygame.Rect(center_x - w // 2 + i * (sw + self.layout.s(12)), y1, sw, self.layout.s(40)))
            )

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        for label, rect in self.options:
            if rect.collidepoint(pos):
                return label
        return None

    def get_options(self) -> list[tuple[str, pygame.Rect]]:
        return self.options

    def display_label(self, key: str) -> str:
        for k, lab in self.PRIMARY + self.SECONDARY:
            if k == key:
                return lab
        return key


class PauseMenu:
    def __init__(self, layout: UILayout) -> None:
        self.layout = layout
        self.options: list[tuple[str, pygame.Rect]] = []
        self.rebuild()

    def rebuild(self) -> None:
        center_x = self.layout.width // 2
        w = min(self.layout.s(320), self.layout.width - self.layout.s(48))
        h = self.layout.s(46)
        gap = self.layout.s(10)
        labels = ["Reprendre", "Nouvelle partie", "Sauvegarder", "Charger", "Paramètres", "Menu principal"]
        total = len(labels) * h + (len(labels) - 1) * gap
        y0 = (self.layout.height - total) // 2 + self.layout.s(20)
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
