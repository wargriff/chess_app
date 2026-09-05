"""Utilitaires visuels style gaming (ambiance sombre, or, pierre, brouillard)."""

from __future__ import annotations

import random

import pygame

GOLD = (212, 165, 72)
GOLD_BRIGHT = (255, 215, 120)
GOLD_DIM = (120, 90, 40)
EMBER = (220, 95, 35)
BLOOD = (150, 30, 30)
STONE_DARK = (16, 14, 12)
STONE_MID = (32, 28, 24)
FOG = (80, 70, 60)


def lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def build_atmospheric_bg(width: int, height: int, sidebar_width: int = 0) -> pygame.Surface:
    """Fond degrade sombre avec vignette et lueur centrale."""
    bg = pygame.Surface((width, height))
    for y in range(height):
        ratio = y / max(height - 1, 1)
        base = lerp_color((6, 4, 3), (18, 12, 8), ratio)
        pygame.draw.line(bg, base, (0, y), (width, y))

    fog = pygame.Surface((width, height), pygame.SRCALPHA)
    cx = (width - sidebar_width) // 2
    cy = height // 2
    for radius in range(max(width, height), 0, -6):
        alpha = int(28 * (1 - radius / max(width, height)))
        if alpha > 0:
            pygame.draw.circle(fog, (40, 25, 15, alpha), (cx, cy), radius)
    bg.blit(fog, (0, 0))

    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        for x in range(0, width, 4):
            dx = abs(x - cx) / max(cx, 1)
            dy = abs(y - cy) / max(cy, 1)
            dist = min(1.0, (dx * dx + dy * dy) ** 0.5)
            alpha = int(180 * dist * dist)
            if alpha > 8:
                vignette.fill((0, 0, 0, min(200, alpha)), (x, y, 4, 1))
    bg.blit(vignette, (0, 0))
    return bg


_stone_texture_cache: dict[tuple[int, int, int], pygame.Surface] = {}


def draw_stone_texture(rect: pygame.Rect, seed: int = 0) -> pygame.Surface:
    """Texture pierre procedurale (cachee par taille)."""
    key = (rect.width, rect.height, seed)
    cached = _stone_texture_cache.get(key)
    if cached is not None:
        return cached
    surf = pygame.Surface((rect.width, rect.height))
    rng = random.Random(seed)
    base = lerp_color(STONE_DARK, STONE_MID, 0.35)
    surf.fill(base)
    for _ in range(rect.width * rect.height // 18):
        x = rng.randint(0, max(0, rect.width - 2))
        y = rng.randint(0, max(0, rect.height - 2))
        shade = rng.randint(-18, 18)
        c = tuple(max(0, min(255, base[i] + shade)) for i in range(3))
        surf.set_at((x, y), c)
    _stone_texture_cache[key] = surf
    return surf


def blit_stone_panel(
    screen: pygame.Surface,
    rect: pygame.Rect,
    *,
    border_color: tuple[int, int, int] = GOLD_DIM,
    inner_glow: bool = False,
    seed: int = 0,
) -> None:
    stone = draw_stone_texture(rect, seed)
    screen.blit(stone, rect.topleft)
    pygame.draw.rect(screen, border_color, rect, 2)
    inner = rect.inflate(-4, -4)
    pygame.draw.rect(screen, (48, 40, 32), inner, 1)
    if inner_glow:
        glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for row in range(rect.height):
            ratio = row / max(rect.height - 1, 1)
            alpha = int(30 * (1 - abs(ratio - 0.15) * 2))
            if alpha > 0:
                pygame.draw.line(glow, (GOLD[0], GOLD[1], GOLD[2], alpha), (0, row), (rect.width, row))
        screen.blit(glow, rect.topleft)


def draw_gold_accent_line(screen: pygame.Surface, y: int, width: int, height: int = 3) -> None:
    line = pygame.Surface((width, height), pygame.SRCALPHA)
    for x in range(width):
        t = x / max(width - 1, 1)
        fade = 0.35 + 0.65 * (1 - abs(t - 0.5) * 1.6)
        a = int(200 * max(0, fade))
        line.set_at((x, 0), (*GOLD, min(255, a)))
        if height > 1:
            line.set_at((x, 1), (*GOLD_DIM, min(180, int(a * 0.6))))
        if height > 2:
            line.set_at((x, 2), (60, 45, 25, min(100, int(a * 0.3))))
    screen.blit(line, (0, y))


def draw_ornate_corners(screen: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int] = GOLD) -> None:
    """Petits ornements d'angle style forge."""
    s = max(6, min(rect.width, rect.height) // 8)
    corners = (
        (rect.topleft, (1, 1)),
        (rect.topright, (-1, 1)),
        (rect.bottomleft, (1, -1)),
        (rect.bottomright, (-1, -1)),
    )
    for (cx, cy), (dx, dy) in corners:
        x = cx + (0 if dx > 0 else -s)
        y = cy + (0 if dy > 0 else -s)
        pygame.draw.line(screen, color, (x, y), (x + dx * s, y), 2)
        pygame.draw.line(screen, color, (x, y), (x, y + dy * s), 2)
        pygame.draw.circle(screen, GOLD_BRIGHT, (x + dx * (s - 2), y + dy * (s - 2)), 2)


def draw_ember_particles(screen: pygame.Surface, tick: int, count: int = 40) -> None:
    """Braises flottantes pour ecrans de chargement / menu."""
    w, h = screen.get_size()
    rng = random.Random(tick // 8)
    for i in range(count):
        seed = (tick // 4 + i * 97) % 10000
        px = (seed * 37 + tick * (3 + i % 5)) % max(w, 1)
        py = h - ((tick * (2 + i % 3) + seed * 13) % (h + 120))
        size = 2 + (seed % 3)
        alpha = 80 + (seed % 120)
        ember = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        color = EMBER if seed % 3 else GOLD
        pygame.draw.circle(ember, (*color, min(255, alpha)), (size, size), size)
        screen.blit(ember, (px, py))


def draw_fog_overlay(screen: pygame.Surface, alpha: int = 40) -> None:
    w, h = screen.get_size()
    fog = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, 2):
        ratio = y / max(h - 1, 1)
        a = int(alpha * (0.5 + 0.5 * ratio))
        pygame.draw.line(fog, (*FOG, a), (0, y), (w, y))
    screen.blit(fog, (0, 0))
