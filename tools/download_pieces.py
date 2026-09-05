"""Telecharge les sets de pieces Lichess (SVG -> PNG)."""

from __future__ import annotations

import os
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config.paths import piece_set_dir  # noqa: E402
from config.settings import PIECE_SETS  # noqa: E402

LICHESS_RAW = "https://raw.githubusercontent.com/lichess-org/lila/master/public/piece"
PIECE_FILES = ["wK", "wQ", "wR", "wB", "wN", "wP", "bK", "bQ", "bR", "bB", "bN", "bP"]
PNG_SIZE = 256


def _convert_svg_to_png(svg_path: str, png_path: str, size: int) -> None:
    import fitz

    doc = fitz.open(svg_path)
    page = doc[0]
    rect = page.rect
    scale = size / max(rect.width, rect.height, 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True)
    pix.save(png_path)
    doc.close()


def _set_complete(folder: str) -> bool:
    return all(os.path.isfile(os.path.join(folder, f"{name}.png")) for name in PIECE_FILES)


def _download_set(set_id: str) -> None:
    folder = piece_set_dir(set_id)
    os.makedirs(folder, exist_ok=True)
    if _set_complete(folder):
        print("  deja present, skip")
        return

    tmp = os.path.join(folder, "_tmp.svg")
    for name in PIECE_FILES:
        url = f"{LICHESS_RAW}/{set_id}/{name}.svg"
        png_path = os.path.join(folder, f"{name}.png")
        print(f"  {name}.png ...", end=" ", flush=True)
        urllib.request.urlretrieve(url, tmp)
        _convert_svg_to_png(tmp, png_path, PNG_SIZE)
        print("ok")

    if os.path.isfile(tmp):
        os.remove(tmp)

    preview_src = os.path.join(folder, "wN.png")
    preview_dst = os.path.join(folder, "preview.png")
    if os.path.isfile(preview_src):
        import shutil
        shutil.copy2(preview_src, preview_dst)


def main() -> None:
    sets = [item["id"] for item in PIECE_SETS]
    print(f"Telechargement de {len(sets)} sets Lichess vers assets/pieces/")
    for set_id in sets:
        print(f"\n[{set_id}]")
        try:
            _download_set(set_id)
        except Exception as exc:
            print(f"  ECHEC: {exc}")

    default = piece_set_dir("california")
    legacy = os.path.join(os.path.dirname(default), "")
    for name in PIECE_FILES:
        src = os.path.join(default, f"{name}.png")
        dst = os.path.join(legacy, f"{name}.png")
        if os.path.isfile(src):
            import shutil
            shutil.copy2(src, dst)
    print("\nTermine.")


if __name__ == "__main__":
    main()
