"""Compile l'exe et produit le package de mise a jour (zip + update.json)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIST_DIR = os.path.join(ROOT, "dist")
APP_DIR = os.path.join(DIST_DIR, "ChessPro")
RELEASES_DIR = os.path.join(DIST_DIR, "releases")
TOOLS_DIR = os.path.join(ROOT, "tools")

sys.path.insert(0, ROOT)
from config import version as app_version  # noqa: E402


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _create_zip(source_dir: str, zip_path: str) -> int:
    total = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for dirpath, _, filenames in os.walk(source_dir):
            for filename in filenames:
                full = os.path.join(dirpath, filename)
                rel = os.path.relpath(full, source_dir)
                archive.write(full, rel)
                total += os.path.getsize(full)
    return total


def main() -> None:
    subprocess.check_call([sys.executable, os.path.join(TOOLS_DIR, "generate_version_info.py")], cwd=ROOT)
    subprocess.check_call([sys.executable, os.path.join(TOOLS_DIR, "build_exe.py")], cwd=ROOT)

    if not os.path.isdir(APP_DIR):
        raise SystemExit(f"Dossier application introuvable : {APP_DIR}")

    os.makedirs(RELEASES_DIR, exist_ok=True)
    zip_name = f"{app_version.APP_ID}-{app_version.VERSION}-b{app_version.BUILD}.zip"
    zip_path = os.path.join(RELEASES_DIR, zip_name)

    if os.path.isfile(zip_path):
        os.remove(zip_path)

    print(f"Creation de l'archive : {zip_name}")
    total_size = _create_zip(APP_DIR, zip_path)
    digest = _sha256_file(zip_path)

    manifest = {
        "app": app_version.APP_ID,
        "version": app_version.VERSION,
        "build": app_version.BUILD,
        "published": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "download": zip_name,
        "download_url": zip_name,
        "sha256": digest,
        "size_bytes": os.path.getsize(zip_path),
        "changelog": f"Mise a jour {app_version.VERSION} (build {app_version.BUILD})",
    }

    manifest_path = os.path.join(RELEASES_DIR, "update.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    shutil.copy2(manifest_path, os.path.join(APP_DIR, "update.json"))
    shutil.copy2(zip_path, os.path.join(APP_DIR, zip_name))

    sample_url = os.path.join(APP_DIR, "update_url.txt")
    with open(sample_url, "w", encoding="utf-8") as handle:
        handle.write(Path(manifest_path).as_uri() + "\n")

    readme = os.path.join(RELEASES_DIR, "README.txt")
    with open(readme, "w", encoding="utf-8") as handle:
        handle.write(
            "CHESS PRO - Publication des mises a jour\n"
            "========================================\n\n"
            f"Version : {app_version.VERSION} (build {app_version.BUILD})\n"
            f"Archive : {zip_name}\n"
            f"Manifeste : update.json\n\n"
            "Hebergement local (test) :\n"
            f"  py -3.12 tools/serve_updates.py\n\n"
            "Puis dans dist/ChessPro/update_url.txt :\n"
            "  http://127.0.0.1:8765/update.json\n\n"
            "Hebergement distant :\n"
            "  Uploadez update.json et le zip sur votre serveur / GitHub Releases.\n"
            "  Mettez l'URL du manifeste dans update_url.txt a cote de ChessPro.exe\n"
        )

    mettre_a_jour = os.path.join(APP_DIR, "METTRE_A_JOUR.bat")
    with open(mettre_a_jour, "w", encoding="utf-8") as handle:
        handle.write(
            "@echo off\r\n"
            "cd /d \"%~dp0\"\r\n"
            "echo Verification des mises a jour Chess Pro...\r\n"
            "powershell -NoProfile -ExecutionPolicy Bypass -Command "
            "\"& { $m = Get-Content -Raw '.\\update.json' | ConvertFrom-Json; "
            "Write-Host ('Derniere version publiee : ' + $m.version + ' build ' + $m.build) }\"\r\n"
            "echo.\r\n"
            "echo Lancez ChessPro.exe : la mise a jour est proposee au demarrage.\r\n"
            "echo Pour forcer une URL distante, editez update_url.txt\r\n"
            "pause\r\n"
        )

    print(f"\nRelease prete : {RELEASES_DIR}")
    print(f"  - {zip_name} ({os.path.getsize(zip_path) / (1024 * 1024):.1f} Mo)")
    print(f"  - update.json")
    print(f"  - Copie locale dans {APP_DIR}")
    print("\nCommande complete : py -3.12 tools/build_release.py")


if __name__ == "__main__":
    main()
