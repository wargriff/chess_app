"""Modèle joueur."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PlayerInfo:
    name: str
    is_white: bool
    is_engine: bool = False
    elo: int | None = None

    @property
    def color_label(self) -> str:
        return "Blancs" if self.is_white else "Noirs"

    @property
    def display_name(self) -> str:
        if self.is_engine:
            return f"Stockfish ({self.elo} ELO)" if self.elo else "Stockfish"
        return self.name
