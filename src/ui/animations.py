"""Système d'animations fluides pour coups, captures, roque et sélection."""

from __future__ import annotations

import math
import time

import chess

from src.models.settings import MOVE_ANIM_MS, SELECT_PULSE_SPEED


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_out_back(t: float) -> float:
    t = max(0.0, min(1.0, t))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


_CASTLING_ROOK: dict[tuple[int, int], tuple[int, int]] = {
    (chess.E1, chess.G1): (chess.H1, chess.F1),
    (chess.E8, chess.G8): (chess.H8, chess.F8),
    (chess.E1, chess.C1): (chess.A1, chess.D1),
    (chess.E8, chess.C8): (chess.A8, chess.D8),
}


def castling_rook_squares(move: chess.Move) -> tuple[chess.Square, chess.Square] | None:
    return _CASTLING_ROOK.get((move.from_square, move.to_square))


class PieceSlide:
    __slots__ = ("symbol", "from_pos", "to_pos", "hidden_square")

    def __init__(
        self,
        symbol: str,
        from_pos: tuple[float, float],
        to_pos: tuple[float, float],
        hidden_square: chess.Square,
    ) -> None:
        self.symbol = symbol
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.hidden_square = hidden_square

    def position_at(self, t: float, lift_px: float) -> tuple[float, float]:
        eased = ease_out_back(t)
        fx, fy = self.from_pos
        tx, ty = self.to_pos
        lift = math.sin(t * math.pi) * lift_px
        x = fx + (tx - fx) * eased
        y = fy + (ty - fy) * eased - lift
        return x, y


class MoveAnimation:
    def __init__(
        self,
        move: chess.Move,
        slides: list[PieceSlide],
        capture: bool,
        captured_symbol: str | None = None,
        capture_square: chess.Square | None = None,
        duration_ms: int = MOVE_ANIM_MS,
        lift_px: float = 14.0,
    ) -> None:
        self.move = move
        self.slides = slides
        self.capture = capture
        self.captured_symbol = captured_symbol
        self.capture_square = capture_square if capture_square is not None else move.to_square
        self.duration_ms = duration_ms
        self.lift_px = lift_px
        self.started = time.monotonic()
        self.done = False

    def progress(self) -> float:
        elapsed = (time.monotonic() - self.started) * 1000
        return ease_out_cubic(elapsed / self.duration_ms)

    def capture_alpha(self) -> int:
        if not self.capture or not self.captured_symbol:
            return 0
        t = self.progress()
        if t < 0.55:
            return 255
        fade = (t - 0.55) / 0.45
        return int(255 * (1.0 - ease_out_cubic(fade)))

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
        capture_square: chess.Square | None = None,
        rook_symbol: str | None = None,
        rook_from: tuple[float, float] | None = None,
        rook_to: tuple[float, float] | None = None,
        rook_hidden: chess.Square | None = None,
        square_size: int = 64,
    ) -> None:
        lift = max(8.0, square_size * 0.22)
        duration = int(MOVE_ANIM_MS * (0.85 + min(1.15, square_size / 72)))
        slides = [
            PieceSlide(piece_symbol, from_pos, to_pos, move.to_square),
        ]
        if rook_symbol and rook_from and rook_to and rook_hidden is not None:
            slides.append(PieceSlide(rook_symbol, rook_from, rook_to, rook_hidden))

        self.move_anim = MoveAnimation(
            move,
            slides,
            capture,
            captured_symbol,
            capture_square,
            duration_ms=duration,
            lift_px=lift,
        )

    def cancel(self) -> None:
        self.move_anim = None

    def update(
        self,
        dt: float,
        selected: chess.Square | None,
        ai_thinking: bool,
        menu_open: bool,
    ) -> None:
        if self.move_anim is not None:
            if not self.move_anim.update():
                self.move_anim = None

        if selected is not None and not self.busy:
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
        raw = 1.0 + math.sin(self.select_phase) * 0.04
        return round(raw, 2)

    def think_pulse(self) -> float:
        return 0.65 + 0.35 * math.sin(self.think_phase)

    def menu_alpha(self) -> int:
        return int(190 * ease_out_cubic(self.menu_phase))
