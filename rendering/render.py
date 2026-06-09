from __future__ import annotations

import chess
import pygame

from config.settings import (
    ACCENT,
    ACCENT_SOFT,
    ACTIVE,
    BACKGROUND,
    BOARD_PIXEL_SIZE,
    BOARD_THEMES,
    CARD_BG,
    CHECK_COLOR,
    ELO_LEVELS,
    FRAME_PADDING,
    HUD_HEIGHT,
    MARGIN,
    MOVE_HINT_COLOR,
    MUTED,
    PANEL_BG,
    PIECE_SETS,
    SELECT_COLOR,
    SIDEBAR_WIDTH,
    SIDEBAR_X,
    SIDEBAR_Y,
    TEXT_COLOR,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from core.board import ChessBoard
from rendering.animations import AnimationManager
from rendering.assets_loader import AssetManager
from systems.sidebar import GameSidebar


class ChessRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.square_size = BOARD_PIXEL_SIZE // 8
        self.assets = AssetManager()
        self.animations = AnimationManager()
        self.font = pygame.font.SysFont("Segoe UI", 20)
        self.small_font = pygame.font.SysFont("Segoe UI", 15)
        self.chip_font = pygame.font.SysFont("Segoe UI Semibold", 14, bold=True)
        self.title_font = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.subtitle_font = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.hover_button: str | None = None
        self._bg = self._build_background()

    def _build_background(self) -> pygame.Surface:
        bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        for y in range(WINDOW_HEIGHT):
            ratio = y / max(WINDOW_HEIGHT - 1, 1)
            r = int(12 * (1 - ratio) + 6 * ratio)
            g = int(14 * (1 - ratio) + 8 * ratio)
            b = int(18 * (1 - ratio) + 14 * ratio)
            pygame.draw.line(bg, (r, g, b), (0, y), (WINDOW_WIDTH, y))
        vignette = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        cx, cy = (WINDOW_WIDTH - SIDEBAR_WIDTH) // 2, WINDOW_HEIGHT // 2
        for radius in range(420, 0, -4):
            alpha = int(18 * (1 - radius / 420))
            pygame.draw.circle(vignette, (0, 0, 0, alpha), (cx, cy), radius)
        bg.blit(vignette, (0, 0))
        return bg

    def set_board_theme(self, theme_id: str) -> None:
        self.assets.set_theme(theme_id)

    def set_piece_set(self, set_id: str) -> None:
        self.assets.set_piece_set(set_id)

    def board_origin(self) -> tuple[int, int]:
        play_width = WINDOW_WIDTH - SIDEBAR_WIDTH - MARGIN * 2
        frame = self.assets.get_frame(BOARD_PIXEL_SIZE)
        total = frame.get_width() if frame else BOARD_PIXEL_SIZE
        x = MARGIN + (play_width - total) // 2 + (FRAME_PADDING // 2 if frame else 0)
        y = MARGIN + (FRAME_PADDING // 2 if frame else 0)
        return x, y

    def square_rect(self, square: chess.Square) -> pygame.Rect:
        origin_x, origin_y = self.board_origin()
        col = chess.square_file(square)
        row = 7 - chess.square_rank(square)
        return pygame.Rect(
            origin_x + col * self.square_size,
            origin_y + row * self.square_size,
            self.square_size,
            self.square_size,
        )

    def square_center(self, square: chess.Square) -> tuple[float, float]:
        rect = self.square_rect(square)
        return float(rect.centerx), float(rect.centery)

    def pixel_to_square(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        origin_x, origin_y = self.board_origin()
        x, y = pos
        if not (origin_x <= x < origin_x + BOARD_PIXEL_SIZE and origin_y <= y < origin_y + BOARD_PIXEL_SIZE):
            return None
        col = (x - origin_x) // self.square_size
        row = (y - origin_y) // self.square_size
        return row, col

    def trigger_move_animation(
        self,
        move: chess.Move,
        piece_symbol: str,
        capture: bool,
        captured_symbol: str | None = None,
    ) -> None:
        self.animations.play_move(
            move,
            piece_symbol,
            self.square_center(move.from_square),
            self.square_center(move.to_square),
            capture,
            captured_symbol,
        )

    def _piece_size(self, selected: bool = False) -> int:
        base = self.square_size - 10
        if selected:
            base = int(base * self.animations.selection_scale())
        return base

    def _draw_piece(
        self,
        symbol: str,
        center: tuple[float, float],
        selected: bool = False,
        alpha: int = 255,
    ) -> None:
        size = self._piece_size(selected)
        cx, cy = int(center[0]), int(center[1])
        if selected:
            cy -= int(self.animations.selection_offset())

        shadow = pygame.Surface((size, size // 3), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 55), shadow.get_rect())
        self.screen.blit(shadow, shadow.get_rect(center=(cx, cy + size // 3)))

        piece_img = self.assets.get_piece(symbol, size)
        if alpha < 255:
            piece_img = piece_img.copy()
            piece_img.set_alpha(alpha)
        rect = piece_img.get_rect(center=(cx, cy))
        self.screen.blit(piece_img, rect)

    def draw_board_header(self, board: ChessBoard, status: str) -> None:
        origin_x, origin_y = self.board_origin()
        header_y = origin_y - 34
        bar_w = BOARD_PIXEL_SIZE + FRAME_PADDING
        bar_x = origin_x - FRAME_PADDING // 2

        bar = pygame.Surface((bar_w, 28), pygame.SRCALPHA)
        bar.fill((18, 20, 26, 210))
        self.screen.blit(bar, (bar_x, header_y))
        pygame.draw.line(self.screen, (45, 48, 58), (bar_x, header_y + 27), (bar_x + bar_w, header_y + 27), 1)

        turn_white = board.board.turn == chess.WHITE
        chip_text = "Trait Blancs" if turn_white else "Trait Noirs"
        chip_color = (235, 235, 240) if turn_white else ACCENT_SOFT
        chip = self.chip_font.render(chip_text, True, chip_color)
        self.screen.blit(chip, (bar_x + 12, header_y + 6))

        status_surf = self.small_font.render(status, True, MUTED)
        self.screen.blit(status_surf, status_surf.get_rect(midright=(bar_x + bar_w - 12, header_y + 14)))

    def draw_board(
        self,
        board: ChessBoard,
        selected,
        legal_targets,
        last_move,
    ) -> None:
        self.screen.blit(self._bg, (0, 0))
        origin_x, origin_y = self.board_origin()

        shadow_rect = pygame.Rect(
            origin_x - FRAME_PADDING // 2 + 8,
            origin_y - FRAME_PADDING // 2 + 10,
            BOARD_PIXEL_SIZE + FRAME_PADDING,
            BOARD_PIXEL_SIZE + FRAME_PADDING,
        )
        shadow = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 70), shadow.get_rect(), border_radius=16)
        self.screen.blit(shadow, shadow_rect.topleft)

        frame = self.assets.get_frame(BOARD_PIXEL_SIZE)
        if frame:
            self.screen.blit(frame, (origin_x - FRAME_PADDING // 2, origin_y - FRAME_PADDING // 2))

        self.draw_board_header(board, board.status_text())

        anim = self.animations.move_anim
        hidden_square = anim.move.to_square if anim and not anim.done else None

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
                self.screen.blit(self.assets.get_square(is_light, self.square_size), rect.topleft)

                if selected == chess_square:
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    overlay.fill(SELECT_COLOR)
                    self.screen.blit(overlay, rect.topleft)

                if chess_square in legal_targets:
                    center = rect.center
                    if board.piece_at(chess_square):
                        pygame.draw.circle(self.screen, ACCENT, center, self.square_size // 2 - 4, 4)
                    else:
                        hint = pygame.Surface((self.square_size // 3, self.square_size // 3), pygame.SRCALPHA)
                        pygame.draw.circle(hint, MOVE_HINT_COLOR, (hint.get_width() // 2, hint.get_height() // 2), hint.get_width() // 2)
                        self.screen.blit(hint, hint.get_rect(center=center))

                if last_move and chess_square in (last_move.from_square, last_move.to_square):
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    overlay.fill((0, 230, 118, 45))
                    self.screen.blit(overlay, rect.topleft)

                if board.is_check() and board.board.king(board.board.turn) == chess_square:
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    overlay.fill(CHECK_COLOR)
                    self.screen.blit(overlay, rect.topleft)

                if anim and anim.capture and anim.captured_symbol and chess_square == anim.move.to_square and not anim.done:
                    fade = anim.capture_alpha()
                    if fade > 0:
                        self._draw_piece(anim.captured_symbol, rect.center, alpha=fade)

                piece = board.piece_at(chess_square)
                if piece and chess_square != hidden_square:
                    is_selected = selected == chess_square
                    self._draw_piece(piece.symbol(), rect.center, selected=is_selected)

        if anim and not anim.done:
            self._draw_piece(anim.piece_symbol, anim.current_pos())

        file_labels = "abcdefgh"
        rank_labels = "87654321"
        for index in range(8):
            fx = origin_x + index * self.square_size + 6
            fy = origin_y + BOARD_PIXEL_SIZE - 18
            rx = origin_x - 16
            ry = origin_y + index * self.square_size + 6
            self.screen.blit(self.small_font.render(file_labels[index], True, MUTED), (fx, fy))
            self.screen.blit(self.small_font.render(rank_labels[index], True, MUTED), (rx, ry))

    def _draw_panel_button(
        self,
        rect: pygame.Rect,
        label: str,
        active: bool,
        hovered: bool,
        preview: pygame.Surface | None = None,
    ) -> None:
        fill = (42, 42, 48) if hovered else (34, 34, 38)
        if active:
            fill = (28, 58, 42)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        border = ACTIVE if active else (ACCENT if hovered else (60, 60, 65))
        pygame.draw.rect(self.screen, border, rect, 3 if active else 1, border_radius=8)

        text_x = rect.x + 10
        if preview is not None:
            prev = preview.get_rect(midleft=(rect.x + 8, rect.centery))
            self.screen.blit(preview, prev)
            text_x = rect.x + 44

        text = self.small_font.render(label, True, ACCENT if active else TEXT_COLOR)
        self.screen.blit(text, (text_x, rect.y + (rect.height - text.get_height()) // 2))

    def _draw_piece_card(
        self,
        rect: pygame.Rect,
        set_id: str,
        label: str,
        desc: str,
        active: bool,
        hovered: bool,
    ) -> None:
        fill = (34, 58, 44) if active else (CARD_BG if not hovered else (38, 40, 48))
        pygame.draw.rect(self.screen, fill, rect, border_radius=10)
        border = ACTIVE if active else (ACCENT if hovered else (52, 55, 65))
        pygame.draw.rect(self.screen, border, rect, 3 if active else 1, border_radius=10)

        preview = self.assets.get_piece_set_card(set_id, rect.width - 16)
        prev_rect = preview.get_rect(midtop=(rect.centerx, rect.y + 4))
        self.screen.blit(preview, prev_rect)

        if active or hovered:
            name_color = ACCENT if active else TEXT_COLOR
            name = self.chip_font.render(label, True, name_color)
            self.screen.blit(name, name.get_rect(midbottom=(rect.centerx, rect.bottom - 14)))
            sub = self.small_font.render(desc, True, MUTED if not active else ACCENT_SOFT)
            self.screen.blit(sub, sub.get_rect(midbottom=(rect.centerx, rect.bottom - 2)))
        else:
            name = self.chip_font.render(label, True, TEXT_COLOR)
            self.screen.blit(name, name.get_rect(midbottom=(rect.centerx, rect.bottom - 4)))

    def draw_sidebar(self, sidebar: GameSidebar) -> None:
        panel = sidebar.panel_rect()
        pygame.draw.rect(self.screen, PANEL_BG, panel, border_radius=16)
        pygame.draw.rect(self.screen, (48, 50, 58), panel, 2, border_radius=16)

        glow = pygame.Surface((panel.width, 40), pygame.SRCALPHA)
        glow.fill((0, 230, 118, 12))
        self.screen.blit(glow, (panel.x, panel.y))

        self.screen.blit(self.subtitle_font.render("Personnalisation", True, ACCENT), (SIDEBAR_X + 18, SIDEBAR_Y + 16))
        self.screen.blit(self.font.render("Style de pièces", True, TEXT_COLOR), (SIDEBAR_X + 18, SIDEBAR_Y + 52))

        pygame.draw.line(
            self.screen,
            (45, 48, 58),
            (SIDEBAR_X + 16, sidebar.piece_section_bottom() + 8),
            (SIDEBAR_X + panel.width - 16, sidebar.piece_section_bottom() + 8),
            1,
        )
        board_title_y = sidebar.piece_section_bottom() + 20
        self.screen.blit(self.font.render("Plateau", True, TEXT_COLOR), (SIDEBAR_X + 18, board_title_y))

        for set_id, rect in sidebar.get_piece_buttons().items():
            meta = next(s for s in PIECE_SETS if s["id"] == set_id)
            self._draw_piece_card(
                rect,
                set_id,
                meta["label"],
                meta["desc"],
                active=set_id == sidebar.piece_set,
                hovered=sidebar.is_hovered("piece", set_id),
            )

        for theme_id, rect in sidebar.get_board_buttons().items():
            label = next(t["label"] for t in BOARD_THEMES if t["id"] == theme_id)
            preview = self.assets.get_theme_preview(theme_id, 14)
            self._draw_panel_button(
                rect,
                label,
                active=theme_id == sidebar.board_theme,
                hovered=sidebar.is_hovered("board", theme_id),
                preview=preview,
            )

        if sidebar.vs_ai:
            elo_buttons = sidebar.get_elo_buttons()
            if elo_buttons:
                first = next(iter(elo_buttons.values()))
                self.screen.blit(self.font.render("Niveau ELO", True, TEXT_COLOR), (SIDEBAR_X + 18, first.y - 28))
                for elo, rect in elo_buttons.items():
                    level = next(item for item in ELO_LEVELS if item["elo"] == elo)
                    self._draw_panel_button(
                        rect,
                        f"{level['label']} • {elo}",
                        active=elo == sidebar.elo,
                        hovered=sidebar.is_hovered("elo", elo),
                    )

    def draw_hud(self, status: str, mode: str, engine: str, buttons: dict[str, pygame.Rect]) -> None:
        hud_y = WINDOW_HEIGHT - HUD_HEIGHT
        hud = pygame.Surface((WINDOW_WIDTH, HUD_HEIGHT), pygame.SRCALPHA)
        hud.fill((16, 18, 24, 245))
        self.screen.blit(hud, (0, hud_y))
        pygame.draw.line(self.screen, ACCENT_SOFT, (0, hud_y), (WINDOW_WIDTH, hud_y), 2)

        logo = self.title_font.render("Chess Pro", True, ACCENT)
        self.screen.blit(logo, (28, hud_y + 12))
        self.screen.blit(self.font.render(status, True, TEXT_COLOR), (28, hud_y + 50))
        self.screen.blit(self.small_font.render(mode, True, MUTED), (28, hud_y + 76))

        chip = pygame.Rect(360, hud_y + 68, 200, 26)
        pygame.draw.rect(self.screen, (28, 32, 40), chip, border_radius=13)
        pygame.draw.rect(self.screen, (55, 60, 72), chip, 1, border_radius=13)
        engine_text = self.chip_font.render(engine, True, ACCENT)
        self.screen.blit(engine_text, engine_text.get_rect(center=chip.center))

        info = f"{self.assets.get_piece_set_label()}  •  {self.assets.get_theme_label()}"
        info_chip = pygame.Rect(580, hud_y + 68, 260, 26)
        pygame.draw.rect(self.screen, (28, 32, 40), info_chip, border_radius=13)
        info_text = self.small_font.render(info, True, MUTED)
        self.screen.blit(info_text, info_text.get_rect(center=info_chip.center))

        for label, rect in buttons.items():
            hovered = self.hover_button == label
            fill = (42, 42, 48) if hovered else (34, 34, 34)
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, ACCENT if hovered else (80, 80, 85), rect, 2, border_radius=8)
            text = self.font.render(label, True, TEXT_COLOR)
            self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_menu_overlay(
        self,
        title: str,
        options: list[tuple[str, pygame.Rect]],
        subtitle: str = "",
    ) -> None:
        alpha = self.animations.menu_alpha()
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

        card = pygame.Rect(WINDOW_WIDTH // 2 - 280, 72, 560, 130)
        pygame.draw.rect(self.screen, (22, 24, 30), card, border_radius=16)
        pygame.draw.rect(self.screen, ACCENT_SOFT, card, 2, border_radius=16)

        title_surface = self.title_font.render(title, True, ACCENT)
        self.screen.blit(title_surface, title_surface.get_rect(center=(WINDOW_WIDTH // 2, 118)))

        if subtitle:
            subtitle_surface = self.small_font.render(subtitle, True, MUTED)
            self.screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, 158)))

        badge = self.chip_font.render("Stockfish UCI", True, ACCENT)
        badge_rect = badge.get_rect(center=(WINDOW_WIDTH // 2, 188))
        chip = badge_rect.inflate(24, 10)
        pygame.draw.rect(self.screen, (28, 32, 40), chip, border_radius=12)
        pygame.draw.rect(self.screen, (55, 60, 72), chip, 1, border_radius=12)
        self.screen.blit(badge, badge_rect)

        for label, rect in options:
            hovered = self.hover_button == label
            fill = (42, 46, 54) if hovered else (28, 30, 36)
            pygame.draw.rect(self.screen, fill, rect, border_radius=10)
            border = ACCENT if hovered else (60, 64, 74)
            pygame.draw.rect(self.screen, border, rect, 2 if hovered else 1, border_radius=10)
            text = self.subtitle_font.render(label, True, TEXT_COLOR)
            self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_thinking_banner(self) -> None:
        pulse = self.animations.think_pulse()
        color = (0, int(230 * pulse), int(118 * pulse))
        banner = self.subtitle_font.render("Stockfish réfléchit...", True, color)
        self.screen.blit(banner, banner.get_rect(center=((WINDOW_WIDTH - SIDEBAR_WIDTH) // 2, 24)))

    def update_hover_buttons(self, pos: tuple[int, int] | None, buttons: dict[str, pygame.Rect]) -> None:
        self.hover_button = None
        if pos is None:
            return
        for label, rect in buttons.items():
            if rect.collidepoint(pos):
                self.hover_button = label
                return
