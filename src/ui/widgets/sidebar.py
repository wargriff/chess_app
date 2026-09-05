from __future__ import annotations

import pygame

from src.models.settings import (
    BOARD_THEMES,
    DEFAULT_BOARD_THEME,
    DEFAULT_ELO,
    DEFAULT_PIECE_SET,
    DEFAULT_TIME_INCREMENT,
    DEFAULT_TIME_MINUTES,
    ELO_LEVELS,
    PIECE_SETS,
    SIDEBAR_TABS,
    TIME_CONTROLS,
)
from src.ui.layout import UILayout


class GameSidebar:
    """Panneau lateral a onglets avec zoom affichage."""

    def __init__(self, layout: UILayout) -> None:
        self.layout = layout
        self.board_theme = DEFAULT_BOARD_THEME
        self.piece_set = DEFAULT_PIECE_SET
        self.elo = DEFAULT_ELO
        self.skill: int | None = 8
        self.time_minutes = DEFAULT_TIME_MINUTES
        self.time_increment = DEFAULT_TIME_INCREMENT
        self.time_control_id = "10_0"
        self.vs_ai = False
        self.active_tab = "pieces"
        self.piece_scroll = 0
        self.board_scroll = 0
        self.hover_key: str | None = None
        self.tab_buttons: dict[str, pygame.Rect] = {}
        self.piece_buttons: dict[str, pygame.Rect] = {}
        self.board_buttons: dict[str, pygame.Rect] = {}
        self.elo_buttons: dict[int, pygame.Rect] = {}
        self.time_buttons: dict[str, pygame.Rect] = {}
        self.display_buttons: dict[str, pygame.Rect] = {}
        self._rebuild()

    def _rebuild_tabs(self) -> None:
        self.tab_buttons.clear()
        x = self.layout.sidebar_x + self.layout.s(14)
        tab_y = self.layout.tab_bar_y
        gap = self.layout.s(5)
        tab_h = self.layout.tab_height
        tab_w = (self.layout.sidebar_inner - gap * (len(SIDEBAR_TABS) - 1)) // len(SIDEBAR_TABS)
        for index, tab in enumerate(SIDEBAR_TABS):
            rect = pygame.Rect(x + index * (tab_w + gap), tab_y, tab_w, tab_h)
            self.tab_buttons[tab["id"]] = rect

    def _rebuild(self) -> None:
        self._rebuild_tabs()
        self.piece_buttons.clear()
        self.board_buttons.clear()
        self.elo_buttons.clear()
        self.time_buttons.clear()
        self.display_buttons.clear()

        x = self.layout.sidebar_x + self.layout.s(14)
        content_y = self.layout.content_y
        cols = 2
        gap = self.layout.s(10)

        if self.active_tab == "pieces":
            card_h = self.layout.s(118)
            card_w = (self.layout.sidebar_inner - gap) // cols
            scroll = int(self.piece_scroll)
            for index, piece_set in enumerate(PIECE_SETS):
                col = index % cols
                row = index // cols
                rect = pygame.Rect(
                    x + col * (card_w + gap),
                    content_y + row * (card_h + gap) - scroll,
                    card_w,
                    card_h,
                )
                self.piece_buttons[piece_set["id"]] = rect

        elif self.active_tab == "board":
            btn_w = (self.layout.sidebar_inner - gap) // cols
            btn_h = self.layout.s(46)
            scroll = int(self.board_scroll)
            for index, theme in enumerate(BOARD_THEMES):
                col = index % cols
                row = index // cols
                rect = pygame.Rect(
                    x + col * (btn_w + gap),
                    content_y + row * (btn_h + gap) - scroll,
                    btn_w,
                    btn_h,
                )
                self.board_buttons[theme["id"]] = rect

        elif self.active_tab == "time":
            time_btn_w = (self.layout.sidebar_inner - gap * 2) // 3
            time_btn_h = self.layout.s(38)
            for index, control in enumerate(TIME_CONTROLS):
                col = index % 3
                row = index // 3
                rect = pygame.Rect(
                    x + col * (time_btn_w + gap),
                    content_y + row * (time_btn_h + gap),
                    time_btn_w,
                    time_btn_h,
                )
                self.time_buttons[control["id"]] = rect

        elif self.active_tab == "display":
            block_h = self.layout.s(88)
            block_w = self.layout.sidebar_inner
            y = content_y
            self.display_buttons["ui_minus"] = pygame.Rect(x, y + self.layout.s(36), self.layout.s(52), self.layout.s(40))
            self.display_buttons["ui_plus"] = pygame.Rect(x + block_w - self.layout.s(52), y + self.layout.s(36), self.layout.s(52), self.layout.s(40))
            y += block_h + gap
            self.display_buttons["piece_minus"] = pygame.Rect(x, y + self.layout.s(36), self.layout.s(52), self.layout.s(40))
            self.display_buttons["piece_plus"] = pygame.Rect(x + block_w - self.layout.s(52), y + self.layout.s(36), self.layout.s(52), self.layout.s(40))
            y += block_h + gap
            reset_w = self.layout.s(160)
            self.display_buttons["reset_zoom"] = pygame.Rect(
                x + (block_w - reset_w) // 2,
                y + self.layout.s(8),
                reset_w,
                self.layout.s(40),
            )

        elif self.active_tab == "elo" and self.vs_ai:
            elo_btn_w = (self.layout.sidebar_inner - gap) // cols
            elo_btn_h = self.layout.s(38)
            for index, level in enumerate(ELO_LEVELS):
                col = index % cols
                row = index // cols
                rect = pygame.Rect(
                    x + col * (elo_btn_w + gap),
                    content_y + row * (elo_btn_h + gap),
                    elo_btn_w,
                    elo_btn_h,
                )
                self.elo_buttons[level["elo"]] = rect

    def set_active_tab(self, tab_id: str) -> None:
        if tab_id == "elo" and not self.vs_ai:
            return
        if tab_id != self.active_tab:
            self.active_tab = tab_id
            self.piece_scroll = 0
            self.board_scroll = 0
            self._rebuild()

    def board_scroll_max(self) -> int:
        btn_h = self.layout.s(46)
        gap = self.layout.s(10)
        rows = (len(BOARD_THEMES) + 1) // 2
        total = rows * (btn_h + gap) - gap
        return max(0, total - self.content_rect().height)

    def scroll_boards(self, delta: float) -> None:
        if self.active_tab != "board":
            return
        self.board_scroll = int(max(0, min(self.board_scroll_max(), self.board_scroll + delta)))
        self._rebuild()

    def piece_scroll_max(self) -> int:
        card_h = self.layout.s(118)
        gap = self.layout.s(10)
        rows = (len(PIECE_SETS) + 1) // 2
        total = rows * (card_h + gap) - gap
        return max(0, total - self.content_rect().height)

    def scroll_pieces(self, delta: float) -> None:
        if self.active_tab != "pieces":
            return
        self.piece_scroll = int(max(0, min(self.piece_scroll_max(), self.piece_scroll + delta)))
        self._rebuild()

    def sync_from_session(
        self,
        theme_id: str,
        piece_set: str,
        elo: int,
        skill: int | None,
        vs_ai: bool,
        time_minutes: int = DEFAULT_TIME_MINUTES,
        time_increment: int = DEFAULT_TIME_INCREMENT,
        time_control_id: str = "10_0",
    ) -> None:
        self.board_theme = theme_id
        self.piece_set = piece_set
        self.elo = elo
        self.skill = skill
        was_ai = self.vs_ai
        self.vs_ai = vs_ai
        self.time_minutes = time_minutes
        self.time_increment = time_increment
        self.time_control_id = time_control_id
        if not vs_ai and self.active_tab == "elo":
            self.active_tab = "pieces"
        if was_ai != vs_ai:
            self._rebuild()

    def update_hover(self, pos: tuple[int, int] | None) -> None:
        self.hover_key = None
        if pos is None:
            return
        for tab_id, rect in self.tab_buttons.items():
            if rect.collidepoint(pos):
                self.hover_key = f"tab:{tab_id}"
                return
        clip = self.content_rect()
        for set_id, rect in self.piece_buttons.items():
            if clip.colliderect(rect) and rect.collidepoint(pos):
                self.hover_key = f"piece:{set_id}"
                return
        for theme_id, rect in self.board_buttons.items():
            if clip.colliderect(rect) and rect.collidepoint(pos):
                self.hover_key = f"board:{theme_id}"
                return
        for control_id, rect in self.time_buttons.items():
            if rect.collidepoint(pos):
                self.hover_key = f"time:{control_id}"
                return
        for key, rect in self.display_buttons.items():
            if rect.collidepoint(pos):
                self.hover_key = f"display:{key}"
                return
        if self.vs_ai:
            for elo, rect in self.elo_buttons.items():
                if rect.collidepoint(pos):
                    self.hover_key = f"elo:{elo}"
                    return

    def handle_click(self, pos: tuple[int, int]) -> tuple[str, object] | None:
        for tab_id, rect in self.tab_buttons.items():
            if rect.collidepoint(pos):
                self.set_active_tab(tab_id)
                return None

        clip = self.content_rect()
        for set_id, rect in self.piece_buttons.items():
            if clip.colliderect(rect) and rect.collidepoint(pos):
                self.piece_set = set_id
                return ("piece", set_id)

        for theme_id, rect in self.board_buttons.items():
            if clip.colliderect(rect) and rect.collidepoint(pos):
                self.board_theme = theme_id
                return ("board", theme_id)

        for control_id, rect in self.time_buttons.items():
            if rect.collidepoint(pos):
                control = next(item for item in TIME_CONTROLS if item["id"] == control_id)
                self.time_control_id = control_id
                self.time_minutes = control["minutes"]
                self.time_increment = control["increment"]
                return ("time", control)

        for key, rect in self.display_buttons.items():
            if rect.collidepoint(pos):
                return ("display", key)

        if self.vs_ai:
            for elo, rect in self.elo_buttons.items():
                if rect.collidepoint(pos):
                    self.elo = elo
                    level = next(item for item in ELO_LEVELS if item["elo"] == elo)
                    self.skill = level["skill"]
                    return ("elo", level)
        return None

    def get_tab_buttons(self) -> dict[str, pygame.Rect]:
        return self.tab_buttons

    def get_piece_buttons(self) -> dict[str, pygame.Rect]:
        return self.piece_buttons

    def get_board_buttons(self) -> dict[str, pygame.Rect]:
        return self.board_buttons

    def get_elo_buttons(self) -> dict[int, pygame.Rect]:
        return self.elo_buttons if self.vs_ai else {}

    def get_time_buttons(self) -> dict[str, pygame.Rect]:
        return self.time_buttons

    def get_display_buttons(self) -> dict[str, pygame.Rect]:
        return self.display_buttons

    def panel_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.layout.sidebar_x,
            self.layout.sidebar_y,
            self.layout.sidebar_width,
            self.layout.height - self.layout.sidebar_y - self.layout.panel_bottom_margin,
        )

    def contains(self, pos: tuple[int, int]) -> bool:
        return self.panel_rect().collidepoint(pos)

    def is_hovered(self, kind: str, key: str | int) -> bool:
        return self.hover_key == f"{kind}:{key}"

    def content_rect(self) -> pygame.Rect:
        panel = self.panel_rect()
        return pygame.Rect(
            panel.x + self.layout.s(12),
            self.layout.content_y,
            panel.width - self.layout.s(24),
            panel.bottom - self.layout.content_y - self.layout.s(12),
        )
