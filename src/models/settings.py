"""Paramètres persistants et catalogues visuels."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


FPS = 60
AI_DEPTH = 3
DEFAULT_ELO = 1200
DEFAULT_BOARD_THEME = "sanctum"
DEFAULT_PIECE_SET = "cburnett"
DEFAULT_TIME_MINUTES = 10
DEFAULT_TIME_INCREMENT = 0
MOVE_ANIM_MS = 240
SELECT_PULSE_SPEED = 5.5

# Palette D4
BACKGROUND = (8, 6, 5)
PANEL_BG = (18, 16, 14)
TEXT_COLOR = (235, 225, 205)
ACCENT = (212, 165, 72)
ACCENT_SOFT = (168, 128, 56)
MUTED = (140, 125, 108)
ACTIVE = (230, 190, 100)
CARD_BG = (26, 22, 18)
SELECT_COLOR = (212, 165, 72, 110)
MOVE_HINT_COLOR = (220, 170, 60, 95)
CHECK_COLOR = (200, 40, 45, 140)

SIDEBAR_TABS = [
    {"id": "pieces", "label": "PIÈCES", "icon": ""},
    {"id": "board", "label": "PLATEAU", "icon": ""},
    {"id": "time", "label": "CHRONO", "icon": ""},
    {"id": "display", "label": "VUE", "icon": ""},
    {"id": "elo", "label": "IA", "icon": ""},
]

TIME_CONTROLS = [
    {"id": "none", "label": "Sans limite", "minutes": 0, "increment": 0},
    {"id": "1_0", "label": "1+0", "minutes": 1, "increment": 0},
    {"id": "2_1", "label": "2+1", "minutes": 2, "increment": 1},
    {"id": "3_2", "label": "3+2", "minutes": 3, "increment": 2},
    {"id": "5_0", "label": "5+0", "minutes": 5, "increment": 0},
    {"id": "5_3", "label": "5+3", "minutes": 5, "increment": 3},
    {"id": "10_0", "label": "10+0", "minutes": 10, "increment": 0},
    {"id": "10_5", "label": "10+5", "minutes": 10, "increment": 5},
    {"id": "15_10", "label": "15+10", "minutes": 15, "increment": 10},
    {"id": "30_0", "label": "30+0", "minutes": 30, "increment": 0},
]

ELO_LEVELS = [
    {"label": "Débutant", "elo": 800, "skill": 0},
    {"label": "Loisir", "elo": 1000, "skill": 4},
    {"label": "Club", "elo": 1200, "skill": 8},
    {"label": "Confirmé", "elo": 1400, "skill": None},
    {"label": "Avancé", "elo": 1600, "skill": None},
    {"label": "Expert", "elo": 1800, "skill": None},
    {"label": "Maître", "elo": 2000, "skill": None},
    {"label": "Grand Maître", "elo": 2400, "skill": None},
]

# Sets principaux affichés dans Personnalisation (pas 20 options d'un coup)
PIECE_SETS = [
    {"id": "cburnett", "label": "Classique", "desc": "Staunton Lichess"},
    {"id": "merida", "label": "Moderne", "desc": "Tournoi net"},
    {"id": "maestro", "label": "Élégant", "desc": "Fin et précis"},
    {"id": "alpha", "label": "Minimaliste", "desc": "Épuré"},
    {"id": "fantasy", "label": "D4", "desc": "Dark fantasy"},
    # Extra (scroll) — styles secondaires
    {"id": "california", "label": "Neo", "desc": "Style chess.com"},
    {"id": "cardinal", "label": "Cardinal", "desc": "Contour net"},
    {"id": "staunty", "label": "Staunty", "desc": "Staunton neo"},
    {"id": "gioco", "label": "Gioco", "desc": "Italien"},
    {"id": "leipzig", "label": "Leipzig", "desc": "Allemand"},
]

# Themes plateau (id = dossier assets/board/<id>) — labels pro demandés
BOARD_THEMES = [
    {"id": "classic", "label": "Classique", "light": ((240, 217, 181), (220, 190, 150)), "dark": ((181, 136, 99), (140, 100, 70)), "frame": ((58, 42, 30), (92, 64, 42))},
    {"id": "sanctum", "label": "Bois", "light": ((168, 148, 118), (138, 118, 92)), "dark": ((78, 58, 42), (52, 38, 28)), "frame": ((28, 20, 14), (160, 120, 50)), "texture": "sanctified"},
    {"id": "marble", "label": "Marbre", "light": ((225, 220, 210), (200, 195, 185)), "dark": ((120, 125, 135), (90, 95, 105)), "frame": ((50, 50, 55), (140, 140, 150)), "texture": "marble"},
    {"id": "midnight", "label": "Dark", "light": ((70, 70, 78), (55, 55, 62)), "dark": ((35, 35, 40), (22, 22, 26)), "frame": ((12, 12, 14), (90, 80, 50)), "texture": "void"},
    {"id": "throne", "label": "Noir & Or", "light": ((142, 118, 82), (110, 90, 60)), "dark": ((68, 48, 32), (42, 28, 18)), "frame": ((32, 22, 14), (150, 110, 40)), "texture": "gold"},
    {"id": "storm", "label": "Futuriste", "light": ((120, 130, 145), (90, 100, 118)), "dark": ((52, 58, 72), (32, 36, 48)), "frame": ((28, 32, 42), (70, 90, 120)), "texture": "fog"},
    {"id": "eclipse", "label": "Eclipse", "light": ((78, 72, 88), (56, 50, 64)), "dark": ((32, 28, 42), (18, 14, 26)), "frame": ((12, 10, 20), (90, 70, 130)), "texture": "void"},
    {"id": "molten", "label": "Fonte", "light": ((145, 82, 42), (110, 58, 28)), "dark": ((72, 38, 18), (48, 22, 10)), "frame": ((28, 14, 6), (180, 90, 25)), "texture": "lava"},
    {"id": "phoenix", "label": "Phoenix", "light": ((195, 128, 62), (155, 95, 42)), "dark": ((115, 52, 28), (78, 32, 16)), "frame": ((38, 18, 8), (200, 110, 35)), "texture": "ember"},
    {"id": "jade", "label": "Jade", "light": ((142, 178, 148), (108, 145, 118)), "dark": ((58, 98, 72), (36, 72, 52)), "frame": ((28, 52, 38), (75, 130, 90)), "texture": "moss"},
    {"id": "infernal", "label": "Infernal", "light": ((145, 70, 40), (110, 50, 28)), "dark": ((70, 30, 18), (40, 16, 10)), "frame": ((24, 10, 6), (190, 70, 20)), "texture": "lava"},
    {"id": "obsidian", "label": "Obsidienne", "light": ((88, 86, 98), (62, 60, 72)), "dark": ((38, 36, 48), (22, 20, 30)), "frame": ((14, 12, 20), (75, 72, 95)), "texture": "stone"},
]


@dataclass
class AppSettings:
    board_theme: str = DEFAULT_BOARD_THEME
    piece_set: str = DEFAULT_PIECE_SET
    elo: int = DEFAULT_ELO
    skill: int | None = 8
    time_control_id: str = "10_0"
    time_minutes: int = DEFAULT_TIME_MINUTES
    time_increment: int = DEFAULT_TIME_INCREMENT
    color_preference: str = "white"  # white | black | random
    animations_enabled: bool = True
    sounds_enabled: bool = True
    sound_volume: float = 0.7
    ui_scale: float = 1.0
    piece_scale: float = 1.08
    stockfish_path: str = ""
    stockfish_depth: int = 18
    stockfish_movetime_ms: int = 800
    player_name: str = "Joueur"
    show_eval_bar: bool = True
    show_coordinates: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppSettings:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)
