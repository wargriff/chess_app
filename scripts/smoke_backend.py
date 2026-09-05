# -*- coding: utf-8 -*-
"""Smoke test Chess Pro D4 backend."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:3848"


def get(path: str):
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return r.status, json.load(r)


def post(path: str, data: dict):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.load(r)


def main() -> None:
    errors = []
    try:
        st, h = get("/health")
        print("health", st, h)
        if h.get("app") != "Chess Pro D4":
            errors.append(f"wrong app: {h}")
        if not h.get("ok"):
            errors.append("ok!=True")
    except Exception as e:
        errors.append(f"health: {e}")
        print("FATAL health", e)
        return

    for path in ["/api/health", "/api/engine/status", "/api/engine/levels", "/api/saves", "/api/rooms"]:
        try:
            st, body = get(path)
            print("GET", path, st, str(body)[:100])
        except Exception as e:
            errors.append(f"GET {path}: {e}")
            print("FAIL", path, e)

    try:
        st, g = post("/api/game/new", {"mode": "pve", "elo": 1200})
        print("new game", g.get("id"), g.get("fen", "")[:40])
        gid = g["id"]
        st, m = post(f"/api/game/{gid}/move", {"uci": "e2e4"})
        print("move", m.get("san"))
        st, ai = post("/api/engine/play", {"fen": "", "moves": m["moves"], "elo": 1200})
        print("ai", ai.get("uci"), ai.get("san"))
        st, an = post("/api/engine/analyze", {"fen": "", "moves": m["moves"] + [ai["uci"]], "depth": 10, "multipv": 2})
        print("analyze", an.get("eval"), "lines", len(an.get("lines") or []))
        st, room = post("/api/rooms", {"host_name": "Test"})
        print("room", room.get("code"), room.get("join_url"))
        code = room["code"]
        with urllib.request.urlopen(room["join_url"], timeout=5) as r:
            html = r.read().decode("utf-8", errors="replace")
            print("join page", r.status, "WebSocket" in html, len(html))
        try:
            urllib.request.urlopen(f"{BASE}/join/ZZZZZZ", timeout=3)
            errors.append("join bad code should 404")
        except urllib.error.HTTPError as e:
            print("join 404 ok", e.code)
    except Exception as e:
        errors.append(f"flow: {e}")
        print("FAIL flow", e)

    print("ERRORS:", errors or "none")


if __name__ == "__main__":
    main()
