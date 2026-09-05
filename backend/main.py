"""Serveur API Chess Pro D4 — Stockfish + parties + rooms locales WebSocket."""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
import socket
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from contextlib import asynccontextmanager

import chess
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Racine projet sur sys.path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.engine.engine_config import strength_for_elo  # noqa: E402
from src.engine.stockfish_manager import StockfishManager  # noqa: E402
from src.services.save_manager import GameSaveData, SaveManager  # noqa: E402
from src.utils.logging_setup import setup_logging  # noqa: E402
from src.utils.paths import ensure_data_dirs  # noqa: E402
from backend import public_tunnel as tunnel_mod  # noqa: E402

logger = setup_logging()
ensure_data_dirs()

engine = StockfishManager()
saves = SaveManager()
_engine_lock = threading.Lock()

# Port libre façon http://127.0.0.1:3847/ (3847 souvent pris → 3848)
API_PORT = 3848


def _start_engine() -> None:
    if not engine.available:
        ok = engine.start(allow_download=True)
        if ok:
            engine.configure(1200)
        logger.info("Stockfish start=%s error=%s", ok, engine.error)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    threading.Thread(target=_start_engine, daemon=True).start()
    tunnel_mod.init_tunnel(API_PORT)
    yield
    if tunnel_mod.tunnel:
        tunnel_mod.tunnel.stop()


