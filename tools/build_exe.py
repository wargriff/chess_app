"""Compile Chess Pro en executable Windows (.exe) avec PyInstaller."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIST_DIR = os.path.join(ROOT, "dist")
BUILD_DIR = os.path.join(ROOT, "build")
TOOLS_DIR = os.path.join(ROOT, "tools")
APP_DIR = os.path.join(DIST_DIR, "ChessPro")

_LEGACY_LAUNCHERS = (
    "Jouer.vbs",
    "OUVRIR-LE-JEU.vbs",
    "Lancer Chess Pro.vbs",
)


def _unblock_folder(path: str) -> None:
    if os.name != "nt":
        return
    ps = (
        f"Get-ChildItem -LiteralPath '{path}' -Recurse -File | "
        f"ForEach-Object {{ Unblock-File -LiteralPath $_.FullName -ErrorAction SilentlyContinue }}"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        check=False,
    )


def _bat_launcher(exe_name: str = "ChessPro.exe") -> str:
    return (
        "@echo off\r\n"
        "cd /d \"%~dp0\"\r\n"
        f"if not exist \"%~dp0{exe_name}\" (\r\n"
        "  echo ChessPro.exe introuvable dans %~dp0\r\n"
        "  echo Utilisez le dossier dist\\ChessPro (pas build\\ChessPro).\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        f"start \"\" /D \"%~dp0\" \"%~dp0{exe_name}\"\r\n"
    )


def _create_shortcut(app_dir: str, exe_path: str) -> None:
    lnk_path = os.path.join(app_dir, "Chess Pro.lnk")
    script = os.path.join(app_dir, "_create_shortcut.ps1")
    with open(script, "w", encoding="utf-8") as handle:
        handle.write(
            f"$ws = New-Object -ComObject WScript.Shell\n"
            f"$s = $ws.CreateShortcut('{lnk_path}')\n"
            f"$s.TargetPath = '{exe_path}'\n"
            f"$s.WorkingDirectory = '{app_dir}'\n"
            f"$s.IconLocation = '{exe_path},0'\n"
            f"$s.Description = 'Chess Pro'\n"
            f"$s.Save()\n"
        )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script],
        check=False,
    )
    try:
        os.remove(script)
    except OSError:
        pass


def _remove_legacy_launchers() -> None:
    for folder in (ROOT, APP_DIR, os.path.join(BUILD_DIR, "ChessPro")):
        for name in _LEGACY_LAUNCHERS:
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


def _write_launchers(app_dir: str) -> None:
    exe_path = os.path.join(app_dir, "ChessPro.exe")
    launcher_bat = _bat_launcher()

    for name in ("JOUEZ-ICI.bat", "Jouer.bat"):
        with open(os.path.join(app_dir, name), "w", encoding="utf-8") as handle:
            handle.write(launcher_bat)

    with open(os.path.join(app_dir, "INSTALLER.bat"), "w", encoding="utf-8") as handle:
        handle.write(
            "@echo off\r\n"
            "cd /d \"%~dp0\"\r\n"
            "powershell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0install_windows.ps1\"\r\n"
            "pause\r\n"
        )

    shutil.copy2(os.path.join(TOOLS_DIR, "install_windows.ps1"), os.path.join(app_dir, "install_windows.ps1"))
    shutil.copy2(os.path.join(TOOLS_DIR, "apply_update.ps1"), os.path.join(app_dir, "apply_update.ps1"))

    prereq_src = os.path.join(TOOLS_DIR, "installer_prerequis.bat")
    if os.path.isfile(prereq_src):
        shutil.copy2(prereq_src, os.path.join(app_dir, "INSTALLER_PREREQUIS.bat"))

    readme = os.path.join(app_dir, "LISEZMOI.txt")
    with open(readme, "w", encoding="utf-8") as handle:
        handle.write(
            "CHESS PRO - Lancement sous Windows\n"
            "==================================\n\n"
            "1. Double-cliquez sur INSTALLER.bat (une seule fois)\n"
            "   -> debloque les fichiers pour Windows Defender\n\n"
            "2. Lancez le jeu avec (depuis l'Explorateur Windows) :\n"
            "      - JOUEZ-ICI.bat  (RECOMMANDE)\n"
            "      - ChessPro.exe   (direct)\n"
            "      - Chess Pro.lnk  (raccourci)\n\n"
            "   NE double-cliquez PAS les .bat depuis Cursor/VS Code.\n"
            "   Les fichiers .vbs sont desactives sur certains PC Windows.\n\n"
            "3. Dossier a utiliser : dist\\ChessPro\\ (PAS build\\ChessPro\\)\n"
            "   Gardez tout le dossier (exe + _internal + DLL).\n\n"
            f"Chemin : {app_dir}\n"
        )

    _create_shortcut(app_dir, exe_path)
    print("  Lanceurs : JOUEZ-ICI.bat, ChessPro.exe, Chess Pro.lnk, INSTALLER.bat")


def _neutralize_build_stub() -> None:
    """Evite de lancer l'exe incomplet laisse par PyInstaller dans build/."""
    stub_dir = os.path.join(BUILD_DIR, "ChessPro")
    if not os.path.isdir(stub_dir):
        return

    bad_exe = os.path.join(stub_dir, "ChessPro.exe")
    if os.path.isfile(bad_exe):
        try:
            os.remove(bad_exe)
        except OSError:
            pass

    redirect_bat = os.path.join(stub_dir, "OUVRIR-LE-JEU.bat")
    with open(redirect_bat, "w", encoding="utf-8") as handle:
        handle.write(
            "@echo off\r\n"
            "echo Ce dossier est temporaire (build). Ouverture du jeu dans dist\\ChessPro...\r\n"
            f"start \"\" \"{os.path.join(APP_DIR, 'JOUEZ-ICI.bat')}\"\r\n"
        )

    readme = os.path.join(stub_dir, "NE-PAS-LANCER-ICI.txt")
    with open(readme, "w", encoding="utf-8") as handle:
        handle.write(
            "DOSSIER DE COMPILATION INTERMEDIAIRE\n"
            "==================================\n\n"
            "Ne lancez rien ici. Utilisez :\n"
            f"  {APP_DIR}\n\n"
            "Double-cliquez sur OUVRIR-LE-JEU.bat pour ouvrir le bon dossier.\n"
        )

    print("  build\\ChessPro : exe incomplet retire, utilisez dist\\ChessPro")


