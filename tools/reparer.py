"""Reparation complete Chess Pro (debloque, deps, assets, build)."""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS = os.path.join(ROOT, "tools")

REQUIRED = (
    "main.py",
    "config/settings.py",
    "core/game.py",
    "rendering/render.py",
    "rendering/gaming_style.py",
    "systems/loader.py",
    "tools/build_exe.py",
)


def main() -> int:
    os.chdir(ROOT)
    print("=" * 55)
    print("  Chess Pro - Reparation")
    print("=" * 55)

    missing = [f for f in REQUIRED if not os.path.isfile(os.path.join(ROOT, f))]
    if missing:
        print("Fichiers manquants :")
        for item in missing:
            print(f"  - {item}")
        print("\nRestaurez depuis git : git restore .")
        return 1

    if os.name == "nt":
        ps = (
            f"Get-ChildItem -LiteralPath '{ROOT}' -Recurse -File | "
            f"ForEach-Object {{ Unblock-File -LiteralPath $_.FullName -ErrorAction SilentlyContinue }}"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            check=False,
        )
        print("Fichiers debloques.")

    return subprocess.call([sys.executable, os.path.join(TOOLS, "mettre_a_jour.py")], cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
