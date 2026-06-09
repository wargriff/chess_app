from __future__ import annotations

import pygame

from config.settings import (
    BOARD_THEMES,
    DEFAULT_BOARD_THEME,
    DEFAULT_ELO,
    DEFAULT_PIECE_SET,
    ELO_LEVELS,
    PIECE_SETS,
    SIDEBAR_INNER,
    SIDEBAR_X,
    SIDEBAR_Y,
)


class GameSidebar:
    """Panneau latéral : styles de pièces, plateau et ELO."""

    PIECE_CARD_H = 86
    PIECE_GAP = 8

    def __init__(self) -> None:
        self.board_theme = DEFAULT_BOARD_THEME
        self.piece_set = DEFAULT_PIECE_SET
        self.elo = DEFAULT_ELO
        self.skill: int | None = 8
        self.vs_ai = False
        self.hover_key: str | None = None
        self.piece_buttons: dict[str, pygame.Rect] = {}
        self.board_buttons: dict[str, pygame.Rect] = {}
        self.elo_buttons: dict[int, pygame.Rect] = {}
        self._rebuild()

    def _rebuild(self) -> None:
        self.piece_buttons.clear()
        self.board_buttons.clear()
        self.elo_buttons.clear()

        x = SIDEBAR_X + 14
        piece_y = SIDEBAR_Y + 78
        cols = 2
        card_w = (SIDEBAR_INNER - self.PIECE_GAP) // cols

        for index, piece_set in enumerate(PIECE_SETS):
            col = index % cols
            row = index // cols
            rect = pygame.Rect(
                x + col * (card_w + self.PIECE_GAP),
                piece_y + row * (self.PIECE_CARD_H + self.PIECE_GAP),
                card_w,
                self.PIECE_CARD_H,
            )
            self.piece_buttons[piece_set["id"]] = rect

        board_y = piece_y + 2 * (self.PIECE_CARD_H + self.PIECE_GAP) + 48
        btn_w = (SIDEBAR_INNER - 8) // 2
        btn_h = 38
        gap = 8

        for index, theme in enumerate(BOARD_THEMES):
            col = index % cols
            row = index // cols
            rect = pygame.Rect(
                x + col * (btn_w + gap),
                board_y + row * (btn_h + gap),
                btn_w,
                btn_h,
            )
            self.board_buttons[theme["id"]] = rect

        elo_y = board_y + ((len(BOARD_THEMES) + 1) // cols) * (btn_h + gap) + 44
        elo_btn_w = (SIDEBAR_INNER - gap) // 2
        elo_btn_h = 28
        for index, level in enumerate(ELO_LEVELS):
            col = index % cols
            row = index // cols
            rect = pygame.Rect(
                x + col * (elo_btn_w + gap),
                elo_y + row * (elo_btn_h + 6),
                elo_btn_w,
                elo_btn_h,
            )
            self.elo_buttons[level["elo"]] = rect

    def sync_from_session(
        self,
        theme_id: str,
        piece_set: str,
        elo: int,
        skill: int | None,
        vs_ai: bool,
    ) -> None:
        self.board_theme = theme_id
        self.piece_set = piece_set
        self.elo = elo
        self.skill = skill
        self.vs_ai = vs_ai

    def update_hover(self, pos: tuple[int, int] | None) -> None:
        self.hover_key = None
        if pos is None:
            return
        for set_id, rect in self.piece_buttons.items():
            if rect.collidepoint(pos):
                self.hover_key = f"piece:{set_id}"
                return
        for theme_id, rect in self.board_buttons.items():
            if rect.collidepoint(pos):
                self.hover_key = f"board:{theme_id}"
                return
        if self.vs_ai:
            for elo, rect in self.elo_buttons.items():
                if rect.collidepoint(pos):
                    self.hover_key = f"elo:{elo}"
                    return

    def handle_click(self, pos: tuple[int, int]) -> tuple[str, object] | None:
        for set_id, rect in self.piece_buttons.items():
            if rect.collidepoint(pos):
                self.piece_set = set_id
                return ("piece", set_id)

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

    def get_piece_buttons(self) -> dict[str, pygame.Rect]:
        return self.piece_buttons

    def get_board_buttons(self) -> dict[str, pygame.Rect]:
        return self.board_buttons

    def get_elo_buttons(self) -> dict[int, pygame.Rect]:
        return self.elo_buttons if self.vs_ai else {}

    def panel_rect(self) -> pygame.Rect:
        from config.settings import SIDEBAR_WIDTH, WINDOW_HEIGHT

        return pygame.Rect(SIDEBAR_X, SIDEBAR_Y, SIDEBAR_WIDTH, WINDOW_HEIGHT - SIDEBAR_Y - 128)

    def contains(self, pos: tuple[int, int]) -> bool:
        return self.panel_rect().collidepoint(pos)

    def is_hovered(self, kind: str, key: str | int) -> bool:
        return self.hover_key == f"{kind}:{key}"

    def piece_section_bottom(self) -> int:
        first = next(iter(self.piece_buttons.values()))
        rows = (len(PIECE_SETS) + 1) // 2
        return first.y + rows * (self.PIECE_CARD_H + self.PIECE_GAP)
