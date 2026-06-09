"""Point d'entrée de Chess App."""

from __future__ import annotations

import os
import sys

import pygame

from config.settings import DEFAULT_ELO, FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from core.game import GameSession
from rendering.render import ChessRenderer
from systems.menu import EloMenu, MainMenu, PauseMenu

MENU = "menu"
ELO_SELECT = "elo_select"
PLAY = "play"
PAUSE = "pause"


def build_buttons() -> dict[str, pygame.Rect]:
    return {
        "Annuler": pygame.Rect(WINDOW_WIDTH - 390, WINDOW_HEIGHT - 88, 110, 42),
        "Rejouer": pygame.Rect(WINDOW_WIDTH - 270, WINDOW_HEIGHT - 88, 110, 42),
        "Pause": pygame.Rect(WINDOW_WIDTH - 150, WINDOW_HEIGHT - 88, 110, 42),
    }


def main() -> None:
    os.environ.setdefault("SDL_AUDIODRIVER", "directsound")
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Chess App — Stockfish")
    clock = pygame.time.Clock()

    renderer = ChessRenderer(screen)
    main_menu = MainMenu()
    elo_menu = EloMenu()
    pause_menu = PauseMenu()
    buttons = build_buttons()

    state = MENU
    session: GameSession | None = None
    mode_label = ""
    selected_elo = DEFAULT_ELO
    selected_skill = 8

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
                    elif state == ELO_SELECT:
                        state = MENU
                    continue

                if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                    continue

                pos = event.pos

                if state == MENU:
                    choice = main_menu.handle_click(pos)
                    if choice == "Joueur vs Joueur":
                        session = GameSession(vs_ai=False)
                        mode_label = "Mode : 2 joueurs"
                        state = PLAY
                    elif choice == "Joueur vs IA (Stockfish)":
                        state = ELO_SELECT
                    elif choice == "Quitter":
                        running = False

                elif state == ELO_SELECT:
                    choice = elo_menu.handle_click(pos)
                    if choice == "Retour":
                        state = MENU
                    elif choice:
                        level = elo_menu.get_level_from_label(choice)
                        if level:
                            selected_elo = level["elo"]
                            selected_skill = level["skill"]
                            session = GameSession(
                                vs_ai=True,
                                elo=selected_elo,
                                skill=selected_skill,
                            )
                            mode_label = f"Mode : vs IA — {level['label']} ({selected_elo} ELO)"
                            state = PLAY

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
                    "Plateau graphique • Stockfish • Niveaux ELO",
                )
            elif state == ELO_SELECT:
                renderer.draw_menu_overlay(
                    "Choisir le niveau ELO",
                    elo_menu.get_options(),
                    "Stockfish adapte sa force au niveau sélectionné",
                )
            elif state == PAUSE:
                if session:
                    renderer.draw_board(
                        session.board,
                        session.selected,
                        session.legal_targets,
                        session.last_move,
                    )
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
