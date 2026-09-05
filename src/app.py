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
from src.ui.dialogs import EndGameDialog, LoadGameDialog
from src.ui.layout import BASE_HEIGHT, BASE_WIDTH, UILayout
from src.ui.menus.main_menu import MainMenu, PauseMenu
from src.ui.panels import SidePanels
from src.ui.renderer import ChessRenderer
from src.ui.screens.bootstrap import run_bootstrap
from src.ui.shell import AppShell
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
        self.shell = AppShell(self.layout)
        self.end_dialog = EndGameDialog(self.layout)
        self.load_dialog = LoadGameDialog(self.layout)
        self.buttons = self.layout.control_buttons()
        self.state = MENU
        self.session: GameSession | None = None
        self.mode_label = ""
        self.mouse_pos: tuple[int, int] | None = None
        self.analysis_active = False
        self.show_settings_panel = False
        self._end_shown_for: str | None = None

    def bootstrap(self) -> bool:
        if not run_bootstrap(self.screen, self.renderer):
            return False
        self.audio.initialize()
        self.audio.set_enabled(self.settings.sounds_enabled)
        self.audio.set_volume(self.settings.sound_volume)
        custom = self.settings.stockfish_path or None
        ok = self.engine.start(custom_path=custom, allow_download=True)
        if ok:
            # movetime vient du preset de force (pas d'override settings fixe)
            self.engine.configure(
                self.settings.elo,
                self.settings.skill,
                self.settings.stockfish_depth,
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
        self.sidebar.sounds_enabled = self.settings.sounds_enabled
        self.sidebar.animations_enabled = self.settings.animations_enabled
        return True

    def refresh_ui(self) -> None:
        self.renderer.apply_layout(self.layout)
        self.sidebar.layout = self.layout
        self.sidebar._rebuild()
        self.panels.layout = self.layout
        self.shell.layout = self.layout
        self.main_menu.rebuild()
        self.pause_menu.rebuild()
        self.buttons = self.layout.control_buttons()

    def set_nav(self, tab_id: str) -> None:
        self.layout.active_nav = tab_id
        self.show_settings_panel = tab_id == "parametres"
        self.layout.show_right_drawer = tab_id == "parametres" and not self.layout.show_side_panels
        self.layout.show_left_drawer = tab_id in ("historique", "stats", "partie") and not self.layout.show_side_panels
        if tab_id == "sauvegardes":
            self.open_load_dialog()
        elif tab_id == "analyse" and self.session:
            self.request_analysis()
            if self.state != MENU:
                self.state = ANALYZE
        elif tab_id == "partie" and self.state == ANALYZE:
            self.state = PLAY
        self.buttons = self.layout.control_buttons()
        self.refresh_ui()
        self.audio.play("ui")

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
            self.mode_label = "Local · 1 contre 1"
        elif mode == GameMode.PVE:
            if not self.engine.available:
                self.mode_label = "Stockfish indisponible"
            else:
                side = "Blancs" if self.session.human_is_white else "Noirs"
                self.mode_label = f"vs {self.engine.engine_label} · vous = {side}"
            # Sync force réelle au démarrage
            self.engine.configure(
                self.settings.elo,
                self.settings.skill,
                self.settings.stockfish_depth,
            )
        else:
            self.mode_label = "Stockfish vs Stockfish"
            self.engine.configure(self.settings.elo, self.settings.skill, self.settings.stockfish_depth)
        self.renderer.animations.cancel()
        self.analysis_active = False
        self.end_dialog.hide()
        self._end_shown_for = None
        self.layout.active_nav = "partie"
        self.show_settings_panel = False
        self.buttons = self.layout.control_buttons()
        self.state = PLAY
        self.audio.play("ui")

    def _check_end_game(self) -> None:
        if not self.session:
            return
        board = self.session.board
        key = None
        title = subtitle = ""
        if board.is_checkmate():
            winner = self.session.black_player.display_name if board.turn() else self.session.white_player.display_name
            key = f"mate:{board.fen()}"
            title = "ÉCHEC ET MAT"
            subtitle = f"Victoire de {winner}"
        elif board.is_stalemate():
            key = f"stale:{board.fen()}"
            title, subtitle = "PAT", "Partie nulle"
        elif board.board.is_insufficient_material():
            key = f"ins:{board.fen()}"
            title, subtitle = "NULLE", "Matériel insuffisant"
        elif board.board.can_claim_fifty_moves() and board.is_game_over():
            key = f"50:{board.fen()}"
            title, subtitle = "NULLE", "Règle des 50 coups"
        elif board.board.is_fivefold_repetition() or board.board.can_claim_threefold_repetition() and board.is_game_over():
            key = f"rep:{board.fen()}"
            title, subtitle = "NULLE", "Répétition"
        elif self.session.clock.flagged_white is not None:
            loser = "Blancs" if self.session.clock.flagged_white else "Noirs"
            winner = "Noirs" if self.session.clock.flagged_white else "Blancs"
            key = f"flag:{loser}"
            title, subtitle = "TEMPS ÉCOULÉ", f"Victoire des {winner}"
        if key and key != self._end_shown_for:
            self._end_shown_for = key
            self.end_dialog.show(title, subtitle)
            if "MAT" in title:
                self.audio.play("checkmate")
            else:
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
        try:
            data = self.session.to_save_data(
                board_theme=self.settings.board_theme,
                piece_set=self.settings.piece_set,
            )
            path = self.save_mgr.save_game(data)
            # Export PGN secondaire pour compatibilité
            try:
                self.save_mgr.save_pgn(self.session.export_pgn(), path.stem + ".pgn")
            except Exception as exc:
                self.log.warning("Export PGN secondaire échoué: %s", exc)
            self.session.message = f"Partie sauvegardée : {path.name}"
            self.audio.play("ui")
        except Exception as exc:
            self.log.exception("Échec sauvegarde")
            if self.session:
                self.session.message = f"Erreur de sauvegarde : {exc}"

    def open_load_dialog(self) -> None:
        saves = self.save_mgr.list_json_saves()
        self.load_dialog.show(saves, empty_message="Aucune partie sauvegardée")
        self.audio.play("ui")

    def load_selected_save(self) -> None:
        path = self.load_dialog.selected_path()
        if path is None:
            return
        try:
            data = self.save_mgr.load_game(path)
            mode = GameMode[data.mode] if data.mode in GameMode.__members__ else GameMode.PVP
            if self.session:
                self.session.close()
            self.session = GameSession(
                mode=mode,
                elo=data.elo,
                skill=data.skill,
                time_minutes=data.time_minutes,
                time_increment=data.time_increment,
                color_preference="white" if data.human_is_white else "black",
                player_name=data.white_name if data.human_is_white else data.black_name,
                engine=self.engine,
            )
            self.session.restore_from_save(data, resume_engine=True)
            if data.board_theme:
                self.settings.board_theme = data.board_theme
                self.renderer.set_board_theme(data.board_theme)
            if data.piece_set:
                self.settings.piece_set = data.piece_set
                self.renderer.set_piece_set(data.piece_set)
            self.sidebar.sync_from_session(
                self.settings.board_theme,
                self.settings.piece_set,
                self.settings.elo if mode == GameMode.PVP else data.elo,
                data.skill,
                mode != GameMode.PVP,
                data.time_minutes,
                data.time_increment,
                self.settings.time_control_id,
            )
            self.mode_label = f"Partie chargée · {data.mode}"
            self.session.message = "Partie chargée"
            self.load_dialog.hide()
            self.end_dialog.hide()
            self._end_shown_for = None
            self.state = PLAY
            self.audio.play("ui")
        except Exception as exc:
            self.log.exception("Échec chargement")
            self.load_dialog.message = f"Impossible de charger : {exc}"

    def request_analysis(self) -> None:
        if not self.session or not self.engine.available:
            if self.session:
                self.session.message = self.engine.error or "Stockfish introuvable"
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
            self.open_load_dialog()
        elif choice == "QUITTER":
            return False
        return True

    def handle_play_click(self, pos: tuple[int, int]) -> None:
        assert self.session is not None

        if self.load_dialog.visible:
            choice = self.load_dialog.handle_click(pos)
            if choice == "Charger":
                self.load_selected_save()
            elif choice == "Annuler":
                self.load_dialog.hide()
                if self.layout.active_nav == "sauvegardes":
                    self.set_nav("partie")
            return

        shell_hit = self.shell.handle_click(pos)
        if shell_hit:
            kind, value = shell_hit
            if kind == "nav":
                self.set_nav(value)
            elif kind == "header" and value == "pause":
                self.state = PAUSE
            return

        if self.end_dialog.visible:
            choice = self.end_dialog.handle_click(pos)
            if choice == "Nouvelle partie":
                self.session.reset()
                self.session.set_time_control(self.settings.time_minutes, self.settings.time_increment)
                self.engine.configure(self.settings.elo, self.settings.skill)
                self.end_dialog.hide()
                self._end_shown_for = None
                self.renderer.animations.cancel()
            elif choice in ("Voir la partie", "Continuer"):
                self.end_dialog.hide()
            return

        for label, rect in self.buttons.items():
            if not rect.collidepoint(pos):
                continue
            disabled = self._toolbar_disabled()
            if label in disabled:
                return
            self.audio.play("ui")
            if label == "Nouvelle partie":
                self.session.reset()
                self.session.set_time_control(self.settings.time_minutes, self.settings.time_increment)
                self.engine.configure(self.settings.elo, self.settings.skill)
                self.end_dialog.hide()
                self._end_shown_for = None
                self.renderer.animations.cancel()
            elif label == "Annuler":
                self.session.undo_move()
                self.renderer.animations.cancel()
            elif label == "Refaire":
                self.session.redo_move()
            return

        # Clic historique
        nav = self.panels.handle_nav_click(pos)
        if nav == "prev" and self.session and not self.session.ai_thinking:
            self.session.undo_move()
            self.renderer.animations.cancel()
            self.audio.play("ui")
            return
        if nav == "next" and self.session and not self.session.ai_thinking:
            self.session.redo_move()
            self.audio.play("ui")
            return

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
                    self.engine.configure(value["elo"], value["skill"], self.settings.stockfish_depth)
                    self.settings.stockfish_movetime_ms = self.engine.movetime_ms
                    self.settings_mgr.update(stockfish_movetime_ms=self.engine.movetime_ms)
                    if self.session.mode != GameMode.PVP:
                        self.session.set_elo_level(value["elo"], value["skill"])
                    if self.session.mode == GameMode.PVE and self.engine.available:
                        side = "Blancs" if self.session.human_is_white else "Noirs"
                        self.mode_label = f"vs {self.engine.engine_label} · vous = {side}"
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
                    elif value == "toggle_sound":
                        self.settings.sounds_enabled = not self.settings.sounds_enabled
                        self.sidebar.sounds_enabled = self.settings.sounds_enabled
                        self.audio.set_enabled(self.settings.sounds_enabled)
                        self.settings_mgr.update(sounds_enabled=self.settings.sounds_enabled)
                        self.audio.play("ui")
                        return
                    elif value == "toggle_anim":
                        self.settings.animations_enabled = not self.settings.animations_enabled
                        self.sidebar.animations_enabled = self.settings.animations_enabled
                        self.settings_mgr.update(animations_enabled=self.settings.animations_enabled)
                        self.audio.play("ui")
                        return
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
            self._check_end_game()

    def draw_play_frame(self) -> None:
        assert self.session is not None
        analysis = self.engine.last_analysis
        nav = self.layout.active_nav

        self.renderer.draw_board(
            self.session.board,
            self.session.selected,
            self.session.legal_targets,
            self.session.last_move,
            None,
        )
        if self.settings.show_eval_bar and nav in ("partie", "analyse"):
            adv = analysis.white_advantage if analysis else None
            self.renderer.draw_eval_bar(adv)

        fonts = {
            "title": self.renderer.subtitle_font,
            "body": self.renderer.font,
            "small": self.renderer.small_font,
            "mono": self.renderer.mono_font,
            "clock": self.renderer.clock_small_font,
            "brand": self.renderer.brand_font,
            "nav": self.renderer.nav_font,
        }
        # Context panel selon onglet
        ctx = nav if nav in ("partie", "analyse", "historique", "stats") else "partie"
        self.panels.draw(self.screen, self.session, analysis, fonts, context=ctx)

        shell_fonts = {
            "brand": self.renderer.brand_font,
            "nav": self.renderer.nav_font,
            "small": self.renderer.small_font,
        }
        eng_label = self.engine.engine_label if self.engine.available else "Stockfish"
        self.shell.draw(
            self.screen,
            shell_fonts,
            engine_online=self.engine.available,
            engine_label=eng_label,
            mode_hint=self.mode_label,
        )

        self.panels.draw_toolbar(
            self.screen,
            self.buttons,
            self.renderer.hover_button,
            self.renderer.chip_font,
            disabled=self._toolbar_disabled(),
        )

        if self.session.awaiting_promotion and self.session.pending_promotion:
            self.renderer.draw_promotion_picker(self.session.pending_promotion, self.session.board)

        if self.show_settings_panel or nav == "parametres":
            # Forcer panneau droit settings
            self.renderer.draw_sidebar(self.sidebar)

        if self.session.ai_thinking:
            self.renderer.draw_thinking_banner()

        if self.end_dialog.visible:
            fonts_dlg = {
                "title": self.renderer.subtitle_font,
                "body": self.renderer.font,
                "small": self.renderer.chip_font,
            }
            self.end_dialog.draw(self.screen, fonts_dlg, self.renderer.hover_button)

        if self.load_dialog.visible:
            fonts_dlg = {
                "title": self.renderer.subtitle_font,
                "body": self.renderer.font,
                "small": self.renderer.chip_font,
            }
            self.load_dialog.draw(self.screen, fonts_dlg, self.renderer.hover_button)

    def _toolbar_disabled(self) -> set[str]:
        disabled: set[str] = set()
        if not self.session:
            return {"Annuler", "Refaire"}
        if not self.session.can_undo():
            disabled.add("Annuler")
        if not self.session.can_redo():
            disabled.add("Refaire")
        if self.session.ai_thinking:
            disabled.update({"Annuler", "Refaire"})
        return disabled

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
                        if self.load_dialog.visible:
                            self.load_dialog.scroll_by(-event.y)
                        elif self.state in (PLAY, PAUSE, ANALYZE) and self.mouse_pos and self.sidebar.contains(self.mouse_pos):
                            if self.sidebar.active_tab == "pieces":
                                self.sidebar.scroll_pieces(-event.y * self.layout.s(36))
                            elif self.sidebar.active_tab == "board":
                                self.sidebar.scroll_boards(-event.y * self.layout.s(36))
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.load_dialog.visible:
                                self.load_dialog.hide()
                            elif self.show_settings_panel or self.layout.active_nav == "parametres":
                                self.set_nav("partie")
                            elif self.state == PLAY and self.session and self.session.awaiting_promotion:
                                self.session.cancel_promotion()
                            elif self.state in (PLAY, ANALYZE):
                                self.state = PAUSE
                            elif self.state == PAUSE:
                                self.state = PLAY
                        elif event.key == pygame.K_n and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                            if self.session and self.state in (PLAY, ANALYZE):
                                self.session.reset()
                                self.session.set_time_control(self.settings.time_minutes, self.settings.time_increment)
                                self.engine.configure(self.settings.elo, self.settings.skill)
                                self.renderer.animations.cancel()
                                self.end_dialog.hide()
                        elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            if self.session and self.state in (PLAY, ANALYZE):
                                self.session.undo_move()
                                self.renderer.animations.cancel()
                        elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            if self.session and self.state in (PLAY, ANALYZE):
                                self.session.redo_move()
                        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            self.save_current()
                        elif event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            self.open_load_dialog()
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        pos = event.pos
                        self.mouse_pos = pos
                        if self.state == MENU:
                            if self.load_dialog.visible:
                                choice = self.load_dialog.handle_click(pos)
                                if choice == "Charger":
                                    self.load_selected_save()
                                elif choice == "Annuler":
                                    self.load_dialog.hide()
                            else:
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
                            elif choice == "Sauvegarder":
                                self.save_current()
                                self.state = PLAY
                            elif choice == "Charger":
                                self.state = PLAY
                                self.open_load_dialog()
                            elif choice == "Paramètres":
                                self.state = PLAY
                                self.set_nav("parametres")
                            elif choice == "Menu principal":
                                if self.session:
                                    self.session.close()
                                self.session = None
                                self.state = MENU
                        elif self.state in (PLAY, ANALYZE) and self.session:
                            self.handle_play_click(pos)

                if self.session:
                    self.session.update_clock(dt, paused=self.state not in (PLAY, ANALYZE))
                    self._check_end_game()
                    move = self.session.poll_engine()
                    if move:
                        self.trigger_anim()
                        self._check_end_game()
                        if (
                            self.engine.available
                            and not self.session.ai_thinking
                            and not self.session.board.is_game_over()
                        ):
                            self.engine.request_analysis(
                                self.session.board.board,
                                depth=12,
                                movetime_ms=200,
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
                if self.end_dialog.visible:
                    hover = self.end_dialog.buttons
                if self.load_dialog.visible:
                    hover = self.load_dialog.buttons
                self.renderer.update_hover_buttons(self.mouse_pos, hover)
                self.sidebar.update_hover(self.mouse_pos if self.state in (PLAY, PAUSE, ANALYZE) else None)
                if self.state in (PLAY, ANALYZE, PAUSE):
                    self.shell.update_hover(self.mouse_pos)

                if self.state == MENU:
                    labels = {k: self.main_menu.display_label(k) for k, _ in self.main_menu.get_options()}
                    self.renderer.draw_main_menu(self.main_menu.get_options(), labels)
                    if self.load_dialog.visible:
                        fonts_dlg = {
                            "title": self.renderer.subtitle_font,
                            "body": self.renderer.font,
                            "small": self.renderer.chip_font,
                        }
                        self.load_dialog.draw(self.screen, fonts_dlg, self.renderer.hover_button)
                elif self.state == PAUSE:
                    if self.session:
                        self.draw_play_frame()
                    self.renderer.draw_menu_overlay("PAUSE", self.pause_menu.get_options())
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
    except Exception:
        logging = __import__("logging")
        logging.getLogger("chesspro").exception("Crash application")
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Chess Pro D4",
                "Une erreur inattendue s'est produite.\nConsultez logs/chess_pro.log",
            )
            root.destroy()
        except Exception:
            pass
        return 1
    finally:
        pygame.quit()
