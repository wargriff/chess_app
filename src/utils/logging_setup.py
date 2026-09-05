"""Configuration logging vers data/logs."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from src.utils.paths import LOGS, ensure_data_dirs


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    ensure_data_dirs()
    logger = logging.getLogger("chesspro")
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        LOGS / "chesspro.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.WARNING)
    logger.addHandler(console)
    return logger
