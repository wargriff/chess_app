from __future__ import annotations

import pygame

from config.settings import (
    BOARD_THEMES,
    DEFAULT_BOARD_THEME,
    DEFAULT_ELO,
    ELO_LEVELS,
    SIDEBAR_INNER,
    SIDEBAR_X,
    SIDEBAR_Y,
)


class GameSidebar:
    """Panneau latéral : sélection plateau et ELO en jeu."""

    def __init__(self) -> None:
        self.board_theme = DEFAULT_BOARD_THEME
        self.elo = DEFAULT_ELO
        self.skill: int | None = 8
        self.vs_ai = False
        self.board_buttons: dict[str, pygame.Rect] = {}
        self.elo_buttons: dict[int, pygame.Rect] = {}
        self._rebuild()

    def _rebuild(self) -> None:
        self.board_buttons.clear()
        self.elo_buttons.clear()

        x = SIDEBAR_X + 12
        y = SIDEBAR_Y + 92
        cols = 2
        btn_w = (SIDEBAR_INNER - 12) // cols
        btn_h = 42
        gap = 8

        for index, theme in enumerate(BOARD_THEMES):
            col = index % cols
            row = index // cols
            rect = pygame.Rect(
                x + col * (btn_w + gap),
                y + row * (btn_h + gap),
                btn_w,
                btn_h,
            )
            self.board_buttons[theme["id"]] = rect

        elo_y = y + ((len(BOARD_THEMES) + 1) // cols) * (btn_h + gap) + 56
        for index, level in enumerate(ELO_LEVELS):
            rect = pygame.Rect(x, elo_y + index * 34, SIDEBAR_INNER, 30)
            self.elo_buttons[level["elo"]] = rect

    def set_vs_ai(self, vs_ai: bool) -> None:
        self.vs_ai = vs_ai

    def sync_from_session(self, theme_id: str, elo: int, skill: int | None, vs_ai: bool) -> None:
        self.board_theme = theme_id
        self.elo = elo
        self.skill = skill
        self.vs_ai = vs_ai

    def handle_click(self, pos: tuple[int, int]) -> tuple[str, object] | None:
        for theme_id, rect in self.board_buttons.items():
            if rect.collidepoint(pos):
                self.board_theme = theme_id
                return ("board", theme_id)

        if self.vs_ai:
            for elo, rect in self.elo_buttons.items():
                if rect.collidepoint(pos):
                    self.elo = elo
                    level = next(item for item in ELO_LEVELS if item["elo"] == elo)
                    self.skill = level["skill"]
                    return ("elo", level)
        return None

    def get_board_buttons(self) -> dict[str, pygame.Rect]:
        return self.board_buttons

    def get_elo_buttons(self) -> dict[int, pygame.Rect]:
        return self.elo_buttons if self.vs_ai else {}

    def panel_rect(self) -> pygame.Rect:
        from config.settings import SIDEBAR_WIDTH, WINDOW_HEIGHT

        return pygame.Rect(SIDEBAR_X, SIDEBAR_Y, SIDEBAR_WIDTH, WINDOW_HEIGHT - SIDEBAR_Y - 120)

    def contains(self, pos: tuple[int, int]) -> bool:
        return self.panel_rect().collidepoint(pos)
