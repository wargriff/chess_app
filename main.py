"""Point d'entrée de Chess App."""

from __future__ import annotations

import os
import sys

import pygame

from config.settings import DEFAULT_BOARD_THEME, DEFAULT_ELO, FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from core.game import GameSession
from rendering.render import ChessRenderer
from systems.menu import MainMenu, PauseMenu
from systems.sidebar import GameSidebar

MENU = "menu"
PLAY = "play"
PAUSE = "pause"


def build_buttons() -> dict[str, pygame.Rect]:
    return {
        "Annuler": pygame.Rect(WINDOW_WIDTH - 390, WINDOW_HEIGHT - 88, 110, 42),
        "Rejouer": pygame.Rect(WINDOW_WIDTH - 270, WINDOW_HEIGHT - 88, 110, 42),
        "Pause": pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 88, 110, 42),
    }


def build_mode_label(vs_ai: bool, elo: int, level_label: str | None = None) -> str:
    if not vs_ai:
        return "Mode : 2 joueurs"
    name = level_label or f"{elo} ELO"
    return f"Mode : vs IA — {name}"


def main() -> None:
    os.environ.setdefault("SDL_AUDIODRIVER", "directsound")
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Chess App — Stockfish")
    clock = pygame.time.Clock()

    renderer = ChessRenderer(screen)
    main_menu = MainMenu()
    pause_menu = PauseMenu()
    sidebar = GameSidebar()
    buttons = build_buttons()

    state = MENU
    session: GameSession | None = None
    mode_label = ""
    board_theme = DEFAULT_BOARD_THEME
    selected_elo = DEFAULT_ELO
    selected_skill = 8
    selected_level_label = "Club"

    running = True
    try:
        while running:
            clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if state == PLAY:
                        state = PAUSE
                    elif state == PAUSE:
                        state = PLAY
                    continue

                if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                    continue

                pos = event.pos

                if state == MENU:
                    choice = main_menu.handle_click(pos)
                    if choice == "Joueur vs Joueur":
                        session = GameSession(vs_ai=False)
                        sidebar.sync_from_session(board_theme, selected_elo, selected_skill, False)
                        mode_label = build_mode_label(False, selected_elo)
                        renderer.set_board_theme(board_theme)
                        state = PLAY
                    elif choice == "Joueur vs IA (Stockfish)":
                        session = GameSession(vs_ai=True, elo=selected_elo, skill=selected_skill)
                        sidebar.sync_from_session(board_theme, selected_elo, selected_skill, True)
                        mode_label = build_mode_label(True, selected_elo, selected_level_label)
                        renderer.set_board_theme(board_theme)
                        state = PLAY
                    elif choice == "Quitter":
                        running = False

                elif state == PAUSE:
                    choice = pause_menu.handle_click(pos)
                    if choice == "Reprendre":
                        state = PLAY
                    elif choice == "Nouvelle partie" and session:
                        session.reset()
                        state = PLAY
                    elif choice == "Menu principal":
                        if session:
                            session.close()
                        session = None
                        state = MENU

                elif state == PLAY and session:
                    if buttons["Pause"].collidepoint(pos):
                        state = PAUSE
                        continue
                    if buttons["Rejouer"].collidepoint(pos):
                        session.reset()
                        continue
                    if buttons["Annuler"].collidepoint(pos):
                        session.undo_move()
                        continue

                    if sidebar.contains(pos):
                        action = sidebar.handle_click(pos)
                        if action:
                            kind, value = action
                            if kind == "board":
                                board_theme = value
                                renderer.set_board_theme(board_theme)
                            elif kind == "elo" and session.vs_ai:
                                selected_elo = value["elo"]
                                selected_skill = value["skill"]
                                selected_level_label = value["label"]
                                session.set_elo_level(selected_elo, selected_skill)
                                mode_label = build_mode_label(True, selected_elo, selected_level_label)
                        continue

                    square_coords = renderer.pixel_to_square(pos)
                    if square_coords is None:
                        continue

                    row, col = square_coords
                    square = session.square_from_pixel(row, col)
                    session.handle_square_click(square)

            if state == MENU:
                renderer.draw_menu_overlay(
                    "Chess App",
                    main_menu.get_options(),
                    "Plateau et ELO modifiables pendant la partie",
                )
            elif state == PAUSE:
                if session:
                    renderer.draw_board(
                        session.board,
                        session.selected,
                        session.legal_targets,
                        session.last_move,
                    )
                    renderer.draw_sidebar(sidebar)
                    renderer.draw_hud(
                        session.message or session.board.status_text(),
                        mode_label,
                        session.engine_label,
                        buttons,
                    )
                renderer.draw_menu_overlay("Pause", pause_menu.get_options())
            elif state == PLAY and session:
                renderer.draw_board(
                    session.board,
                    session.selected,
                    session.legal_targets,
                    session.last_move,
                )
                renderer.draw_sidebar(sidebar)
                renderer.draw_hud(
                    session.message or session.board.status_text(),
                    mode_label,
                    session.engine_label,
                    buttons,
                )
                if session.ai_thinking:
                    renderer.draw_thinking_banner()

            pygame.display.flip()
    finally:
        if session:
            session.close()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
