"""Helpers purs sans dépendance UI."""

from __future__ import annotations

import random


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def choose_color(preference: str) -> bool:
    """Retourne True si le joueur humain joue les Blancs."""
    if preference == "white":
        return True
    if preference == "black":
        return False
    return bool(random.getrandbits(1))
