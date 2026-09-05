"""Verification et installation automatique des mises a jour (Windows / exe)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from typing import Callable

from config import version as app_version
from config.paths import RUNTIME_DIR, user_data_dir


ProgressCallback = Callable[[float, str], None]


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    build: int
    download_url: str
    sha256: str
    size_bytes: int
    changelog: str
    published: str = ""

    @property
    def label(self) -> str:
        return f"v{self.version} (build {self.build})"


def parse_version(value: str) -> tuple[int, int, int]:
    parts = value.strip().split(".")
    nums: list[int] = []
    for part in parts[:3]:
        try:
            nums.append(int(part))
        except ValueError:
            nums.append(0)
    while len(nums) < 3:
        nums.append(0)
    return nums[0], nums[1], nums[2]


def is_newer(remote_version: str, remote_build: int, local_version: str, local_build: int) -> bool:
    remote = parse_version(remote_version)
    local = parse_version(local_version)
    if remote > local:
        return True
    if remote < local:
        return False
    return remote_build > local_build


def current_version_label() -> str:
    return f"{app_version.VERSION} (build {app_version.BUILD})"


def _read_update_url_file() -> str:
    for name in ("update_url.txt", "update.json"):
        path = os.path.join(RUNTIME_DIR, name)
        if not os.path.isfile(path):
            continue
        if name.endswith(".txt"):
            with open(path, encoding="utf-8") as handle:
                return handle.read().strip()
        return path
    config_path = os.path.join(user_data_dir(), "update_url.txt")
    if os.path.isfile(config_path):
        with open(config_path, encoding="utf-8") as handle:
            return handle.read().strip()
    return app_version.DEFAULT_UPDATE_MANIFEST_URL.strip()


def resolve_manifest_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        local_manifest = os.path.join(RUNTIME_DIR, "update.json")
        if os.path.isfile(local_manifest):
            return local_manifest
        return ""
    if raw.lower().startswith(("http://", "https://", "file://")):
        return raw
    if os.path.isfile(raw):
        return raw
    joined = os.path.join(RUNTIME_DIR, raw)
    if os.path.isfile(joined):
        return joined
    return raw


def _fetch_text(url: str, timeout: float = 12.0) -> str:
    if url.startswith("file://"):
        path = url[7:]
        if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
            path = path[1:]
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    if os.path.isfile(url):
        with open(url, encoding="utf-8") as handle:
            return handle.read()
    request = urllib.request.Request(url, headers={"User-Agent": f"{app_version.APP_ID}/{app_version.VERSION}"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _resolve_download_url(manifest_url: str, data: dict) -> str:
    if data.get("download_url"):
        return str(data["download_url"])
    download_name = data.get("download", "")
    if not download_name:
        raise ValueError("Manifeste invalide : champ download ou download_url manquant")
    if str(download_name).lower().startswith(("http://", "https://")):
        return str(download_name)
    base = manifest_url
    if base.startswith("file://"):
        base = base[7:]
        if os.name == "nt" and base.startswith("/") and len(base) > 2 and base[2] == ":":
            base = base[1:]
    if os.path.isfile(base):
        base = os.path.dirname(os.path.abspath(base))
    elif "://" in base:
        base = base.rsplit("/", 1)[0]
    return f"{base}/{download_name}".replace("\\", "/")


def parse_manifest(manifest_url: str, payload: str) -> UpdateInfo:
    data = json.loads(payload)
    version = str(data.get("version", "0.0.0"))
    build = int(data.get("build", 0))
    sha256 = str(data.get("sha256", "")).lower()
    size_bytes = int(data.get("size_bytes", 0))
    changelog = str(data.get("changelog", "")).strip()
    published = str(data.get("published", ""))
    download_url = _resolve_download_url(manifest_url, data)
    return UpdateInfo(
        version=version,
        build=build,
        download_url=download_url,
        sha256=sha256,
        size_bytes=size_bytes,
        changelog=changelog,
        published=published,
    )


def check_for_update(manifest_url: str | None = None) -> UpdateInfo | None:
    url = resolve_manifest_url(manifest_url or _read_update_url_file())
    if not url:
        return None
    try:
        payload = _fetch_text(url)
        info = parse_manifest(url, payload)
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, ValueError):
        return None
    if not is_newer(info.version, info.build, app_version.VERSION, app_version.BUILD):
        return None
    return info


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_update(info: UpdateInfo, on_progress: ProgressCallback | None = None) -> str:
    updates_dir = os.path.join(user_data_dir(), "updates")
    os.makedirs(updates_dir, exist_ok=True)
    filename = f"{app_version.APP_ID}-{info.version}-b{info.build}.zip"
    dest = os.path.join(updates_dir, filename)

    if on_progress:
        on_progress(0.02, "Connexion au serveur de mise a jour...")

    if info.download_url.startswith(("http://", "https://")):
        request = urllib.request.Request(
            info.download_url,
            headers={"User-Agent": f"{app_version.APP_ID}/{app_version.VERSION}"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            total = int(response.headers.get("Content-Length", info.size_bytes or 0))
            read = 0
            tmp_path = dest + ".part"
            with open(tmp_path, "wb") as handle:
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    handle.write(chunk)
                    read += len(chunk)
                    if on_progress and total > 0:
                        on_progress(min(0.82, 0.05 + (read / total) * 0.75), "Telechargement...")
            os.replace(tmp_path, dest)
    else:
        source = info.download_url
        if source.startswith("file://"):
            source = source[7:]
            if os.name == "nt" and source.startswith("/") and len(source) > 2 and source[2] == ":":
                source = source[1:]
        if not os.path.isfile(source):
            raise FileNotFoundError(f"Archive introuvable : {source}")
        shutil.copy2(source, dest)
        if on_progress:
            on_progress(0.75, "Archive locale copiee")

    if info.sha256:
        if on_progress:
            on_progress(0.86, "Verification de l'integrite...")
        digest = _sha256_file(dest)
        if digest.lower() != info.sha256.lower():
            os.remove(dest)
            raise ValueError("Echec verification SHA256 de la mise a jour")

    if on_progress:
        on_progress(0.92, "Preparation de l'installation...")
    return dest


def apply_update(zip_path: str, on_progress: ProgressCallback | None = None) -> None:
    install_dir = RUNTIME_DIR
    staging_dir = os.path.join(user_data_dir(), "updates", "staging")
    if os.path.isdir(staging_dir):
        shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)

    if on_progress:
        on_progress(0.94, "Extraction de la mise a jour...")
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(staging_dir)

    apply_script = os.path.join(install_dir, "apply_update.ps1")
    if not os.path.isfile(apply_script):
        bundled = os.path.join(os.path.dirname(__file__), "..", "tools", "apply_update.ps1")
        if os.path.isfile(bundled):
            shutil.copy2(bundled, apply_script)

    exe_name = f"{app_version.APP_ID}.exe"
    pid = os.getpid()

    if on_progress:
        on_progress(0.98, "Redemarrage pour appliquer la mise a jour...")

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        apply_script,
        "-InstallDir",
        install_dir,
        "-StagingDir",
        staging_dir,
        "-ExeName",
        exe_name,
        "-ParentPid",
        str(pid),
    ]
    subprocess.Popen(
        cmd,
        cwd=install_dir,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        if os.name == "nt"
        else 0,
        close_fds=True,
    )


def download_and_apply(info: UpdateInfo, on_progress: ProgressCallback | None = None) -> None:
    zip_path = download_update(info, on_progress=on_progress)
    apply_update(zip_path, on_progress=on_progress)


def run_update_check(only_if_frozen: bool = True) -> UpdateInfo | None:
    if only_if_frozen and not getattr(sys, "frozen", False):
        forced = os.environ.get("CHESSPRO_UPDATE_URL", "").strip()
        if not forced:
            return None
    return check_for_update()
