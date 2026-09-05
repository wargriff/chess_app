"""Detection et telechargement de Stockfish."""

from __future__ import annotations

import logging
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

from src.utils.paths import STOCKFISH_DIR, ensure_data_dirs, stockfish_candidates

logger = logging.getLogger("chesspro.engine")

STOCKFISH_RELEASE_URL = (
    "https://github.com/official-stockfish/Stockfish/releases/download/"
    "sf_17.1/stockfish-windows-x86-64-avx2.zip"
)


def find_stockfish_binary(custom_path: str | None = None) -> Path | None:
    for candidate in stockfish_candidates(custom_path):
        if not candidate:
            continue
        path = candidate.expanduser()
        if path.is_file():
            return path.resolve()
        which = shutil.which(str(candidate))
        if which:
            return Path(which).resolve()
    return None


def download_stockfish() -> Path | None:
    ensure_data_dirs()
    zip_path = STOCKFISH_DIR / "stockfish.zip"
    extract_dir = STOCKFISH_DIR / "_extract"
    try:
        logger.info("Telechargement Stockfish...")
        urlretrieve(STOCKFISH_RELEASE_URL, zip_path)
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(extract_dir)
        for path in extract_dir.rglob("stockfish*.exe"):
            target = STOCKFISH_DIR / "stockfish.exe"
            shutil.copy2(path, target)
            logger.info("Stockfish installe: %s", target)
            return target
    except OSError as exc:
        logger.error("Echec telechargement Stockfish: %s", exc)
        return None
    finally:
        if zip_path.is_file():
            zip_path.unlink(missing_ok=True)
        if extract_dir.is_dir():
            shutil.rmtree(extract_dir, ignore_errors=True)
    return None


def resolve_stockfish(custom_path: str | None = None, allow_download: bool = True) -> Path | None:
    found = find_stockfish_binary(custom_path)
    if found:
        return found
    if allow_download:
        return download_stockfish()
    return None
