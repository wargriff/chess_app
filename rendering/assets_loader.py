from __future__ import annotations

import os

import pygame

from config.paths import piece_set_dir, theme_dir
from config.settings import BOARD_THEMES, DEFAULT_BOARD_THEME, DEFAULT_PIECE_SET, PIECE_SETS


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
                    raise FileNotFoundError(f"Asset manquant : {path}. Lance tools/generate_assets.py")
            pieces[symbol] = pygame.image.load(path).convert_alpha()
        self._piece_cache[set_id] = pieces

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

    def set_piece_set(self, set_id: str) -> None:
        self.piece_set = set_id
        self._load_piece_set(set_id)

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

    def get_piece(self, symbol: str, size: int) -> pygame.Surface:
        base = self._pieces[symbol]
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
        knight = pygame.transform.smoothscale(self._piece_cache[set_id]["N"], (36, 36))
        queen = pygame.transform.smoothscale(self._piece_cache[set_id]["q"], (36, 36))
        card.blit(knight, (8, 6))
        card.blit(queen, (52, 6))
        return card
