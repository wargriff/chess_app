"""Persistance des paramètres utilisateur."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.models.settings import AppSettings
from src.utils.paths import settings_file

logger = logging.getLogger("chesspro.settings")


class SettingsManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings_file()
        self.settings = AppSettings()

    def load(self) -> AppSettings:
        if not self.path.is_file():
            return self.settings
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.settings = AppSettings.from_dict(data)
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            logger.warning("Parametres invalides (%s), defauts utilises", exc)
            self.settings = AppSettings()
        return self.settings

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.settings.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def update(self, **kwargs) -> AppSettings:
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.save()
        return self.settings
