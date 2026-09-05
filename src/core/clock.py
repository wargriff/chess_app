"""Horloge d'échecs avec increment."""

from __future__ import annotations


class ChessClock:
    def __init__(self, minutes: int = 10, increment: int = 0) -> None:
        self.minutes = minutes
        self.increment = increment
        self.enabled = minutes > 0
        base = float(minutes * 60)
        self.white_seconds = base
        self.black_seconds = base
        self.running = False
        self.flagged_white: bool | None = None

    def reset(self, minutes: int | None = None, increment: int | None = None) -> None:
        if minutes is not None:
            self.minutes = minutes
        if increment is not None:
            self.increment = increment
        self.enabled = self.minutes > 0
        base = float(self.minutes * 60)
        self.white_seconds = base
        self.black_seconds = base
        self.running = False
        self.flagged_white = None

    def set_control(self, minutes: int, increment: int) -> None:
        self.reset(minutes, increment)

    def start(self) -> None:
        if self.enabled:
            self.running = True

    def pause(self) -> None:
        self.running = False

    def tick(self, dt: float, active_white: bool) -> None:
        if not self.running or not self.enabled or self.flagged_white is not None:
            return
        if active_white:
            self.white_seconds = max(0.0, self.white_seconds - dt)
            if self.white_seconds <= 0:
                self.flagged_white = True
                self.running = False
        else:
            self.black_seconds = max(0.0, self.black_seconds - dt)
            if self.black_seconds <= 0:
                self.flagged_white = False
                self.running = False

    def on_move(self, mover_white: bool) -> None:
        if not self.enabled:
            return
        if mover_white:
            self.white_seconds += self.increment
        else:
            self.black_seconds += self.increment

    def format_time(self, seconds: float) -> str:
        total = max(0, int(seconds))
        if total >= 3600:
            h = total // 3600
            m = (total % 3600) // 60
            s = total % 60
            return f"{h}:{m:02d}:{s:02d}"
        m = total // 60
        s = total % 60
        return f"{m}:{s:02d}"

    def label(self) -> str:
        if not self.enabled:
            return "Sans limite"
        if self.increment:
            return f"{self.minutes}+{self.increment}"
        return f"{self.minutes} min"

    def is_low_time(self, seconds: float) -> bool:
        return self.enabled and seconds <= 20.0
