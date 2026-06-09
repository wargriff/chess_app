"""Génère les assets PNG du plateau et des pièces."""

from __future__ import annotations

import os
import sys

import pygame

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config.paths import BOARD_DIR, PIECES_DIR, theme_dir  # noqa: E402
from config.settings import BOARD_THEMES  # noqa: E402

SQUARE = 128
PIECE = 112


def ensure_dirs() -> None:
    os.makedirs(BOARD_DIR, exist_ok=True)
    os.makedirs(PIECES_DIR, exist_ok=True)


def draw_gradient_square(color_a, color_b) -> pygame.Surface:
    surface = pygame.Surface((SQUARE, SQUARE))
    for y in range(SQUARE):
        ratio = y / max(SQUARE - 1, 1)
        r = int(color_a[0] * (1 - ratio) + color_b[0] * ratio)
        g = int(color_a[1] * (1 - ratio) + color_b[1] * ratio)
        b = int(color_a[2] * (1 - ratio) + color_b[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (SQUARE, y))
    return surface


def draw_board_assets() -> None:
    for theme in BOARD_THEMES:
        folder = theme_dir(theme["id"])
        os.makedirs(folder, exist_ok=True)

        light = draw_gradient_square(*theme["light"])
        dark = draw_gradient_square(*theme["dark"])
        pygame.image.save(light, os.path.join(folder, "light_square.png"))
        pygame.image.save(dark, os.path.join(folder, "dark_square.png"))

        outer_color, inner_color = theme["frame"]
        frame = pygame.Surface((SQUARE * 8 + 48, SQUARE * 8 + 48), pygame.SRCALPHA)
        frame.fill((0, 0, 0, 0))
        outer = pygame.Rect(0, 0, frame.get_width(), frame.get_height())
        inner = outer.inflate(-16, -16)
        pygame.draw.rect(frame, outer_color, outer, border_radius=12)
        pygame.draw.rect(frame, inner_color, inner, 6, border_radius=8)
        pygame.draw.rect(frame, (20, 20, 20), inner.inflate(-10, -10), 2, border_radius=6)
        pygame.image.save(frame, os.path.join(folder, "frame.png"))

    # Compatibilité ancien chemin
    classic = theme_dir("classic")
    for name in ("light_square.png", "dark_square.png", "frame.png"):
        source = os.path.join(classic, name)
        target = os.path.join(BOARD_DIR, name)
        if os.path.isfile(source):
            with open(source, "rb") as src, open(target, "wb") as dst:
                dst.write(src.read())


def piece_surface(draw_fn, white: bool) -> pygame.Surface:
    surface = pygame.Surface((PIECE, PIECE), pygame.SRCALPHA)
    fill = (245, 245, 235) if white else (35, 35, 40)
    outline = (40, 40, 40) if white else (210, 210, 210)
    shadow = (0, 0, 0, 60)
    shadow_surf = pygame.Surface((PIECE, PIECE), pygame.SRCALPHA)
    draw_fn(shadow_surf, (245, 245, 235) if white else (20, 20, 24), (0, 0, 0, 80), offset=(3, 4))
    surface.blit(shadow_surf, (0, 0))
    draw_fn(surface, fill, outline, offset=(0, 0))
    return surface


def draw_pawn(s, fill, outline, offset=(0, 0)):
    ox, oy = offset
    cx, cy = PIECE // 2 + ox, PIECE // 2 + oy
    pygame.draw.ellipse(s, fill, (cx - 24, cy + 18, 48, 22))
    pygame.draw.ellipse(s, outline, (cx - 24, cy + 18, 48, 22), 2)
    pygame.draw.circle(s, fill, (cx, cy - 4), 18)
    pygame.draw.circle(s, outline, (cx, cy - 4), 18, 2)
    pygame.draw.circle(s, fill, (cx, cy - 24), 10)
    pygame.draw.circle(s, outline, (cx, cy - 24), 10, 2)


def draw_rook(s, fill, outline, offset=(0, 0)):
    ox, oy = offset
    body = pygame.Rect(ox + 28, oy + 34, 56, 44)
    top = pygame.Rect(ox + 22, oy + 18, 68, 20)
    pygame.draw.rect(s, fill, body, border_radius=4)
    pygame.draw.rect(s, outline, body, 2, border_radius=4)
    pygame.draw.rect(s, fill, top, border_radius=3)
    pygame.draw.rect(s, outline, top, 2, border_radius=3)
    for x in range(ox + 26, ox + 86, 14):
        pygame.draw.rect(s, fill, (x, oy + 10, 10, 12))
        pygame.draw.rect(s, outline, (x, oy + 10, 10, 12), 1)


def draw_knight(s, fill, outline, offset=(0, 0)):
    ox, oy = offset
    points = [
        (ox + 30, oy + 78), (ox + 34, oy + 58), (ox + 42, oy + 44),
        (ox + 38, oy + 28), (ox + 52, oy + 18), (ox + 68, oy + 24),
        (ox + 78, oy + 38), (ox + 72, oy + 52), (ox + 58, oy + 58),
        (ox + 54, oy + 68), (ox + 62, oy + 78),
    ]
    pygame.draw.polygon(s, fill, points)
    pygame.draw.polygon(s, outline, points, 2)
    pygame.draw.circle(s, outline, (ox + 58, oy + 30), 3)


def draw_bishop(s, fill, outline, offset=(0, 0)):
    ox, oy = offset
    cx = ox + PIECE // 2
    pygame.draw.ellipse(s, fill, (cx - 26, oy + 58, 52, 20))
    pygame.draw.ellipse(s, outline, (cx - 26, oy + 58, 52, 20), 2)
    pygame.draw.ellipse(s, fill, (cx - 18, oy + 28, 36, 36))
    pygame.draw.ellipse(s, outline, (cx - 18, oy + 28, 36, 36), 2)
    pygame.draw.circle(s, fill, (cx, oy + 20), 14)
    pygame.draw.circle(s, outline, (cx, oy + 20), 14, 2)
    pygame.draw.line(s, outline, (cx, oy + 34), (cx, oy + 52), 2)
    pygame.draw.circle(s, outline, (cx, oy + 12), 4, 1)


def draw_queen(s, fill, outline, offset=(0, 0)):
    ox, oy = offset
    cx = ox + PIECE // 2
    pygame.draw.ellipse(s, fill, (cx - 28, oy + 58, 56, 20))
    pygame.draw.ellipse(s, outline, (cx - 28, oy + 58, 56, 20), 2)
    pygame.draw.ellipse(s, fill, (cx - 22, oy + 30, 44, 34))
    pygame.draw.ellipse(s, outline, (cx - 22, oy + 30, 44, 34), 2)
    for dx in (-18, -6, 6, 18):
        pygame.draw.circle(s, fill, (cx + dx, oy + 18), 7)
        pygame.draw.circle(s, outline, (cx + dx, oy + 18), 7, 2)
    pygame.draw.circle(s, fill, (cx, oy + 8), 8)
    pygame.draw.circle(s, outline, (cx, oy + 8), 8, 2)


def draw_king(s, fill, outline, offset=(0, 0)):
    ox, oy = offset
    cx = ox + PIECE // 2
    pygame.draw.ellipse(s, fill, (cx - 28, oy + 58, 56, 20))
    pygame.draw.ellipse(s, outline, (cx - 28, oy + 58, 56, 20), 2)
    pygame.draw.ellipse(s, fill, (cx - 24, oy + 30, 48, 34))
    pygame.draw.ellipse(s, outline, (cx - 24, oy + 30, 48, 34), 2)
    pygame.draw.rect(s, fill, (cx - 4, oy + 6, 8, 18))
    pygame.draw.rect(s, fill, (cx - 12, oy + 12, 24, 8))
    pygame.draw.rect(s, outline, (cx - 4, oy + 6, 8, 18), 2)
    pygame.draw.rect(s, outline, (cx - 12, oy + 12, 24, 8), 2)


PIECE_DRAWERS = {
    "P": draw_pawn,
    "N": draw_knight,
    "B": draw_bishop,
    "R": draw_rook,
    "Q": draw_queen,
    "K": draw_king,
}


def draw_piece_assets() -> None:
    for symbol, drawer in PIECE_DRAWERS.items():
        white = piece_surface(drawer, True)
        black = piece_surface(drawer, False)
        pygame.image.save(white, os.path.join(PIECES_DIR, f"w{symbol}.png"))
        pygame.image.save(black, os.path.join(PIECES_DIR, f"b{symbol}.png"))


def main() -> None:
    pygame.init()
    ensure_dirs()
    draw_board_assets()
    draw_piece_assets()
    print(f"Assets générés dans {os.path.join(ROOT, 'assets')}")


if __name__ == "__main__":
    main()
