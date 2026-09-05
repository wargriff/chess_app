"""Layout responsive — header, onglets, plateau prioritaire, breakpoints."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import pygame


class Breakpoint(Enum):
    XS = "xs"  # < 900
    SM = "sm"  # 900–1099
    MD = "md"  # 1100–1399
    LG = "lg"  # 1400–1799
    XL = "xl"  # >= 1800


MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 560
BASE_WIDTH = 1440
BASE_HEIGHT = 900

NAV_TABS = [
    ("partie", "Partie"),
    ("analyse", "Analyse"),
    ("historique", "Historique"),
    ("sauvegardes", "Sauvegardes"),
    ("stats", "Stats"),
    ("parametres", "Paramètres"),
]


@dataclass
class UILayout:
    width: int = BASE_WIDTH
    height: int = BASE_HEIGHT
    ui_scale: float = 1.0
    piece_scale: float = 1.04
    active_nav: str = "partie"
    show_left_drawer: bool = False
    show_right_drawer: bool = False

    UI_SCALE_MIN: float = field(default=0.85, repr=False)
    UI_SCALE_MAX: float = field(default=1.35, repr=False)
    PIECE_SCALE_MIN: float = field(default=0.8, repr=False)
    PIECE_SCALE_MAX: float = field(default=1.3, repr=False)

    def resize(self, width: int, height: int) -> None:
        self.width = max(MIN_WINDOW_WIDTH, width)
        self.height = max(MIN_WINDOW_HEIGHT, height)

    @property
    def breakpoint(self) -> Breakpoint:
        w = self.width
        if w < 900:
            return Breakpoint.XS
        if w < 1100:
            return Breakpoint.SM
        if w < 1400:
            return Breakpoint.MD
        if w < 1800:
            return Breakpoint.LG
        return Breakpoint.XL

    @property
    def fit_scale(self) -> float:
        return max(0.72, min(1.55, min(self.width / BASE_WIDTH, self.height / BASE_HEIGHT)))

    @property
    def effective_scale(self) -> float:
        return self.ui_scale * self.fit_scale

    def bump_ui(self, delta: float) -> None:
        self.ui_scale = round(max(self.UI_SCALE_MIN, min(self.UI_SCALE_MAX, self.ui_scale + delta)), 2)

    def bump_piece(self, delta: float) -> None:
        self.piece_scale = round(max(self.PIECE_SCALE_MIN, min(self.PIECE_SCALE_MAX, self.piece_scale + delta)), 2)

    def reset_zoom(self) -> None:
        self.ui_scale = 1.0
        self.piece_scale = 1.04

    def s(self, value: float) -> int:
        return max(1, int(value * self.effective_scale))

    def font_size(self, base: int, *, min_size: int = 11, max_size: int = 42) -> int:
        return max(min_size, min(max_size, self.s(base)))

    def brand_title(self) -> str:
        bp = self.breakpoint
        if bp == Breakpoint.XS:
            return "D4"
        if bp == Breakpoint.SM:
            return "Chess Pro"
        return "Chess Pro D4"

    # --- Chrome heights ---
    @property
    def header_height(self) -> int:
        return self.s(52)

    @property
    def nav_height(self) -> int:
        return self.s(44)

    @property
    def action_bar_height(self) -> int:
        if self.active_nav != "partie":
            return self.s(8)
        return self.s(56)

    @property
    def chrome_top(self) -> int:
        return self.header_height + self.nav_height

    @property
    def chrome_bottom(self) -> int:
        return self.action_bar_height

    @property
    def gap(self) -> int:
        return self.s(12 if self.breakpoint.value in ("xs", "sm") else 16)

    @property
    def show_side_panels(self) -> bool:
        """Panneaux latéraux persistants (grand écran)."""
        return self.breakpoint in (Breakpoint.MD, Breakpoint.LG, Breakpoint.XL)

    @property
    def show_both_panels(self) -> bool:
        return self.breakpoint in (Breakpoint.LG, Breakpoint.XL)

    @property
    def panel_width(self) -> int:
        bp = self.breakpoint
        if bp == Breakpoint.XL:
            return self.s(280)
        if bp == Breakpoint.LG:
            return self.s(250)
        if bp == Breakpoint.MD:
            return self.s(220)
        return self.s(260)  # drawer width

    @property
    def content_top(self) -> int:
        return self.chrome_top + self.gap

    @property
    def content_bottom(self) -> int:
        return self.height - self.chrome_bottom - self.gap

    @property
    def content_height(self) -> int:
        return max(200, self.content_bottom - self.content_top)

    @property
    def board_area_top(self) -> int:
        return self.content_top

    @property
    def board_area_height(self) -> int:
        return self.content_height

    @property
    def board_area_left(self) -> int:
        left = self.left_panel_rect()
        if left:
            return left.right + self.gap
        return self.gap

    @property
    def board_area_width(self) -> int:
        left = self.left_panel_rect()
        right = self.right_panel_rect()
        left_w = (left.width + self.gap) if left else 0
        right_w = (right.width + self.gap) if right else 0
        return max(200, self.width - left_w - right_w - self.gap * 2)

    @property
    def board_pixel_size(self) -> int:
        size = min(self.board_area_width, self.board_area_height - self.s(4))
        if self.breakpoint in (Breakpoint.XS, Breakpoint.SM):
            size = min(self.width - self.gap * 2, self.content_height - self.s(4))
        size = max(240, size)
        return (size // 8) * 8

    @property
    def square_size(self) -> int:
        return max(1, self.board_pixel_size // 8)

    def piece_draw_size(self, selected: bool = False, selection_mul: float = 1.0) -> int:
        base = int((self.square_size - self.s(4)) * self.piece_scale)
        base = min(base, self.square_size - 2)
        if selected:
            base = int(base * selection_mul)
        return max(self.s(16), (base // 2) * 2)

    def board_origin(self) -> tuple[int, int]:
        size = self.board_pixel_size
        x = self.board_area_left + (self.board_area_width - size) // 2
        y = self.board_area_top + (self.board_area_height - size) // 2
        return x, y

    def header_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.width, self.header_height)

    def nav_rect(self) -> pygame.Rect:
        return pygame.Rect(0, self.header_height, self.width, self.nav_height)

    def left_panel_rect(self) -> pygame.Rect | None:
        if self.show_both_panels:
            return pygame.Rect(self.gap, self.content_top, self.panel_width, self.content_height)
        if self.show_side_panels:
            if self.active_nav in ("analyse", "parametres", "sauvegardes"):
                return None
            return pygame.Rect(self.gap, self.content_top, self.panel_width, self.content_height)
        if self.show_left_drawer:
            return pygame.Rect(self.gap, self.content_top, self.panel_width, self.content_height)
        return None

    def right_panel_rect(self) -> pygame.Rect | None:
        if self.show_both_panels:
            return pygame.Rect(
                self.width - self.panel_width - self.gap,
                self.content_top,
                self.panel_width,
                self.content_height,
            )
        if self.show_side_panels and self.active_nav in ("analyse", "parametres"):
            return pygame.Rect(
                self.width - self.panel_width - self.gap,
                self.content_top,
                self.panel_width,
                self.content_height,
            )
        if self.show_right_drawer:
            return pygame.Rect(
                self.width - self.panel_width - self.gap,
                self.content_top,
                self.panel_width,
                self.content_height,
            )
        return None

    def action_bar_rect(self) -> pygame.Rect:
        return pygame.Rect(0, self.height - self.action_bar_height, self.width, self.action_bar_height)

    def toolbar_rect(self) -> pygame.Rect:
        return self.action_bar_rect()

    def control_buttons(self) -> dict[str, pygame.Rect]:
        """Actions essentielles uniquement — plus de rangée de 8 boutons."""
        if self.active_nav != "partie":
            return {}
        labels = ["Nouvelle partie", "Annuler", "Refaire"]
        bh = self.s(36)
        bw = self.s(140)
        gap = self.s(10)
        total = len(labels) * bw + (len(labels) - 1) * gap
        y = self.height - self.action_bar_height + (self.action_bar_height - bh) // 2
        x0 = (self.width - total) // 2
        return {label: pygame.Rect(x0 + i * (bw + gap), y, bw, bh) for i, label in enumerate(labels)}

    def nav_tab_rects(self) -> dict[str, pygame.Rect]:
        bar = self.nav_rect()
        n = len(NAV_TABS)
        pad = self.s(8)
        gap = self.s(4)
        usable = bar.width - pad * 2 - gap * (n - 1)
        tw = max(self.s(64), usable // n)
        # Sur XS, labels courts
        rects: dict[str, pygame.Rect] = {}
        x = bar.x + pad
        for tab_id, _ in NAV_TABS:
            rects[tab_id] = pygame.Rect(x, bar.y + self.s(4), tw, bar.height - self.s(8))
            x += tw + gap
        return rects

    def nav_label(self, tab_id: str) -> str:
        full = dict(NAV_TABS).get(tab_id, tab_id)
        if self.breakpoint == Breakpoint.XS:
            short = {
                "partie": "Jeu",
                "analyse": "Ana",
                "historique": "Hist",
                "sauvegardes": "Sav",
                "stats": "Stat",
                "parametres": "Régl",
            }
            return short.get(tab_id, full[:4])
        return full

    # --- Compat renderer/sidebar ---
    @property
    def sidebar_width(self) -> int:
        return self.panel_width

    @property
    def sidebar_x(self) -> int:
        r = self.right_panel_rect()
        return r.x if r else self.width - self.panel_width - self.gap

    @property
    def sidebar_y(self) -> int:
        return self.content_top

    @property
    def sidebar_inner(self) -> int:
        return self.panel_width - self.s(24)

    @property
    def hud_height(self) -> int:
        return self.action_bar_height

    @property
    def play_area_width(self) -> int:
        return self.board_area_width

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
        return self.s(6)

    @property
    def clock_box_height(self) -> int:
        return self.s(40)

    @property
    def clock_box_width(self) -> int:
        return min(self.s(180), self.board_pixel_size)

    @property
    def board_gap(self) -> int:
        return self.s(4)

    @property
    def eval_bar_width(self) -> int:
        return self.s(12)

    def eval_bar_rect(self) -> pygame.Rect:
        ox, oy = self.board_origin()
        return pygame.Rect(ox - self.eval_bar_width - self.s(6), oy, self.eval_bar_width, self.board_pixel_size)

    def black_clock_rect(self) -> pygame.Rect:
        r = self.left_panel_rect() or pygame.Rect(0, 0, 100, 40)
        return pygame.Rect(r.x + self.s(12), r.y + self.s(70), r.width - self.s(24), self.s(36))

    def white_clock_rect(self) -> pygame.Rect:
        r = self.left_panel_rect() or pygame.Rect(0, 0, 100, 40)
        return pygame.Rect(r.x + self.s(12), r.bottom - self.s(90), r.width - self.s(24), self.s(36))

    @property
    def tab_height(self) -> int:
        return self.s(36)

    @property
    def tab_bar_y(self) -> int:
        r = self.right_panel_rect()
        return (r.y if r else self.content_top) + self.s(8)

    @property
    def content_y(self) -> int:
        return self.tab_bar_y + self.tab_height + self.s(8)

    @property
    def panel_bottom_margin(self) -> int:
        return self.action_bar_height + self.s(4)

    def hud_action_buttons(self) -> dict[str, pygame.Rect]:
        return self.control_buttons()
