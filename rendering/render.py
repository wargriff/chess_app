from __future__ import annotations

import chess
import pygame

from config.settings import (
    ACCENT,
    ACTIVE,
    BACKGROUND,
    BOARD_PIXEL_SIZE,
    BOARD_THEMES,
    CHECK_COLOR,
    ELO_LEVELS,
    FRAME_PADDING,
    HUD_HEIGHT,
    MARGIN,
    MOVE_HINT_COLOR,
    MUTED,
    PANEL_BG,
    SELECT_COLOR,
    SIDEBAR_WIDTH,
    SIDEBAR_X,
    SIDEBAR_Y,
    TEXT_COLOR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from core.board import ChessBoard
from rendering.assets_loader import AssetManager
from systems.sidebar import GameSidebar


class ChessRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.square_size = BOARD_PIXEL_SIZE // 8
        self.assets = AssetManager()
        self.font = pygame.font.SysFont("Segoe UI", 20)
        self.small_font = pygame.font.SysFont("Segoe UI", 17)
        self.title_font = pygame.font.SysFont("Segoe UI", 30, bold=True)
        self.subtitle_font = pygame.font.SysFont("Segoe UI", 22, bold=True)

    def set_board_theme(self, theme_id: str) -> None:
        self.assets.set_theme(theme_id)

    def board_origin(self) -> tuple[int, int]:
        play_width = WINDOW_WIDTH - SIDEBAR_WIDTH - MARGIN * 2
        frame = self.assets.get_frame(BOARD_PIXEL_SIZE)
        total = frame.get_width() if frame else BOARD_PIXEL_SIZE
        x = MARGIN + (play_width - total) // 2 + (FRAME_PADDING // 2 if frame else 0)
        y = MARGIN + (FRAME_PADDING // 2 if frame else 0)
        return x, y

    def pixel_to_square(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        origin_x, origin_y = self.board_origin()
        x, y = pos
        if not (origin_x <= x < origin_x + BOARD_PIXEL_SIZE and origin_y <= y < origin_y + BOARD_PIXEL_SIZE):
            return None
        col = (x - origin_x) // self.square_size
        row = (y - origin_y) // self.square_size
        return row, col

    def draw_board(
        self,
        board: ChessBoard,
        selected,
        legal_targets,
        last_move,
    ) -> None:
        self.screen.fill(BACKGROUND)
        origin_x, origin_y = self.board_origin()
        frame = self.assets.get_frame(BOARD_PIXEL_SIZE)
        if frame:
            frame_x = origin_x - FRAME_PADDING // 2
            frame_y = origin_y - FRAME_PADDING // 2
            self.screen.blit(frame, (frame_x, frame_y))

        for row in range(8):
            for col in range(8):
                chess_square = chess.square(col, 7 - row)
                rect = pygame.Rect(
                    origin_x + col * self.square_size,
                    origin_y + row * self.square_size,
                    self.square_size,
                    self.square_size,
                )
                is_light = (row + col) % 2 == 0
                square_img = self.assets.get_square(is_light, self.square_size)
                self.screen.blit(square_img, rect.topleft)

                if selected == chess_square:
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    overlay.fill(SELECT_COLOR)
                    self.screen.blit(overlay, rect.topleft)

                if chess_square in legal_targets:
                    center = rect.center
                    radius = self.square_size // 6
                    capture = board.piece_at(chess_square) is not None
                    if capture:
                        pygame.draw.circle(self.screen, ACCENT, center, self.square_size // 2 - 4, 4)
                    else:
                        pygame.draw.circle(self.screen, MOVE_HINT_COLOR[:3], center, radius)

                if last_move and chess_square in (last_move.from_square, last_move.to_square):
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    overlay.fill((0, 230, 118, 50))
                    self.screen.blit(overlay, rect.topleft)

                if board.is_check() and board.board.king(board.board.turn) == chess_square:
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    overlay.fill(CHECK_COLOR)
                    self.screen.blit(overlay, rect.topleft)

                piece = board.piece_at(chess_square)
                if piece:
                    piece_img = self.assets.get_piece(piece.symbol(), self.square_size - 8)
                    piece_rect = piece_img.get_rect(center=rect.center)
                    self.screen.blit(piece_img, piece_rect)

        file_labels = "abcdefgh"
        rank_labels = "87654321"
        label_y = origin_y + BOARD_PIXEL_SIZE + 8
        for index in range(8):
            file_text = self.small_font.render(file_labels[index], True, MUTED)
            rank_text = self.small_font.render(rank_labels[index], True, MUTED)
            self.screen.blit(file_text, (origin_x + index * self.square_size + 8, label_y))
            self.screen.blit(rank_text, (origin_x - 22, origin_y + index * self.square_size + 8))

    def draw_sidebar(self, sidebar: GameSidebar) -> None:
        panel = sidebar.panel_rect()
        pygame.draw.rect(self.screen, PANEL_BG, panel, border_radius=14)
        pygame.draw.rect(self.screen, (45, 45, 50), panel, 2, border_radius=14)

        title = self.subtitle_font.render("Options", True, ACCENT)
        self.screen.blit(title, (SIDEBAR_X + 16, SIDEBAR_Y + 16))

        board_title = self.font.render("Plateau", True, TEXT_COLOR)
        self.screen.blit(board_title, (SIDEBAR_X + 16, SIDEBAR_Y + 58))

        for theme_id, rect in sidebar.get_board_buttons().items():
            active = theme_id == sidebar.board_theme
            pygame.draw.rect(self.screen, (34, 34, 38), rect, border_radius=8)
            border = ACTIVE if active else (60, 60, 65)
            pygame.draw.rect(self.screen, border, rect, 3 if active else 1, border_radius=8)

            preview = self.assets.get_theme_preview(theme_id, 18)
            preview_rect = preview.get_rect(midleft=(rect.x + 8, rect.centery))
            self.screen.blit(preview, preview_rect)

            label = next(t["label"] for t in BOARD_THEMES if t["id"] == theme_id)
            text = self.small_font.render(label, True, ACCENT if active else TEXT_COLOR)
            self.screen.blit(text, (rect.x + 52, rect.y + 11))

        if sidebar.vs_ai:
            elo_buttons = sidebar.get_elo_buttons()
            if elo_buttons:
                first_rect = next(iter(elo_buttons.values()))
                elo_title_y = first_rect.y - 34
                elo_title = self.font.render("Niveau ELO (Stockfish)", True, TEXT_COLOR)
                self.screen.blit(elo_title, (SIDEBAR_X + 16, elo_title_y))

                for elo, rect in elo_buttons.items():
                    active = elo == sidebar.elo
                    level = next(item for item in ELO_LEVELS if item["elo"] == elo)
                    pygame.draw.rect(self.screen, (34, 34, 38), rect, border_radius=6)
                    border = ACTIVE if active else (60, 60, 65)
                    pygame.draw.rect(self.screen, border, rect, 3 if active else 1, border_radius=6)
                    label = f"{level['label']}  •  {elo}"
                    text = self.small_font.render(label, True, ACCENT if active else TEXT_COLOR)
                    text_rect = text.get_rect(midleft=(rect.x + 10, rect.centery))
                    self.screen.blit(text, text_rect)

    def draw_hud(self, status: str, mode: str, engine: str, buttons: dict[str, pygame.Rect]) -> None:
        hud_y = WINDOW_HEIGHT - HUD_HEIGHT
        pygame.draw.rect(self.screen, (22, 22, 22), (0, hud_y, WINDOW_WIDTH, HUD_HEIGHT))
        pygame.draw.line(self.screen, (40, 40, 40), (0, hud_y), (WINDOW_WIDTH, hud_y), 2)

        title = self.title_font.render("Chess App", True, ACCENT)
        self.screen.blit(title, (24, hud_y + 12))

        status_surface = self.font.render(status, True, TEXT_COLOR)
        self.screen.blit(status_surface, (24, hud_y + 50))

        mode_surface = self.small_font.render(mode, True, MUTED)
        self.screen.blit(mode_surface, (24, hud_y + 76))

        engine_surface = self.small_font.render(engine, True, ACCENT)
        self.screen.blit(engine_surface, (360, hud_y + 76))

        theme_surface = self.small_font.render(f"Plateau : {self.assets.get_theme_label()}", True, MUTED)
        self.screen.blit(theme_surface, (620, hud_y + 76))

        for label, rect in buttons.items():
            pygame.draw.rect(self.screen, (34, 34, 34), rect, border_radius=8)
            pygame.draw.rect(self.screen, ACCENT, rect, 2, border_radius=8)
            text = self.font.render(label, True, TEXT_COLOR)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def draw_menu_overlay(
        self,
        title: str,
        options: list[tuple[str, pygame.Rect]],
        subtitle: str = "",
    ) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        title_surface = self.title_font.render(title, True, ACCENT)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 120))
        self.screen.blit(title_surface, title_rect)

        if subtitle:
            subtitle_surface = self.small_font.render(subtitle, True, MUTED)
            subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, 158))
            self.screen.blit(subtitle_surface, subtitle_rect)

        for label, rect in options:
            pygame.draw.rect(self.screen, (28, 28, 28), rect, border_radius=10)
            pygame.draw.rect(self.screen, ACCENT, rect, 2, border_radius=10)
            text = self.subtitle_font.render(label, True, TEXT_COLOR)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def draw_thinking_banner(self) -> None:
        banner = self.subtitle_font.render("Stockfish réfléchit...", True, ACCENT)
        rect = banner.get_rect(center=((WINDOW_WIDTH - SIDEBAR_WIDTH) // 2, 24))
        self.screen.blit(banner, rect)
