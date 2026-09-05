from __future__ import annotations

import chess
import pygame

from src.core.board import ChessBoard
from src.core.clock import ChessClock
from src.models.settings import (
    ACCENT,
    ACCENT_SOFT,
    ACTIVE,
    BOARD_THEMES,
    CARD_BG,
    CHECK_COLOR,
    ELO_LEVELS,
    MOVE_HINT_COLOR,
    MUTED,
    PANEL_BG,
    PIECE_SETS,
    SELECT_COLOR,
    SIDEBAR_TABS,
    TEXT_COLOR,
    TIME_CONTROLS,
)
from src.services.asset_manager import AssetManager
from src.ui.animations import AnimationManager, castling_rook_squares
from src.ui.layout import UILayout
from src.ui.style.gaming_style import (
    EMBER,
    GOLD,
    GOLD_BRIGHT,
    GOLD_DIM,
    blit_stone_panel,
    build_atmospheric_bg,
    draw_ember_particles,
    draw_fog_overlay,
    draw_gold_accent_line,
    draw_ornate_corners,
)
from src.ui.widgets.sidebar import GameSidebar

PROMOTION_ORDER = (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)
PROMOTION_LABELS = {
    chess.QUEEN: "Dame",
    chess.ROOK: "Tour",
    chess.BISHOP: "Fou",
    chess.KNIGHT: "Cavalier",
}


