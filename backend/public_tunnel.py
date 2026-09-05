"""Tunnel public (Cloudflare quick tunnel) — QR / join depuis n'importe quel pays."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger("chess_pro_d4.tunnel")

ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = ROOT / "data" / "bin"
CLOUDFLARED_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    "cloudflared-windows-amd64.exe"
)
URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.I)


class PublicTunnel:
    """Expose localhost:port en HTTPS mondial (Los Angeles, EU, etc.)."""

    def __init__(self, local_port: int) -> None:
        self.local_port = local_port
        self.public_base: Optional[str] = None
        self.error: Optional[str] = None
        self._proc: Optional[subprocess.Popen[str]] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._started = False

    @property
    def ready(self) -> bool:
        return bool(self.public_base)

    def ensure_binary(self) -> Optional[Path]:
        """Cherche cloudflared ou le télécharge dans data/bin."""
        which = shutil.which("cloudflared")
        if which:
            return Path(which)
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        exe = BIN_DIR / "cloudflared.exe"
        if exe.is_file() and exe.stat().st_size > 1_000_000:
            return exe
        logger.info("Téléchargement cloudflared → %s", exe)
        try:
            tmp = exe.with_suffix(".download")
            urllib.request.urlretrieve(CLOUDFLARED_URL, tmp)
            tmp.replace(exe)
            return exe
        except Exception as exc:
            self.error = f"Impossible de télécharger cloudflared: {exc}"
            logger.exception(self.error)
            return None

    def start_async(self) -> None:
        if self._started:
            return
        self._started = True
        self._thread = threading.Thread(target=self._run, name="public-tunnel", daemon=True)
        self._thread.start()

    def wait_ready(self, timeout: float = 25.0) -> Optional[str]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.public_base:
                return self.public_base
            if self.error and not self._proc:
                break
            time.sleep(0.35)
        return self.public_base

    def _run(self) -> None:
        exe = self.ensure_binary()
        if not exe:
            return
        target = f"http://127.0.0.1:{self.local_port}"
        cmd = [str(exe), "tunnel", "--url", target, "--no-autoupdate"]
        logger.info("Démarrage tunnel public: %s", " ".join(cmd))
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception as exc:
            self.error = f"Échec lancement cloudflared: {exc}"
            logger.exception(self.error)
            return

        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            line = line.strip()
            if not line:
                continue
            logger.debug("cloudflared: %s", line)
            m = URL_RE.search(line)
            if m:
                with self._lock:
                    self.public_base = m.group(0).rstrip("/")
                    self.error = None
                logger.info("Tunnel public prêt: %s", self.public_base)
                # continue reading to keep process alive / log

        code = self._proc.wait()
        with self._lock:
            if not self.public_base:
                self.error = self.error or f"Tunnel terminé (code {code})"
            self.public_base = None
        logger.warning("Tunnel public arrêté (code %s)", code)

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def status(self) -> dict:
        return {
            "ready": self.ready,
            "public_base": self.public_base,
            "error": self.error,
            "local_port": self.local_port,
        }


# Instance globale initialisée depuis main
tunnel: Optional[PublicTunnel] = None


def init_tunnel(port: int) -> PublicTunnel:
    global tunnel
    tunnel = PublicTunnel(port)
    # Désactiver avec CHESS_NO_TUNNEL=1
    if os.environ.get("CHESS_NO_TUNNEL", "").strip() in ("1", "true", "yes"):
        tunnel.error = "Tunnel désactivé (CHESS_NO_TUNNEL)"
        return tunnel
    tunnel.start_async()
    return tunnel


def public_base_url(wait: float = 0.0) -> Optional[str]:
    if tunnel is None:
        return None
    if wait > 0 and not tunnel.ready:
        tunnel.wait_ready(wait)
    return tunnel.public_base
