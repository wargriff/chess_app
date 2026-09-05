"""Panneaux contextuels épurés (match, historique, analyse)."""

from __future__ import annotations

import pygame

from src.core.session import GameSession
from src.engine.uci_client import AnalysisInfo
from src.ui.layout import UILayout
from src.ui.style.gaming_style import GOLD, GOLD_BRIGHT, LINE, MUTED, PANEL, PANEL_SOFT, TEXT, draw_separator


def _label(surface: pygame.Surface, font: pygame.font.Font, text: str, pos: tuple[int, int], color=MUTED) -> int:
    surf = font.render(text, True, color)
    surface.blit(surf, pos)
    return surf.get_height()


class SidePanels:
    def __init__(self, layout: UILayout) -> None:
        self.layout = layout
        self.history_scroll = 0
        self.selected_ply: int | None = None
        self._history_hit: list[tuple[pygame.Rect, int]] = []
        self._nav_buttons: dict[str, pygame.Rect] = {}
        self._action_hits: dict[str, pygame.Rect] = {}

    def draw(
        self,
        screen: pygame.Surface,
        session: GameSession | None,
        analysis: AnalysisInfo | None,
        fonts: dict[str, pygame.font.Font],
        *,
        context: str = "partie",
    ) -> None:
        left = self.layout.left_panel_rect()
        right = self.layout.right_panel_rect()

        if context in ("partie", "historique") and left:
            self._draw_match_panel(screen, session, fonts, left, show_history=True)
        elif context == "stats" and left:
            self._draw_stats_panel(screen, session, fonts, left)

        if context == "analyse" and right:
            self._draw_analysis_panel(screen, session, analysis, fonts, right)
        elif context == "partie" and right and self.layout.show_both_panels:
            self._draw_engine_panel(screen, session, analysis, fonts, right)

    def _panel_bg(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(screen, PANEL, rect, border_radius=10)
        pygame.draw.rect(screen, LINE, rect, width=1, border_radius=10)

    def _draw_match_panel(
        self,
        screen: pygame.Surface,
        session: GameSession | None,
        fonts: dict[str, pygame.font.Font],
        rect: pygame.Rect,
        *,
        show_history: bool,
    ) -> None:
        self._panel_bg(screen, rect)
        x = rect.x + self.layout.s(14)
        y = rect.y + self.layout.s(14)
        y += _label(screen, fonts["title"], "Match", (x, y), GOLD) + self.layout.s(12)

        if session is None:
            _label(screen, fonts["body"], "Aucune partie", (x, y), MUTED)
            return

        top = session.black_player
        bottom = session.white_player
        top_time = session.clock.format_time(session.clock.black_seconds) if session.clock.enabled else "∞"
        bottom_time = session.clock.format_time(session.clock.white_seconds) if session.clock.enabled else "∞"

        y = self._player_row(
            screen, fonts, x, y, rect.width - self.layout.s(28),
            "Stockfish" if top.is_engine else top.name,
            top.color_label,
            top_time,
            not session.board.turn(),
            top.elo if top.is_engine else None,
        )
        vs = fonts["small"].render("contre", True, MUTED)
        screen.blit(vs, (x, y))
        y += vs.get_height() + self.layout.s(6)
        y = self._player_row(
            screen, fonts, x, y, rect.width - self.layout.s(28),
            "Stockfish" if bottom.is_engine else bottom.name,
            bottom.color_label,
            bottom_time,
            session.board.turn(),
            bottom.elo if bottom.is_engine else None,
        )

        status = session.message or session.turn_status()
        y += self.layout.s(6)
        status_box = pygame.Rect(x, y, rect.width - self.layout.s(28), self.layout.s(36))
        pygame.draw.rect(screen, PANEL_SOFT, status_box, border_radius=6)
        st = fonts["small"].render(status[:36], True, GOLD if session.ai_thinking else TEXT)
        screen.blit(st, st.get_rect(midleft=(status_box.x + self.layout.s(10), status_box.centery)))
        y = status_box.bottom + self.layout.s(14)

        if not show_history:
            return

        draw_separator(screen, x, y, rect.width - self.layout.s(28))
        y += self.layout.s(10)
        y += _label(screen, fonts["title"], "Historique", (x, y), GOLD) + self.layout.s(8)

        nav_h = self.layout.s(28)
        prev = pygame.Rect(x, y, (rect.width - self.layout.s(36)) // 2, nav_h)
        nxt = pygame.Rect(prev.right + self.layout.s(8), y, prev.width, nav_h)
        self._nav_buttons = {"prev": prev, "next": nxt}
        for rct, lab in ((prev, "↑"), (nxt, "↓")):
            pygame.draw.rect(screen, PANEL_SOFT, rct, border_radius=5)
            t = fonts["small"].render(lab, True, TEXT)
            screen.blit(t, t.get_rect(center=rct.center))
        y += nav_h + self.layout.s(8)

        sans = session.move_list_san()
        pairs: list[tuple[int, str, str]] = []
        i = n = 0
        n = 1
        while i < len(sans):
            pairs.append((n, sans[i], sans[i + 1] if i + 1 < len(sans) else ""))
            i += 2
            n += 1

        max_lines = max(3, (rect.bottom - y - self.layout.s(12)) // self.layout.s(22))
        start = max(0, len(pairs) - max_lines - self.history_scroll)
        self._history_hit = []
        if not pairs:
            _label(screen, fonts["body"], "—", (x, y), MUTED)
            return
        col_w = x + self.layout.s(32)
        col_b = x + self.layout.s(100)
        for idx, (num, wsan, bsan) in enumerate(pairs[start : start + max_lines]):
            pair_index = start + idx
            end_ply = min(len(sans), (pair_index + 1) * 2)
            is_current = pair_index == len(pairs) - 1
            row = pygame.Rect(x, y, rect.width - self.layout.s(28), self.layout.s(20))
            if is_current:
                pygame.draw.rect(screen, (40, 34, 26), row, border_radius=3)
            self._history_hit.append((row, end_ply))
            color = GOLD if is_current else TEXT
            _label(screen, fonts["mono"], f"{num}.", (x, y), MUTED)
            _label(screen, fonts["mono"], wsan[:7], (col_w, y), color)
            if bsan:
                _label(screen, fonts["mono"], bsan[:7], (col_b, y), color)
            y += self.layout.s(22)

    def _draw_engine_panel(
        self,
        screen: pygame.Surface,
        session: GameSession | None,
        analysis: AnalysisInfo | None,
        fonts: dict[str, pygame.font.Font],
        rect: pygame.Rect,
    ) -> None:
        self._panel_bg(screen, rect)
        x = rect.x + self.layout.s(14)
        y = rect.y + self.layout.s(14)
        y += _label(screen, fonts["title"], "Stockfish", (x, y), GOLD) + self.layout.s(12)
        if session is None:
            _label(screen, fonts["body"], "—", (x, y), MUTED)
            return
        eng = session.engine
        online = eng.available
        pygame.draw.circle(screen, (80, 190, 110) if online else (200, 80, 70), (x + 6, y + 8), 5)
        _label(screen, fonts["body"], "En ligne" if online else "Hors ligne", (x + 18, y), TEXT)
        y += self.layout.s(28)
        lines = [
            ("Niveau", getattr(eng, "strength_label", "—")),
            ("ELO", str(getattr(eng, "elo", session.elo))),
            ("Réflexion", f"{getattr(eng, 'movetime_ms', 800) / 1000:.1f} s"),
            ("Statut", eng.status_label if hasattr(eng, "status_label") else "—"),
        ]
        if analysis:
            lines.append(("Éval", analysis.eval_text))
            lines.append(("Prof.", str(analysis.depth)))
        for lab, val in lines:
            _label(screen, fonts["small"], lab, (x, y), MUTED)
            _label(screen, fonts["body"], str(val)[:18], (x, y + self.layout.s(16)), TEXT)
            y += self.layout.s(40)

    def _draw_analysis_panel(
        self,
        screen: pygame.Surface,
        session: GameSession | None,
        analysis: AnalysisInfo | None,
        fonts: dict[str, pygame.font.Font],
        rect: pygame.Rect,
    ) -> None:
        self._draw_engine_panel(screen, session, analysis, fonts, rect)

    def _draw_stats_panel(
        self,
        screen: pygame.Surface,
        session: GameSession | None,
        fonts: dict[str, pygame.font.Font],
        rect: pygame.Rect,
    ) -> None:
        self._panel_bg(screen, rect)
        x = rect.x + self.layout.s(14)
        y = rect.y + self.layout.s(14)
        y += _label(screen, fonts["title"], "Statistiques", (x, y), GOLD) + self.layout.s(14)
        if session is None:
            _label(screen, fonts["body"], "Lancez une partie", (x, y), MUTED)
            return
        ply = len(session.board.board.move_stack)
        material = session.board.board.occupied.bit_count() if hasattr(session.board.board, "occupied") else 32
        lines = [
            ("Coups joués", str(ply)),
            ("Mode", session.mode.name),
            ("Chrono", session.clock.label()),
            ("Pièces", str(material)),
            ("État", session.turn_status()[:22]),
        ]
        for lab, val in lines:
            _label(screen, fonts["small"], lab, (x, y), MUTED)
            _label(screen, fonts["body"], val, (x, y + self.layout.s(16)), TEXT)
            y += self.layout.s(42)

    def _player_row(
        self,
        screen: pygame.Surface,
        fonts: dict[str, pygame.font.Font],
        x: int,
        y: int,
        width: int,
        name: str,
        color_label: str,
        time_text: str,
        active: bool,
        elo: int | None,
    ) -> int:
        box = pygame.Rect(x, y, width, self.layout.s(58))
        pygame.draw.rect(screen, PANEL_SOFT if active else PANEL, box, border_radius=8)
        if active:
            pygame.draw.rect(screen, GOLD, box, width=1, border_radius=8)
        _label(screen, fonts["body"], name[:16], (box.x + self.layout.s(10), box.y + self.layout.s(8)), TEXT)
        sub = f"{color_label}" + (f" · {elo}" if elo else "")
        _label(screen, fonts["small"], sub, (box.x + self.layout.s(10), box.y + self.layout.s(32)), MUTED)
        t = fonts["clock"].render(time_text, True, GOLD if active else TEXT)
        screen.blit(t, t.get_rect(midright=(box.right - self.layout.s(10), box.centery)))
        return box.bottom + self.layout.s(6)

    def handle_history_click(self, pos: tuple[int, int]) -> int | None:
        for rect, end_ply in self._history_hit:
            if rect.collidepoint(pos):
                return end_ply
        return None

    def handle_nav_click(self, pos: tuple[int, int]) -> str | None:
        for key, rect in self._nav_buttons.items():
            if rect.collidepoint(pos):
                return key
        return None

    def draw_toolbar(
        self,
        screen: pygame.Surface,
        buttons: dict[str, pygame.Rect],
        hover: str | None,
        font: pygame.font.Font,
        disabled: set[str] | None = None,
    ) -> None:
        if not buttons:
            return
        bar = self.layout.action_bar_rect()
        pygame.draw.rect(screen, (14, 13, 12), bar)
        pygame.draw.line(screen, LINE, (0, bar.y), (self.layout.width, bar.y), 1)
        disabled = disabled or set()
        for label, rect in buttons.items():
            is_disabled = label in disabled
            active = hover == label and not is_disabled
            primary = label == "Nouvelle partie"
            if is_disabled:
                bg, border, color = (20, 19, 18), LINE, (70, 65, 58)
            else:
                bg = (48, 40, 28) if primary else (PANEL_SOFT if active else PANEL)
                border = GOLD if active or primary else LINE
                color = TEXT
            pygame.draw.rect(screen, bg, rect, border_radius=7)
            pygame.draw.rect(screen, border, rect, width=1, border_radius=7)
            text = font.render(label, True, color)
            screen.blit(text, text.get_rect(center=rect.center))
