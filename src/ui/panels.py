"""Panneaux UI modernes (gauche joueurs/historique, droite moteur)."""

from __future__ import annotations

import pygame

from src.core.session import GameSession
from src.engine.uci_client import AnalysisInfo
from src.models.settings import MUTED, TEXT_COLOR
from src.ui.layout import UILayout


BG_PANEL = (22, 20, 18)
BG_SOFT = (30, 27, 24)
LINE = (55, 48, 40)
ACCENT = (212, 165, 72)
WHITE = (240, 232, 218)


def _panel(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, BG_PANEL, rect, border_radius=10)
    pygame.draw.rect(surface, LINE, rect, width=1, border_radius=10)


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

    def draw(
        self,
        screen: pygame.Surface,
        session: GameSession | None,
        analysis: AnalysisInfo | None,
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        self._draw_left(screen, session, fonts)
        self._draw_right(screen, session, analysis, fonts)

    def _draw_left(self, screen: pygame.Surface, session: GameSession | None, fonts: dict[str, pygame.font.Font]) -> None:
        rect = self.layout.left_panel_rect()
        _panel(screen, rect)
        x = rect.x + self.layout.s(16)
        y = rect.y + self.layout.s(16)
        y += _label(screen, fonts["title"], "Partie", (x, y), ACCENT) + self.layout.s(14)

        if session is None:
            _label(screen, fonts["body"], "Aucune partie", (x, y), MUTED)
            return

        # Adversaire (haut) puis joueur (bas) — convention chess.com
        top = session.black_player
        bottom = session.white_player
        top_time = session.clock.format_time(session.clock.black_seconds) if session.clock.enabled else "∞"
        bottom_time = session.clock.format_time(session.clock.white_seconds) if session.clock.enabled else "∞"
        top_active = not session.board.turn()
        bottom_active = session.board.turn()

        y = self._player_block(screen, fonts, x, y, rect.width - self.layout.s(32), top.display_name, top.color_label, top_time, top_active)
        y += self.layout.s(10)
        pygame.draw.line(screen, LINE, (x, y), (rect.right - self.layout.s(16), y), 1)
        y += self.layout.s(12)
        y = self._player_block(screen, fonts, x, y, rect.width - self.layout.s(32), bottom.display_name, bottom.color_label, bottom_time, bottom_active)

        y += self.layout.s(18)
        y += _label(screen, fonts["title"], "Historique", (x, y), ACCENT) + self.layout.s(10)

        sans = session.move_list_san()
        pairs: list[str] = []
        i = 0
        n = 1
        while i < len(sans):
            w = sans[i]
            b = sans[i + 1] if i + 1 < len(sans) else ""
            pairs.append(f"{n}. {w}  {b}".rstrip())
            i += 2
            n += 1

        max_lines = max(4, (rect.bottom - y - self.layout.s(16)) // self.layout.s(22))
        start = max(0, len(pairs) - max_lines - self.history_scroll)
        visible = pairs[start : start + max_lines]
        self._history_hit: list[tuple[pygame.Rect, int]] = []
        if not visible:
            _label(screen, fonts["body"], "—", (x, y), MUTED)
            return
        for idx, line in enumerate(visible):
            pair_index = start + idx
            # ply apres ce tour complet (blanc+noir) ; clic = fin du demi-coup blanc min
            end_ply = min(len(sans), (pair_index + 1) * 2)
            color = ACCENT if self.selected_ply == pair_index else WHITE
            row = pygame.Rect(x, y, rect.width - self.layout.s(32), self.layout.s(20))
            self._history_hit.append((row, end_ply))
            _label(screen, fonts["mono"], line[:26], (x, y), color)
            y += self.layout.s(22)

    def handle_history_click(self, pos: tuple[int, int]) -> int | None:
        for rect, end_ply in getattr(self, "_history_hit", []):
            if rect.collidepoint(pos):
                return end_ply
        return None

    def _player_block(
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
    ) -> int:
        box = pygame.Rect(x, y, width, self.layout.s(64))
        pygame.draw.rect(screen, BG_SOFT if active else BG_PANEL, box, border_radius=8)
        if active:
            pygame.draw.rect(screen, ACCENT, box, width=1, border_radius=8)
        _label(screen, fonts["body"], name[:20], (box.x + self.layout.s(10), box.y + self.layout.s(8)), WHITE)
        _label(screen, fonts["small"], color_label, (box.x + self.layout.s(10), box.y + self.layout.s(34)), MUTED)
        t = fonts["clock"].render(time_text, True, ACCENT if active else WHITE)
        screen.blit(t, t.get_rect(midright=(box.right - self.layout.s(10), box.centery)))
        return box.bottom + self.layout.s(8)

    def _draw_right(
        self,
        screen: pygame.Surface,
        session: GameSession | None,
        analysis: AnalysisInfo | None,
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        rect = self.layout.right_panel_rect()
        _panel(screen, rect)
        x = rect.x + self.layout.s(16)
        y = rect.y + self.layout.s(16)
        y += _label(screen, fonts["title"], "Stockfish", (x, y), ACCENT) + self.layout.s(14)

        if session is None:
            _label(screen, fonts["body"], "—", (x, y), MUTED)
            return

        status = "Réflexion..." if session.ai_thinking else ("Pret" if session.engine.available else "Hors ligne")
        status_color = ACCENT if session.ai_thinking else (WHITE if session.engine.available else (200, 80, 70))
        lines = [
            ("Niveau", f"{session.elo} ELO"),
            ("Statut", status),
        ]
        if analysis:
            lines.extend(
                [
                    ("Evaluation", analysis.eval_text),
                    ("Profondeur", str(analysis.depth)),
                    ("Temps", f"{analysis.time_ms / 1000:.1f}s"),
                ]
            )
            if analysis.best_move:
                lines.append(("Meilleur", analysis.best_move.uci()))
        elif session.engine.error:
            lines.append(("Erreur", session.engine.error[:28]))

        for label, value in lines:
            _label(screen, fonts["small"], label, (x, y), MUTED)
            color = status_color if label == "Statut" else WHITE
            val = fonts["body"].render(str(value)[:18], True, color)
            screen.blit(val, (x, y + self.layout.s(16)))
            y += self.layout.s(44)

        # Themes rapides
        y = max(y + self.layout.s(8), rect.bottom - self.layout.s(120))
        pygame.draw.line(screen, LINE, (x, y), (rect.right - self.layout.s(16), y), 1)
        y += self.layout.s(12)
        _label(screen, fonts["small"], "Astuce: pieces / plateau", (x, y), MUTED)
        y += self.layout.s(18)
        _label(screen, fonts["small"], "via Parametres", (x, y), MUTED)

    def draw_toolbar(self, screen: pygame.Surface, buttons: dict[str, pygame.Rect], hover: str | None, font: pygame.font.Font) -> None:
        bar = self.layout.toolbar_rect()
        pygame.draw.rect(screen, (14, 12, 11), bar)
        pygame.draw.line(screen, LINE, (0, bar.y), (self.layout.width, bar.y), 1)
        for label, rect in buttons.items():
            active = hover == label
            bg = (48, 40, 30) if active else BG_SOFT
            border = ACCENT if active or label == "Nouvelle partie" else LINE
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, width=1, border_radius=8)
            text = font.render(label, True, WHITE)
            screen.blit(text, text.get_rect(center=rect.center))
