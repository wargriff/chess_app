"""Dialogues UI (fin de partie, chargement sauvegardes)."""

from __future__ import annotations

import pygame

from src.services.save_manager import GameSaveMeta
from src.ui.layout import UILayout

ACCENT = (212, 165, 72)
BG = (28, 25, 22)
LINE = (70, 58, 42)
WHITE = (245, 238, 225)
MUTED = (150, 140, 125)
SOFT = (38, 34, 30)


class EndGameDialog:
    def __init__(self, layout: UILayout) -> None:
        self.layout = layout
        self.visible = False
        self.title = ""
        self.subtitle = ""
        self.buttons: dict[str, pygame.Rect] = {}
        self.card = pygame.Rect(0, 0, 0, 0)

    def show(self, title: str, subtitle: str) -> None:
        self.visible = True
        self.title = title
        self.subtitle = subtitle
        self._rebuild()

    def hide(self) -> None:
        self.visible = False

    def _rebuild(self) -> None:
        w, h = self.layout.s(420), self.layout.s(220)
        card = pygame.Rect(0, 0, w, h)
        card.center = (self.layout.width // 2, self.layout.height // 2)
        bw, bh = self.layout.s(160), self.layout.s(44)
        gap = self.layout.s(12)
        y = card.bottom - self.layout.s(28) - bh
        x0 = card.centerx - bw - gap // 2
        self.card = card
        self.buttons = {
            "Nouvelle partie": pygame.Rect(x0, y, bw, bh),
            "Voir la partie": pygame.Rect(x0 + bw + gap, y, bw, bh),
        }

    def draw(self, screen: pygame.Surface, fonts: dict[str, pygame.font.Font], hover: str | None) -> None:
        if not self.visible:
            return
        dim = pygame.Surface((self.layout.width, self.layout.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        screen.blit(dim, (0, 0))
        self._rebuild()
        pygame.draw.rect(screen, BG, self.card, border_radius=14)
        pygame.draw.rect(screen, ACCENT, self.card, width=1, border_radius=14)
        t = fonts["title"].render(self.title, True, ACCENT)
        screen.blit(t, t.get_rect(midtop=(self.card.centerx, self.card.y + self.layout.s(28))))
        s = fonts["body"].render(self.subtitle, True, WHITE)
        screen.blit(s, s.get_rect(midtop=(self.card.centerx, self.card.y + self.layout.s(78))))
        for label, rect in self.buttons.items():
            primary = label == "Nouvelle partie"
            bg = (48, 38, 28) if hover == label else (32, 28, 24)
            border = ACCENT if primary or hover == label else LINE
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, width=1, border_radius=8)
            text = fonts["small"].render(label, True, WHITE)
            screen.blit(text, text.get_rect(center=rect.center))

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        if not self.visible:
            return None
        for label, rect in self.buttons.items():
            if rect.collidepoint(pos):
                return label
        return None


class LoadGameDialog:
    """Liste des parties JSON sauvegardées."""

    def __init__(self, layout: UILayout) -> None:
        self.layout = layout
        self.visible = False
        self.saves: list[GameSaveMeta] = []
        self.selected = 0
        self.scroll = 0
        self.message = ""
        self.buttons: dict[str, pygame.Rect] = {}
        self.row_hits: list[tuple[pygame.Rect, int]] = []
        self.card = pygame.Rect(0, 0, 0, 0)

    def show(self, saves: list[GameSaveMeta], empty_message: str = "Aucune partie sauvegardée") -> None:
        self.visible = True
        self.saves = saves
        self.selected = 0
        self.scroll = 0
        self.message = empty_message if not saves else ""
        self._rebuild()

    def hide(self) -> None:
        self.visible = False

    def _rebuild(self) -> None:
        w, h = self.layout.s(560), self.layout.s(420)
        card = pygame.Rect(0, 0, w, h)
        card.center = (self.layout.width // 2, self.layout.height // 2)
        self.card = card
        bw, bh = self.layout.s(140), self.layout.s(40)
        y = card.bottom - self.layout.s(24) - bh
        self.buttons = {
            "Charger": pygame.Rect(card.centerx - bw - self.layout.s(8), y, bw, bh),
            "Annuler": pygame.Rect(card.centerx + self.layout.s(8), y, bw, bh),
        }

    def draw(self, screen: pygame.Surface, fonts: dict[str, pygame.font.Font], hover: str | None) -> None:
        if not self.visible:
            return
        dim = pygame.Surface((self.layout.width, self.layout.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        screen.blit(dim, (0, 0))
        self._rebuild()
        pygame.draw.rect(screen, BG, self.card, border_radius=14)
        pygame.draw.rect(screen, ACCENT, self.card, width=1, border_radius=14)

        title = fonts["title"].render("Charger une partie", True, ACCENT)
        screen.blit(title, title.get_rect(midtop=(self.card.centerx, self.card.y + self.layout.s(18))))

        list_top = self.card.y + self.layout.s(60)
        list_bottom = self.buttons["Charger"].y - self.layout.s(16)
        row_h = self.layout.s(54)
        max_rows = max(1, (list_bottom - list_top) // row_h)
        self.row_hits = []

        if not self.saves:
            msg = fonts["body"].render(self.message or "Aucune partie sauvegardée", True, MUTED)
            screen.blit(msg, msg.get_rect(center=(self.card.centerx, (list_top + list_bottom) // 2)))
        else:
            start = max(0, min(self.scroll, max(0, len(self.saves) - max_rows)))
            self.scroll = start
            for i, meta in enumerate(self.saves[start : start + max_rows]):
                idx = start + i
                row = pygame.Rect(
                    self.card.x + self.layout.s(20),
                    list_top + i * row_h,
                    self.card.width - self.layout.s(40),
                    row_h - self.layout.s(6),
                )
                self.row_hits.append((row, idx))
                selected = idx == self.selected
                pygame.draw.rect(screen, (52, 42, 28) if selected else SOFT, row, border_radius=8)
                pygame.draw.rect(screen, ACCENT if selected else LINE, row, width=1, border_radius=8)
                line1 = fonts["body"].render(f"{meta.label}  ·  {meta.mode}", True, WHITE)
                elo = f" · {meta.elo} ELO" if meta.elo else ""
                line2 = fonts["small"].render(
                    f"{meta.saved_at}  ·  {meta.ply} coups  ·  {meta.result}{elo}",
                    True,
                    MUTED,
                )
                screen.blit(line1, (row.x + self.layout.s(12), row.y + self.layout.s(8)))
                screen.blit(line2, (row.x + self.layout.s(12), row.y + self.layout.s(28)))

        for label, rect in self.buttons.items():
            disabled = label == "Charger" and not self.saves
            hovered = hover == label and not disabled
            bg = (48, 38, 28) if hovered else (32, 28, 24)
            border = ACCENT if (hovered or label == "Charger") and not disabled else LINE
            color = MUTED if disabled else WHITE
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, width=1, border_radius=8)
            text = fonts["small"].render(label, True, color)
            screen.blit(text, text.get_rect(center=rect.center))

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        if not self.visible:
            return None
        for rect, idx in self.row_hits:
            if rect.collidepoint(pos):
                self.selected = idx
                return "select"
        for label, rect in self.buttons.items():
            if rect.collidepoint(pos):
                if label == "Charger" and not self.saves:
                    return None
                return label
        return None

    def selected_path(self):
        if not self.saves:
            return None
        self.selected = max(0, min(self.selected, len(self.saves) - 1))
        return self.saves[self.selected].path

    def scroll_by(self, delta: int) -> None:
        if not self.saves:
            return
        self.scroll = max(0, min(len(self.saves) - 1, self.scroll + delta))