def _write_root_launcher() -> None:
    launcher = os.path.join(ROOT, "Lancer Chess Pro.bat")
    with open(launcher, "w", encoding="utf-8") as handle:
        handle.write(
            "@echo off\r\n"
            "cd /d \"%~dp0\"\r\n"
            f"set \"GAME={os.path.join(APP_DIR, 'JOUEZ-ICI.bat')}\"\r\n"
            "if not exist \"%GAME%\" (\r\n"
            "  echo Compilez d'abord : py -3.12 tools\\build_exe.py\r\n"
            "  pause\r\n"
            "  exit /b 1\r\n"
            ")\r\n"
            "start \"\" \"%GAME%\"\r\n"
        )
    print(f"  Lanceur racine : {launcher}")


def _ensure_dependencies() -> None:
    missing: list[str] = []
    for module, package in (("pygame", "pygame"), ("chess", "python-chess"), ("PyInstaller", "pyinstaller")):
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        print("Installation des dependances :", ", ".join(missing))
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
    req = os.path.join(ROOT, "requirements.txt")
    if os.path.isfile(req):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req])


def main() -> None:
    _ensure_dependencies()
    _remove_legacy_launchers()

    subprocess.check_call([sys.executable, os.path.join(TOOLS_DIR, "generate_version_info.py")], cwd=ROOT)

    assets = os.path.join(ROOT, "assets")
    sep = ";" if os.name == "nt" else ":"
    add_data = f"{assets}{sep}assets"
    version_file = os.path.join(TOOLS_DIR, "version_info.txt")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        os.path.join(ROOT, "main.py"),
        "--name=ChessPro",
        "--onedir",
        "--noupx",
        "--windowed",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={ROOT}",
        f"--paths={ROOT}",
        f"--add-data={add_data}",
        f"--version-file={version_file}",
        "--hidden-import=chess.engine",
        "--hidden-import=chess.polyglot",
        "--hidden-import=src",
        "--hidden-import=src.app",
        "--collect-submodules=chess",
        "--collect-submodules=src",
        "--collect-all=pygame",
        "--collect-binaries=pygame",
        "--noconfirm",
        "--clean",
    ]

    print("Compilation (--onedir, sans UPX)...")
    subprocess.check_call(cmd, cwd=ROOT)

    exe_path = os.path.join(APP_DIR, "ChessPro.exe")
    if not os.path.isfile(exe_path):
        raise SystemExit(
            f"Echec : {exe_path} introuvable.\n"
            "N'utilisez PAS build\\ChessPro\\ — lancez uniquement dist\\ChessPro\\"
        )

    print("Copie des DLL runtime (MSVC)...")
    subprocess.check_call([sys.executable, os.path.join(TOOLS_DIR, "bundle_runtime.py")], cwd=ROOT)

    # Bundler Stockfish a cote de l'exe
    for src_name, dst_name in (
        (os.path.join(ROOT, "stockfish", "stockfish.exe"), os.path.join(APP_DIR, "stockfish", "stockfish.exe")),
        (os.path.join(ROOT, "engines", "stockfish.exe"), os.path.join(APP_DIR, "engines", "stockfish.exe")),
    ):
        if os.path.isfile(src_name):
            os.makedirs(os.path.dirname(dst_name), exist_ok=True)
            shutil.copy2(src_name, dst_name)
            print(f"  Stockfish copie -> {dst_name}")

    print("Deblocage des fichiers (zone Internet)...")
    _unblock_folder(APP_DIR)
    _write_launchers(APP_DIR)
    _neutralize_build_stub()
    _write_root_launcher()
    _remove_legacy_launchers()

    print("Verification des DLL...")
    subprocess.check_call([sys.executable, os.path.join(TOOLS_DIR, "verify_build.py")], cwd=ROOT)

    total = sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, _, filenames in os.walk(APP_DIR)
        for filename in filenames
    )
    size_mb = total / (1024 * 1024)

    print(f"\nJeu pret dans : {APP_DIR}")
    print(f"Taille totale : {size_mb:.1f} Mo")
    print("\n>>> Lancez dist\\ChessPro\\JOUEZ-ICI.bat ou ChessPro.exe <<<")
    print(">>> (PAS de .vbs — bloque sur votre PC Windows) <<<")


if __name__ == "__main__":
    main()
