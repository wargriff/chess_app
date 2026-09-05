"""Genere les assets PNG du plateau (textures gaming + cadres ornes)."""

from __future__ import annotations

import os
import random
import sys

import pygame

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config.paths import BOARD_DIR, PIECES_DIR, theme_dir  # noqa: E402
from config.settings import BOARD_THEMES  # noqa: E402

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


def _apply_noise(surface: pygame.Surface, strength: int, seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(SQUARE * SQUARE // 6):
        x = rng.randint(0, SQUARE - 1)
        y = rng.randint(0, SQUARE - 1)
        c = surface.get_at((x, y))
        delta = rng.randint(-strength, strength)
        surface.set_at((x, y), tuple(max(0, min(255, c[i] + delta)) for i in range(3)))


def _apply_lava_cracks(surface: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(8):
        x = rng.randint(0, SQUARE - 1)
        y = rng.randint(0, SQUARE - 1)
        color = (220, 90 + rng.randint(0, 40), 20 + rng.randint(0, 30))
        for _ in range(rng.randint(6, 14)):
            x = max(0, min(SQUARE - 1, x + rng.randint(-3, 3)))
            y = max(0, min(SQUARE - 1, y + rng.randint(-3, 3)))
            pygame.draw.circle(surface, color, (x, y), rng.randint(1, 2))


def _apply_veins(surface: pygame.Surface, seed: int, light: bool) -> None:
    rng = random.Random(seed)
    color = (255, 255, 255, 40) if light else (0, 0, 0, 50)
    overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
    for _ in range(5):
        x = rng.randint(0, SQUARE)
        y = rng.randint(0, SQUARE)
        points = [(x, y)]
        for _ in range(6):
            points.append((points[-1][0] + rng.randint(-20, 20), points[-1][1] + rng.randint(-20, 20)))
        pygame.draw.lines(overlay, color, False, points, 1)
    surface.blit(overlay, (0, 0))


def _apply_metal_brush(surface: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    for y in range(0, SQUARE, 3):
        shade = rng.randint(-12, 12)
        for x in range(SQUARE):
            c = surface.get_at((x, y))
            surface.set_at((x, y), tuple(max(0, min(255, c[i] + shade)) for i in range(3)))


def _apply_frost(surface: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
    for _ in range(30):
        x, y = rng.randint(0, SQUARE - 1), rng.randint(0, SQUARE - 1)
        pygame.draw.circle(overlay, (220, 235, 255, rng.randint(20, 60)), (x, y), rng.randint(1, 3))
    surface.blit(overlay, (0, 0))


def _apply_cracks(surface: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(4):
        x = rng.randint(0, SQUARE)
        y = rng.randint(0, SQUARE)
        points = [(x, y)]
        for _ in range(5):
            points.append((points[-1][0] + rng.randint(-25, 25), points[-1][1] + rng.randint(-25, 25)))
        pygame.draw.lines(surface, (30, 24, 18), False, points, 1)


def _apply_stone_grain(surface: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(80):
        x, y = rng.randint(0, SQUARE - 1), rng.randint(0, SQUARE - 1)
        shade = rng.randint(-18, 18)
        c = surface.get_at((x, y))
        surface.set_at((x, y), tuple(max(0, min(255, c[i] + shade)) for i in range(3)))


def _apply_moss(surface: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
    for _ in range(18):
        x, y = rng.randint(0, SQUARE - 1), rng.randint(0, SQUARE - 1)
        pygame.draw.circle(overlay, (55, 95, 48, rng.randint(35, 75)), (x, y), rng.randint(2, 6))
    surface.blit(overlay, (0, 0))


def _apply_venom(surface: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
    for _ in range(14):
        x, y = rng.randint(0, SQUARE - 1), rng.randint(0, SQUARE - 1)
        pygame.draw.circle(overlay, (90, 180, 45, rng.randint(40, 90)), (x, y), rng.randint(2, 5))
    surface.blit(overlay, (0, 0))


def _apply_crystal(surface: pygame.Surface, seed: int, light: bool) -> None:
    rng = random.Random(seed)
    overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
    color = (200, 210, 255, 55) if light else (120, 130, 200, 45)
    for _ in range(10):
        x, y = rng.randint(0, SQUARE - 1), rng.randint(0, SQUARE - 1)
        pts = [(x, y)]
        for _ in range(4):
            pts.append((pts[-1][0] + rng.randint(-12, 12), pts[-1][1] + rng.randint(-12, 12)))
        pygame.draw.lines(overlay, color, False, pts, 1)
    surface.blit(overlay, (0, 0))


def _apply_silk(surface: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
    for y in range(0, SQUARE, 6):
        alpha = rng.randint(8, 22)
        pygame.draw.line(overlay, (255, 250, 255, alpha), (0, y), (SQUARE, y), 1)
    surface.blit(overlay, (0, 0))


def _apply_sand(surface: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(120):
        x, y = rng.randint(0, SQUARE - 1), rng.randint(0, SQUARE - 1)
        c = surface.get_at((x, y))
        delta = rng.randint(-8, 8)
        surface.set_at((x, y), tuple(max(0, min(255, c[i] + delta)) for i in range(3)))


def _apply_ash(surface: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
    for _ in range(25):
        x, y = rng.randint(0, SQUARE - 1), rng.randint(0, SQUARE - 1)
        pygame.draw.circle(overlay, (180, 175, 168, rng.randint(20, 50)), (x, y), rng.randint(1, 4))
    surface.blit(overlay, (0, 0))


def draw_textured_square(theme: dict, light: bool, seed: int) -> pygame.Surface:
    colors = theme["light"] if light else theme["dark"]
    surface = draw_gradient_square(*colors)
    texture = theme.get("texture", "gradient")
    _apply_noise(surface, 10, seed)

    if texture == "lava":
        _apply_lava_cracks(surface, seed + 1)
    elif texture == "ember":
        _apply_lava_cracks(surface, seed + 2)
        overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (255, 140, 40, 35), (SQUARE // 2, SQUARE // 2), SQUARE // 3)
        surface.blit(overlay, (0, 0))
    elif texture == "gold":
        overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
        rng = random.Random(seed + 8)
        for _ in range(20):
            x, y = rng.randint(0, SQUARE - 1), rng.randint(0, SQUARE - 1)
            pygame.draw.circle(overlay, (220, 175, 60, rng.randint(25, 55)), (x, y), rng.randint(1, 3))
        surface.blit(overlay, (0, 0))
    elif texture in ("marble", "sanctified", "parchment"):
        _apply_veins(surface, seed + 3, light)
    elif texture == "metal":
        _apply_metal_brush(surface, seed + 4)
    elif texture == "frost":
        _apply_frost(surface, seed + 5)
    elif texture == "cracked":
        _apply_cracks(surface, seed + 6)
    elif texture == "blood":
        overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
        rng = random.Random(seed + 7)
        for _ in range(12):
            x, y = rng.randint(0, SQUARE - 1), rng.randint(0, SQUARE - 1)
            pygame.draw.circle(overlay, (120, 20, 20, rng.randint(30, 70)), (x, y), rng.randint(2, 5))
        surface.blit(overlay, (0, 0))
    elif texture == "scale":
        overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
        for row in range(0, SQUARE, 14):
            for col in range(0, SQUARE, 14):
                pygame.draw.arc(overlay, (0, 0, 0, 25), (col, row, 14, 14), 0, 3.14, 1)
        surface.blit(overlay, (0, 0))
    elif texture in ("fog", "void", "glass"):
        overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
        overlay.fill((80, 70, 100, 18) if texture == "void" else (100, 100, 120, 15))
        surface.blit(overlay, (0, 0))
    elif texture == "stone":
        _apply_stone_grain(surface, seed + 9)
    elif texture == "bone":
        _apply_veins(surface, seed + 10, light)
        overlay = pygame.Surface((SQUARE, SQUARE), pygame.SRCALPHA)
        overlay.fill((220, 215, 200, 12))
        surface.blit(overlay, (0, 0))
    elif texture == "moss":
        _apply_moss(surface, seed + 11)
    elif texture == "venom":
        _apply_venom(surface, seed + 12)
    elif texture == "crystal":
        _apply_crystal(surface, seed + 13, light)
    elif texture == "silk":
        _apply_silk(surface, seed + 14)
    elif texture == "sand":
        _apply_sand(surface, seed + 15)
    elif texture == "ash":
        _apply_ash(surface, seed + 16)

    return surface


def draw_ornate_frame(theme: dict) -> pygame.Surface:
    outer_color, inner_color = theme["frame"]
    size = SQUARE * 8 + 48
    frame = pygame.Surface((size, size), pygame.SRCALPHA)
    frame.fill((0, 0, 0, 0))
    outer = pygame.Rect(0, 0, size, size)
    inner = outer.inflate(-18, -18)

    pygame.draw.rect(frame, outer_color, outer, border_radius=6)
    pygame.draw.rect(frame, inner_color, inner, 5, border_radius=4)
    pygame.draw.rect(frame, (12, 10, 8), inner.inflate(-8, -8), 2, border_radius=3)

    gold = (180, 130, 50)
    gold_bright = (230, 190, 90)
    corner = 22
    for rect, flip_x, flip_y in (
        (pygame.Rect(4, 4, corner, corner), 1, 1),
        (pygame.Rect(size - corner - 4, 4, corner, corner), -1, 1),
        (pygame.Rect(4, size - corner - 4, corner, corner), 1, -1),
        (pygame.Rect(size - corner - 4, size - corner - 4, corner, corner), -1, -1),
    ):
        cx = rect.centerx
        cy = rect.centery
        pygame.draw.line(frame, gold, (cx, cy), (cx + flip_x * corner, cy), 2)
        pygame.draw.line(frame, gold, (cx, cy), (cx, cy + flip_y * corner), 2)
        pygame.draw.circle(frame, gold_bright, (cx + flip_x * (corner // 2), cy + flip_y * (corner // 2)), 3)

    mid = size // 2
    for edge_y in (10, size - 10):
        pygame.draw.line(frame, gold_dim := (100, 75, 35), (mid - 30, edge_y), (mid + 30, edge_y), 2)
    for edge_x in (10, size - 10):
        pygame.draw.line(frame, gold_dim, (edge_x, mid - 30), (edge_x, mid + 30), 2)

    return frame


def draw_board_assets() -> None:
    for index, theme in enumerate(BOARD_THEMES):
        folder = theme_dir(theme["id"])
        os.makedirs(folder, exist_ok=True)

        light = draw_textured_square(theme, True, index * 100 + 1)
        dark = draw_textured_square(theme, False, index * 100 + 2)
        pygame.image.save(light, os.path.join(folder, "light_square.png"))
        pygame.image.save(dark, os.path.join(folder, "dark_square.png"))
        pygame.image.save(draw_ornate_frame(theme), os.path.join(folder, "frame.png"))

    classic = theme_dir("sanctum")
    if not os.path.isdir(classic):
        classic = theme_dir("classic")
    for name in ("light_square.png", "dark_square.png", "frame.png"):
        source = os.path.join(classic, name)
        target = os.path.join(BOARD_DIR, name)
        if os.path.isfile(source):
            with open(source, "rb") as src, open(target, "wb") as dst:
                dst.write(src.read())


def main() -> None:
    pygame.init()
    ensure_dirs()
    draw_board_assets()
    print(f"Assets plateau generes ({len(BOARD_THEMES)} themes). Pieces : python tools/download_pieces.py")


if __name__ == "__main__":
    main()
