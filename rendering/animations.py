"""Système d'animations fluides pour coups, captures et sélection."""

from __future__ import annotations

import math
import time

import chess
import pygame

from config.settings import MOVE_ANIM_MS, SELECT_PULSE_SPEED


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_out_back(t: float) -> float:
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


class MoveAnimation:
    def __init__(
        self,
        move: chess.Move,
        piece_symbol: str,
        from_pos: tuple[float, float],
        to_pos: tuple[float, float],
        capture: bool,
        captured_symbol: str | None = None,
        duration_ms: int = MOVE_ANIM_MS,
    ) -> None:
        self.move = move
        self.piece_symbol = piece_symbol
        self.captured_symbol = captured_symbol
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.capture = capture
        self.duration_ms = duration_ms
        self.started = time.monotonic()
        self.capture_started = time.monotonic()
        self.done = False

    def progress(self) -> float:
        elapsed = (time.monotonic() - self.started) * 1000
        return ease_out_cubic(elapsed / self.duration_ms)

    def capture_alpha(self) -> int:
        if not self.capture:
            return 0
        elapsed = (time.monotonic() - self.capture_started) * 1000
        fade = min(1.0, elapsed / (self.duration_ms * 0.45))
        return int(255 * (1.0 - ease_out_cubic(fade)))

    def current_pos(self) -> tuple[float, float]:
        t = self.progress()
        fx, fy = self.from_pos
        tx, ty = self.to_pos
        lift = math.sin(t * math.pi) * 14
        x = fx + (tx - fx) * t
        y = fy + (ty - fy) * t - lift
        return x, y

    def update(self) -> bool:
        if self.progress() >= 1.0:
            self.done = True
        return not self.done


class AnimationManager:
    def __init__(self) -> None:
        self.move_anim: MoveAnimation | None = None
        self.select_phase = 0.0
        self.think_phase = 0.0
        self.menu_phase = 0.0

    @property
    def busy(self) -> bool:
        return self.move_anim is not None and not self.move_anim.done

    def play_move(
        self,
        move: chess.Move,
        piece_symbol: str,
        from_pos: tuple[float, float],
        to_pos: tuple[float, float],
        capture: bool,
        captured_symbol: str | None = None,
    ) -> None:
        self.move_anim = MoveAnimation(
            move, piece_symbol, from_pos, to_pos, capture, captured_symbol
        )

    def cancel(self) -> None:
        self.move_anim = None

    def update(self, dt: float, selected: chess.Square | None, ai_thinking: bool, menu_open: bool) -> None:
        if self.move_anim is not None:
            if not self.move_anim.update():
                self.move_anim = None

        if selected is not None:
            self.select_phase += dt * SELECT_PULSE_SPEED
        else:
            self.select_phase *= 0.85

        if ai_thinking:
            self.think_phase += dt * 4.0
        else:
            self.think_phase *= 0.9

        if menu_open:
            self.menu_phase = min(1.0, self.menu_phase + dt * 5.0)
        else:
            self.menu_phase = max(0.0, self.menu_phase - dt * 6.0)

    def selection_offset(self) -> float:
        return math.sin(self.select_phase) * 5.0

    def selection_scale(self) -> float:
        return 1.0 + math.sin(self.select_phase) * 0.04

    def think_pulse(self) -> float:
        return 0.65 + 0.35 * math.sin(self.think_phase)

    def menu_alpha(self) -> int:
        return int(190 * ease_out_cubic(self.menu_phase))
