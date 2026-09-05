"""Session de partie — orchestration règles / joueurs / moteur (sans UI)."""

from __future__ import annotations

from enum import Enum, auto

import chess

from src.core.board import ChessBoard
from src.core.clock import ChessClock
from src.engine.stockfish_manager import EngineJob, EngineResult, StockfishManager
from src.models.player import PlayerInfo
from src.utils.helpers import choose_color


class GameMode(Enum):
    PVP = auto()
    PVE = auto()
    EVE = auto()  # Stockfish vs Stockfish


class GameSession:
    """Gère sélection, coups, IA asynchrone, undo/redo et métadonnées d'animation."""

    def __init__(
        self,
        mode: GameMode = GameMode.PVP,
        elo: int = 1200,
        skill: int | None = 8,
        time_minutes: int = 10,
        time_increment: int = 0,
        color_preference: str = "white",
        player_name: str = "Joueur",
        engine: StockfishManager | None = None,
    ) -> None:
        self.mode = mode
        self.elo = elo
        self.skill = skill
        self.human_is_white = True if mode == GameMode.PVP else choose_color(color_preference or "white")
        # PVE : forcer Blancs si preference invalide / absente
        if mode == GameMode.PVE and color_preference in ("", None):
            self.human_is_white = True
        self.board = ChessBoard()
        self.clock = ChessClock(time_minutes, time_increment)
        self.engine = engine or StockfishManager()
        self.owns_engine = engine is None
        self.selected: chess.Square | None = None
        self.legal_targets: list[chess.Square] = []
        self.last_move: chess.Move | None = None
        self.last_move_piece: str | None = None
        self.last_move_capture = False
        self.last_captured_symbol: str | None = None
        self.last_captured_square: chess.Square | None = None
        self.pending_promotion: list[chess.Move] | None = None
        self.pending_ai_move: chess.Move | None = None
        self.message = ""
        self.ai_thinking = False
        self._redo_stack: list[chess.Move] = []
        self._pending_request_id: int | None = None
        self.white_player = self._make_white_player(player_name)
        self.black_player = self._make_black_player(player_name)
        if self.clock.enabled:
            self.clock.start()
        if mode in (GameMode.PVE, GameMode.EVE) and not self.engine.available:
            self.engine.start()
            self.engine.configure(elo, skill)
        if mode == GameMode.EVE or (mode == GameMode.PVE and not self.human_is_white):
            self._request_engine_move()

    def _make_white_player(self, name: str) -> PlayerInfo:
        if self.mode == GameMode.EVE:
            return PlayerInfo("Stockfish W", True, True, self.elo)
        if self.mode == GameMode.PVE and not self.human_is_white:
            return PlayerInfo("Stockfish", True, True, self.elo)
        return PlayerInfo(name, True, False)

    def _make_black_player(self, name: str) -> PlayerInfo:
        if self.mode == GameMode.EVE:
            return PlayerInfo("Stockfish B", False, True, self.elo)
        if self.mode == GameMode.PVE and self.human_is_white:
            return PlayerInfo("Stockfish", False, True, self.elo)
        return PlayerInfo(name if self.mode == GameMode.PVP else name, False, False)

    @property
    def vs_ai(self) -> bool:
        return self.mode == GameMode.PVE

    @property
    def engine_label(self) -> str:
        if self.mode == GameMode.PVP:
            return "Humain vs Humain"
        return self.engine.engine_label

    @property
    def awaiting_promotion(self) -> bool:
        return bool(self.pending_promotion)

    def close(self) -> None:
        if self.owns_engine:
            self.engine.stop()

    def reset(self) -> None:
        self.board.reset()
        self.clear_selection()
        self.last_move = None
        self.last_move_piece = None
        self.last_move_capture = False
        self.last_captured_symbol = None
        self.last_captured_square = None
        self.pending_ai_move = None
        self.pending_promotion = None
        self._redo_stack.clear()
        self._pending_request_id = None
        self.ai_thinking = False
        self.message = ""
        self.clock.reset()
        if self.clock.enabled:
            self.clock.start()
        if self.mode == GameMode.EVE or (self.mode == GameMode.PVE and not self.human_is_white):
            self._request_engine_move()

    def clear_selection(self) -> None:
        self.selected = None
        self.legal_targets = []

    def clear_promotion(self) -> None:
        self.pending_promotion = None

    def cancel_promotion(self) -> None:
        self.pending_promotion = None
        self.clear_selection()
        self.message = self.board.status_text()

    def can_interact(self) -> bool:
        if self.ai_thinking or self.pending_ai_move is not None:
            return False
        if self.board.is_game_over() or self.clock.flagged_white is not None:
            return False
        if self.mode == GameMode.EVE:
            return False
        if self.mode == GameMode.PVE:
            human_turn = self.board.turn() == (chess.WHITE if self.human_is_white else chess.BLACK)
            return human_turn
        return True

    def set_time_control(self, minutes: int, increment: int) -> None:
        was_running = self.clock.running
        self.clock.set_control(minutes, increment)
        if was_running and self.clock.enabled and not self.board.is_game_over():
            self.clock.start()
        self.message = f"Chrono : {self.clock.label()}"

    def set_elo_level(self, elo: int, skill: int | None) -> None:
        self.elo = elo
        self.skill = skill
        self.engine.configure(elo, skill)
        if self.white_player.is_engine:
            self.white_player.elo = elo
        if self.black_player.is_engine:
            self.black_player.elo = elo
        self.message = f"Niveau IA : {elo} ELO"

    def update_clock(self, dt: float, paused: bool) -> None:
        if paused or self.board.is_game_over() or self.clock.flagged_white is not None:
            self.clock.pause()
            return
        if not self.clock.enabled:
            return
        self.clock.running = True
        self.clock.tick(dt, self.board.turn() == chess.WHITE)
        if self.clock.flagged_white is not None:
            loser = "Blancs" if self.clock.flagged_white else "Noirs"
            winner = "Noirs" if self.clock.flagged_white else "Blancs"
            self.message = f"Temps ecoule — {loser} perdent. Victoire {winner}."

    def square_from_pixel(self, row: int, col: int) -> chess.Square:
        return chess.square(col, 7 - row)

    def apply_move(self, move: chess.Move) -> tuple[str, bool, str | None]:
        board = self.board.board
        piece = board.piece_at(move.from_square)
        captured = board.piece_at(move.to_square)
        en_passant = board.is_en_passant(move)
        capture = captured is not None or en_passant
        captured_symbol = captured.symbol() if captured else None
        captured_square: chess.Square | None = move.to_square if captured else None
        if en_passant and piece is not None:
            ep_square = chess.square(chess.square_file(move.to_square), chess.square_rank(move.from_square))
            ep_pawn = board.piece_at(ep_square)
            if ep_pawn is not None:
                captured_symbol = ep_pawn.symbol()
                captured_square = ep_square
        symbol = piece.symbol() if piece else "P"
        if move.promotion and piece is not None:
            symbol = chess.Piece(move.promotion, piece.color).symbol()
        mover_white = piece.color == chess.WHITE if piece else True
        self.board.push(move)
        self.clock.on_move(mover_white)
        self.last_move = move
        self.last_move_piece = symbol
        self.last_move_capture = capture
        self.last_captured_symbol = captured_symbol
        self.last_captured_square = captured_square
        self.clear_selection()
        self.message = self.board.status_text()
        return symbol, capture, captured_symbol

    def _apply_player_move(self, move: chess.Move) -> tuple[str, bool, str | None]:
        self._redo_stack.clear()
        return self.apply_move(move)

    def handle_square_click(self, square: chess.Square) -> chess.Move | None:
        if not self.can_interact():
            return None
        if self.selected is None:
            moves = self.board.legal_moves_from(square)
            if not moves:
                return None
            self.selected = square
            self.legal_targets = [m.to_square for m in moves]
            return None
        if square == self.selected:
            self.clear_selection()
            return None
        candidates = [m for m in self.board.legal_moves_from(self.selected) if m.to_square == square]
        if not candidates:
            moves = self.board.legal_moves_from(square)
            if moves:
                self.selected = square
                self.legal_targets = [m.to_square for m in moves]
            else:
                self.clear_selection()
            return None
        promos = [m for m in candidates if m.promotion]
        if promos:
            self.pending_promotion = promos
            self.message = "Promotion — choisissez une piece"
            return None
        chosen = candidates[0]
        self._apply_player_move(chosen)
        self._maybe_start_engine()
        return chosen

    def pick_promotion(self, move: chess.Move) -> chess.Move | None:
        if not self.pending_promotion or move not in self.pending_promotion:
            return None
        self.pending_promotion = None
        self._apply_player_move(move)
        self._maybe_start_engine()
        return move

    def _engine_to_move(self) -> bool:
        if self.mode == GameMode.EVE:
            return True
        if self.mode != GameMode.PVE:
            return False
        engine_is_white = not self.human_is_white
        return self.board.turn() == (chess.WHITE if engine_is_white else chess.BLACK)

    def _maybe_start_engine(self) -> None:
        if self.board.is_game_over():
            return
        if self._engine_to_move():
            self._request_engine_move()

    def _request_engine_move(self) -> None:
        if not self.engine.available:
            self.ai_thinking = False
            self.message = self.engine.error or "Stockfish indisponible — selectionnez le moteur"
            return
        self.ai_thinking = True
        self.message = "Stockfish réfléchit..."
        rid = self.engine.request_move(self.board.board)
        if rid < 0:
            self.ai_thinking = False
            self.message = self.engine.error or "Impossible d'interroger Stockfish"
            self._pending_request_id = None
            return
        self._pending_request_id = rid

    def poll_engine(self) -> chess.Move | None:
        """À appeler chaque frame depuis l'UI — non bloquant."""
        results = self.engine.poll_results()
        played: chess.Move | None = None
        for result in results:
            if result.kind == EngineJob.START:
                if not result.ok:
                    self.ai_thinking = False
                    self.message = result.error or "Stockfish indisponible"
                continue
            if result.kind == EngineJob.ANALYSE and result.analysis is not None:
                if not self.ai_thinking or self._pending_request_id is None:
                    self.message = (
                        f"Eval {result.analysis.eval_text}  ·  "
                        f"prof. {result.analysis.depth}  ·  "
                        f"{result.elapsed_s:.1f}s"
                    )
                continue
            if result.kind != EngineJob.PLAY:
                continue
            if self._pending_request_id is not None and result.request_id != self._pending_request_id:
                continue
            self.ai_thinking = False
            self._pending_request_id = None
            if result.error or result.move is None:
                self.message = f"Erreur moteur: {result.error or 'bestmove manquant'}"
                continue
            if not self.board.is_legal(result.move):
                self.message = f"Coup IA invalide: {result.move.uci()}"
                continue
            self.apply_move(result.move)
            self.message = self.board.status_text()
            if self.mode == GameMode.EVE and not self.board.is_game_over():
                self._request_engine_move()
            played = result.move
        # Ne pas écraser ai_thinking si une requête PLAY est encore en cours
        if self._pending_request_id is not None:
            self.ai_thinking = True
        elif not self.engine.thinking:
            # laisser False sauf si on vient de relancer EVE
            pass
        return played

    def goto_ply(self, ply: int) -> None:
        """Revenir a une position apres `ply` demi-coups (0 = depart)."""
        if self.ai_thinking:
            return
        ply = max(0, ply)
        while len(self.board.board.move_stack) > ply:
            if not self.board.board.move_stack:
                break
            move = self.board.board.peek()
            self.board.undo()
            self._redo_stack.append(move)
        self.clear_selection()
        self.clear_promotion()
        self.last_move = self.board.board.peek() if self.board.board.move_stack else None
        self.last_move_piece = None
        self.last_move_capture = False
        self.last_captured_symbol = None
        self.last_captured_square = None
        self.message = self.board.status_text()

    def undo_move(self) -> None:
        if self.ai_thinking:
            return
        self.clear_promotion()
        plies = 2 if self.mode == GameMode.PVE else 1
        for _ in range(plies):
            if not self.board.board.move_stack:
                break
            move = self.board.board.peek()
            self.board.undo()
            self._redo_stack.append(move)
        self.clear_selection()
        self.last_move = self.board.board.peek() if self.board.board.move_stack else None
        self.last_move_piece = None
        self.last_move_capture = False
        self.last_captured_symbol = None
        self.last_captured_square = None
        self.message = self.board.status_text()

    def redo_move(self) -> None:
        if self.ai_thinking or not self._redo_stack:
            return
        move = self._redo_stack.pop()
        if self.board.is_legal(move):
            self.apply_move(move)
            if self.mode == GameMode.PVE and self._redo_stack:
                engine_move = self._redo_stack.pop()
                if self.board.is_legal(engine_move):
                    self.apply_move(engine_move)
        self.message = self.board.status_text()

    def export_fen(self) -> str:
        return self.board.fen()

    def import_fen(self, fen: str) -> None:
        self.board.set_fen(fen)
        self.clear_selection()
        self._redo_stack.clear()
        self.message = self.board.status_text()

    def export_pgn(self) -> str:
        return self.board.export_pgn(
            white=self.white_player.display_name,
            black=self.black_player.display_name,
        )

    def move_list_san(self) -> list[str]:
        return self.board.san_history()
