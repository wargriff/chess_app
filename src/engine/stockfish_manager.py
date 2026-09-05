"""Gestionnaire Stockfish asynchrone — UCI uniquement dans le worker."""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any

import chess

from src.engine.engine_config import strength_for_elo
from src.engine.finder import resolve_stockfish
from src.engine.uci_client import AnalysisInfo, UCIClient

logger = logging.getLogger("chesspro.stockfish")


class EngineJob(Enum):
    START = auto()
    PLAY = auto()
    ANALYSE = auto()
    STOP = auto()
    RECONFIG = auto()


@dataclass
class EngineResult:
    kind: EngineJob
    move: chess.Move | None = None
    analysis: AnalysisInfo | None = None
    error: str | None = None
    elapsed_s: float = 0.0
    request_id: int = 0
    ok: bool = True


class StockfishManager:
    """File de jobs UCI. Le SimpleEngine vit uniquement dans le thread worker."""

    def __init__(self) -> None:
        self._queue: queue.Queue[tuple[EngineJob, dict[str, Any], int]] = queue.Queue()
        self._results: queue.Queue[EngineResult] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._running = False
        self._request_id = 0
        self._lock = threading.Lock()
        self._started_event = threading.Event()
        self.binary: Path | None = None
        self.error: str | None = None
        self.thinking = False
        self.analyzing = False
        self.last_analysis: AnalysisInfo | None = None
        self.last_bestmove: chess.Move | None = None
        self.elo = 1200
        self.skill: int | None = 8
        self.depth = 18
        self.movetime_ms = 800
        self.strength_label = "Club"
        self._available = False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def engine_label(self) -> str:
        if not self.available:
            return "Stockfish introuvable"
        return f"Stockfish · {self.strength_label} ({self.elo})"

    @property
    def status_label(self) -> str:
        if not self.available:
            return self.error or "Hors ligne"
        if self.thinking:
            return "Réfléchit..."
        if self.analyzing:
            return "Analyse..."
        return "Prêt"

    def start(self, custom_path: str | None = None, allow_download: bool = True) -> bool:
        binary = resolve_stockfish(custom_path, allow_download=allow_download)
        if binary is None:
            self.error = "Stockfish introuvable. Placez stockfish.exe dans le dossier stockfish/."
            self._available = False
            logger.error(self.error)
            return False
        self.binary = Path(binary)
        self._ensure_worker()
        self._started_event.clear()
        self._enqueue(EngineJob.START, {"binary": str(self.binary), "elo": self.elo, "skill": self.skill})
        if not self._started_event.wait(timeout=12.0):
            self.error = "Timeout demarrage Stockfish"
            self._available = False
            logger.error(self.error)
            return False
        return self._available

    def set_binary(self, path: str | Path) -> bool:
        path = Path(path)
        if not path.is_file():
            self.error = f"Fichier invalide: {path}"
            return False
        self.binary = path
        return self.start(custom_path=str(path), allow_download=False)

    def stop(self) -> None:
        self._running = False
        try:
            self._queue.put((EngineJob.STOP, {}, 0))
        except Exception:
            pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._thread = None
        self.thinking = False
        self._available = False

    def restart(self) -> bool:
        path = self.binary
        self.stop()
        if path is None:
            return self.start()
        return self.set_binary(path)

    def configure(self, elo: int, skill: int | None = None, depth: int = 18, movetime_ms: int | None = None) -> None:
        strength = strength_for_elo(int(elo))
        self.elo = strength.elo
        self.skill = skill if skill is not None else strength.skill
        self.depth = int(depth)
        self.movetime_ms = int(movetime_ms if movetime_ms is not None else strength.movetime_ms)
        self.strength_label = strength.label
        logger.info(
            "Configure niveau=%s elo=%s movetime=%sms",
            self.strength_label,
            self.elo,
            self.movetime_ms,
        )
        if self._available:
            self._enqueue(
                EngineJob.RECONFIG,
                {"elo": self.elo, "skill": self.skill},
            )

    def request_move(self, board: chess.Board) -> int:
        if not self._available:
            logger.error("request_move: moteur indisponible (%s)", self.error)
            self.thinking = False
            return -1
        self.thinking = True
        fen = board.fen()
        moves = [m.uci() for m in board.move_stack]
        strength = strength_for_elo(self.elo)
        depth = strength.depth
        logger.info("Queue PLAY fen=%s moves=%s movetime=%sms depth=%s", fen, moves, self.movetime_ms, depth)
        return self._enqueue(
            EngineJob.PLAY,
            {"fen": fen, "movetime_ms": self.movetime_ms, "depth": depth},
        )

    def request_analysis(
        self,
        board: chess.Board,
        depth: int | None = None,
        movetime_ms: int | None = None,
        multipv: int = 1,
    ) -> int:
        if not self._available:
            return -1
        self.analyzing = True
        return self._enqueue(
            EngineJob.ANALYSE,
            {
                "fen": board.fen(),
                "depth": depth or self.depth,
                "movetime_ms": movetime_ms,
                "multipv": max(1, min(int(multipv), 5)),
            },
        )

    def poll_results(self) -> list[EngineResult]:
        out: list[EngineResult] = []
        while True:
            try:
                result = self._results.get_nowait()
            except queue.Empty:
                break
            if result.kind == EngineJob.START:
                self._available = result.ok
                if not result.ok:
                    self.error = result.error
                else:
                    self.error = None
                # event deja pose par le worker
            if result.analysis is not None:
                self.last_analysis = result.analysis
            if result.move is not None:
                self.last_bestmove = result.move
            if result.kind == EngineJob.PLAY:
                self.thinking = False
            if result.kind == EngineJob.ANALYSE:
                self.analyzing = False
            out.append(result)
        return out

    def _enqueue(self, kind: EngineJob, payload: dict[str, Any]) -> int:
        with self._lock:
            self._request_id += 1
            rid = self._request_id
        self._ensure_worker()
        self._queue.put((kind, payload, rid))
        return rid

    def _ensure_worker(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, name="stockfish-uci", daemon=True)
        self._thread.start()

    def _worker(self) -> None:
        client = UCIClient()
        logger.info("Worker Stockfish demarre")
        while self._running:
            try:
                kind, payload, rid = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if kind == EngineJob.STOP:
                break
            started = time.monotonic()
            try:
                if kind == EngineJob.START:
                    ok = client.start(Path(payload["binary"]))
                    if ok:
                        client.configure_strength(int(payload["elo"]), payload.get("skill"))
                    self._available = ok
                    if not ok:
                        self.error = client.error or "echec"
                    else:
                        self.error = None
                    self._started_event.set()
                    self._results.put(
                        EngineResult(
                            kind=kind,
                            ok=ok,
                            error=None if ok else (client.error or "echec"),
                            request_id=rid,
                            elapsed_s=time.monotonic() - started,
                        )
                    )
                    continue
                if kind == EngineJob.RECONFIG:
                    client.configure_strength(int(payload["elo"]), payload.get("skill"))
                    continue
                board = chess.Board(payload["fen"])
                if kind == EngineJob.PLAY:
                    move = client.play(board, movetime_ms=payload.get("movetime_ms"), depth=payload.get("depth"))
                    err = None if move else (client.error or "pas de bestmove")
                    self._results.put(
                        EngineResult(
                            kind=kind,
                            move=move,
                            error=err,
                            ok=move is not None,
                            elapsed_s=time.monotonic() - started,
                            request_id=rid,
                        )
                    )
                elif kind == EngineJob.ANALYSE:
                    analysis = client.analyse(
                        board,
                        depth=int(payload.get("depth") or self.depth),
                        movetime_ms=payload.get("movetime_ms"),
                        multipv=int(payload.get("multipv") or 1),
                    )
                    self._results.put(
                        EngineResult(
                            kind=kind,
                            analysis=analysis,
                            move=analysis.best_move,
                            elapsed_s=time.monotonic() - started,
                            request_id=rid,
                            ok=True,
                        )
                    )
            except Exception as exc:
                logger.exception("Erreur worker Stockfish")
                self._results.put(
                    EngineResult(
                        kind=kind,
                        error=str(exc),
                        ok=False,
                        elapsed_s=time.monotonic() - started,
                        request_id=rid,
                    )
                )
                self.thinking = False
                if kind == EngineJob.START:
                    self._available = False
                    self.error = str(exc)
                    self._started_event.set()
        client.stop()
        logger.info("Worker Stockfish arrete")
