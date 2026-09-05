"""Contrôleur principal de l'application (boucle hors main.py)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pygame

from src.core.session import GameMode, GameSession
from src.engine.stockfish_manager import StockfishManager
import chess
from src.models import version as app_version
from src.models.settings import (
    DEFAULT_BOARD_THEME,
    DEFAULT_ELO,
    DEFAULT_PIECE_SET,
    FPS,
)
from src.services.audio_manager import AudioManager
from src.services.save_manager import SaveManager
from src.services.settings_manager import SettingsManager
from src.ui.layout import BASE_HEIGHT, BASE_WIDTH, UILayout
from src.ui.menus.main_menu import MainMenu, PauseMenu
from src.ui.renderer import ChessRenderer
from src.ui.screens.bootstrap import run_bootstrap
from src.ui.panels import SidePanels
from src.ui.widgets.sidebar import GameSidebar
from src.utils.logging_setup import setup_logging
from src.utils.paths import ensure_data_dirs

MENU = "menu"
PLAY = "play"
PAUSE = "pause"
ANALYZE = "analyze"
SETTINGS = "settings"


class ChessApp:
    def __init__(self) -> None:
        ensure_data_dirs()
        self.log = setup_logging()
        self.settings_mgr = SettingsManager()
        self.settings = self.settings_mgr.load()
        self.save_mgr = SaveManager()
        self.audio = AudioManager()
        self.engine = StockfishManager()
        self.layout = UILayout(BASE_WIDTH, BASE_HEIGHT)
        self.layout.ui_scale = self.settings.ui_scale
        self.layout.piece_scale = self.settings.piece_scale
        self.screen = pygame.display.set_mode((self.layout.width, self.layout.height), pygame.RESIZABLE)
        pygame.display.set_caption(f"{app_version.APP_NAME} v{app_version.VERSION}")
        self.clock = pygame.time.Clock()
        self.renderer = ChessRenderer(self.screen, self.layout)
        self.main_menu = MainMenu(self.layout)
        self.pause_menu = PauseMenu(self.layout)
        self.sidebar = GameSidebar(self.layout)
        self.panels = SidePanels(self.layout)
        self.buttons = self.layout.control_buttons()
        self.state = MENU
        self.session: GameSession | None = None
        self.mode_label = ""
        self.mouse_pos: tuple[int, int] | None = None
        self.analysis_active = False
        self.show_settings_panel = False

    def bootstrap(self) -> bool:
        if not run_bootstrap(self.screen, self.renderer):
            return False
        self.audio.initialize()
        self.audio.set_enabled(self.settings.sounds_enabled)
        self.audio.set_volume(self.settings.sound_volume)
        custom = self.settings.stockfish_path or None
        ok = self.engine.start(custom_path=custom, allow_download=True)
        if ok:
            self.engine.configure(
                self.settings.elo,
                self.settings.skill,
                self.settings.stockfish_depth,
                self.settings.stockfish_movetime_ms,
            )
        else:
            self.log.warning("Stockfish: %s", self.engine.error)
        self.renderer.set_board_theme(self.settings.board_theme)
        self.renderer.set_piece_set(self.settings.piece_set)
        self.sidebar.sync_from_session(
            self.settings.board_theme,
            self.settings.piece_set,
            self.settings.elo,
            self.settings.skill,
            True,
            self.settings.time_minutes,
            self.settings.time_increment,
            self.settings.time_control_id,
        )
        return True

    def refresh_ui(self) -> None:
        self.renderer.apply_layout(self.layout)
        self.sidebar.layout = self.layout
        self.sidebar._rebuild()
        self.panels.layout = self.layout
        self.main_menu.rebuild()
        self.pause_menu.rebuild()
        self.buttons = self.layout.control_buttons()

    def start_game(self, mode: GameMode) -> None:
        if self.session:
            self.session.close()
        # Contre Stockfish : Blancs par defaut (preference settings)
        color = self.settings.color_preference or "white"
        self.session = GameSession(
            mode=mode,
            elo=self.settings.elo,
            skill=self.settings.skill,
            time_minutes=self.settings.time_minutes,
            time_increment=self.settings.time_increment,
            color_preference=color,
            player_name=self.settings.player_name,
            engine=self.engine,
        )
        if mode == GameMode.PVE and not self.engine.available:
            self.log.error("Partie PVE sans Stockfish: %s", self.engine.error)
            self.session.message = self.engine.error or "Stockfish introuvable"
        self.sidebar.sync_from_session(
            self.settings.board_theme,
            self.settings.piece_set,
            self.settings.elo,
            self.settings.skill,
            mode != GameMode.PVP,
            self.settings.time_minutes,
            self.settings.time_increment,
            self.settings.time_control_id,
        )
        if mode == GameMode.PVP:
            self.mode_label = "Mode : Local 1v1"
        elif mode == GameMode.PVE:
            side = "Blancs" if self.session.human_is_white else "Noirs"
            self.mode_label = f"Mode : vs Stockfish — vous jouez {side}"
        else:
            self.mode_label = "Mode : Stockfish vs Stockfish"
        self.renderer.animations.cancel()
        self.analysis_active = False
        self.state = PLAY
        self.audio.play("ui")

    def trigger_anim(self) -> None:
        if not self.session or not self.settings.animations_enabled:
            return
        if self.session.last_move is None or self.session.last_move_piece is None:
            return
        self.renderer.trigger_move_animation(
            self.session.last_move,
            self.session.last_move_piece,
            self.session.last_move_capture,
            self.session.last_captured_symbol,
            self.session.last_captured_square,
        )
        if self.session.last_move_capture:
            self.audio.play("capture")
        elif self.session.board.is_checkmate():
            self.audio.play("checkmate")
        elif self.session.board.is_check():
            self.audio.play("check")
        else:
            move = self.session.last_move
            if move and move.promotion:
                self.audio.play("promote")
            elif move and abs(move.to_square - move.from_square) in (2, 3) and self.session.last_move_piece in "Kk":
                # roi a bouge de 2 cases => roque
                files = abs(chess.square_file(move.to_square) - chess.square_file(move.from_square))
                if files == 2:
                    self.audio.play("castle")
                else:
                    self.audio.play("move")
            else:
                self.audio.play("move")

    def save_current(self) -> None:
        if not self.session:
            return
        path = self.save_mgr.save_pgn(self.session.export_pgn())
        self.session.message = f"Sauvegarde : {path.name}"
        self.audio.play("ui")

    def request_analysis(self) -> None:
        if not self.session or not self.engine.available:
            if self.session:
                self.session.message = self.engine.error or "Stockfish indisponible"
            return
        self.analysis_active = True
        self.engine.request_analysis(self.session.board.board, depth=self.settings.stockfish_depth)
        self.session.message = "Analyse Stockfish..."

    def handle_menu_choice(self, choice: str) -> bool:
        if choice == "JOUER CONTRE STOCKFISH":
            self.start_game(GameMode.PVE)
        elif choice == "JOUER EN LOCAL":
            self.start_game(GameMode.PVP)
        elif choice == "STOCKFISH VS STOCKFISH":
            self.start_game(GameMode.EVE)
        elif choice == "ANALYSE":
            self.start_game(GameMode.PVP)
            self.state = ANALYZE
            self.mode_label = "Mode : Analyse"
            self.request_analysis()
        elif choice == "PARTIES SAUVEGARDEES":
            saves = self.save_mgr.list_saves()
            if not saves:
                # reste au menu, message via caption temporaire
                pygame.display.set_caption(f"{app_version.APP_NAME} — Aucune sauvegarde")
            else:
                board, _ = self.save_mgr.load_pgn(saves[0])
                self.start_game(GameMode.PVP)
                assert self.session is not None
                self.session.board = board
                self.session.message = f"Charge : {saves[0].name}"
                self.mode_label = "Mode : Partie sauvegardee"
        elif choice == "PARAMETRES":
            self.start_game(GameMode.PVP)
            self.show_settings_panel = True
            self.mode_label = "Parametres"
        elif choice == "QUITTER":
            return False
        return True

    def handle_play_click(self, pos: tuple[int, int]) -> None:
        assert self.session is not None
        for label, rect in self.buttons.items():
            if not rect.collidepoint(pos):
                continue
            self.audio.play("ui")
            if label == "Pause":
                self.state = PAUSE
            elif label == "Nouvelle partie":
                self.session.reset()
                self.session.set_time_control(self.settings.time_minutes, self.settings.time_increment)
                self.renderer.animations.cancel()
                if self.session.mode == GameMode.PVE and self.engine.available:
                    self.engine.request_analysis(self.session.board.board, depth=12)
            elif label == "Annuler":
                self.session.undo_move()
                self.renderer.animations.cancel()
            elif label == "Refaire":
                self.session.redo_move()
            elif label == "Parametres":
                self.show_settings_panel = not self.show_settings_panel
            return

        # Clic historique
        end_ply = self.panels.handle_history_click(pos)
        if end_ply is not None and not self.session.ai_thinking:
            self.session.goto_ply(end_ply)
            self.renderer.animations.cancel()
            self.audio.play("ui")
            return

        if self.show_settings_panel and self.sidebar.contains(pos):
            action = self.sidebar.handle_click(pos)
            if action:
                kind, value = action
                if kind == "board":
                    self.settings.board_theme = value
                    self.renderer.set_board_theme(value)
                    self.settings_mgr.update(board_theme=value)
                elif kind == "piece":
                    try:
                        self.renderer.set_piece_set(value)
                        self.settings.piece_set = value
                        self.settings_mgr.update(piece_set=value)
                    except FileNotFoundError:
                        self.session.message = "Set de pieces manquant"
                elif kind == "elo":
                    self.settings.elo = value["elo"]
                    self.settings.skill = value["skill"]
                    self.settings_mgr.update(elo=value["elo"], skill=value["skill"])
                    self.engine.configure(value["elo"], value["skill"], self.settings.stockfish_depth, self.settings.stockfish_movetime_ms)
                    if self.session.mode != GameMode.PVP:
                        self.session.set_elo_level(value["elo"], value["skill"])
                elif kind == "time":
                    self.settings.time_minutes = value["minutes"]
                    self.settings.time_increment = value["increment"]
                    self.settings.time_control_id = value["id"]
                    self.settings_mgr.update(
                        time_minutes=value["minutes"],
                        time_increment=value["increment"],
                        time_control_id=value["id"],
                    )
                    self.session.set_time_control(value["minutes"], value["increment"])
                elif kind == "display":
                    if value == "ui_minus":
                        self.layout.bump_ui(-0.08)
                    elif value == "ui_plus":
                        self.layout.bump_ui(0.08)
                    elif value == "piece_minus":
                        self.layout.bump_piece(-0.06)
                    elif value == "piece_plus":
                        self.layout.bump_piece(0.06)
                    elif value == "reset_zoom":
                        self.layout.reset_zoom()
                    self.settings_mgr.update(ui_scale=self.layout.ui_scale, piece_scale=self.layout.piece_scale)
                    self.refresh_ui()
            return

        if self.session.awaiting_promotion and self.session.pending_promotion:
            picked = self.renderer.pick_promotion_at(pos, self.session.pending_promotion)
            if picked:
                move = self.session.pick_promotion(picked)
                if move:
                    self.trigger_anim()
            else:
                self.session.cancel_promotion()
            return

        if self.renderer.animations.busy or not self.session.can_interact():
            return
        coords = self.renderer.pixel_to_square(pos)
        if coords is None:
            return
        row, col = coords
        move = self.session.handle_square_click(self.session.square_from_pixel(row, col))
        if move:
            self.trigger_anim()
            # Analyse légère en arrière-plan après le coup joueur (n'interrompt pas le PLAY)
            if self.session.mode == GameMode.PVE and self.engine.available and not self.session.ai_thinking:
                pass

    def draw_play_frame(self) -> None:
        assert self.session is not None
        analysis = self.engine.last_analysis
        # clock=None : horloges dans les panneaux, pas autour du plateau
        self.renderer.draw_board(
            self.session.board,
            self.session.selected,
            self.session.legal_targets,
            self.session.last_move,
            None,
        )
        if self.settings.show_eval_bar:
            adv = analysis.white_advantage if analysis else None
            self.renderer.draw_eval_bar(adv)

        fonts = {
            "title": self.renderer.subtitle_font,
            "body": self.renderer.font,
            "small": self.renderer.small_font,
            "mono": self.renderer.chip_font,
            "clock": self.renderer.clock_small_font,
        }
        self.panels.draw(self.screen, self.session, analysis, fonts)
        hover = self.renderer.hover_button
        self.panels.draw_toolbar(self.screen, self.buttons, hover, self.renderer.chip_font)

        if self.session.awaiting_promotion and self.session.pending_promotion:
            self.renderer.draw_promotion_picker(self.session.pending_promotion, self.session.board)

        if self.show_settings_panel:
            self.renderer.draw_sidebar(self.sidebar)

        if self.session.ai_thinking:
            self.renderer.draw_thinking_banner()

        # Status compact sous le plateau
        status = self.session.message or self.session.board.status_text()
        tip = self.renderer.small_font.render(f"{self.mode_label}  ·  {status}", True, (160, 150, 135))
        ox, oy = self.layout.board_origin()
        self.screen.blit(tip, tip.get_rect(midtop=(ox + self.layout.board_pixel_size // 2, oy + self.layout.board_pixel_size + 6)))

    def run(self) -> int:
        if not self.bootstrap():
            return 0
        running = True
        try:
            while running:
                dt = self.clock.tick(FPS) / 1000.0
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self.layout.resize(event.w, event.h)
                        self.screen = pygame.display.set_mode((self.layout.width, self.layout.height), pygame.RESIZABLE)
                        self.renderer.screen = self.screen
                        self.refresh_ui()
                    elif event.type == pygame.MOUSEMOTION:
                        self.mouse_pos = event.pos
                    elif event.type == pygame.MOUSEWHEEL:
                        if self.state in (PLAY, PAUSE, ANALYZE) and self.mouse_pos and self.sidebar.contains(self.mouse_pos):
                            if self.sidebar.active_tab == "pieces":
                                self.sidebar.scroll_pieces(-event.y * self.layout.s(36))
                            elif self.sidebar.active_tab == "board":
                                self.sidebar.scroll_boards(-event.y * self.layout.s(36))
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.show_settings_panel:
                                self.show_settings_panel = False
                            elif self.state == PLAY and self.session and self.session.awaiting_promotion:
                                self.session.cancel_promotion()
                            elif self.state in (PLAY, ANALYZE):
                                self.state = PAUSE
                            elif self.state == PAUSE:
                                self.state = PLAY
                        elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            if self.session and self.state in (PLAY, ANALYZE):
                                self.session.undo_move()
                                self.renderer.animations.cancel()
                        elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            if self.session and self.state in (PLAY, ANALYZE):
                                self.session.redo_move()
                        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            self.save_current()
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        pos = event.pos
                        self.mouse_pos = pos
                        if self.state == MENU:
                            choice = self.main_menu.handle_click(pos)
                            if choice and not self.handle_menu_choice(choice):
                                running = False
                        elif self.state == PAUSE:
                            choice = self.pause_menu.handle_click(pos)
                            if choice == "Reprendre":
                                self.state = PLAY
                            elif choice == "Nouvelle partie" and self.session:
                                self.session.reset()
                                self.state = PLAY
                            elif choice == "Sauver PGN":
                                self.save_current()
                            elif choice == "Parametres":
                                self.show_settings_panel = True
                                self.state = PLAY
                            elif choice == "Menu principal":
                                if self.session:
                                    self.session.close()
                                self.session = None
                                self.state = MENU
                        elif self.state in (PLAY, ANALYZE) and self.session:
                            self.handle_play_click(pos)

                if self.session:
                    self.session.update_clock(dt, paused=self.state not in (PLAY, ANALYZE))
                    move = self.session.poll_engine()
                    if move:
                        self.trigger_anim()
                        # Eval rapide apres le coup Stockfish (ne bloque pas longtemps)
                        if self.engine.available and not self.session.ai_thinking:
                            self.engine.request_analysis(
                                self.session.board.board,
                                depth=14,
                                movetime_ms=250,
                            )

                menu_open = self.state in (MENU, PAUSE)
                self.renderer.animations.update(
                    dt,
                    self.session.selected if self.session else None,
                    self.session.ai_thinking if self.session else False,
                    menu_open,
                )
                hover = self.buttons if self.state in (PLAY, PAUSE, ANALYZE) else dict(self.main_menu.get_options())
                if self.state == PAUSE:
                    hover = dict(self.pause_menu.get_options())
                self.renderer.update_hover_buttons(self.mouse_pos, hover)
                self.sidebar.update_hover(self.mouse_pos if self.state in (PLAY, PAUSE, ANALYZE) else None)

                if self.state == MENU:
                    self.renderer.draw_main_menu(self.main_menu.get_options())
                elif self.state == PAUSE:
                    if self.session:
                        self.draw_play_frame()
                    self.renderer.draw_menu_overlay("Pause", self.pause_menu.get_options())
                elif self.state in (PLAY, ANALYZE) and self.session:
                    self.draw_play_frame()

                pygame.display.flip()
        finally:
            if self.session:
                self.session.close()
            self.engine.stop()
            self.settings_mgr.save()
        return 0


def run() -> int:
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    os.environ.setdefault("SDL_AUDIODRIVER", "directsound")
    pygame.init()
    try:
        return ChessApp().run()
    finally:
        pygame.quit()
