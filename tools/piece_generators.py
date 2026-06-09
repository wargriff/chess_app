"""Générateurs de pièces — chaque set a des silhouettes uniques (pas seulement des couleurs)."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pygame

PIECE = 128
CX = PIECE // 2
CY = PIECE // 2 + 6


def _colors(white: bool, style: dict, shadow: bool):
    if shadow:
        return (20, 20, 24, 85), (0, 0, 0, 70)
    if white:
        return style["white_fill"], style["white_edge"]
    return style["black_fill"], style["black_edge"]


class PieceSetGenerator(ABC):
    style: dict

    def render(self, symbol: str, white: bool) -> pygame.Surface:
        surface = pygame.Surface((PIECE, PIECE), pygame.SRCALPHA)
        shadow = pygame.Surface((PIECE, PIECE), pygame.SRCALPHA)
        self._draw(shadow, symbol, white, (5, 7), shadow=True)
        surface.blit(shadow, (0, 0))
        self._draw(surface, symbol, white, (0, 0), shadow=False)
        return surface

    @abstractmethod
    def _draw(self, s, symbol: str, white: bool, offset, shadow: bool) -> None: ...

    def _route(self, s, symbol, white, ox, oy, shadow):
        fn = {
            "P": self.pawn, "N": self.knight, "B": self.bishop,
            "R": self.rook, "Q": self.queen, "K": self.king,
        }[symbol]
        fn(s, white, ox, oy, shadow)

    def pawn(self, s, white, ox=0, oy=0, shadow=False): ...
    def knight(self, s, white, ox=0, oy=0, shadow=False): ...
    def bishop(self, s, white, ox=0, oy=0, shadow=False): ...
    def rook(self, s, white, ox=0, oy=0, shadow=False): ...
    def queen(self, s, white, ox=0, oy=0, shadow=False): ...
    def king(self, s, white, ox=0, oy=0, shadow=False): ...


class StauntonGenerator(PieceSetGenerator):
    style = {
        "white_fill": (248, 246, 236),
        "white_edge": (52, 52, 58),
        "black_fill": (32, 32, 38),
        "black_edge": (205, 205, 212),
    }

    def _draw(self, s, symbol, white, offset, shadow):
        self._route(s, symbol, white, offset[0], offset[1], shadow)

    def _base(self, s, cx, cy, fill, outline, w=52):
        pygame.draw.ellipse(s, fill, (cx - w // 2, cy + 14, w, 16))
        pygame.draw.ellipse(s, outline, (cx - w // 2, cy + 14, w, 16), 2)
        pygame.draw.ellipse(s, fill, (cx - w // 2 + 5, cy + 6, w - 10, 12))
        pygame.draw.ellipse(s, outline, (cx - w // 2 + 5, cy + 6, w - 10, 12), 2)

    def pawn(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._base(s, cx, cy, fill, outline, 44)
        pygame.draw.circle(s, fill, (cx, cy - 4), 16)
        pygame.draw.circle(s, outline, (cx, cy - 4), 16, 2)
        pygame.draw.circle(s, fill, (cx, cy - 24), 10)
        pygame.draw.circle(s, outline, (cx, cy - 24), 10, 2)

    def rook(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._base(s, cx, cy, fill, outline, 56)
        body = pygame.Rect(ox + 36, oy + 36, 56, 36)
        head = pygame.Rect(ox + 30, oy + 18, 68, 20)
        pygame.draw.rect(s, fill, body, border_radius=4)
        pygame.draw.rect(s, outline, body, 2, border_radius=4)
        pygame.draw.rect(s, fill, head, border_radius=3)
        pygame.draw.rect(s, outline, head, 2, border_radius=3)
        for x in range(ox + 32, ox + 96, 13):
            pygame.draw.rect(s, fill, (x, oy + 8, 10, 12))
            pygame.draw.rect(s, outline, (x, oy + 8, 10, 12), 1)

    def knight(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._base(s, cx, cy, fill, outline, 54)
        pts = [(ox + 30, oy + 80), (ox + 36, oy + 58), (ox + 40, oy + 42), (ox + 38, oy + 26),
               (ox + 52, oy + 14), (ox + 70, oy + 18), (ox + 84, oy + 32), (ox + 78, oy + 48),
               (ox + 62, oy + 56), (ox + 58, oy + 68), (ox + 68, oy + 80)]
        pygame.draw.polygon(s, fill, pts)
        pygame.draw.polygon(s, outline, pts, 2)
        pygame.draw.circle(s, outline, (ox + 64, oy + 28), 3)

    def bishop(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._base(s, cx, cy, fill, outline, 50)
        pygame.draw.polygon(s, fill, [(cx - 16, oy + 56), (cx + 16, oy + 56), (cx + 8, oy + 28), (cx - 8, oy + 28)])
        pygame.draw.polygon(s, outline, [(cx - 16, oy + 56), (cx + 16, oy + 56), (cx + 8, oy + 28), (cx - 8, oy + 28)], 2)
        pygame.draw.ellipse(s, fill, (cx - 14, oy + 22, 28, 32))
        pygame.draw.ellipse(s, outline, (cx - 14, oy + 22, 28, 32), 2)
        pygame.draw.circle(s, fill, (cx, oy + 14), 12)
        pygame.draw.circle(s, outline, (cx, oy + 14), 12, 2)
        pygame.draw.line(s, outline, (cx, oy + 28), (cx, oy + 48), 2)

    def queen(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._base(s, cx, cy, fill, outline, 56)
        pygame.draw.polygon(s, fill, [(cx - 20, oy + 56), (cx + 20, oy + 56), (cx + 14, oy + 28), (cx - 14, oy + 28)])
        pygame.draw.polygon(s, outline, [(cx - 20, oy + 56), (cx + 20, oy + 56), (cx + 14, oy + 28), (cx - 14, oy + 28)], 2)
        for dx in (-18, -6, 6, 18):
            pygame.draw.circle(s, fill, (cx + dx, oy + 16), 7)
            pygame.draw.circle(s, outline, (cx + dx, oy + 16), 7, 2)

    def king(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._base(s, cx, cy, fill, outline, 56)
        pygame.draw.polygon(s, fill, [(cx - 18, oy + 56), (cx + 18, oy + 56), (cx + 12, oy + 28), (cx - 12, oy + 28)])
        pygame.draw.polygon(s, outline, [(cx - 18, oy + 56), (cx + 18, oy + 56), (cx + 12, oy + 28), (cx - 12, oy + 28)], 2)
        pygame.draw.rect(s, fill, (cx - 4, oy + 4, 8, 18))
        pygame.draw.rect(s, fill, (cx - 12, oy + 10, 24, 7))
        pygame.draw.rect(s, outline, (cx - 4, oy + 4, 8, 18), 2)
        pygame.draw.rect(s, outline, (cx - 12, oy + 10, 24, 7), 2)


class AlphaGenerator(PieceSetGenerator):
    """Style flat type Lichess Alpha — silhouettes pleines, sans socle."""

    style = {
        "white_fill": (240, 240, 240),
        "white_edge": (30, 30, 35),
        "black_fill": (40, 44, 52),
        "black_edge": (210, 215, 225),
    }

    def _draw(self, s, symbol, white, offset, shadow):
        self._route(s, symbol, white, offset[0], offset[1], shadow)

    def pawn(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx = CX + ox
        pygame.draw.circle(s, fill, (cx, oy + 36), 14)
        pygame.draw.circle(s, outline, (cx, oy + 36), 14, 3)
        pygame.draw.circle(s, fill, (cx, oy + 18), 12)
        pygame.draw.circle(s, outline, (cx, oy + 18), 12, 3)
        pygame.draw.rect(s, fill, (cx - 18, oy + 48, 36, 10), border_radius=3)
        pygame.draw.rect(s, outline, (cx - 18, oy + 48, 36, 10), 3, border_radius=3)

    def rook(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        body = pygame.Rect(ox + 38, oy + 30, 52, 48)
        pygame.draw.rect(s, fill, body, border_radius=2)
        pygame.draw.rect(s, outline, body, 3, border_radius=2)
        for x in range(ox + 34, ox + 94, 12):
            pygame.draw.rect(s, fill, (x, oy + 14, 8, 18))
            pygame.draw.rect(s, outline, (x, oy + 14, 8, 18), 2)
        pygame.draw.rect(s, fill, (ox + 32, oy + 72, 64, 8))
        pygame.draw.rect(s, outline, (ox + 32, oy + 72, 64, 8), 2)

    def knight(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        pts = [(ox + 28, oy + 78), (ox + 32, oy + 52), (ox + 34, oy + 34), (ox + 48, oy + 18),
               (ox + 72, oy + 22), (ox + 88, oy + 40), (ox + 78, oy + 56), (ox + 58, oy + 60), (ox + 54, oy + 78)]
        pygame.draw.polygon(s, fill, pts)
        pygame.draw.polygon(s, outline, pts, 3)
        pygame.draw.line(s, outline, (ox + 52, oy + 26), (ox + 68, oy + 32), 2)

    def bishop(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx = CX + ox
        pygame.draw.polygon(s, fill, [(cx, oy + 12), (cx + 18, oy + 52), (cx - 18, oy + 52)])
        pygame.draw.polygon(s, outline, [(cx, oy + 12), (cx + 18, oy + 52), (cx - 18, oy + 52)], 3)
        pygame.draw.rect(s, fill, (cx - 22, oy + 52, 44, 12))
        pygame.draw.rect(s, outline, (cx - 22, oy + 52, 44, 12), 3)
        pygame.draw.line(s, outline, (cx, oy + 24), (cx, oy + 46), 2)
        pygame.draw.circle(s, outline, (cx, oy + 10), 5, 2)

    def queen(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx = CX + ox
        crown = [(cx, oy + 8), (cx - 22, oy + 28), (cx - 12, oy + 18), (cx, oy + 24),
                 (cx + 12, oy + 18), (cx + 22, oy + 28)]
        pygame.draw.polygon(s, fill, crown)
        pygame.draw.polygon(s, outline, crown, 3)
        pygame.draw.rect(s, fill, (cx - 20, oy + 28, 40, 34))
        pygame.draw.rect(s, outline, (cx - 20, oy + 28, 40, 34), 3)

    def king(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx = CX + ox
        pygame.draw.rect(s, fill, (cx - 18, oy + 28, 36, 34))
        pygame.draw.rect(s, outline, (cx - 18, oy + 28, 36, 34), 3)
        pygame.draw.rect(s, fill, (cx - 4, oy + 6, 8, 22))
        pygame.draw.rect(s, fill, (cx - 12, oy + 12, 24, 6))
        pygame.draw.rect(s, outline, (cx - 4, oy + 6, 8, 22), 3)
        pygame.draw.rect(s, outline, (cx - 12, oy + 12, 24, 6), 3)


class MeridaGenerator(PieceSetGenerator):
    """Style tournoi Merida — formes larges et massives."""

    style = {
        "white_fill": (255, 252, 245),
        "white_edge": (70, 55, 40),
        "black_fill": (25, 25, 28),
        "black_edge": (190, 175, 155),
    }

    def _draw(self, s, symbol, white, offset, shadow):
        self._route(s, symbol, white, offset[0], offset[1], shadow)

    def _pedestal(self, s, cx, cy, fill, outline):
        pygame.draw.ellipse(s, fill, (cx - 30, cy + 20, 60, 14))
        pygame.draw.ellipse(s, outline, (cx - 30, cy + 20, 60, 14), 2)

    def pawn(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._pedestal(s, cx, cy, fill, outline)
        pygame.draw.ellipse(s, fill, (cx - 14, cy - 6, 28, 30))
        pygame.draw.ellipse(s, outline, (cx - 14, cy - 6, 28, 30), 2)
        pygame.draw.circle(s, fill, (cx, cy - 18), 9)
        pygame.draw.circle(s, outline, (cx, cy - 18), 9, 2)

    def rook(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._pedestal(s, cx, cy, fill, outline)
        pygame.draw.rect(s, fill, (ox + 34, oy + 24, 60, 44))
        pygame.draw.rect(s, outline, (ox + 34, oy + 24, 60, 44), 2)
        for x in range(ox + 30, ox + 98, 11):
            pygame.draw.rect(s, fill, (x, oy + 10, 9, 16))
            pygame.draw.rect(s, outline, (x, oy + 10, 9, 16), 1)

    def knight(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._pedestal(s, cx, cy, fill, outline)
        pts = [(ox + 32, oy + 76), (ox + 38, oy + 54), (ox + 44, oy + 38), (ox + 56, oy + 22),
               (ox + 74, oy + 26), (ox + 86, oy + 42), (ox + 76, oy + 58), (ox + 60, oy + 64), (ox + 66, oy + 76)]
        pygame.draw.polygon(s, fill, pts)
        pygame.draw.polygon(s, outline, pts, 2)

    def bishop(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._pedestal(s, cx, cy, fill, outline)
        pygame.draw.ellipse(s, fill, (cx - 12, oy + 20, 24, 38))
        pygame.draw.ellipse(s, outline, (cx - 12, oy + 20, 24, 38), 2)
        pygame.draw.polygon(s, fill, [(cx, oy + 6), (cx + 10, oy + 18), (cx - 10, oy + 18)])
        pygame.draw.polygon(s, outline, [(cx, oy + 6), (cx + 10, oy + 18), (cx - 10, oy + 18)], 2)
        pygame.draw.line(s, outline, (cx, oy + 26), (cx, oy + 50), 2)

    def queen(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._pedestal(s, cx, cy, fill, outline)
        pygame.draw.ellipse(s, fill, (cx - 16, oy + 22, 32, 36))
        pygame.draw.ellipse(s, outline, (cx - 16, oy + 22, 32, 36), 2)
        for dx, tip in [(-14, oy + 8), (0, oy + 4), (14, oy + 8)]:
            pygame.draw.polygon(s, fill, [(cx + dx, tip), (cx + dx - 5, oy + 20), (cx + dx + 5, oy + 20)])
            pygame.draw.polygon(s, outline, [(cx + dx, tip), (cx + dx - 5, oy + 20), (cx + dx + 5, oy + 20)], 2)

    def king(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        cx, cy = CX + ox, CY + oy
        self._pedestal(s, cx, cy, fill, outline)
        pygame.draw.ellipse(s, fill, (cx - 14, oy + 22, 28, 36))
        pygame.draw.ellipse(s, outline, (cx - 14, oy + 22, 28, 36), 2)
        pygame.draw.circle(s, fill, (cx, oy + 10), 6)
        pygame.draw.circle(s, outline, (cx, oy + 10), 6, 2)
        pygame.draw.rect(s, fill, (cx - 3, oy + 2, 6, 14))
        pygame.draw.rect(s, fill, (cx - 9, oy + 6, 18, 5))
        pygame.draw.rect(s, outline, (cx - 3, oy + 2, 6, 14), 2)
        pygame.draw.rect(s, outline, (cx - 9, oy + 6, 18, 5), 2)


class PixelGenerator(PieceSetGenerator):
    """Style pixel art 8-bit — formes cubiques distinctes."""

    style = {
        "white_fill": (255, 255, 255),
        "white_edge": (80, 80, 90),
        "black_fill": (50, 50, 60),
        "black_edge": (180, 180, 190),
    }

    def _draw(self, s, symbol, white, offset, shadow):
        self._route(s, symbol, white, offset[0], offset[1], shadow)

    def _px(self, s, x, y, w, h, fill, outline, ox, oy):
        r = pygame.Rect(ox + x, oy + y, w, h)
        pygame.draw.rect(s, fill, r)
        pygame.draw.rect(s, outline, r, 1)

    def pawn(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        self._px(s, 52, 70, 24, 12, fill, outline, ox, oy)
        self._px(s, 56, 48, 16, 22, fill, outline, ox, oy)
        self._px(s, 58, 34, 12, 14, fill, outline, ox, oy)

    def rook(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        for x in range(40, 88, 12):
            self._px(s, x, 18, 8, 14, fill, outline, ox, oy)
        self._px(s, 44, 32, 40, 38, fill, outline, ox, oy)
        self._px(s, 40, 70, 48, 12, fill, outline, ox, oy)

    def knight(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        blocks = [(48, 72, 20, 10), (52, 52, 16, 20), (56, 36, 12, 16), (64, 24, 16, 12),
                  (76, 28, 12, 16), (72, 44, 14, 12), (58, 58, 12, 14), (62, 72, 14, 10)]
        for bx, by, bw, bh in blocks:
            self._px(s, bx, by, bw, bh, fill, outline, ox, oy)

    def bishop(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        self._px(s, 48, 70, 32, 12, fill, outline, ox, oy)
        self._px(s, 52, 40, 24, 30, fill, outline, ox, oy)
        self._px(s, 56, 28, 16, 12, fill, outline, ox, oy)
        self._px(s, 60, 18, 8, 10, fill, outline, ox, oy)

    def queen(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        for dx in (44, 56, 68):
            self._px(s, dx, 16, 8, 12, fill, outline, ox, oy)
        self._px(s, 50, 28, 28, 32, fill, outline, ox, oy)
        self._px(s, 46, 60, 36, 12, fill, outline, ox, oy)

    def king(self, s, white, ox=0, oy=0, shadow=False):
        fill, outline = _colors(white, self.style, shadow)
        self._px(s, 48, 70, 32, 12, fill, outline, ox, oy)
        self._px(s, 52, 36, 24, 34, fill, outline, ox, oy)
        self._px(s, 60, 14, 8, 22, fill, outline, ox, oy)
        self._px(s, 52, 20, 24, 8, fill, outline, ox, oy)


GENERATORS: dict[str, PieceSetGenerator] = {
    "staunton": StauntonGenerator(),
    "alpha": AlphaGenerator(),
    "merida": MeridaGenerator(),
    "pixel": PixelGenerator(),
}


def build_set_preview(generator: PieceSetGenerator) -> pygame.Surface:
    preview = pygame.Surface((256, 64), pygame.SRCALPHA)
    preview.fill((30, 32, 38, 255))
    pieces = [("N", True), ("Q", False), ("P", True), ("R", False)]
    for index, (symbol, white) in enumerate(pieces):
        img = generator.render(symbol, white)
        small = pygame.transform.smoothscale(img, (48, 48))
        preview.blit(small, (8 + index * 62, 8))
    pygame.draw.rect(preview, (70, 75, 85), preview.get_rect(), 2, border_radius=6)
    return preview
