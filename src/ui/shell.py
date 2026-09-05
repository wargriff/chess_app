"""Chrome UI : header + navigation par onglets."""

from __future__ import annotations

import pygame

from src.ui.layout import NAV_TABS, UILayout
from src.ui.style.gaming_style import GOLD, GOLD_BRIGHT, LINE, MUTED, PANEL, PANEL_SOFT, TEXT


class AppShell:
    def __init__(self, layout: UILayout) -> None:
        self.layout = layout
        self.hover_nav: str | None = None
        self.header_buttons: dict[str, pygame.Rect] = {}

    def rebuild_header_buttons(self) -> None:
        h = self.layout.header_rect()
        bw = self.layout.s(100)
        bh = self.layout.s(32)
        y = h.y + (h.height - bh) // 2
        self.header_buttons = {
            "pause": pygame.Rect(h.right - self.layout.s(16) - bw, y, bw, bh),
        }

    def draw(
        self,
        screen: pygame.Surface,
        fonts: dict[str, pygame.font.Font],
        *,
        engine_online: bool,
        engine_label: str,
        mode_hint: str = "",
    ) -> None:
        self.rebuild_header_buttons()
        self._draw_header(screen, fonts, engine_online, engine_label, mode_hint)
        self._draw_nav(screen, fonts)

    def _draw_header(
        self,
        screen: pygame.Surface,
        fonts: dict[str, pygame.font.Font],
        engine_online: bool,
        engine_label: str,
        mode_hint: str,
    ) -> None:
        h = self.layout.header_rect()
        pygame.draw.rect(screen, PANEL, h)
        pygame.draw.line(screen, LINE, (0, h.bottom - 1), (self.layout.width, h.bottom - 1), 1)

        brand = fonts["brand"].render(self.layout.brand_title(), True, GOLD_BRIGHT)
        screen.blit(brand, (self.layout.s(20), h.centery - brand.get_height() // 2))

        # Statut Stockfish
        dot_x = self.layout.s(20) + brand.get_width() + self.layout.s(18)
        status_color = (80, 190, 110) if engine_online else (200, 80, 70)
        pygame.draw.circle(screen, status_color, (dot_x, h.centery), self.layout.s(5))
        label = engine_label if engine_online else "Stockfish hors ligne"
        if self.layout.breakpoint.value == "xs":
            label = "SF" if engine_online else "SF off"
        st = fonts["small"].render(label[:28], True, MUTED)
        screen.blit(st, (dot_x + self.layout.s(12), h.centery - st.get_height() // 2))

        if mode_hint and self.layout.width >= 1100:
            hint = fonts["small"].render(mode_hint[:40], True, MUTED)
            screen.blit(hint, hint.get_rect(center=(self.layout.width // 2, h.centery)))

        # Bouton pause header
        for key, rect in self.header_buttons.items():
            hovered = self.hover_nav == f"header:{key}"
            pygame.draw.rect(screen, PANEL_SOFT if not hovered else (40, 36, 32), rect, border_radius=6)
            pygame.draw.rect(screen, GOLD if hovered else LINE, rect, width=1, border_radius=6)
            lab = fonts["small"].render("Pause", True, TEXT)
            screen.blit(lab, lab.get_rect(center=rect.center))

    def _draw_nav(self, screen: pygame.Surface, fonts: dict[str, pygame.font.Font]) -> None:
        bar = self.layout.nav_rect()
        pygame.draw.rect(screen, (16, 15, 14), bar)
        pygame.draw.line(screen, LINE, (0, bar.bottom - 1), (self.layout.width, bar.bottom - 1), 1)

        rects = self.layout.nav_tab_rects()
        for tab_id, _ in NAV_TABS:
            rect = rects[tab_id]
            active = self.layout.active_nav == tab_id
            hovered = self.hover_nav == tab_id
            if active:
                pygame.draw.rect(screen, PANEL_SOFT, rect, border_radius=6)
                pygame.draw.line(screen, GOLD, (rect.x + 8, rect.bottom - 2), (rect.right - 8, rect.bottom - 2), 2)
            elif hovered:
                pygame.draw.rect(screen, (26, 24, 22), rect, border_radius=6)
            color = GOLD_BRIGHT if active else (TEXT if hovered else MUTED)
            text = fonts["nav"].render(self.layout.nav_label(tab_id), True, color)
            screen.blit(text, text.get_rect(center=rect.center))

    def update_hover(self, pos: tuple[int, int] | None) -> None:
        self.hover_nav = None
        if pos is None:
            return
        for tab_id, rect in self.layout.nav_tab_rects().items():
            if rect.collidepoint(pos):
                self.hover_nav = tab_id
                return
        for key, rect in self.header_buttons.items():
            if rect.collidepoint(pos):
                self.hover_nav = f"header:{key}"
                return

    def handle_click(self, pos: tuple[int, int]) -> tuple[str, str] | None:
        for tab_id, rect in self.layout.nav_tab_rects().items():
            if rect.collidepoint(pos):
                return ("nav", tab_id)
        for key, rect in self.header_buttons.items():
            if rect.collidepoint(pos):
                return ("header", key)
        return None
