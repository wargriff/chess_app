"""Serveur HTTP local pour tester les mises a jour automatiques."""

from __future__ import annotations

import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RELEASES_DIR = os.path.join(ROOT, "dist", "releases")
HOST = "127.0.0.1"
PORT = 8765


def main() -> None:
    if not os.path.isdir(RELEASES_DIR):
        raise SystemExit(f"Dossier introuvable : {RELEASES_DIR}\nLancez d'abord : py -3.12 tools/build_release.py")

    os.chdir(RELEASES_DIR)
    server = ThreadingHTTPServer((HOST, PORT), SimpleHTTPRequestHandler)
    print(f"Serving {RELEASES_DIR}")
    print(f"Manifeste : http://{HOST}:{PORT}/update.json")
    print("Dans dist/ChessPro/update_url.txt mettez cette URL, puis lancez ChessPro.exe")
    print("Ctrl+C pour arreter")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArret.")


if __name__ == "__main__":
    main()
