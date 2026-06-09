from __future__ import annotations

import os

import pygame

from config.paths import PIECES_DIR, theme_dir
from config.settings import BOARD_THEMES, DEFAULT_BOARD_THEME


class AssetManager:
    """Charge et met en cache les sprites du plateau et des pièces."""

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

    def __init__(self, theme_id: str = DEFAULT_BOARD_THEME) -> None:
        self.theme_id = theme_id
        self._theme_cache: dict[str, dict[str, pygame.Surface | None]] = {}
        self.pieces: dict[str, pygame.Surface] = {}
        self._load_pieces()
        self._load_theme(theme_id)

    def _load_pieces(self) -> None:
        for symbol, filename in self.PIECE_FILES.items():
            path = os.path.join(PIECES_DIR, filename)
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Asset manquant : {path}. Lance tools/generate_assets.py")
            self.pieces[symbol] = pygame.image.load(path).convert_alpha()

    def _load_board_file(self, folder: str, filename: str, optional: bool = False) -> pygame.Surface | None:
        path = os.path.join(folder, filename)
        if not os.path.isfile(path):
            if optional:
                return None
            raise FileNotFoundError(f"Asset manquant : {path}. Lance tools/generate_assets.py")
        return pygame.image.load(path).convert_alpha()

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

    def get_theme_label(self) -> str:
        for theme in BOARD_THEMES:
            if theme["id"] == self.theme_id:
                return theme["label"]
        return self.theme_id

    @property
    def _active(self) -> dict[str, pygame.Surface | None]:
        self._load_theme(self.theme_id)
        return self._theme_cache[self.theme_id]

    def get_piece(self, symbol: str, size: int) -> pygame.Surface:
        base = self.pieces[symbol]
        if base.get_width() == size:
            return base
        return pygame.transform.smoothscale(base, (size, size))

    def get_square(self, light: bool, size: int) -> pygame.Surface:
        base = self._active["light"] if light else self._active["dark"]
        assert base is not None
        if base.get_width() == size:
            return base
        return pygame.transform.smoothscale(base, (size, size))

    def get_frame(self, board_size: int) -> pygame.Surface | None:
        frame = self._active["frame"]
        if frame is None:
            return None
        target = board_size + 48
        if frame.get_width() == target:
            return frame
        return pygame.transform.smoothscale(frame, (target, target))

    def get_theme_preview(self, theme_id: str, size: int = 36) -> pygame.Surface:
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
        return preview
