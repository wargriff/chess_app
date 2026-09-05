"""Style premium épuré — sans particules ni ornements."""

from __future__ import annotations

import pygame

GOLD = (212, 165, 72)
GOLD_BRIGHT = (230, 190, 110)
GOLD_DIM = (110, 85, 45)
EMBER = (180, 80, 40)
BLOOD = (150, 30, 30)
STONE_DARK = (18, 17, 16)
STONE_MID = (28, 26, 24)
PANEL = (22, 21, 20)
PANEL_SOFT = (30, 28, 26)
LINE = (48, 44, 40)
TEXT = (236, 230, 220)
MUTED = (140, 132, 120)
FOG = (60, 55, 50)


def lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def build_atmospheric_bg(width: int, height: int, sidebar_width: int = 0) -> pygame.Surface:
    """Fond anthracite sobre — sans cercles / brouillard procédural."""
    bg = pygame.Surface((width, height))
    for y in range(height):
        ratio = y / max(height - 1, 1)
        base = lerp_color((10, 10, 11), (16, 15, 14), ratio)
        pygame.draw.line(bg, base, (0, y), (width, y))
    return bg


def blit_stone_panel(
    screen: pygame.Surface,
    rect: pygame.Rect,
    *,
    border_color: tuple[int, int, int] = LINE,
    inner_glow: bool = False,
    seed: int = 0,
) -> None:
    """Panneau plat premium — plus de texture pierre ni double cadre."""
    pygame.draw.rect(screen, PANEL, rect, border_radius=8)
    if border_color:
        pygame.draw.rect(screen, border_color, rect, width=1, border_radius=8)
    if inner_glow:
        # Accent discret en haut uniquement
        accent = pygame.Rect(rect.x + 8, rect.y + 1, max(0, rect.width - 16), 1)
        pygame.draw.rect(screen, GOLD_DIM, accent)


def blit_soft_surface(screen: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int] = PANEL_SOFT) -> None:
    pygame.draw.rect(screen, color, rect, border_radius=6)


def draw_gold_accent_line(screen: pygame.Surface, y: int, width: int, height: int = 1) -> None:
    """Ligne d'accent fine (plus de dégradé lourd)."""
    pygame.draw.line(screen, GOLD_DIM, (0, y), (width, y), max(1, height))


def draw_ornate_corners(screen: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int] = GOLD) -> None:
    """No-op : ornements d'angle retirés."""
    return


def draw_ember_particles(screen: pygame.Surface, tick: int, count: int = 40) -> None:
    """No-op : particules décoratives retirées."""
    return


def draw_fog_overlay(screen: pygame.Surface, alpha: int = 40) -> None:
    """No-op : brouillard décoratif retiré."""
    return


def draw_separator(screen: pygame.Surface, x: int, y: int, width: int) -> None:
    pygame.draw.line(screen, LINE, (x, y), (x + width, y), 1)
