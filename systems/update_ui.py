"""Ecran de proposition / telechargement de mise a jour."""

from __future__ import annotations

import pygame

from config.settings import MUTED
from rendering.gaming_style import GOLD, GOLD_BRIGHT, GOLD_DIM, blit_stone_panel, draw_gold_accent_line, draw_ornate_corners
from rendering.render import ChessRenderer
from systems.updater import UpdateInfo, current_version_label, download_and_apply


def _wrap_lines(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    if not text.strip():
        return []
    words = text.replace("\r", "").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def prompt_for_update(screen: pygame.Surface, renderer: ChessRenderer, info: UpdateInfo) -> str:
    """Retourne 'install', 'later' ou 'quit'."""
    layout = renderer.layout
    w, h = layout.width, layout.height
    card = pygame.Rect(w // 2 - layout.s(320), h // 2 - layout.s(190), layout.s(640), layout.s(380))
    install_rect = pygame.Rect(card.centerx - layout.s(250), card.bottom - layout.s(118), layout.s(230), layout.s(52))
    later_rect = pygame.Rect(card.centerx + layout.s(20), card.bottom - layout.s(118), layout.s(230), layout.s(52))

    hover: str | None = None
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEMOTION:
                pos = event.pos
                hover = None
                if install_rect.collidepoint(pos):
                    hover = "install"
                elif later_rect.collidepoint(pos):
                    hover = "later"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if install_rect.collidepoint(event.pos):
                    return "install"
                if later_rect.collidepoint(event.pos):
                    return "later"

        renderer.screen.blit(renderer._bg, (0, 0))
        blit_stone_panel(renderer.screen, card, border_color=GOLD, inner_glow=True, seed=202)
        draw_ornate_corners(renderer.screen, card, GOLD_BRIGHT)
        draw_gold_accent_line(renderer.screen, card.y + layout.s(72), card.width, layout.s(2))

        title = renderer.title_font.render("Mise a jour disponible", True, GOLD_BRIGHT)
        renderer.screen.blit(title, title.get_rect(center=(w // 2, card.y + layout.s(42))))

        current = renderer.small_font.render(f"Version actuelle : {current_version_label()}", True, MUTED)
        renderer.screen.blit(current, current.get_rect(center=(w // 2, card.y + layout.s(96))))
        new = renderer.hud_font.render(f"Nouvelle version : {info.label}", True, GOLD_BRIGHT)
        renderer.screen.blit(new, new.get_rect(center=(w // 2, card.y + layout.s(128))))

        y = card.y + layout.s(156)
        for line in _wrap_lines(renderer.small_font, info.changelog, card.width - layout.s(48))[:4]:
            surf = renderer.small_font.render(line, True, (200, 190, 170))
            renderer.screen.blit(surf, (card.x + layout.s(24), y))
            y += layout.s(22)

        for label, rect, key, primary in (
            ("Installer maintenant", install_rect, "install", True),
            ("Plus tard", later_rect, "later", False),
        ):
            border = GOLD_BRIGHT if hover == key else GOLD_DIM
            blit_stone_panel(renderer.screen, rect, border_color=border, inner_glow=hover == key or primary, seed=hash(label) % 50)
            color = GOLD_BRIGHT if hover == key else (220, 210, 190)
            text = renderer.chip_font.render(label, True, color)
            renderer.screen.blit(text, text.get_rect(center=rect.center))

        pygame.display.flip()

    return "later"


def run_update_install(screen: pygame.Surface, renderer: ChessRenderer, info: UpdateInfo) -> tuple[bool, str]:
    def on_progress(value: float, msg: str) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit(0)
        renderer.draw_loading_screen(msg, value)
        pygame.display.flip()

    try:
        on_progress(0.0, "Demarrage de la mise a jour...")
        download_and_apply(info, on_progress=on_progress)
    except Exception as exc:  # noqa: BLE001
        on_progress(0.0, f"Echec : {exc}")
        pygame.time.wait(1800)
        return False, str(exc)

    on_progress(1.0, "Redemarrage pour finaliser...")
    pygame.time.wait(600)
    return True, ""