class ChessRenderer:
    def __init__(self, screen: pygame.Surface, layout: UILayout) -> None:
        self.screen = screen
        self.layout = layout
        self.assets = AssetManager()
        self.animations = AnimationManager()
        self.hover_button: str | None = None
        self.promotion_hover: chess.Move | None = None
        self._load_tick = 0
        self._board_sq = 0
        self._select_overlay: pygame.Surface | None = None
        self._last_move_overlay: pygame.Surface | None = None
        self._check_overlay: pygame.Surface | None = None
        self._hint_surface: pygame.Surface | None = None
        self._board_shadow: pygame.Surface | None = None
        self._board_shadow_key: tuple[int, int, int] | None = None
        self._piece_shadow_cache: dict[int, pygame.Surface] = {}
        self._rebuild_fonts()
        self._bg = self._build_background()
        sq = layout.square_size
        self.assets.warm_board(sq, layout.piece_draw_size(), layout.piece_draw_size(True, 1.04))

    def _rebuild_fonts(self) -> None:
        s = self.layout.effective_scale
        self.font = pygame.font.SysFont("Segoe UI", max(14, int(20 * s)))
        self.small_font = pygame.font.SysFont("Segoe UI", max(12, int(15 * s)))
        self.chip_font = pygame.font.SysFont("Segoe UI Semibold", max(14, int(18 * s)), bold=True)
        self.tab_font = pygame.font.SysFont("Segoe UI Semibold", max(13, int(16 * s)), bold=True)
        self.tab_label_font = pygame.font.SysFont("Segoe UI", max(10, int(12 * s)))
        self.hud_font = pygame.font.SysFont("Segoe UI Semibold", max(18, int(28 * s)), bold=True)
        self.title_font = pygame.font.SysFont("Cambria", max(24, int(36 * s)), bold=True)
        self.subtitle_font = pygame.font.SysFont("Cambria", max(16, int(22 * s)), bold=True)
        self.clock_font = pygame.font.SysFont("Segoe UI", max(26, int(40 * s)), bold=True)
        self.clock_small_font = pygame.font.SysFont("Segoe UI Semibold", max(12, int(16 * s)), bold=True)

    def apply_layout(self, layout: UILayout) -> None:
        self.layout = layout
        self._board_sq = 0
        self._board_shadow = None
        self._board_shadow_key = None
        self._piece_shadow_cache.clear()
        self.assets.clear_scale_caches()
        self._rebuild_fonts()
        self._bg = self._build_background()
        sq = layout.square_size
        piece = layout.piece_draw_size()
        selected = layout.piece_draw_size(True, 1.04)
        self.assets.warm_board(sq, piece, selected)

    def _build_background(self) -> pygame.Surface:
        return build_atmospheric_bg(
            self.layout.width,
            self.layout.height,
            self.layout.sidebar_width,
        )

    def set_board_theme(self, theme_id: str) -> None:
        self.assets.set_theme(theme_id)

    def set_piece_set(self, set_id: str) -> None:
        self.assets.set_piece_set(set_id)

    def board_origin(self) -> tuple[int, int]:
        return self.layout.board_origin()

    def square_rect(self, square: chess.Square) -> pygame.Rect:
        origin_x, origin_y = self.board_origin()
        sq = self.layout.square_size
        col = chess.square_file(square)
        row = 7 - chess.square_rank(square)
        return pygame.Rect(origin_x + col * sq, origin_y + row * sq, sq, sq)

    def square_center(self, square: chess.Square) -> tuple[float, float]:
        rect = self.square_rect(square)
        return float(rect.centerx), float(rect.centery)

    def pixel_to_square(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        origin_x, origin_y = self.board_origin()
        board_size = self.layout.board_pixel_size
        sq = self.layout.square_size
        x, y = pos
        if not (origin_x <= x < origin_x + board_size and origin_y <= y < origin_y + board_size):
            return None
        col = (x - origin_x) // sq
        row = (y - origin_y) // sq
        return row, col

    def trigger_move_animation(
        self,
        move: chess.Move,
        piece_symbol: str,
        capture: bool,
        captured_symbol: str | None = None,
        captured_square: chess.Square | None = None,
    ) -> None:
        sq = self.layout.square_size
        size = self.layout.piece_draw_size()
        self.assets.get_piece(piece_symbol, size)
        if capture and captured_symbol:
            self.assets.get_piece(captured_symbol, size)

        rook_symbol = None
        rook_from = None
        rook_to = None
        rook_hidden = None
        castling = castling_rook_squares(move)
        if castling is not None:
            rook_from_sq, rook_to_sq = castling
            rook_color = chess.WHITE if piece_symbol.isupper() else chess.BLACK
            rook_symbol = chess.Piece(chess.ROOK, rook_color).symbol()
            self.assets.get_piece(rook_symbol, size)
            rook_from = self.square_center(rook_from_sq)
            rook_to = self.square_center(rook_to_sq)
            rook_hidden = rook_to_sq

        self.animations.play_move(
            move,
            piece_symbol,
            self.square_center(move.from_square),
            self.square_center(move.to_square),
            capture,
            captured_symbol,
            capture_square=captured_square,
            rook_symbol=rook_symbol,
            rook_from=rook_from,
            rook_to=rook_to,
            rook_hidden=rook_hidden,
            square_size=sq,
        )

    def _piece_shadow(self, size: int) -> pygame.Surface:
        cached = self._piece_shadow_cache.get(size)
        if cached is not None:
            return cached
        shadow_h = max(4, size // 3)
        shadow = pygame.Surface((size, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 55), shadow.get_rect())
        self._piece_shadow_cache[size] = shadow
        return shadow

    def _ensure_board_buffers(self, sq: int) -> None:
        if self._board_sq == sq:
            return
        self._board_sq = sq
        self._select_overlay = pygame.Surface((sq, sq), pygame.SRCALPHA)
        self._select_overlay.fill(SELECT_COLOR)
        self._last_move_overlay = pygame.Surface((sq, sq), pygame.SRCALPHA)
        self._last_move_overlay.fill((212, 165, 72, 50))
        self._check_overlay = pygame.Surface((sq, sq), pygame.SRCALPHA)
        self._check_overlay.fill(CHECK_COLOR)
        hint_d = max(6, sq // 3)
        self._hint_surface = pygame.Surface((hint_d, hint_d), pygame.SRCALPHA)
        pygame.draw.circle(
            self._hint_surface,
            MOVE_HINT_COLOR,
            (hint_d // 2, hint_d // 2),
            hint_d // 2,
        )

    def _board_drop_shadow(self, width: int, height: int, radius: int) -> pygame.Surface:
        key = (width, height, radius)
        if self._board_shadow is not None and self._board_shadow_key == key:
            return self._board_shadow
        shadow = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 70), shadow.get_rect(), border_radius=radius)
        self._board_shadow = shadow
        self._board_shadow_key = key
        return shadow

    def _draw_piece(
        self,
        symbol: str,
        center: tuple[float, float],
        selected: bool = False,
        alpha: int = 255,
    ) -> None:
        sel_mul = self.animations.selection_scale() if selected else 1.0
        size = self.layout.piece_draw_size(selected, sel_mul)
        cx, cy = int(center[0]), int(center[1])
        if selected:
            cy -= int(self.animations.selection_offset())

        shadow = self._piece_shadow(size)
        self.screen.blit(shadow, shadow.get_rect(center=(cx, cy + size // 3)))

        piece_img = self.assets.get_piece(symbol, size, alpha=alpha)
        self.screen.blit(piece_img, piece_img.get_rect(center=(cx, cy)))

    def _draw_clock_box(
        self,
        rect: pygame.Rect,
        label: str,
        time_text: str,
        active: bool,
        low_time: bool,
    ) -> None:
        seed = hash(label) % 1000
        border = GOLD if active and not low_time else GOLD_DIM
        if low_time:
            border = (220, 70, 55) if active else (150, 55, 45)
        blit_stone_panel(self.screen, rect, border_color=border, inner_glow=active, seed=seed)
        draw_ornate_corners(self.screen, rect, GOLD_BRIGHT if active else GOLD_DIM)

        ox, oy = self.board_origin()
        board_size = self.layout.board_pixel_size
        board_center_x = ox + board_size // 2
        if label == "Noirs":
            pygame.draw.line(self.screen, GOLD_DIM, (board_center_x, rect.bottom), (board_center_x, oy), 1)
        else:
            pygame.draw.line(
                self.screen,
                GOLD_DIM,
                (board_center_x, rect.y),
                (board_center_x, oy + board_size),
                1,
            )

        name = self.clock_small_font.render(label, True, MUTED if not active else ACCENT_SOFT)
        self.screen.blit(name, name.get_rect(midtop=(rect.centerx, rect.y + self.layout.s(6))))
        color = (255, 220, 210) if low_time else (TEXT_COLOR if not active else GOLD_BRIGHT)
        clock = self.clock_font.render(time_text, True, color)
        self.screen.blit(clock, clock.get_rect(center=(rect.centerx, rect.centery + self.layout.s(6))))

    def draw_clocks(self, clock: ChessClock, active_white: bool) -> None:
        if not clock.enabled:
            return
        black_rect = self.layout.black_clock_rect()
        white_rect = self.layout.white_clock_rect()
        self._draw_clock_box(
            black_rect,
            "Noirs",
            clock.format_time(clock.black_seconds),
            active=not active_white,
            low_time=clock.is_low_time(clock.black_seconds),
        )
        self._draw_clock_box(
            white_rect,
            "Blancs",
            clock.format_time(clock.white_seconds),
            active=active_white,
            low_time=clock.is_low_time(clock.white_seconds),
        )

    def draw_board_header(self, board: ChessBoard, status: str) -> None:
        header = self.layout.board_header_rect()
        blit_stone_panel(self.screen, header, border_color=GOLD_DIM, seed=42)
        draw_gold_accent_line(self.screen, header.bottom - self.layout.s(2), header.width, self.layout.s(2))

        turn_white = board.board.turn == chess.WHITE
        chip_text = "Trait aux Blancs" if turn_white else "Trait aux Noirs"
        chip_color = GOLD_BRIGHT if turn_white else ACCENT_SOFT
        chip = self.chip_font.render(chip_text, True, chip_color)
        self.screen.blit(chip, chip.get_rect(midleft=(header.x + self.layout.s(14), header.centery)))
        status_surf = self.small_font.render(status, True, MUTED)
        self.screen.blit(status_surf, status_surf.get_rect(midright=(header.right - self.layout.s(14), header.centery)))

    def draw_board(
        self,
        board: ChessBoard,
        selected,
        legal_targets,
        last_move,
        clock: ChessClock | None = None,
    ) -> None:
        self.screen.blit(self._bg, (0, 0))
        origin_x, origin_y = self.board_origin()
        board_size = self.layout.board_pixel_size
        sq = self.layout.square_size
        pad = self.layout.frame_padding

        shadow_rect = pygame.Rect(
            origin_x - pad // 2 + self.layout.s(8),
            origin_y - pad // 2 + self.layout.s(10),
            board_size + pad,
            board_size + pad,
        )
        shadow = self._board_drop_shadow(shadow_rect.width, shadow_rect.height, self.layout.s(16))
        self.screen.blit(shadow, shadow_rect.topleft)
        self._ensure_board_buffers(sq)

        frame = self.assets.get_frame(board_size)
        if frame:
            # Cadre leger : reduit l'effet "tableau de bord"
            scaled = pygame.transform.smoothscale(frame, (board_size + pad, board_size + pad))
            self.screen.blit(scaled, (origin_x - pad // 2, origin_y - pad // 2))
        else:
            pygame.draw.rect(
                self.screen,
                (90, 70, 40),
                pygame.Rect(origin_x - 2, origin_y - 2, board_size + 4, board_size + 4),
                width=2,
                border_radius=4,
            )

        anim = self.animations.move_anim
        hidden_squares: set[chess.Square] = set()
        if anim and not anim.done:
            hidden_squares = {slide.hidden_square for slide in anim.slides}

        for row in range(8):
            for col in range(8):
                chess_square = chess.square(col, 7 - row)
                rect = pygame.Rect(origin_x + col * sq, origin_y + row * sq, sq, sq)
                is_light = (row + col) % 2 == 0
                self.screen.blit(self.assets.get_square(is_light, sq), rect.topleft)

                if selected == chess_square and self._select_overlay is not None:
                    self.screen.blit(self._select_overlay, rect.topleft)

                if chess_square in legal_targets:
                    center = rect.center
                    if board.piece_at(chess_square):
                        pygame.draw.circle(self.screen, ACCENT, center, sq // 2 - 4, 4)
                    elif self._hint_surface is not None:
                        self.screen.blit(self._hint_surface, self._hint_surface.get_rect(center=center))

                if last_move and chess_square in (last_move.from_square, last_move.to_square) and self._last_move_overlay is not None:
                    self.screen.blit(self._last_move_overlay, rect.topleft)

                if board.is_check() and board.board.king(board.board.turn) == chess_square and self._check_overlay is not None:
                    self.screen.blit(self._check_overlay, rect.topleft)

                if (
                    anim
                    and anim.capture
                    and anim.captured_symbol
                    and chess_square == anim.capture_square
                    and not anim.done
                ):
                    fade = anim.capture_alpha()
                    if fade > 0:
                        self._draw_piece(anim.captured_symbol, rect.center, alpha=fade)

                piece = board.piece_at(chess_square)
                if piece and chess_square not in hidden_squares:
                    self._draw_piece(piece.symbol(), rect.center, selected=selected == chess_square)

        if anim and not anim.done:
            for slide in anim.slides:
                self._draw_piece(slide.symbol, slide.position_at(anim.progress(), anim.lift_px))

        if clock is not None:
            self.draw_clocks(clock, board.board.turn == chess.WHITE)

        file_labels = "abcdefgh"
        rank_labels = "87654321"
        for index in range(8):
            fx = origin_x + index * sq + self.layout.s(6)
            fy = origin_y + board_size - self.layout.s(18)
            rx = origin_x - self.layout.s(16)
            ry = origin_y + index * sq + self.layout.s(6)
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
        r = self.layout.s(8)
        border = GOLD if active else (GOLD_DIM if hovered else (55, 48, 38))
        blit_stone_panel(self.screen, rect, border_color=border, inner_glow=active, seed=hash(label) % 500)
        if active:
            draw_ornate_corners(self.screen, rect, GOLD_BRIGHT)

        text_x = rect.x + self.layout.s(10)
        if preview is not None:
            prev = preview.get_rect(midleft=(rect.x + self.layout.s(8), rect.centery))
            self.screen.blit(preview, prev)
            text_x = rect.x + self.layout.s(44)

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
        r = self.layout.s(12)
        pygame.draw.rect(self.screen, fill, rect, border_radius=r)
        border = ACTIVE if active else (ACCENT if hovered else (52, 55, 65))
        pygame.draw.rect(self.screen, border, rect, 3 if active else 1, border_radius=r)

        max_prev_h = int(rect.height * 0.34)
        preview_w = max(self.layout.s(72), int((rect.width - self.layout.s(32)) * 0.72))
        preview = self.assets.get_piece_set_card(set_id, preview_w)
        if preview.get_height() > max_prev_h:
            ratio = max_prev_h / preview.get_height()
            preview = pygame.transform.smoothscale(
                preview,
                (max(1, int(preview.get_width() * ratio)), max_prev_h),
            )
        prev_rect = preview.get_rect(midtop=(rect.centerx, rect.y + self.layout.s(8)))
        self.screen.blit(preview, prev_rect)

        name_color = ACCENT if active else TEXT_COLOR
        name = self.chip_font.render(label, True, name_color)
        self.screen.blit(name, name.get_rect(midtop=(rect.centerx, prev_rect.bottom + self.layout.s(6))))
        sub_color = ACCENT_SOFT if active else MUTED
        sub = self.small_font.render(desc, True, sub_color)
        self.screen.blit(sub, sub.get_rect(midtop=(rect.centerx, prev_rect.bottom + self.layout.s(24))))

    def _draw_tab_button(
        self,
        rect: pygame.Rect,
        label: str,
        icon: str,
        active: bool,
        hovered: bool,
        disabled: bool = False,
    ) -> None:
        r = self.layout.s(10)
        if disabled:
            text_color = (80, 74, 68)
            border = (42, 38, 34)
            icon_color = text_color
        elif active:
            text_color = GOLD_BRIGHT
            border = GOLD
            icon_color = GOLD_BRIGHT
        elif hovered:
            text_color = TEXT_COLOR
            border = GOLD_DIM
            icon_color = ACCENT_SOFT
        else:
            text_color = MUTED
            border = (55, 48, 38)
            icon_color = (100, 90, 75)

        blit_stone_panel(self.screen, rect, border_color=border, inner_glow=active, seed=hash(label) % 300)
        if active:
            indicator = pygame.Rect(rect.x + self.layout.s(8), rect.bottom - self.layout.s(4), rect.width - self.layout.s(16), self.layout.s(3))
            pygame.draw.rect(self.screen, GOLD, indicator, border_radius=1)

        icon_surf = self.tab_font.render(icon, True, icon_color)
        label_surf = self.tab_label_font.render(label, True, text_color)
        self.screen.blit(icon_surf, icon_surf.get_rect(midtop=(rect.centerx, rect.y + self.layout.s(8))))
        self.screen.blit(label_surf, label_surf.get_rect(midbottom=(rect.centerx, rect.bottom - self.layout.s(7))))

    def _draw_piece_scrollbar(self, sidebar: GameSidebar, content: pygame.Rect) -> None:
        max_scroll = sidebar.piece_scroll_max()
        if max_scroll <= 0:
            return
        track = pygame.Rect(content.right - self.layout.s(8), content.y + self.layout.s(6), self.layout.s(5), content.height - self.layout.s(12))
        pygame.draw.rect(self.screen, (32, 34, 40), track, border_radius=3)
        ratio = sidebar.piece_scroll / max_scroll
        thumb_h = max(self.layout.s(28), int(track.height * content.height / (content.height + max_scroll)))
        thumb_y = track.y + int((track.height - thumb_h) * ratio)
        thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_h)
        pygame.draw.rect(self.screen, ACCENT_SOFT, thumb, border_radius=3)

    def _draw_display_tab(self, sidebar: GameSidebar) -> None:
        content_y = self.layout.content_y
        buttons = sidebar.get_display_buttons()
        if not buttons:
            return

        x = self.layout.sidebar_x + self.layout.s(14)
        w = self.layout.sidebar_inner
        gap = self.layout.s(10)
        block_h = self.layout.s(88)

        auto_pct = int(self.layout.fit_scale * 100)
        blocks = [
            (f"Auto fenetre ({auto_pct}%)", self.layout.ui_scale, "ui"),
            ("Taille des pieces", self.layout.piece_scale, "piece"),
        ]
        for index, (title, value, prefix) in enumerate(blocks):
            y = content_y + index * (block_h + gap)
            block = pygame.Rect(x, y, w, block_h)
            pygame.draw.rect(self.screen, (28, 30, 38), block, border_radius=self.layout.s(12))
            pygame.draw.rect(self.screen, (48, 52, 62), block, 1, border_radius=self.layout.s(12))
            self.screen.blit(self.font.render(title, True, TEXT_COLOR), (block.x + self.layout.s(14), block.y + self.layout.s(10)))
            pct = self.subtitle_font.render(f"{int(value * 100)}%", True, ACCENT)
            self.screen.blit(pct, pct.get_rect(center=(block.centerx, block.y + self.layout.s(56))))

            minus_key = f"{prefix}_minus"
            plus_key = f"{prefix}_plus"
            for rect_key, symbol in ((minus_key, "−"), (plus_key, "+")):
                rect = buttons[rect_key]
                hovered = sidebar.is_hovered("display", rect_key)
                fill = (38, 54, 44) if hovered else (34, 36, 44)
                pygame.draw.rect(self.screen, fill, rect, border_radius=self.layout.s(10))
                pygame.draw.rect(self.screen, ACCENT if hovered else (60, 64, 74), rect, 2, border_radius=self.layout.s(10))
                sym = self.subtitle_font.render(symbol, True, ACCENT if hovered else TEXT_COLOR)
                self.screen.blit(sym, sym.get_rect(center=rect.center))

        reset = buttons.get("reset_zoom")
        if reset:
            hovered = sidebar.is_hovered("display", "reset_zoom")
            fill = (28, 52, 40) if hovered else (32, 34, 40)
            pygame.draw.rect(self.screen, fill, reset, border_radius=self.layout.s(10))
            pygame.draw.rect(self.screen, ACCENT if hovered else (60, 64, 74), reset, 2, border_radius=self.layout.s(10))
            text = self.chip_font.render("Reinitialiser", True, ACCENT if hovered else TEXT_COLOR)
            self.screen.blit(text, text.get_rect(center=reset.center))

    def _draw_board_scrollbar(self, sidebar: GameSidebar, content: pygame.Rect) -> None:
        max_scroll = sidebar.board_scroll_max()
        if max_scroll <= 0:
            return
        track = pygame.Rect(content.right - self.layout.s(8), content.y + self.layout.s(6), self.layout.s(5), content.height - self.layout.s(12))
        pygame.draw.rect(self.screen, (32, 28, 22), track, border_radius=3)
        ratio = sidebar.board_scroll / max_scroll
        thumb_h = max(self.layout.s(28), int(track.height * content.height / (content.height + max_scroll)))
        thumb_y = track.y + int((track.height - thumb_h) * ratio)
        pygame.draw.rect(self.screen, GOLD_DIM, pygame.Rect(track.x, thumb_y, track.width, thumb_h), border_radius=3)

    def draw_sidebar(self, sidebar: GameSidebar) -> None:
        panel = sidebar.panel_rect()
        blit_stone_panel(self.screen, panel, border_color=GOLD_DIM, inner_glow=True, seed=7)
        draw_ornate_corners(self.screen, panel, GOLD)

        title = self.subtitle_font.render("Personnalisation", True, GOLD_BRIGHT)
        self.screen.blit(title, (self.layout.sidebar_x + self.layout.s(18), self.layout.sidebar_y + self.layout.s(12)))

        tab_bar_bg = pygame.Rect(
            self.layout.sidebar_x + self.layout.s(10),
            self.layout.tab_bar_y - self.layout.s(4),
            self.layout.sidebar_width - self.layout.s(20),
            self.layout.tab_height + self.layout.s(8),
        )
        blit_stone_panel(self.screen, tab_bar_bg, border_color=(45, 38, 28), seed=11)

        for tab in SIDEBAR_TABS:
            tab_id = tab["id"]
            rect = sidebar.get_tab_buttons()[tab_id]
            disabled = tab_id == "elo" and not sidebar.vs_ai
            self._draw_tab_button(
                rect,
                tab["label"],
                tab.get("icon", ""),
                active=sidebar.active_tab == tab_id,
                hovered=sidebar.is_hovered("tab", tab_id),
                disabled=disabled,
            )

        content = sidebar.content_rect()
        blit_stone_panel(self.screen, content, border_color=(50, 42, 32), seed=19)

        if sidebar.active_tab == "pieces":
            count = self.small_font.render(f"{len(PIECE_SETS)} styles", True, MUTED)
            self.screen.blit(count, count.get_rect(topright=(content.topright[0] - self.layout.s(8), content.y - self.layout.s(18))))
            self.screen.set_clip(content)
            for set_id, rect in sidebar.get_piece_buttons().items():
                if not content.colliderect(rect):
                    continue
                meta = next(s for s in PIECE_SETS if s["id"] == set_id)
                self._draw_piece_card(rect, set_id, meta["label"], meta["desc"], set_id == sidebar.piece_set, sidebar.is_hovered("piece", set_id))
            self.screen.set_clip(None)
            self._draw_piece_scrollbar(sidebar, content)

        elif sidebar.active_tab == "board":
            count = self.small_font.render(f"{len(BOARD_THEMES)} plateaux", True, MUTED)
            self.screen.blit(count, count.get_rect(topright=(content.topright[0] - self.layout.s(8), content.y - self.layout.s(18))))
            self.screen.set_clip(content)
            for theme_id, rect in sidebar.get_board_buttons().items():
                if not content.colliderect(rect):
                    continue
                label = next(t["label"] for t in BOARD_THEMES if t["id"] == theme_id)
                preview = self.assets.get_theme_preview(theme_id, self.layout.s(16))
                self._draw_panel_button(rect, label, theme_id == sidebar.board_theme, sidebar.is_hovered("board", theme_id), preview)
            self.screen.set_clip(None)
            self._draw_board_scrollbar(sidebar, content)

        elif sidebar.active_tab == "time":
            for control_id, rect in sidebar.get_time_buttons().items():
                control = next(item for item in TIME_CONTROLS if item["id"] == control_id)
                self._draw_panel_button(rect, control["label"], control_id == sidebar.time_control_id, sidebar.is_hovered("time", control_id))

        elif sidebar.active_tab == "display":
            self._draw_display_tab(sidebar)

        elif sidebar.active_tab == "elo":
            if sidebar.vs_ai:
                for elo, rect in sidebar.get_elo_buttons().items():
                    level = next(item for item in ELO_LEVELS if item["elo"] == elo)
                    self._draw_panel_button(rect, f"{level['label']} - {elo}", elo == sidebar.elo, sidebar.is_hovered("elo", elo))
            else:
                hint = self.font.render("Disponible en mode vs IA", True, MUTED)
                self.screen.blit(hint, hint.get_rect(center=content.center))

    def draw_loading_screen(self, message: str, progress: float) -> None:
        self._load_tick += 1
        self.screen.blit(self._bg, (0, 0))
        draw_ember_particles(self.screen, self._load_tick, count=55)
        draw_fog_overlay(self.screen, alpha=35)

        w, h = self.layout.width, self.layout.height
        card = pygame.Rect(w // 2 - self.layout.s(320), h // 2 - self.layout.s(140), self.layout.s(640), self.layout.s(280))
        blit_stone_panel(self.screen, card, border_color=GOLD, inner_glow=True, seed=99)
        draw_ornate_corners(self.screen, card, GOLD_BRIGHT)

        title = self.title_font.render("Chess Pro D4", True, GOLD_BRIGHT)
        self.screen.blit(title, title.get_rect(center=(w // 2, card.y + self.layout.s(58))))
        subtitle = self.small_font.render("Edition D4 — Sanctuaire des Echecs", True, MUTED)
        self.screen.blit(subtitle, subtitle.get_rect(center=(w // 2, card.y + self.layout.s(96))))
        draw_gold_accent_line(self.screen, card.y + self.layout.s(112), card.width, self.layout.s(2))

        bar_x = card.x + self.layout.s(52)
        bar_y = card.y + self.layout.s(148)
        bar_w = card.width - self.layout.s(104)
        bar_h = self.layout.s(16)
        track = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        blit_stone_panel(self.screen, track, border_color=GOLD_DIM, seed=55)
        fill_w = max(0, int(bar_w * max(0.0, min(1.0, progress))))
        if fill_w > 0:
            fill_rect = pygame.Rect(bar_x + 2, bar_y + 2, fill_w - 4, bar_h - 4)
            glow = pygame.Surface((fill_rect.width, fill_rect.height), pygame.SRCALPHA)
            for row in range(fill_rect.height):
                ratio = row / max(fill_rect.height - 1, 1)
                c = (int(220 * (1 - ratio * 0.4)), int(140 * (1 - ratio * 0.3)), int(40 * (1 - ratio * 0.2)))
                pygame.draw.line(glow, (*c, 220), (0, row), (fill_rect.width, row))
            self.screen.blit(glow, fill_rect.topleft)

        pct = self.chip_font.render(f"{int(progress * 100)}%", True, GOLD_BRIGHT)
        self.screen.blit(pct, pct.get_rect(midright=(bar_x + bar_w, bar_y - self.layout.s(10))))
        status = self.font.render(message, True, TEXT_COLOR)
        self.screen.blit(status, status.get_rect(center=(w // 2, card.y + self.layout.s(210))))

    def _draw_hud_chip(self, rect: pygame.Rect, text: str, accent: bool = False) -> None:
        border = GOLD if accent else GOLD_DIM
        blit_stone_panel(self.screen, rect, border_color=border, inner_glow=accent, seed=hash(text) % 200)
        color = GOLD_BRIGHT if accent else MUTED
        surf = self.chip_font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def _draw_hud_action(self, rect: pygame.Rect, label: str, icon: str, hovered: bool, primary: bool = False) -> None:
        if primary and hovered:
            border = GOLD_BRIGHT
            text_color = GOLD_BRIGHT
        elif hovered:
            border = GOLD
            text_color = TEXT_COLOR
        elif primary:
            border = GOLD_DIM
            text_color = ACCENT_SOFT
        else:
            border = (55, 48, 38)
            text_color = TEXT_COLOR

        blit_stone_panel(self.screen, rect, border_color=border, inner_glow=primary or hovered, seed=hash(label) % 400)
        icon_surf = self.chip_font.render(icon, True, text_color)
        label_surf = self.small_font.render(label, True, text_color)
        self.screen.blit(icon_surf, icon_surf.get_rect(midtop=(rect.centerx, rect.y + self.layout.s(10))))
        self.screen.blit(label_surf, label_surf.get_rect(midbottom=(rect.centerx, rect.bottom - self.layout.s(10))))

    def draw_eval_bar(self, white_advantage: float | None) -> None:
        rect = self.layout.eval_bar_rect()
        blit_stone_panel(self.screen, rect, border_color=GOLD_DIM, seed=19)
        inner = rect.inflate(-4, -4)
        pygame.draw.rect(self.screen, (28, 26, 24), inner)
        adv = 0.0 if white_advantage is None else max(-1.0, min(1.0, white_advantage))
        white_h = int(inner.height * (0.5 + adv * 0.5))
        white_h = max(2, min(inner.height - 2, white_h))
        white_rect = pygame.Rect(inner.x, inner.bottom - white_h, inner.width, white_h)
        pygame.draw.rect(self.screen, (230, 220, 200), white_rect)
        black_rect = pygame.Rect(inner.x, inner.y, inner.width, inner.height - white_h)
        pygame.draw.rect(self.screen, (28, 26, 32), black_rect)
        mid_y = inner.centery
        pygame.draw.line(self.screen, GOLD_DIM, (inner.left, mid_y), (inner.right, mid_y), 1)

    def draw_hud(self, status: str, mode: str, engine: str, buttons: dict[str, pygame.Rect]) -> None:
        hud_h = self.layout.hud_height
        hud_y = self.layout.height - hud_h
        full_w = self.layout.width - self.layout.sidebar_width - self.layout.s(8)

        hud_rect = pygame.Rect(0, hud_y, full_w, hud_h)
        blit_stone_panel(self.screen, hud_rect, border_color=GOLD_DIM, inner_glow=True, seed=88)
        draw_gold_accent_line(self.screen, hud_y, full_w, self.layout.s(3))

        pad = self.layout.s(18)
        cy = hud_y + hud_h // 2

        brand_size = self.layout.s(58)
        brand = pygame.Rect(pad, cy - brand_size // 2, brand_size, brand_size)
        blit_stone_panel(self.screen, brand, border_color=GOLD, inner_glow=True, seed=12)
        draw_ornate_corners(self.screen, brand, GOLD_BRIGHT)
        piece_icon = self.title_font.render("♞", True, GOLD_BRIGHT)
        self.screen.blit(piece_icon, piece_icon.get_rect(center=brand.center))

        info_x = brand.right + self.layout.s(12)
        status_surf = self.hud_font.render(status[:48], True, TEXT_COLOR)
        self.screen.blit(status_surf, (info_x, cy - self.layout.s(20)))
        mode_surf = self.small_font.render(mode, True, MUTED)
        self.screen.blit(mode_surf, (info_x, cy + self.layout.s(8)))

        if buttons:
            rects = list(buttons.values())
            group = rects[0].unionall(rects)
            tray = group.inflate(self.layout.s(8), self.layout.s(6))
            blit_stone_panel(self.screen, tray, border_color=(45, 38, 28), seed=33)

        action_icons = {
            "Annuler": "↶",
            "Refaire": "↷",
            "Rejouer": "↻",
            "Analyse": "◈",
            "Sauver": "💾",
            "Pause": "⏸",
        }
        for label, rect in buttons.items():
            self._draw_hud_action(
                rect,
                label,
                action_icons.get(label, "•"),
                hovered=self.hover_button == label,
                primary=label in ("Pause", "Analyse"),
            )

    def draw_main_menu(self, options: list[tuple[str, pygame.Rect]]) -> None:
        """Menu principal moderne et epure."""
        self._load_tick += 1
        w, h = self.layout.width, self.layout.height
        self.screen.blit(self._bg, (0, 0))
        draw_ember_particles(self.screen, self._load_tick, count=28)
        draw_fog_overlay(self.screen, alpha=28)

        title = self.title_font.render("Chess Pro", True, GOLD_BRIGHT)
        self.screen.blit(title, title.get_rect(center=(w // 2, self.layout.s(110))))
        sub = self.small_font.render("D4  ·  Stockfish UCI  ·  Echecs premium", True, MUTED)
        self.screen.blit(sub, sub.get_rect(center=(w // 2, self.layout.s(150))))

        for label, rect in options:
            hovered = self.hover_button == label
            primary = label == "JOUER CONTRE STOCKFISH"
            bg = (42, 34, 26) if hovered else (28, 24, 20)
            border = GOLD_BRIGHT if primary or hovered else (70, 58, 42)
            pygame.draw.rect(self.screen, bg, rect, border_radius=10)
            pygame.draw.rect(self.screen, border, rect, width=1, border_radius=10)
            text = self.chip_font.render(label, True, GOLD_BRIGHT if primary else TEXT_COLOR)
            self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_menu_overlay(self, title: str, options: list[tuple[str, pygame.Rect]], subtitle: str = "") -> None:
        """Overlay menu (pause) par-dessus la partie."""
        w, h = self.layout.width, self.layout.height
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.animations.menu_alpha()))
        self.screen.blit(overlay, (0, 0))
        draw_fog_overlay(self.screen, alpha=min(50, self.animations.menu_alpha() // 4))
        draw_ember_particles(self.screen, pygame.time.get_ticks() // 16, count=35)

        card = pygame.Rect(w // 2 - self.layout.s(300), self.layout.s(64), self.layout.s(600), self.layout.s(150))
        blit_stone_panel(self.screen, card, border_color=GOLD, inner_glow=True, seed=77)
        draw_ornate_corners(self.screen, card, GOLD_BRIGHT)
        draw_gold_accent_line(self.screen, card.bottom - self.layout.s(3), card.width, self.layout.s(2))

        title_surf = self.title_font.render(title, True, GOLD_BRIGHT)
        self.screen.blit(title_surf, title_surf.get_rect(center=(w // 2, card.y + self.layout.s(50))))
        if subtitle:
            sub_surf = self.small_font.render(subtitle, True, MUTED)
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(w // 2, card.y + self.layout.s(92))))

        pause_icons = {"Reprendre": "▶", "Nouvelle partie": "↻", "Menu principal": "⌂"}
        for label, rect in options:
            self._draw_hud_action(
                rect,
                label,
                pause_icons.get(label, "•"),
                hovered=self.hover_button == label,
                primary=label == "Reprendre",
            )

    def _sorted_promotion_moves(self, moves: list[chess.Move]) -> list[chess.Move]:
        order = {piece: index for index, piece in enumerate(PROMOTION_ORDER)}
        return sorted(moves, key=lambda move: order.get(move.promotion or chess.QUEEN, 99))

    def promotion_picker_rects(self, moves: list[chess.Move]) -> dict[chess.Move, pygame.Rect]:
        if not moves:
            return {}
        to_square = moves[0].to_square
        sq_rect = self.square_rect(to_square)
        ordered = self._sorted_promotion_moves(moves)
        count = len(ordered)
        btn = self.layout.s(58)
        gap = self.layout.s(8)
        total_w = count * btn + (count - 1) * gap
        x0 = sq_rect.centerx - total_w // 2

        rank = chess.square_rank(to_square)
        if rank >= 6:
            y = max(self.layout.s(8), sq_rect.top - btn - self.layout.s(12))
        else:
            y = min(self.layout.play_area_height - btn - self.layout.s(8), sq_rect.bottom + self.layout.s(12))

        rects: dict[chess.Move, pygame.Rect] = {}
        for index, move in enumerate(ordered):
            rects[move] = pygame.Rect(x0 + index * (btn + gap), y, btn, btn)
        return rects

    def update_promotion_hover(self, pos: tuple[int, int] | None, moves: list[chess.Move] | None) -> None:
        self.promotion_hover = None
        if pos is None or not moves:
            return
        for move, rect in self.promotion_picker_rects(moves).items():
            if rect.collidepoint(pos):
                self.promotion_hover = move
                return

    def pick_promotion_at(self, pos: tuple[int, int], moves: list[chess.Move]) -> chess.Move | None:
        for move, rect in self.promotion_picker_rects(moves).items():
            if rect.collidepoint(pos):
                return move
        return None

    def draw_promotion_picker(self, moves: list[chess.Move], board: ChessBoard) -> None:
        if not moves:
            return

        play_w = self.layout.play_area_width
        dim = pygame.Surface((play_w, self.layout.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        self.screen.blit(dim, (0, 0))

        to_square = moves[0].to_square
        highlight = self.square_rect(to_square)
        glow = pygame.Surface((highlight.width, highlight.height), pygame.SRCALPHA)
        glow.fill((212, 165, 72, 90))
        self.screen.blit(glow, highlight.topleft)

        piece_color = board.board.turn
        rects = self.promotion_picker_rects(moves)
        panel = pygame.Rect(0, 0, 0, 0)
        if rects:
            all_rects = list(rects.values())
            panel = all_rects[0].unionall(all_rects).inflate(self.layout.s(20), self.layout.s(28))
            panel.y -= self.layout.s(18)
            panel.height += self.layout.s(18)
        blit_stone_panel(self.screen, panel, border_color=GOLD, inner_glow=True, seed=301)
        draw_ornate_corners(self.screen, panel, GOLD_BRIGHT)

        title = self.chip_font.render("Promouvoir en", True, GOLD_BRIGHT)
        self.screen.blit(title, title.get_rect(midbottom=(panel.centerx, panel.y + self.layout.s(16))))

        for move, rect in rects.items():
            promo = move.promotion or chess.QUEEN
            symbol = chess.Piece(promo, piece_color).symbol()
            hovered = self.promotion_hover == move
            border = GOLD_BRIGHT if hovered else GOLD_DIM
            blit_stone_panel(self.screen, rect, border_color=border, inner_glow=hovered, seed=promo)
            if hovered:
                draw_ornate_corners(self.screen, rect, GOLD_BRIGHT)

            icon_size = rect.width - self.layout.s(10)
            piece_img = self.assets.get_piece(symbol, icon_size)
            self.screen.blit(piece_img, piece_img.get_rect(center=rect.center))

            label = self.small_font.render(PROMOTION_LABELS.get(promo, "?"), True, GOLD_BRIGHT if hovered else TEXT_COLOR)
            self.screen.blit(label, label.get_rect(midtop=(rect.centerx, rect.bottom + self.layout.s(4))))

    def draw_thinking_banner(self) -> None:
        pulse = self.animations.think_pulse()
        color = (int(220 * pulse), int(160 * pulse), int(55 * pulse))
        banner = self.subtitle_font.render("Stockfish réfléchit...", True, color)
        ox, oy = self.layout.board_origin()
        cx = ox + self.layout.board_pixel_size // 2
        cy = max(self.layout.s(28), oy - self.layout.s(28))
        # Fond discret derrière le texte
        pad_x, pad_y = self.layout.s(18), self.layout.s(8)
        bg = pygame.Rect(0, 0, banner.get_width() + pad_x * 2, banner.get_height() + pad_y * 2)
        bg.center = (cx, cy)
        pygame.draw.rect(self.screen, (18, 15, 12), bg, border_radius=8)
        pygame.draw.rect(self.screen, (90, 70, 35), bg, width=1, border_radius=8)
        self.screen.blit(banner, banner.get_rect(center=(cx, cy)))

    def update_hover_buttons(self, pos: tuple[int, int] | None, buttons: dict[str, pygame.Rect]) -> None:
        self.hover_button = None
        if pos is None:
            return
        for label, rect in buttons.items():
            if rect.collidepoint(pos):
                self.hover_button = label
                return
