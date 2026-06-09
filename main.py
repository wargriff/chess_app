"""Point d'entrée de Chess Pro."""

from __future__ import annotations

import os
import sys

import pygame

from config.settings import DEFAULT_BOARD_THEME, DEFAULT_ELO, DEFAULT_PIECE_SET, FPS, WINDOW_HEIGHT, WINDOW_WIDTH
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


def trigger_session_move_animation(renderer: ChessRenderer, session: GameSession) -> None:
    if session.last_move is None or session.last_move_piece is None:
        return
    renderer.trigger_move_animation(
        session.last_move,
        session.last_move_piece,
        session.last_move_capture,
        session.last_captured_symbol,
    )


def main() -> None:
    os.environ.setdefault("SDL_AUDIODRIVER", "directsound")
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Chess Pro — Stockfish")
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
    piece_set = DEFAULT_PIECE_SET
    selected_elo = DEFAULT_ELO
    selected_skill = 8
    selected_level_label = "Club"
    mouse_pos: tuple[int, int] | None = None

    running = True
    try:
        while running:
            dt = clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue

                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = event.pos
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
                mouse_pos = pos

                if state == MENU:
                    choice = main_menu.handle_click(pos)
                    if choice == "Joueur vs Joueur":
                        session = GameSession(vs_ai=False)
                        sidebar.sync_from_session(board_theme, piece_set, selected_elo, selected_skill, False)
                        mode_label = build_mode_label(False, selected_elo)
                        renderer.set_board_theme(board_theme)
                        renderer.set_piece_set(piece_set)
                        renderer.animations.cancel()
                        state = PLAY
                    elif choice == "Joueur vs IA (Stockfish)":
                        session = GameSession(vs_ai=True, elo=selected_elo, skill=selected_skill)
                        sidebar.sync_from_session(board_theme, piece_set, selected_elo, selected_skill, True)
                        mode_label = build_mode_label(True, selected_elo, selected_level_label)
                        renderer.set_board_theme(board_theme)
                        renderer.set_piece_set(piece_set)
                        renderer.animations.cancel()
                        state = PLAY
                    elif choice == "Quitter":
                        running = False

                elif state == PAUSE:
                    choice = pause_menu.handle_click(pos)
                    if choice == "Reprendre":
                        state = PLAY
                    elif choice == "Nouvelle partie" and session:
                        session.reset()
                        renderer.animations.cancel()
                        state = PLAY
                    elif choice == "Menu principal":
                        if session:
                            session.close()
                        session = None
                        renderer.animations.cancel()
                        state = MENU

                elif state == PLAY and session:
                    if renderer.animations.busy:
                        continue

                    if buttons["Pause"].collidepoint(pos):
                        state = PAUSE
                        continue
                    if buttons["Rejouer"].collidepoint(pos):
                        session.reset()
                        renderer.animations.cancel()
                        continue
                    if buttons["Annuler"].collidepoint(pos):
                        session.undo_move()
                        renderer.animations.cancel()
                        continue

                    if sidebar.contains(pos):
                        action = sidebar.handle_click(pos)
                        if action:
                            kind, value = action
                            if kind == "board":
                                board_theme = value
                                renderer.set_board_theme(board_theme)
                            elif kind == "piece":
                                piece_set = value
                                renderer.set_piece_set(piece_set)
                            elif kind == "elo" and session.vs_ai:
                                selected_elo = value["elo"]
                                selected_skill = value["skill"]
                                selected_level_label = value["label"]
                                session.set_elo_level(selected_elo, selected_skill)
                                mode_label = build_mode_label(True, selected_elo, selected_level_label)
                        continue

                    if not session.can_interact():
                        continue

                    square_coords = renderer.pixel_to_square(pos)
                    if square_coords is None:
                        continue

                    row, col = square_coords
                    square = session.square_from_pixel(row, col)
                    move = session.handle_square_click(square)
                    if move:
                        trigger_session_move_animation(renderer, session)

            if session and session.pending_ai_move and not renderer.animations.busy:
                ai_move = session.consume_ai_move()
                if ai_move:
                    trigger_session_move_animation(renderer, session)

            menu_open = state in (MENU, PAUSE)
            selected = session.selected if session else None
            ai_thinking = session.ai_thinking if session else False
            renderer.animations.update(dt, selected, ai_thinking, menu_open)

            hover_buttons = buttons if state in (PLAY, PAUSE) else (
                {label: rect for label, rect in main_menu.get_options()} if state == MENU else
                {label: rect for label, rect in pause_menu.get_options()}
            )
            renderer.update_hover_buttons(mouse_pos, hover_buttons)
            sidebar.update_hover(mouse_pos if state in (PLAY, PAUSE) else None)

            if state == MENU:
                renderer.draw_menu_overlay(
                    "Chess Pro",
                    main_menu.get_options(),
                    "4 styles de pièces • Plateau • ELO en direct",
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
