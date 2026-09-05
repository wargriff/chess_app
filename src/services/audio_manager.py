"""Gestionnaire audio centralise (sons desactivables)."""

from __future__ import annotations

import logging
import struct
import wave
from pathlib import Path

import pygame

from src.utils.paths import SOUND_ASSETS, ensure_data_dirs

logger = logging.getLogger("chesspro.audio")


def _write_tone_wav(path: Path, freq: float, duration: float = 0.12, volume: float = 0.35) -> None:
    rate = 22050
    n = int(rate * duration)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        frames = bytearray()
        for i in range(n):
            # simple decaying square-ish tone
            t = i / rate
            amp = volume * (1.0 - t / duration)
            sample = int(amp * 32767 * (1 if int(t * freq) % 2 == 0 else -1))
            frames += struct.pack("<h", sample)
        wf.writeframes(frames)


class AudioManager:
    EVENTS = {
        "move": ("move", "move.wav", 440),
        "capture": ("capture", "capture.wav", 220),
        "check": ("check", "check.wav", 660),
        "checkmate": ("checkmate", "checkmate.wav", 180),
        "promote": ("ui", "promote.wav", 520),
        "castle": ("move", "castle.wav", 330),
        "ui": ("ui", "click.wav", 700),
    }

    def __init__(self) -> None:
        self.enabled = True
        self.volume = 0.7
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._ready = False

    def initialize(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._ensure_default_sounds()
            for key, (subdir, filename, _) in self.EVENTS.items():
                path = SOUND_ASSETS / subdir / filename
                if path.is_file():
                    self._sounds[key] = pygame.mixer.Sound(str(path))
            self._ready = True
        except pygame.error as exc:
            logger.warning("Audio indisponible: %s", exc)
            self._ready = False

    def _ensure_default_sounds(self) -> None:
        ensure_data_dirs()
        for key, (subdir, filename, freq) in self.EVENTS.items():
            path = SOUND_ASSETS / subdir / filename
            if not path.is_file():
                try:
                    _write_tone_wav(path, freq)
                except OSError as exc:
                    logger.warning("Impossible de generer %s: %s", path, exc)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        for sound in self._sounds.values():
            sound.set_volume(self.volume)

    def play(self, event: str) -> None:
        if not self.enabled or not self._ready:
            return
        sound = self._sounds.get(event)
        if sound is None:
            return
        sound.set_volume(self.volume)
        sound.play()
