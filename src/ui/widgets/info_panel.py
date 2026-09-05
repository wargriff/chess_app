"""Panneau gauche : joueurs, historique, statut Stockfish."""

from __future__ import annotations

import pygame

from src.core.session import GameSession
from src.engine.uci_client import AnalysisInfo
from src.models.settings import MUTED, TEXT_COLOR
from src.ui.layout import UILayout
from src.ui.style.gaming_style import GOLD, GOLD_BRIGHT, GOLD_DIM, blit_stone_panel, draw_ornate_corners


class InfoPanel:
    def __init__(self, layout: UILayout) -> None:
        self.layout = layout
        self.scroll = 0

    def draw(
        self,
        screen: pygame.Surface,
        session: GameSession | None,
        analysis: AnalysisInfo | None,
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        rect = self.layout.left_panel_rect()
        blit_stone_panel(screen, rect, border_color=GOLD_DIM, inner_glow=True, seed=41)
        draw_ornate_corners(screen, rect, GOLD)

        x = rect.x + self.layout.s(14)
        y = rect.y + self.layout.s(14)
        title = fonts["title"].render("COMBAT", True, GOLD_BRIGHT)
        screen.blit(title, (x, y))
        y += self.layout.s(36)

        if session is None:
            screen.blit(fonts["small"].render("Aucune partie", True, MUTED), (x, y))
            return

        for player, active in (
            (session.black_player, not session.board.turn()),
            (session.white_player, session.board.turn()),
        ):
            box = pygame.Rect(x, y, rect.width - self.layout.s(28), self.layout.s(58))
            blit_stone_panel(screen, box, border_color=GOLD if active else (50, 42, 34), inner_glow=active, seed=hash(player.name) % 90)
            name = fonts["chip"].render(player.display_name[:18], True, TEXT_COLOR)
            color = fonts["small"].render(player.color_label, True, GOLD if active else MUTED)
            screen.blit(name, (box.x + self.layout.s(10), box.y + self.layout.s(8)))
            screen.blit(color, (box.x + self.layout.s(10), box.y + self.layout.s(30)))
            y += self.layout.s(66)

        y += self.layout.s(6)
        screen.blit(fonts["chip"].render("STOCKFISH", True, GOLD_BRIGHT), (x, y))
        y += self.layout.s(26)
        engine_lines = [
            f"Statut : {'Réfléchit...' if session.ai_thinking else 'Pret'}",
            f"Niveau : {session.elo} ELO",
        ]
        if analysis:
            engine_lines.extend(
                [
                    f"Eval : {analysis.eval_text}",
                    f"Profondeur : {analysis.depth}",
                    f"Noeuds : {analysis.nodes}",
                    f"Temps : {analysis.time_ms / 1000:.1f}s",
                ]
            )
            if analysis.best_move:
                engine_lines.append(f"Meilleur : {analysis.best_move}")
        elif session.engine.error:
            engine_lines.append(session.engine.error[:40])
        for line in engine_lines:
            screen.blit(fonts["small"].render(line, True, TEXT_COLOR if "Réfléchit" not in line else GOLD), (x, y))
            y += self.layout.s(18)

        y += self.layout.s(10)
        screen.blit(fonts["chip"].render("HISTORIQUE", True, GOLD_BRIGHT), (x, y))
        y += self.layout.s(24)
        sans = session.move_list_san()
        if not sans:
            screen.blit(fonts["small"].render("—", True, MUTED), (x, y))
            return
        # Affiche par paires 1. e4 e5
        pairs: list[str] = []
        i = 0
        n = 1
        while i < len(sans):
            white = sans[i]
            black = sans[i + 1] if i + 1 < len(sans) else ""
            pairs.append(f"{n}. {white} {black}".strip())
            i += 2
            n += 1
        visible = pairs[max(0, len(pairs) - 12) :]
        for line in visible:
            screen.blit(fonts["small"].render(line[:28], True, TEXT_COLOR), (x, y))
            y += self.layout.s(17)
            if y > rect.bottom - self.layout.s(20):
                break
