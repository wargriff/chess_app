"""Presets de force Stockfish (Skill / Elo / Threads / Hash / temps) — 400 → 3200."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineStrength:
    label: str
    elo: int
    skill: int | None
    limit_strength: bool
    threads: int
    hash_mb: int
    movetime_ms: int
    depth: int | None = None


# Mapping UI → configuration UCI réelle (comportement moteur, pas seulement un label)
STRENGTH_PRESETS: dict[int, EngineStrength] = {
    400: EngineStrength("Débutant", 400, 0, False, 1, 16, 80, 5),
    600: EngineStrength("Novice", 600, 1, False, 1, 16, 120, 6),
    800: EngineStrength("Amateur", 800, 2, False, 1, 16, 180, 7),
    1000: EngineStrength("Amateur+", 1000, 4, False, 1, 16, 250, 8),
    1200: EngineStrength("Club", 1200, 6, False, 1, 32, 350, 10),
    1400: EngineStrength("Club+", 1400, 8, False, 1, 32, 450, 12),
    1600: EngineStrength("Confirmé", 1600, None, True, 1, 64, 600, None),
    1800: EngineStrength("Fort", 1800, None, True, 2, 64, 800, None),
    2000: EngineStrength("Expert", 2000, None, True, 2, 128, 1000, None),
    2200: EngineStrength("Maître", 2200, None, True, 2, 128, 1200, None),
    2400: EngineStrength("Maître FIDE", 2400, None, True, 2, 128, 1400, None),
    2600: EngineStrength("Grand Maître", 2600, None, True, 2, 256, 1600, None),
    2800: EngineStrength("Grand Maître+", 2800, None, True, 3, 256, 1800, None),
    3000: EngineStrength("Élite", 3000, None, True, 3, 512, 2200, None),
    3200: EngineStrength("Grand Maître / Maximum", 3200, None, False, 4, 512, 3000, None),
}

ELO_LEVELS_UI = [
    {"elo": e, "label": p.label}
    for e, p in sorted(STRENGTH_PRESETS.items())
]


def strength_for_elo(elo: int) -> EngineStrength:
    elo = int(elo)
    if elo in STRENGTH_PRESETS:
        return STRENGTH_PRESETS[elo]
    best = min(STRENGTH_PRESETS.keys(), key=lambda k: abs(k - elo))
    return STRENGTH_PRESETS[best]


def uci_options_for(strength: EngineStrength) -> dict:
    opts: dict = {
        "Threads": strength.threads,
        "Hash": strength.hash_mb,
    }
    if strength.elo >= 3200:
        # Force maximale : pas de LimitStrength, skill max
        opts["UCI_LimitStrength"] = False
        opts["Skill Level"] = 20
        return opts
    if strength.limit_strength:
        opts["UCI_LimitStrength"] = True
        # Stockfish UCI_Elo typiquement 1320–3190
        opts["UCI_Elo"] = min(max(strength.elo, 1320), 3190)
    else:
        opts["UCI_LimitStrength"] = False
        opts["Skill Level"] = int(strength.skill if strength.skill is not None else 10)
    return opts
