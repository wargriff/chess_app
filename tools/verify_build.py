"""Verifie que l'exe PyInstaller embarque bien les DLL necessaires."""

from __future__ import annotations

import glob
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_DIR = os.path.join(ROOT, "dist", "ChessPro")


def _internal_dir(app_dir: str) -> str:
    for name in ("_internal", "internal"):
        path = os.path.join(app_dir, name)
        if os.path.isdir(path):
            return path
    return app_dir


def verify(app_dir: str = APP_DIR) -> list[str]:
    errors: list[str] = []
    exe = os.path.join(app_dir, "ChessPro.exe")
    if not os.path.isfile(exe):
        errors.append(f"ChessPro.exe introuvable : {exe}")
        return errors

    internal = _internal_dir(app_dir)
    python_dlls = glob.glob(os.path.join(internal, "python*.dll"))
    if not python_dlls:
        errors.append("DLL Python manquante (python3xx.dll) dans _internal")

    sdl_dlls = glob.glob(os.path.join(internal, "**", "SDL2*.dll"), recursive=True)
    if not sdl_dlls:
        errors.append("SDL2.dll manquante (pygame) — ajoutez --collect-all pygame au build")

    zlib_dlls = glob.glob(os.path.join(internal, "**", "zlib*.dll"), recursive=True)
    if not zlib_dlls:
        errors.append("zlib*.dll manquante")

    assets = os.path.join(internal, "assets")
    if not os.path.isdir(assets):
        alt = os.path.join(app_dir, "assets")
        if not os.path.isdir(alt):
            errors.append("Dossier assets/ manquant dans le build")

    return errors


def main() -> None:
    errors = verify()
    strict = "--strict" in sys.argv
    if errors:
        print("Verification du build : AVERTISSEMENTS")
        for item in errors:
            print(f"  - {item}")
        if strict:
            sys.exit(1)
        print("(Build conserve — installez pygame/chess puis recompilez si le jeu ne demarre pas)")
        sys.exit(0)
    print("Verification du build : OK (exe + DLL critiques presents)")


if __name__ == "__main__":
    main()
