from __future__ import annotations

import os

import pygame

from src.models.settings import BOARD_THEMES, DEFAULT_BOARD_THEME, DEFAULT_PIECE_SET, PIECE_SETS
from src.utils.paths import piece_set_dir, theme_dir


class AssetManager:
    PIECE_FILES = {
        "K": "wK.png",
        "Q": "wQ.png",
        "R": "wR.png",
        "B": "wB.png",
        "N": "wN.png",
        "P": "wP.png",
        "k": "bK.png",
        "q": "bQ.png",
        "r": "bR.png",
        "b": "bB.png",
        "n": "bN.png",
        "p": "bP.png",
    }

    def __init__(
        self,
        theme_id: str = DEFAULT_BOARD_THEME,
        piece_set: str = DEFAULT_PIECE_SET,
    ) -> None:
        self.theme_id = theme_id
        self.piece_set = piece_set
        self._theme_cache: dict[str, dict[str, pygame.Surface | None]] = {}
        self._piece_cache: dict[str, dict[str, pygame.Surface]] = {}
        self._piece_scale_cache: dict[tuple[str, str, int], pygame.Surface] = {}
        self._piece_alpha_cache: dict[tuple[str, str, int, int], pygame.Surface] = {}
        self._square_scale_cache: dict[tuple[str, bool, int], pygame.Surface] = {}
        self._frame_scale_cache: dict[tuple[str, int], pygame.Surface] = {}
        self._theme_preview_cache: dict[tuple[str, int], pygame.Surface] = {}
        self._load_piece_set(piece_set)
        self._load_theme(theme_id)

    def _load_piece_set(self, set_id: str) -> None:
        if set_id in self._piece_cache:
            return
        folder = piece_set_dir(set_id)
        pieces: dict[str, pygame.Surface] = {}
        for symbol, filename in self.PIECE_FILES.items():
            path = os.path.join(folder, filename)
            if not os.path.isfile(path):
                legacy = os.path.join(os.path.dirname(folder), filename)
                if os.path.isfile(legacy):
                    path = legacy
                else:
                    raise FileNotFoundError(f"Asset manquant : {path}. Lance tools/download_pieces.py")
            pieces[symbol] = pygame.image.load(path).convert_alpha()
        self._piece_cache[set_id] = pieces

    def _load_board_file(self, folder: str, filename: str, optional: bool = False) -> pygame.Surface | None:
        path = os.path.join(folder, filename)
        if not os.path.isfile(path):
            if optional:
                return None
            raise FileNotFoundError(f"Asset manquant : {path}. Lance tools/generate_assets.py")
        image = pygame.image.load(path)
        if image.get_flags() & pygame.SRCALPHA:
            return image.convert_alpha()
        return image.convert()

    def _load_theme(self, theme_id: str) -> None:
        if theme_id in self._theme_cache:
            return
        folder = theme_dir(theme_id)
        self._theme_cache[theme_id] = {
            "light": self._load_board_file(folder, "light_square.png"),
            "dark": self._load_board_file(folder, "dark_square.png"),
            "frame": self._load_board_file(folder, "frame.png", optional=True),
        }

    def set_theme(self, theme_id: str) -> None:
        self.theme_id = theme_id
        self._load_theme(theme_id)
        self._square_scale_cache.clear()
        self._frame_scale_cache.clear()

    def set_piece_set(self, set_id: str) -> None:
        self.piece_set = set_id
        self._load_piece_set(set_id)
        self._piece_scale_cache.clear()
        self._piece_alpha_cache.clear()

    def clear_scale_caches(self) -> None:
        self._piece_scale_cache.clear()
        self._piece_alpha_cache.clear()
        self._square_scale_cache.clear()
        self._frame_scale_cache.clear()

    def get_theme_label(self) -> str:
        for theme in BOARD_THEMES:
            if theme["id"] == self.theme_id:
                return theme["label"]
        return self.theme_id

    def get_piece_set_label(self) -> str:
        for piece_set in PIECE_SETS:
            if piece_set["id"] == self.piece_set:
                return piece_set["label"]
        return self.piece_set

    @property
    def _active(self) -> dict[str, pygame.Surface | None]:
        self._load_theme(self.theme_id)
        return self._theme_cache[self.theme_id]

    @property
    def _pieces(self) -> dict[str, pygame.Surface]:
        self._load_piece_set(self.piece_set)
        return self._piece_cache[self.piece_set]

    def _scale_surface(self, base: pygame.Surface, size: int, *, smooth: bool) -> pygame.Surface:
        if base.get_width() == size and base.get_height() == size:
            return base
        if smooth:
            return pygame.transform.smoothscale(base, (size, size))
        return pygame.transform.scale(base, (size, size))

    def get_piece(self, symbol: str, size: int, *, alpha: int = 255, smooth: bool = False) -> pygame.Surface:
        size = max(1, int(size))
        if alpha < 255:
            alpha_key = min(255, (alpha // 16) * 16)
            key = (self.piece_set, symbol, size, alpha_key)
            cached = self._piece_alpha_cache.get(key)
            if cached is not None:
                return cached
            base = self.get_piece(symbol, size, smooth=smooth)
            faded = base.copy()
            faded.set_alpha(alpha_key)
            self._piece_alpha_cache[key] = faded
            return faded

        key = (self.piece_set, symbol, size)
        cached = self._piece_scale_cache.get(key)
        if cached is not None:
            return cached
        scaled = self._scale_surface(self._pieces[symbol], size, smooth=smooth)
        self._piece_scale_cache[key] = scaled
        return scaled

    def get_square(self, light: bool, size: int) -> pygame.Surface:
        size = max(1, int(size))
        key = (self.theme_id, light, size)
        cached = self._square_scale_cache.get(key)
        if cached is not None:
            return cached
        base = self._active["light"] if light else self._active["dark"]
        assert base is not None
        scaled = self._scale_surface(base, size, smooth=False)
        self._square_scale_cache[key] = scaled
        return scaled

    def get_frame(self, board_size: int) -> pygame.Surface | None:
        frame = self._active["frame"]
        if frame is None:
            return None
        target = board_size + 48
        key = (self.theme_id, target)
        cached = self._frame_scale_cache.get(key)
        if cached is not None:
            return cached
        scaled = self._scale_surface(frame, target, smooth=False)
        self._frame_scale_cache[key] = scaled
        return scaled

    def warm_board(self, square_size: int, piece_size: int, selected_size: int) -> None:
        """Precalcule les tailles les plus utilisees pour eviter les pics pendant l'animation."""
        for symbol in self.PIECE_FILES:
            self.get_piece(symbol, piece_size)
            if selected_size != piece_size:
                self.get_piece(symbol, selected_size)
        self.get_square(True, square_size)
        self.get_square(False, square_size)

    def get_theme_preview(self, theme_id: str, size: int = 36) -> pygame.Surface:
        size = max(1, int(size))
        key = (theme_id, size)
        cached = self._theme_preview_cache.get(key)
        if cached is not None:
            return cached
        self._load_theme(theme_id)
        theme = self._theme_cache[theme_id]
        preview = pygame.Surface((size * 2, size * 2))
        light = theme["light"]
        dark = theme["dark"]
        assert light is not None and dark is not None
        preview.blit(pygame.transform.smoothscale(light, (size, size)), (0, 0))
        preview.blit(pygame.transform.smoothscale(dark, (size, size)), (size, 0))
        preview.blit(pygame.transform.smoothscale(dark, (size, size)), (0, size))
        preview.blit(pygame.transform.smoothscale(light, (size, size)), (size, size))
        self._theme_preview_cache[key] = preview
        return preview

    def preload_piece_set(self, set_id: str) -> None:
        self._load_piece_set(set_id)

    def preload_theme(self, theme_id: str) -> None:
        self._load_theme(theme_id)

    def preload_all(self) -> None:
        for piece_set in PIECE_SETS:
            self._load_piece_set(piece_set["id"])
        for theme in BOARD_THEMES:
            self._load_theme(theme["id"])

    def get_piece_set_card(self, set_id: str, width: int = 140) -> pygame.Surface:
        folder = piece_set_dir(set_id)
        path = os.path.join(folder, "preview.png")
        if os.path.isfile(path):
            img = pygame.image.load(path).convert_alpha()
            height = max(1, int(width * img.get_height() / img.get_width()))
            return pygame.transform.smoothscale(img, (width, height))
        self._load_piece_set(set_id)
        card = pygame.Surface((width, 48), pygame.SRCALPHA)
        card.fill((30, 32, 38, 255))
        icon = max(18, min(28, width // 6))
        knight = pygame.transform.smoothscale(self._piece_cache[set_id]["N"], (icon, icon))
        queen = pygame.transform.smoothscale(self._piece_cache[set_id]["q"], (icon, icon))
        gap = max(4, icon // 3)
        start_x = (width - icon * 2 - gap) // 2
        card.blit(knight, (start_x, 4))
        card.blit(queen, (start_x + icon + gap, 4))
        return card