app = FastAPI(title="Chess Pro D4 API", version="3.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_ASSETS = ROOT / "assets"
if _ASSETS.is_dir():
    app.mount("/static", StaticFiles(directory=str(_ASSETS)), name="static")

_JOIN_TEMPLATE = (Path(__file__).resolve().parent / "templates" / "join.html").read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class NewGameRequest(BaseModel):
    mode: str = "pve"  # pve | pvp | eve
    elo: int = 1200
    color: str = "random"  # white | black | random
    time_minutes: int = 10
    time_increment: int = 0
    white_name: str = "Joueur"
    black_name: str = "Stockfish"


class MoveRequest(BaseModel):
    uci: str


class EngineMoveRequest(BaseModel):
    fen: str
    moves: list[str] = Field(default_factory=list)
    elo: int = 1200
    movetime_ms: int | None = None


class AnalyzeRequest(BaseModel):
    fen: str = ""
    moves: list[str] = Field(default_factory=list)
    depth: int = 15
    movetime_ms: int = 400
    multipv: int = 3


class EngineConfigureRequest(BaseModel):
    elo: int = 1200
    depth: int | None = None
    movetime_ms: int | None = None
    threads: int | None = None
    hash_mb: int | None = None
    multipv: int | None = None


class SaveRequest(BaseModel):
    mode: str = "PVE"
    moves: list[str] = Field(default_factory=list)
    white_name: str = "Joueur"
    black_name: str = "Stockfish"
    human_is_white: bool = True
    elo: int = 1200
    skill: int | None = 8
    time_minutes: int = 10
    time_increment: int = 0
    white_seconds: float = 600
    black_seconds: float = 600
    clock_enabled: bool = True
    result: str = "*"
    message: str = ""


class CreateRoomRequest(BaseModel):
    host_name: str = "Joueur 1"
    time_minutes: int = 10
    time_increment: int = 0


class JoinRoomRequest(BaseModel):
    name: str = "Joueur 2"


# ---------------------------------------------------------------------------
# In-memory games (vs Stockfish / local single)
# ---------------------------------------------------------------------------


@dataclass
class ServerGame:
    id: str
    mode: str
    board: chess.Board = field(default_factory=chess.Board)
    elo: int = 1200
    human_is_white: bool = True
    white_name: str = "Joueur"
    black_name: str = "Stockfish"
    white_seconds: float = 600
    black_seconds: float = 600
    time_minutes: int = 10
    time_increment: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def snapshot(self) -> dict[str, Any]:
        turn = "white" if self.board.turn == chess.WHITE else "black"
        over = self.board.is_game_over()
        result = self.board.result(claim_draw=True) if over else "*"
        status = "finished" if over else ("check" if self.board.is_check() else "playing")
        return {
            "id": self.id,
            "mode": self.mode,
            "fen": self.board.fen(),
            "moves": [m.uci() for m in self.board.move_stack],
            "san": _san_list(self.board),
            "turn": turn,
            "legal": [m.uci() for m in self.board.legal_moves],
            "white_name": self.white_name,
            "black_name": self.black_name,
            "elo": self.elo,
            "human_is_white": self.human_is_white,
            "white_seconds": self.white_seconds,
            "black_seconds": self.black_seconds,
            "time_minutes": self.time_minutes,
            "time_increment": self.time_increment,
            "status": status,
            "result": result,
            "check": self.board.is_check(),
            "checkmate": self.board.is_checkmate(),
            "stalemate": self.board.is_stalemate(),
            "created_at": self.created_at,
        }


GAMES: dict[str, ServerGame] = {}


def _san_list(board: chess.Board) -> list[str]:
    temp = chess.Board()
    out: list[str] = []
    for move in board.move_stack:
        out.append(temp.san(move))
        temp.push(move)
    return out


def _pv_san(board: chess.Board, pv: list[chess.Move], max_plies: int = 12) -> list[str]:
    b = board.copy(stack=False)
    out: list[str] = []
    for move in pv[:max_plies]:
        if move not in b.legal_moves:
            break
        out.append(b.san(move))
        b.push(move)
    return out


def _enrich_line(board: chess.Board, line: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(line)
    ucis = line.get("pv_uci") or []
    moves: list[chess.Move] = []
    for u in ucis:
        try:
            moves.append(chess.Move.from_uci(u))
        except ValueError:
            break
    enriched["pv_san"] = _pv_san(board, moves)
    return enriched


def _board_from(fen: str, moves: list[str]) -> chess.Board:
    board = chess.Board(fen) if fen else chess.Board()
    if moves and fen.count(" ") >= 5 and fen.startswith("rnbqkbnr/pppppppp"):
        # si FEN départ + moves, rejouer
        board = chess.Board()
    elif moves and not fen:
        board = chess.Board()
    if moves:
        # Rejouer depuis départ si liste fournie
        board = chess.Board()
        for u in moves:
            move = chess.Move.from_uci(u)
            if move not in board.legal_moves:
                raise HTTPException(400, f"Coup illégal dans l'historique: {u}")
            board.push(move)
    return board


# ---------------------------------------------------------------------------
# Local rooms (WebSocket realtime)
# ---------------------------------------------------------------------------


@dataclass
class RoomPlayer:
    id: str
    name: str
    color: str  # white | black
    ws: WebSocket | None = None


@dataclass
class LocalRoom:
    code: str
    board: chess.Board = field(default_factory=chess.Board)
    host: RoomPlayer | None = None
    guest: RoomPlayer | None = None
    white_seconds: float = 600
    black_seconds: float = 600
    time_minutes: int = 10
    time_increment: int = 0
    status: str = "waiting"  # waiting | playing | finished
    created_at: float = field(default_factory=time.time)
    last_move_at: float = field(default_factory=time.time)

    def players_count(self) -> int:
        n = 0
        if self.host and self.host.ws:
            n += 1
        if self.guest and self.guest.ws:
            n += 1
        return n

    def both_connected(self) -> bool:
        return bool(self.host and self.host.ws and self.guest and self.guest.ws)

    def snapshot(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "status": self.status,
            "fen": self.board.fen(),
            "moves": [m.uci() for m in self.board.move_stack],
            "san": _san_list(self.board),
            "turn": "white" if self.board.turn else "black",
            "legal": [m.uci() for m in self.board.legal_moves] if self.status == "playing" else [],
            "white_name": (self.host.name if self.host and self.host.color == "white" else (self.guest.name if self.guest else "—")),
            "black_name": (self.host.name if self.host and self.host.color == "black" else (self.guest.name if self.guest else "—")),
            "host_name": self.host.name if self.host else None,
            "guest_name": self.guest.name if self.guest else None,
            "players": self.players_count(),
            "white_seconds": self.white_seconds,
            "black_seconds": self.black_seconds,
            "time_minutes": self.time_minutes,
            "time_increment": self.time_increment,
            "check": self.board.is_check(),
            "checkmate": self.board.is_checkmate(),
            "stalemate": self.board.is_stalemate(),
            "result": self.board.result(claim_draw=True) if self.board.is_game_over() else "*",
        }


ROOMS: dict[str, LocalRoom] = {}


def local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def make_room_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


# ---------------------------------------------------------------------------
# Health / meta
# ---------------------------------------------------------------------------


def _join_urls(code: str) -> dict[str, Any]:
    """Liens local / LAN / mondial (tunnel HTTPS)."""
    code = code.upper()
    ip = local_ip()
    local_url = f"http://127.0.0.1:{API_PORT}/"
    join_local = f"http://127.0.0.1:{API_PORT}/join/{code}"
    join_lan = f"http://{ip}:{API_PORT}/join/{code}"
    # Attendre le tunnel si besoin (LA / autres pays)
    pub = tunnel_mod.public_base_url(wait=20.0)
    join_public = f"{pub}/join/{code}" if pub else None
    primary = join_public or join_lan
    return {
        "join_url": primary,
        "web_url": primary,
        "qr_payload": primary,
        "join_url_local": join_local,
        "join_url_lan": join_lan,
        "join_url_public": join_public,
        "home_url": local_url,
        "public_base": pub,
        "worldwide": bool(join_public),
        "api_base": pub or f"http://{ip}:{API_PORT}",
        "local_ip": ip,
        "port": API_PORT,
    }


def _health_payload() -> dict[str, Any]:
    pub = tunnel_mod.public_base_url(wait=0)
    tstat = tunnel_mod.tunnel.status() if tunnel_mod.tunnel else {"ready": False}
    return {
        "ok": True,
        "app": "Chess Pro D4",
        "status": "ready" if engine.available else "starting",
        "stockfish": engine.available,
        "stockfish_label": engine.engine_label if engine.available else (engine.error or "Démarrage Stockfish…"),
        "local_ip": local_ip(),
        "port": API_PORT,
        "url": f"http://127.0.0.1:{API_PORT}/",
        "public_base": pub,
        "worldwide": bool(pub),
        "tunnel": tstat,
    }


@app.get("/api/tunnel")
def tunnel_status() -> dict[str, Any]:
    """État du lien mondial (QR utilisable hors Wi‑Fi / autre pays)."""
    if tunnel_mod.tunnel is None:
        return {"ready": False, "error": "Tunnel non initialisé"}
    # Petit wait pour les clients qui créent une room trop tôt
    tunnel_mod.public_base_url(wait=2.0)
    return tunnel_mod.tunnel.status()


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    """Page navigateur : http://127.0.0.1:3848/"""
    ip = local_ip()
    pub = tunnel_mod.public_base_url(wait=0) or ""
    pub_line = (
        f'Monde entier : <a href="{pub}/">{pub}/</a>'
        if pub
        else "Monde entier : tunnel en cours d’ouverture… (rechargez dans quelques secondes)"
    )
    html = f"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Chess Pro D4</title>
<style>
body{{margin:0;min-height:100vh;font-family:Segoe UI,system-ui,sans-serif;background:#080605;color:#EBE1CD;
display:flex;align-items:center;justify-content:center}}
.card{{max-width:440px;width:92%;padding:28px;border:1px solid #3A342C;border-radius:14px;background:#12100E}}
h1{{margin:0 0 8px;color:#D4A548;font-size:1.5rem}}
p{{color:#8C7D6C;line-height:1.5}}
input{{width:100%;padding:12px;border-radius:8px;border:1px solid #3A342C;background:#080605;color:#EBE1CD;
font-size:1.2rem;letter-spacing:.25em;text-transform:uppercase;text-align:center;margin:12px 0}}
button{{width:100%;padding:12px;border:0;border-radius:8px;background:#D4A548;color:#080605;font-weight:700;cursor:pointer}}
a{{color:#D4A548;word-break:break-all}}
.ok{{color:#50BE6E;font-size:.9rem}}
</style></head><body>
<div class="card">
  <h1>Chess Pro D4</h1>
  <p class="ok">Serveur actif · port {API_PORT}</p>
  <p>PC : <a href="http://127.0.0.1:{API_PORT}/">http://127.0.0.1:{API_PORT}/</a><br/>
  Wi‑Fi local : <a href="http://{ip}:{API_PORT}/">http://{ip}:{API_PORT}/</a><br/>
  {pub_line}</p>
  <p>Code de partie</p>
  <input id="code" maxlength="8" placeholder="ABC123" autocomplete="off"/>
  <button type="button" onclick="go()">Rejoindre</button>
  <p style="margin-top:16px;font-size:.85rem">API · <a href="/health">/health</a> · <a href="/api/tunnel">/api/tunnel</a></p>
</div>
<script>
function go(){{
  const c=(document.getElementById('code').value||'').trim().toUpperCase();
  if(c.length>=4) location.href='/join/'+encodeURIComponent(c);
}}
document.getElementById('code').addEventListener('keydown',e=>{{ if(e.key==='Enter') go(); }});
const q=new URLSearchParams(location.search).get('code');
if(q) location.replace('/join/'+encodeURIComponent(q.toUpperCase()));
</script>
</body></html>"""
    return HTMLResponse(content=html)


@app.get("/api")
def api_root() -> dict[str, Any]:
    return {
        "app": "Chess Pro D4",
        "ok": True,
        "health": "/health",
        "docs": "/docs",
        "local_ip": local_ip(),
        "port": API_PORT,
        "url": f"http://127.0.0.1:{API_PORT}/",
    }


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, Any]:
    return _health_payload()


@app.get("/api/engine/status")
def engine_status() -> dict[str, Any]:
    return {
        "online": engine.available,
        "label": engine.engine_label,
        "status": engine.status_label,
        "elo": engine.elo,
        "movetime_ms": engine.movetime_ms,
        "depth": engine.depth,
        "error": engine.error,
    }


@app.get("/api/engine/levels")
def engine_levels() -> dict[str, Any]:
    from src.engine.engine_config import ELO_LEVELS_UI, STRENGTH_PRESETS

    return {
        "levels": [
            {
                **lvl,
                "movetime_ms": STRENGTH_PRESETS[lvl["elo"]].movetime_ms,
                "threads": STRENGTH_PRESETS[lvl["elo"]].threads,
                "hash_mb": STRENGTH_PRESETS[lvl["elo"]].hash_mb,
                "skill": STRENGTH_PRESETS[lvl["elo"]].skill,
                "limit_strength": STRENGTH_PRESETS[lvl["elo"]].limit_strength,
            }
            for lvl in ELO_LEVELS_UI
        ]
    }


@app.post("/api/engine/configure")
def engine_configure(req: EngineConfigureRequest) -> dict[str, Any]:
    if not engine.available:
        _start_engine()
    if not engine.available:
        raise HTTPException(503, engine.error or "Stockfish hors ligne")
    strength = strength_for_elo(req.elo)
    depth = req.depth if req.depth is not None else (strength.depth or 18)
    engine.configure(req.elo, depth=depth, movetime_ms=req.movetime_ms)
    return {
        "ok": True,
        "elo": engine.elo,
        "label": engine.engine_label,
        "movetime_ms": engine.movetime_ms,
        "depth": engine.depth,
        "strength": strength.label,
    }


# ---------------------------------------------------------------------------
# Games vs Stockfish
# ---------------------------------------------------------------------------


@app.post("/api/game/new")
def new_game(req: NewGameRequest) -> dict[str, Any]:
    gid = str(uuid.uuid4())
    color = (req.color or "random").lower().strip()
    if color == "random":
        color = "white" if secrets.randbelow(2) == 0 else "black"
    human_white = color != "black"
    g = ServerGame(
        id=gid,
        mode=req.mode,
        elo=req.elo,
        human_is_white=human_white,
        white_name=req.white_name if human_white else req.black_name,
        black_name=req.black_name if human_white else req.white_name,
        white_seconds=float(req.time_minutes * 60),
        black_seconds=float(req.time_minutes * 60),
        time_minutes=req.time_minutes,
        time_increment=req.time_increment,
    )
    if req.mode == "pve":
        g.black_name = f"Stockfish ({req.elo})" if human_white else req.white_name
        g.white_name = req.white_name if human_white else f"Stockfish ({req.elo})"
    GAMES[gid] = g
    snap = g.snapshot()
    snap["assigned_color"] = "white" if human_white else "black"
    return snap


@app.get("/api/game/{game_id}")
def get_game(game_id: str) -> dict[str, Any]:
    g = GAMES.get(game_id)
    if not g:
        raise HTTPException(404, "Partie introuvable")
    return g.snapshot()


@app.post("/api/game/{game_id}/move")
def play_move(game_id: str, req: MoveRequest) -> dict[str, Any]:
    g = GAMES.get(game_id)
    if not g:
        raise HTTPException(404, "Partie introuvable")
    try:
        move = chess.Move.from_uci(req.uci)
    except ValueError as exc:
        raise HTTPException(400, f"UCI invalide: {exc}") from exc
    if move not in g.board.legal_moves:
        raise HTTPException(400, "Coup illégal")
    mover_white = g.board.turn == chess.WHITE
    g.board.push(move)
    if mover_white:
        g.white_seconds += g.time_increment
    else:
        g.black_seconds += g.time_increment
    return g.snapshot()


@app.post("/api/game/{game_id}/undo")
def undo_move(game_id: str) -> dict[str, Any]:
    g = GAMES.get(game_id)
    if not g:
        raise HTTPException(404, "Partie introuvable")
    if not g.board.move_stack:
        raise HTTPException(400, "Rien à annuler")
    g.board.pop()
    return g.snapshot()


@app.post("/api/game/{game_id}/undo_pair")
def undo_pair(game_id: str) -> dict[str, Any]:
    """Annule le coup humain + réponse moteur (PVE)."""
    g = GAMES.get(game_id)
    if not g:
        raise HTTPException(404, "Partie introuvable")
    n = min(2, len(g.board.move_stack))
    if n == 0:
        raise HTTPException(400, "Rien à annuler")
    for _ in range(n):
        g.board.pop()
    return g.snapshot()


@app.get("/api/saves/{name}/pgn")
def export_pgn(name: str) -> dict[str, Any]:
    path = saves.folder / name
    if not path.is_file():
        raise HTTPException(404, "Sauvegarde introuvable")
    data = saves.load_game(path)
    board = chess.Board()
    san_moves: list[str] = []
    for u in data.moves:
        move = chess.Move.from_uci(u)
        if move not in board.legal_moves:
            break
        san_moves.append(board.san(move))
        board.push(move)
    headers = [
        f'[Event "Chess Pro D4"]',
        f'[White "{data.white_name}"]',
        f'[Black "{data.black_name}"]',
        f'[Result "{data.result}"]',
        f'[Site "Local"]',
    ]
    body_parts: list[str] = []
    for i, san in enumerate(san_moves):
        if i % 2 == 0:
            body_parts.append(f"{i // 2 + 1}. {san}")
        else:
            body_parts.append(san)
    pgn = "\n".join(headers) + "\n\n" + " ".join(body_parts) + f" {data.result}\n"
    return {"ok": True, "pgn": pgn, "name": name}


@app.post("/api/board/fen")
def board_fen(req: AnalyzeRequest) -> dict[str, Any]:
    """Calcule le FEN après une liste de coups (navigation analyse)."""
    board = chess.Board()
    for u in req.moves:
        try:
            m = chess.Move.from_uci(u)
        except ValueError as e:
            raise HTTPException(400, f"Coup invalide: {u}") from e
        if m not in board.legal_moves:
            raise HTTPException(400, f"Historique illégal: {u}")
        board.push(m)
    return {"ok": True, "fen": board.fen(), "ply": len(req.moves), "turn": "white" if board.turn else "black"}


@app.post("/api/engine/analyze")
def engine_analyze(req: AnalyzeRequest) -> dict[str, Any]:
    if not engine.available:
        _start_engine()
    if not engine.available:
        raise HTTPException(503, engine.error or "Stockfish hors ligne")
    board = chess.Board()
    for u in req.moves:
        m = chess.Move.from_uci(u)
        if m not in board.legal_moves:
            raise HTTPException(400, f"Historique illégal: {u}")
        board.push(m)
    if req.fen and not req.moves:
        board = chess.Board(req.fen)
    with _engine_lock:
        rid = engine.request_analysis(
            board,
            depth=req.depth,
            movetime_ms=req.movetime_ms,
            multipv=req.multipv,
        )
        if rid < 0:
            raise HTTPException(503, engine.error or "Analyse impossible")
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            for result in engine.poll_results():
                if result.analysis is not None:
                    a = result.analysis
                    return {
                        "eval": a.eval_text,
                        "score_cp": a.score_cp,
                        "mate": a.mate,
                        "white_advantage": a.white_advantage,
                        "depth": a.depth,
                        "time_ms": a.time_ms,
                        "nodes": a.nodes,
                        "nps": a.nps,
                        "best_move": a.best_move.uci() if a.best_move else None,
                        "pv": [m.uci() for m in a.pv],
                        "pv_uci": " ".join(m.uci() for m in a.pv),
                        "pv_san": _pv_san(board, a.pv),
                        "lines": [_enrich_line(board, line) for line in a.multipv_lines],
                        "fen": board.fen(),
                        "turn": "white" if board.turn == chess.WHITE else "black",
                    }
                if result.error and result.kind.name == "ANALYSE":
                    raise HTTPException(500, result.error)
            time.sleep(0.05)
    raise HTTPException(504, "Timeout analyse")


@app.post("/api/engine/play")
def engine_play(req: EngineMoveRequest) -> dict[str, Any]:
    """Stockfish joue un coup sur la position (moves UCI depuis le départ)."""
    if not engine.available:
        _start_engine()
    if not engine.available:
        raise HTTPException(503, engine.error or "Stockfish hors ligne")
    board = chess.Board()
    for u in req.moves:
        m = chess.Move.from_uci(u)
        if m not in board.legal_moves:
            raise HTTPException(400, f"Historique illégal: {u}")
        board.push(m)
    if req.fen and not req.moves:
        board = chess.Board(req.fen)
    before = board.copy()
    with _engine_lock:
        engine.configure(req.elo, movetime_ms=req.movetime_ms)
        rid = engine.request_move(board)
        if rid < 0:
            raise HTTPException(503, engine.error or "Stockfish indisponible")
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            for result in engine.poll_results():
                if result.kind.name == "PLAY" and (result.request_id == rid or result.move):
                    if result.error or not result.move:
                        raise HTTPException(500, result.error or "Pas de bestmove")
                    if result.move not in board.legal_moves:
                        raise HTTPException(500, f"Coup IA invalide: {result.move.uci()}")
                    san = before.san(result.move)
                    board.push(result.move)
                    return {
                        "uci": result.move.uci(),
                        "san": san,
                        "fen": board.fen(),
                        "moves": [m.uci() for m in board.move_stack],
                        "check": board.is_check(),
                        "checkmate": board.is_checkmate(),
                        "stalemate": board.is_stalemate(),
                        "result": board.result(claim_draw=True) if board.is_game_over() else "*",
                        "legal": [m.uci() for m in board.legal_moves],
                    }
            time.sleep(0.05)
    raise HTTPException(504, "Timeout Stockfish")


# ---------------------------------------------------------------------------
# Saves
# ---------------------------------------------------------------------------


@app.get("/api/saves")
def list_saves() -> dict[str, Any]:
    items = []
    for meta in saves.list_json_saves():
        items.append(
            {
                "path": meta.path.name,
                "saved_at": meta.saved_at,
                "mode": meta.mode,
                "white": meta.white,
                "black": meta.black,
                "elo": meta.elo,
                "result": meta.result,
                "ply": meta.ply,
                "label": meta.label,
            }
        )
    return {"saves": items, "count": len(items)}


@app.post("/api/saves")
def save_game(req: SaveRequest) -> dict[str, Any]:
    data = GameSaveData(
        mode=req.mode,
        moves=req.moves,
        white_name=req.white_name,
        black_name=req.black_name,
        human_is_white=req.human_is_white,
        elo=req.elo,
        skill=req.skill,
        time_minutes=req.time_minutes,
        time_increment=req.time_increment,
        white_seconds=req.white_seconds,
        black_seconds=req.black_seconds,
        clock_enabled=req.clock_enabled,
        result=req.result,
        message=req.message,
    )
    path = saves.save_game(data)
    return {"ok": True, "path": path.name, "message": f"Partie sauvegardée : {path.name}"}


@app.get("/api/saves/{name}")
def load_save(name: str) -> dict[str, Any]:
    path = saves.folder / name
    if not path.is_file():
        raise HTTPException(404, "Sauvegarde introuvable")
    data = saves.load_game(path)
    return data.to_dict()


@app.delete("/api/saves/{name}")
def delete_save(name: str) -> dict[str, Any]:
    path = saves.folder / name
    if not path.is_file():
        raise HTTPException(404, "Sauvegarde introuvable")
    path.unlink()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Local rooms
# ---------------------------------------------------------------------------


@app.post("/api/rooms")
def create_room(req: CreateRoomRequest) -> dict[str, Any]:
    code = make_room_code()
    while code in ROOMS:
        code = make_room_code()
    room = LocalRoom(
        code=code,
        time_minutes=req.time_minutes,
        time_increment=req.time_increment,
        white_seconds=float(req.time_minutes * 60),
        black_seconds=float(req.time_minutes * 60),
    )
    host_id = str(uuid.uuid4())
    host_color = "white" if secrets.randbelow(2) == 0 else "black"
    guest_color = "black" if host_color == "white" else "white"
    room.host = RoomPlayer(id=host_id, name=req.host_name, color=host_color)
    ROOMS[code] = room
    links = _join_urls(code)
    return {
        "code": code,
        "host_id": host_id,
        "host_color": host_color,
        "guest_color": guest_color,
        "status": room.status,
        **links,
        "message": (
            f"Lien mondial prêt — vous êtes les {'Blancs' if host_color == 'white' else 'Noirs'} (aléatoire)"
            if links.get("worldwide")
            else "Tunnel mondial en cours… utilisez le lien local si même Wi‑Fi"
        ),
        "room": room.snapshot(),
    }


@app.get("/api/rooms")
def list_rooms() -> dict[str, Any]:
    now = time.time()
    # purge vieilles rooms (>2h)
    dead = [c for c, r in ROOMS.items() if now - r.created_at > 7200]
    for c in dead:
        ROOMS.pop(c, None)
    return {
        "rooms": [
            {
                "code": r.code,
                "status": r.status,
                "players": r.players_count(),
                "host": r.host.name if r.host else None,
                "created_ago_s": int(now - r.created_at),
            }
            for r in ROOMS.values()
            if r.status == "waiting"
        ]
    }


@app.get("/api/rooms/{code}")
def get_room(code: str) -> dict[str, Any]:
    room = ROOMS.get(code.upper())
    if not room:
        raise HTTPException(404, "Partie locale introuvable")
    return {
        **room.snapshot(),
        **_join_urls(room.code),
    }


@app.get("/join/{code}", response_class=HTMLResponse)
def join_page(code: str) -> HTMLResponse:
    """Page jouable : plateau premium + pièces PNG (téléphone / navigateur)."""
    code = code.upper()
    room = ROOMS.get(code)
    if not room:
        return HTMLResponse(
            f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>404 — {code}</title>
<style>body{{font-family:Segoe UI,sans-serif;background:#080605;color:#EBE1CD;display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0}}
.card{{max-width:420px;padding:28px;border:1px solid #3A342C;border-radius:12px;background:#12100E;text-align:center}}
h1{{color:#C85046}}</style></head><body><div class="card">
<h1>Partie introuvable</h1>
<p>Le code <b>{code}</b> n'existe pas ou a expiré.<br/>Créez une nouvelle partie dans Chess Pro D4 → Local.</p>
</div></body></html>""",
            status_code=404,
        )
    html = _JOIN_TEMPLATE.replace("{{CODE}}", code)
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")


async def _broadcast(room: LocalRoom, payload: dict[str, Any]) -> None:
    raw = json.dumps(payload)
    for player in (room.host, room.guest):
        if player and player.ws:
            try:
                await player.ws.send_text(raw)
            except Exception:
                pass


@app.websocket("/ws/room/{code}")
async def room_ws(websocket: WebSocket, code: str) -> None:
    await websocket.accept()
    code = code.upper()
    room = ROOMS.get(code)
    if not room:
        await websocket.send_json({"type": "error", "message": "Partie introuvable"})
        await websocket.close()
        return

    player_id = websocket.query_params.get("player_id") or str(uuid.uuid4())
    name = websocket.query_params.get("name") or "Joueur"
    role = websocket.query_params.get("role")  # host | guest

    # Assign seat
    me: RoomPlayer | None = None
    host_color = room.host.color if room.host else "white"
    guest_color = "black" if host_color == "white" else "white"
    if role == "host" or (room.host and room.host.id == player_id):
        if room.host is None:
            room.host = RoomPlayer(id=player_id, name=name, color=host_color, ws=websocket)
        else:
            room.host.ws = websocket
            room.host.name = name or room.host.name
            player_id = room.host.id
        me = room.host
    else:
        if room.guest is None:
            room.guest = RoomPlayer(id=player_id, name=name, color=guest_color, ws=websocket)
        else:
            # Siège déjà pris par un guest encore connecté
            if room.guest.id != player_id and room.guest.ws is not None:
                await websocket.send_json({"type": "error", "message": "Partie déjà complète"})
                await websocket.close()
                return
            # Reclaim si l'ancien guest est déconnecté, sinon reconnexion
            if room.guest.id != player_id and room.guest.ws is None:
                room.guest = RoomPlayer(id=player_id, name=name, color=guest_color, ws=websocket)
            else:
                room.guest.ws = websocket
                room.guest.name = name or room.guest.name
                player_id = room.guest.id
        me = room.guest

    # Ne démarrer que si les DEUX WebSockets sont actifs
    if room.both_connected() and room.status == "waiting":
        room.status = "playing"
        room.last_move_at = time.time()
        logger.info("Room %s: partie démarrée (2 joueurs connectés)", code)

    await websocket.send_json(
        {
            "type": "welcome",
            "player_id": player_id,
            "color": me.color if me else None,
            "room": room.snapshot(),
        }
    )
    await _broadcast(room, {"type": "state", "room": room.snapshot()})

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            mtype = msg.get("type")
            if mtype == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if mtype == "move":
                if room.status != "playing":
                    await websocket.send_json({"type": "error", "message": "La partie n'a pas commencé"})
                    continue
                uci = msg.get("uci", "")
                try:
                    move = chess.Move.from_uci(uci)
                except ValueError:
                    await websocket.send_json({"type": "error", "message": "UCI invalide"})
                    continue
                # Vérifier couleur
                expected = "white" if room.board.turn else "black"
                if not me or me.color != expected:
                    await websocket.send_json({"type": "error", "message": "Ce n'est pas votre tour"})
                    continue
                if move not in room.board.legal_moves:
                    await websocket.send_json({"type": "error", "message": "Coup illégal"})
                    continue
                mover_white = room.board.turn
                room.board.push(move)
                if mover_white:
                    room.white_seconds += room.time_increment
                else:
                    room.black_seconds += room.time_increment
                room.last_move_at = time.time()
                if room.board.is_game_over():
                    room.status = "finished"
                await _broadcast(
                    room,
                    {
                        "type": "move",
                        "uci": uci,
                        "room": room.snapshot(),
                    },
                )
                continue
            if mtype == "resign":
                room.status = "finished"
                await _broadcast(room, {"type": "resign", "by": me.color if me else None, "room": room.snapshot()})
                continue
            if mtype == "chat":
                await _broadcast(
                    room,
                    {"type": "chat", "from": me.name if me else "?", "text": str(msg.get("text", ""))[:200]},
                )
                continue
            if mtype == "sync":
                await websocket.send_json({"type": "state", "room": room.snapshot()})
    except WebSocketDisconnect:
        if me:
            me.ws = None
        await _broadcast(room, {"type": "player_left", "room": room.snapshot()})
    except Exception as exc:
        logger.exception("WS room error: %s", exc)
        try:
            await websocket.close()
        except Exception:
            pass


def main() -> None:
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
