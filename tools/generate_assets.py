"""Génère les assets PNG du plateau et des pièces."""

from __future__ import annotations

import os
import sys

import pygame

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config.paths import BOARD_DIR, PIECES_DIR, piece_set_dir, theme_dir  # noqa: E402
from config.settings import BOARD_THEMES, PIECE_SETS  # noqa: E402
from tools.piece_generators import GENERATORS, build_set_preview  # noqa: E402

SQUARE = 128


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

    classic = theme_dir("classic")
    for name in ("light_square.png", "dark_square.png", "frame.png"):
        source = os.path.join(classic, name)
        target = os.path.join(BOARD_DIR, name)
        if os.path.isfile(source):
            with open(source, "rb") as src, open(target, "wb") as dst:
                dst.write(src.read())


def draw_piece_assets() -> None:
    symbols = ["P", "N", "B", "R", "Q", "K"]
    for piece_set in PIECE_SETS:
        set_id = piece_set["id"]
        generator = GENERATORS[set_id]
        folder = piece_set_dir(set_id)
        os.makedirs(folder, exist_ok=True)

        for symbol in symbols:
            white_img = generator.render(symbol, True)
            black_img = generator.render(symbol, False)
            pygame.image.save(white_img, os.path.join(folder, f"w{symbol}.png"))
            pygame.image.save(black_img, os.path.join(folder, f"b{symbol}.png"))

        preview = build_set_preview(generator)
        pygame.image.save(preview, os.path.join(folder, "preview.png"))

    staunton = piece_set_dir("staunton")
    for name in os.listdir(staunton):
        if name.endswith(".png"):
            with open(os.path.join(staunton, name), "rb") as src, open(os.path.join(PIECES_DIR, name), "wb") as dst:
                dst.write(src.read())


def main() -> None:
    pygame.init()
    ensure_dirs()
    draw_board_assets()
    draw_piece_assets()
    print(f"Assets générés : {len(PIECE_SETS)} sets de pièces distincts")


if __name__ == "__main__":
    main()
