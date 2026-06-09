"""Configuration visuelle et paramètres du jeu."""

BOARD_SIZE = 8
WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 860
BOARD_PIXEL_SIZE = 600
SIDEBAR_WIDTH = 300
MARGIN = 40
HUD_HEIGHT = 110
FRAME_PADDING = 24
SIDEBAR_X = WINDOW_WIDTH - SIDEBAR_WIDTH - 16
SIDEBAR_Y = MARGIN
SIDEBAR_INNER = SIDEBAR_WIDTH - 24

SELECT_COLOR = (186, 202, 68, 120)
MOVE_HINT_COLOR = (106, 135, 77, 120)
CHECK_COLOR = (220, 53, 69, 140)
BACKGROUND = (15, 15, 15)
PANEL_BG = (22, 22, 26)
TEXT_COLOR = (230, 230, 230)
ACCENT = (0, 230, 118)
MUTED = (160, 160, 160)
ACTIVE = (0, 180, 90)

FPS = 60
AI_DEPTH = 3
DEFAULT_ELO = 1200
DEFAULT_BOARD_THEME = "classic"
DEFAULT_PIECE_SET = "staunton"

MOVE_ANIM_MS = 220
SELECT_PULSE_SPEED = 5.5

PIECE_SETS = [
    {"id": "staunton", "label": "Staunton"},
    {"id": "neo", "label": "Neo"},
    {"id": "gold", "label": "Or"},
]

BOARD_THEMES = [
    {
        "id": "classic",
        "label": "Classique",
        "light": ((240, 217, 181), (220, 190, 150)),
        "dark": ((181, 136, 99), (140, 100, 70)),
        "frame": ((58, 42, 30), (92, 64, 42)),
    },
    {
        "id": "blue",
        "label": "Bleu",
        "light": ((222, 227, 230), (190, 198, 205)),
        "dark": ((140, 162, 173), (100, 120, 130)),
        "frame": ((45, 58, 72), (70, 90, 110)),
    },
    {
        "id": "green",
        "label": "Vert",
        "light": ((235, 236, 208), (210, 212, 175)),
        "dark": ((119, 148, 86), (85, 110, 60)),
        "frame": ((40, 58, 35), (65, 90, 50)),
    },
    {
        "id": "marble",
        "label": "Marbre",
        "light": ((240, 240, 240), (210, 210, 210)),
        "dark": ((180, 180, 180), (140, 140, 140)),
        "frame": ((90, 90, 90), (130, 130, 130)),
    },
    {
        "id": "midnight",
        "label": "Minuit",
        "light": ((90, 106, 140), (70, 84, 112)),
        "dark": ((45, 52, 72), (30, 36, 52)),
        "frame": ((25, 28, 40), (45, 50, 68)),
    },
    {
        "id": "coral",
        "label": "Corail",
        "light": ((255, 228, 205), (235, 200, 170)),
        "dark": ((209, 139, 106), (170, 100, 75)),
        "frame": ((120, 60, 45), (160, 85, 60)),
    },
    {
        "id": "ice",
        "label": "Glace",
        "light": ((230, 245, 255), (200, 225, 245)),
        "dark": ((160, 195, 220), (120, 160, 190)),
        "frame": ((70, 100, 130), (100, 140, 175)),
    },
    {
        "id": "forest",
        "label": "Forêt",
        "light": ((210, 220, 190), (180, 195, 160)),
        "dark": ((80, 110, 70), (55, 80, 48)),
        "frame": ((35, 50, 30), (55, 75, 45)),
    },
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
