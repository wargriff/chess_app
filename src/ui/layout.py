"""Mise en page moderne — plateau central, panneaux minimes, barre de controle."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame


MIN_WINDOW_WIDTH = 1100
MIN_WINDOW_HEIGHT = 720
BASE_WIDTH = 1280
BASE_HEIGHT = 820


@dataclass
class UILayout:
    width: int = BASE_WIDTH
    height: int = BASE_HEIGHT
    ui_scale: float = 1.0
    piece_scale: float = 1.02

    UI_SCALE_MIN: float = field(default=0.85, repr=False)
    UI_SCALE_MAX: float = field(default=1.4, repr=False)
    PIECE_SCALE_MIN: float = field(default=0.8, repr=False)
    PIECE_SCALE_MAX: float = field(default=1.3, repr=False)

    def resize(self, width: int, height: int) -> None:
        self.width = max(MIN_WINDOW_WIDTH, width)
        self.height = max(MIN_WINDOW_HEIGHT, height)

    @property
    def fit_scale(self) -> float:
        return max(0.78, min(1.7, min(self.width / BASE_WIDTH, self.height / BASE_HEIGHT)))

    @property
    def effective_scale(self) -> float:
        return self.ui_scale * self.fit_scale

    def bump_ui(self, delta: float) -> None:
        self.ui_scale = round(max(self.UI_SCALE_MIN, min(self.UI_SCALE_MAX, self.ui_scale + delta)), 2)

    def bump_piece(self, delta: float) -> None:
        self.piece_scale = round(max(self.PIECE_SCALE_MIN, min(self.PIECE_SCALE_MAX, self.piece_scale + delta)), 2)

    def reset_zoom(self) -> None:
        self.ui_scale = 1.0
        self.piece_scale = 1.02

    def s(self, value: float) -> int:
        return max(1, int(value * self.effective_scale))

    @property
    def toolbar_height(self) -> int:
        return self.s(64)

    @property
    def panel_width(self) -> int:
        return self.s(240)

    @property
    def gap(self) -> int:
        return self.s(16)

    @property
    def board_area_top(self) -> int:
        return self.gap

    @property
    def board_area_height(self) -> int:
        return self.height - self.toolbar_height - self.gap * 2

    @property
    def board_area_left(self) -> int:
        return self.panel_width + self.gap * 2

    @property
    def board_area_width(self) -> int:
        return self.width - self.panel_width * 2 - self.gap * 4

    @property
    def board_pixel_size(self) -> int:
        size = min(self.board_area_width, self.board_area_height - self.s(8))
        size = max(320, size)
        return (size // 8) * 8

    @property
    def square_size(self) -> int:
        return max(1, self.board_pixel_size // 8)

    def piece_draw_size(self, selected: bool = False, selection_mul: float = 1.0) -> int:
        base = int((self.square_size - self.s(4)) * self.piece_scale)
        base = min(base, self.square_size - 2)
        if selected:
            base = int(base * selection_mul)
        return max(self.s(20), (base // 2) * 2)

    def board_origin(self) -> tuple[int, int]:
        size = self.board_pixel_size
        x = self.board_area_left + (self.board_area_width - size) // 2
        y = self.board_area_top + (self.board_area_height - size) // 2
        return x, y

    def left_panel_rect(self) -> pygame.Rect:
        return pygame.Rect(self.gap, self.gap, self.panel_width, self.board_area_height)

    def right_panel_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.width - self.panel_width - self.gap,
            self.gap,
            self.panel_width,
            self.board_area_height,
        )

    def toolbar_rect(self) -> pygame.Rect:
        return pygame.Rect(0, self.height - self.toolbar_height, self.width, self.toolbar_height)

    def control_buttons(self) -> dict[str, pygame.Rect]:
        labels = ["Nouvelle partie", "Annuler", "Refaire", "Pause", "Parametres"]
        bh = self.s(40)
        bw = self.s(132)
        gap = self.s(10)
        total = len(labels) * bw + (len(labels) - 1) * gap
        y = self.height - self.toolbar_height + (self.toolbar_height - bh) // 2
        x0 = (self.width - total) // 2
        return {label: pygame.Rect(x0 + i * (bw + gap), y, bw, bh) for i, label in enumerate(labels)}

    # --- Compat anciens appels renderer ---
    @property
    def sidebar_width(self) -> int:
        return self.panel_width

    @property
    def sidebar_x(self) -> int:
        return self.right_panel_rect().x

    @property
    def sidebar_y(self) -> int:
        return self.gap

    @property
    def sidebar_inner(self) -> int:
        return self.panel_width - self.s(24)

    @property
    def hud_height(self) -> int:
        return self.toolbar_height

    @property
    def play_area_width(self) -> int:
        return self.board_area_width + self.panel_width + self.gap

    @property
    def play_area_height(self) -> int:
        return self.board_area_height

    @property
    def play_area_left(self) -> int:
        return self.board_area_left

    @property
    def margin(self) -> int:
        return self.gap

    @property
    def frame_padding(self) -> int:
        return self.s(8)

    @property
    def clock_box_height(self) -> int:
        return self.s(48)

    @property
    def clock_box_width(self) -> int:
        return min(self.s(200), self.board_pixel_size)

    @property
    def board_gap(self) -> int:
        return self.s(4)

    @property
    def eval_bar_width(self) -> int:
        return self.s(14)

    def eval_bar_rect(self) -> pygame.Rect:
        ox, oy = self.board_origin()
        return pygame.Rect(ox - self.eval_bar_width - self.s(8), oy, self.eval_bar_width, self.board_pixel_size)

    def black_clock_rect(self) -> pygame.Rect:
        # Horloges intégrées aux panneaux — rects factices pour compat
        r = self.left_panel_rect()
        return pygame.Rect(r.x + self.s(12), r.y + self.s(70), r.width - self.s(24), self.s(40))

    def white_clock_rect(self) -> pygame.Rect:
        r = self.left_panel_rect()
        return pygame.Rect(r.x + self.s(12), r.bottom - self.s(100), r.width - self.s(24), self.s(40))

    @property
    def tab_height(self) -> int:
        return self.s(40)

    @property
    def tab_bar_y(self) -> int:
        return self.right_panel_rect().y + self.s(40)

    @property
    def content_y(self) -> int:
        return self.tab_bar_y + self.tab_height + self.s(8)

    @property
    def panel_bottom_margin(self) -> int:
        return self.toolbar_height + self.s(8)

    def hud_action_buttons(self) -> dict[str, pygame.Rect]:
        return self.control_buttons()
