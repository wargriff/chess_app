"""Copie les DLL MSVC/Python necessaires dans le dossier PyInstaller."""

from __future__ import annotations

import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_DIR = os.path.join(ROOT, "dist", "ChessPro")

RUNTIME_DLLS = (
    "vcruntime140.dll",
    "vcruntime140_1.dll",
    "msvcp140.dll",
)


def _internal_dir(app_dir: str) -> str:
    for name in ("_internal", "internal"):
        path = os.path.join(app_dir, name)
        if os.path.isdir(path):
            return path
    return app_dir


def _python_dll_name() -> str:
    version = sys.version_info
    return f"python{version.major}{version.minor}.dll"


def bundle_runtime(app_dir: str = APP_DIR) -> list[str]:
    if not os.path.isdir(app_dir):
        raise FileNotFoundError(f"Dossier application introuvable : {app_dir}")

    target = _internal_dir(app_dir)
    search_dirs = [
        sys.base_prefix,
        os.path.join(sys.base_prefix, "DLLs"),
        os.path.dirname(sys.executable),
    ]

    copied: list[str] = []
    for dll_name in (*RUNTIME_DLLS, _python_dll_name()):
        if os.path.isfile(os.path.join(target, dll_name)):
            continue
        for folder in search_dirs:
            source = os.path.join(folder, dll_name)
            if not os.path.isfile(source):
                continue
            shutil.copy2(source, os.path.join(target, dll_name))
            copied.append(dll_name)
            break
    return copied


def main() -> None:
    copied = bundle_runtime()
    if copied:
        print("DLL runtime copiees :", ", ".join(copied))
    else:
        print("DLL runtime deja presentes.")


if __name__ == "__main__":
    main()
