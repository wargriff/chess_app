"""Tests parametres."""

from pathlib import Path

from src.models.settings import AppSettings
from src.services.settings_manager import SettingsManager


def test_settings_roundtrip(tmp_path: Path):
    path = tmp_path / "settings.json"
    mgr = SettingsManager(path)
    mgr.update(player_name="Testeur", elo=1600)
    other = SettingsManager(path)
    loaded = other.load()
    assert loaded.player_name == "Testeur"
    assert loaded.elo == 1600


def test_app_settings_from_dict():
    s = AppSettings.from_dict({"elo": 2000, "unknown": 1})
    assert s.elo == 2000
