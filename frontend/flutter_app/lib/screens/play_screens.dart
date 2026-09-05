import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'package:chess_pro_d4/api/api_client.dart';
import 'package:chess_pro_d4/services/sound_service.dart';
import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/ui/game_over_dialog.dart';
import 'package:chess_pro_d4/widgets/chess_board.dart';

class PlayHubScreen extends StatelessWidget {
  const PlayHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const Text('Jouer',
            style: TextStyle(fontSize: 22, color: D4Theme.goldBright, fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        const Text('Choisissez un mode', style: TextStyle(color: D4Theme.muted)),
        const SizedBox(height: 20),
        _ModeCard(
          title: 'Contre Stockfish',
          subtitle: 'Moteur UCI réel · force ELO configurable',
          action: 'Lancer la partie',
          onTap: () => context.go('/play/stockfish'),
        ),
        const SizedBox(height: 12),
        _ModeCard(
          title: 'Partie locale',
          subtitle: 'QR Code · lien · synchronisation WebSocket',
          action: 'Ouvrir Local',
          onTap: () => context.go('/local'),
        ),
        const SizedBox(height: 12),
        _ModeCard(
          title: 'Joueur contre Joueur',
          subtitle: 'Hotseat sur le même appareil',
          action: 'Lancer',
          onTap: () => context.go('/play/local-hotseat'),
        ),
      ],
    );
  }
}

class _ModeCard extends StatelessWidget {
  const _ModeCard({
    required this.title,
    required this.subtitle,
    required this.action,
    required this.onTap,
  });
  final String title;
  final String subtitle;
  final String action;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 440),
        child: Card(
          margin: const EdgeInsets.all(24),
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(title,
                    style: const TextStyle(
                        fontSize: 22, color: D4Theme.goldBright, fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),
                Text(subtitle, textAlign: TextAlign.center, style: const TextStyle(color: D4Theme.muted)),
                const SizedBox(height: 22),
                ElevatedButton(onPressed: onTap, child: Text(action)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Écran de partie riche : onglets haut + 3 colonnes.
class StockfishGameScreen extends StatefulWidget {
  const StockfishGameScreen({super.key});

  @override
  State<StockfishGameScreen> createState() => _StockfishGameScreenState();
}

class _StockfishGameScreenState extends State<StockfishGameScreen> {
  final _api = ApiClient();
  String? _gameId;
  String _fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  List<String> _moves = [];
  List<String> _legal = [];
  List<String> _san = [];
  String? _selected;
  String? _lastFrom;
  String? _lastTo;
  bool _thinking = false;
  bool _paused = false;
  String _status = 'Votre tour';
  String? _error;
  Map<String, dynamic>? _analysis;
  Map<String, dynamic>? _snap;
  String _whiteName = 'Joueur';
  String _blackName = 'Stockfish';
  bool _humanIsWhite = true;

  @override
  void initState() {
    super.initState();
    _start();
  }

  String _resolveColor(String pref) {
    if (pref == 'black') return 'black';
    if (pref == 'white') return 'white';
    return math.Random().nextBool() ? 'white' : 'black';
  }

  Future<void> _start() async {
    final state = context.read<AppState>();
    SoundService.instance.enabled = state.sounds;
    SoundService.instance.warmUp();
    try {
      final color = _resolveColor(state.colorPref);
      final g = await _api.newGame(
        mode: 'pve',
        elo: state.elo,
        color: color,
        timeMinutes: state.timeMinutes <= 0 ? 10 : state.timeMinutes,
        whiteName: state.playerName,
        blackName: 'Stockfish (${state.elo})',
      );
      final humanWhite = g['human_is_white'] != false;
      setState(() {
        _gameId = g['id'] as String?;
        _humanIsWhite = humanWhite;
        _applySnap(g);
        _error = null;
        _paused = false;
        _thinking = false;
        _whiteName = g['white_name']?.toString() ?? state.playerName;
        _blackName = g['black_name']?.toString() ?? 'Stockfish';
        _status = humanWhite
            ? 'Vous jouez les Blancs'
            : 'Vous jouez les Noirs — Stockfish ouvre…';
      });
      if (!humanWhite && (g['result'] == null || g['result'] == '*')) {
        await _engineReply();
      } else {
        _refreshAnalysis();
      }
    } catch (e) {
      setState(() {
        _error =
            'Impossible de créer la partie.\n$e\n\nVérifiez le backend sur le port 3848 (FLUTTER.bat / BACKEND.bat).';
        _gameId = null;
      });
    }
  }

  Future<void> _onGameEnd(Map<String, dynamic> g) async {
    if (!mounted) return;
    setState(() {
      _thinking = false;
      _status = g['checkmate'] == true ? 'Échec et mat' : 'Partie terminée (${g['result']})';
    });
    await showGameOverDialog(
      context,
      title: gameOverTitle(g, humanIsWhite: _humanIsWhite),
      subtitle: gameOverSubtitle(g),
      onReplay: _start,
      homeRoute: '/play',
    );
  }

  void _applySnap(Map<String, dynamic> g, {String? lastUci}) {
    final moves = (g['moves'] as List?)?.cast<String>() ?? [];
    String? lf;
    String? lt;
    final u = lastUci ?? (moves.isNotEmpty ? moves.last : null);
    if (u != null && u.length >= 4) {
      lf = u.substring(0, 2);
      lt = u.substring(2, 4);
    }
    _snap = g;
    _fen = g['fen'] as String;
    _moves = moves;
    _legal = (g['legal'] as List?)?.cast<String>() ?? [];
    _san = (g['san'] as List?)?.cast<String>() ?? [];
    _lastFrom = lf;
    _lastTo = lt;
    if (g.containsKey('human_is_white')) {
      _humanIsWhite = g['human_is_white'] != false;
    }
    _whiteName = g['white_name']?.toString() ?? _whiteName;
    _blackName = g['black_name']?.toString() ?? _blackName;
  }

  Future<void> _onTap(String sq) async {
    if (_thinking || _paused || _gameId == null) return;
    if (_selected == null) {
      if (_legal.any((u) => u.startsWith(sq))) setState(() => _selected = sq);
      return;
    }
    if (_selected == sq) {
      setState(() => _selected = null);
      return;
    }
    final cands = _legal.where((u) => u.startsWith('${_selected!}$sq')).toList();
    if (cands.isEmpty) {
      setState(() => _selected = _legal.any((u) => u.startsWith(sq)) ? sq : null);
      return;
    }
    var uci = cands.first;
    if (cands.length > 1) {
      uci = cands.firstWhere((u) => u.endsWith('q'), orElse: () => cands.first);
    }
    await _playHuman(uci);
  }

  Future<void> _playHuman(String uci) async {
    final turn = _snap?['turn']?.toString() ?? 'white';
    final myTurn = (_humanIsWhite && turn == 'white') || (!_humanIsWhite && turn == 'black');
    if (!myTurn) return;

    final before = piecesFromFen(_fen);
    setState(() {
      _thinking = true;
      _selected = null;
      _status = 'Coup envoyé…';
    });
    try {
      SoundService.instance.enabled = context.read<AppState>().sounds;
      final g = await _api.playMove(_gameId!, uci);
      if (!mounted) return;
      setState(() => _applySnap(g, lastUci: uci));
      SoundService.instance.enabled = context.read<AppState>().sounds;
      SoundService.instance.playForMove(uci: uci, after: g, piecesBefore: before);
      if (g['result'] != '*' && g['result'] != null) {
        await _onGameEnd(g);
        return;
      }
      await _engineReply();
    } catch (e) {
      setState(() {
        _thinking = false;
        _status = 'Erreur';
        _error = '$e';
      });
    }
  }

  Future<void> _engineReply() async {
    final elo = context.read<AppState>().elo;
    setState(() {
      _thinking = true;
      _status = 'Stockfish réfléchit…';
    });
    try {
      final before = piecesFromFen(_fen);
      final ai = await _api.enginePlay(moves: _moves, elo: elo);
      if (!mounted) return;
      final uci = ai['uci'] as String;
      final g2 = await _api.playMove(_gameId!, uci);
      if (!mounted) return;
      setState(() {
        _applySnap(g2, lastUci: uci);
        _thinking = false;
        _status = g2['checkmate'] == true
            ? 'Échec et mat — Stockfish'
            : (g2['check'] == true ? 'Votre tour — Échec' : 'Votre tour');
      });
      SoundService.instance.enabled = context.read<AppState>().sounds;
      SoundService.instance.playForMove(uci: uci, after: g2, piecesBefore: before);
      if (g2['result'] != '*' && g2['result'] != null) {
        await _onGameEnd(g2);
        return;
      }
      _refreshAnalysis();
    } catch (e) {
      setState(() {
        _thinking = false;
        _status = 'Erreur moteur';
        _error = '$e';
      });
    }
  }

  Future<void> _refreshAnalysis() async {
    try {
      final a = await _api.analyze(moves: _moves, depth: 18, multipv: 3);
      if (mounted) setState(() => _analysis = a);
    } catch (_) {}
  }

  Future<void> _undo() async {
    if (_gameId == null || _thinking || _moves.isEmpty) return;
    try {
      final g = await _api.undoPair(_gameId!);
      setState(() {
        _applySnap(g);
        _status = 'Votre tour';
      });
      _refreshAnalysis();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  Future<void> _save() async {
    final elo = context.read<AppState>().elo;
    try {
      final r = await _api.saveGame({
        'mode': 'PVE',
        'moves': _moves,
        'white_name': _whiteName,
        'black_name': _blackName,
        'elo': elo,
        'time_minutes': context.read<AppState>().timeMinutes,
        'result': _snap?['result'] ?? '*',
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(r['message']?.toString() ?? 'Sauvegardé')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e')));
      }
    }
  }

  String _fmtClock(dynamic seconds) {
    final s = (seconds is num) ? seconds.toDouble() : 600.0;
    final m = s ~/ 60;
    final sec = (s % 60).floor().toString().padLeft(2, '0');
    return '$m:$sec';
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null && _gameId == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off, color: D4Theme.offline, size: 40),
              const SizedBox(height: 12),
              Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: D4Theme.offline)),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: _start, child: const Text('Réessayer')),
              const SizedBox(height: 8),
              TextButton(onPressed: () => context.go('/settings'), child: const Text('Paramètres réseau')),
            ],
          ),
        ),
      );
    }

    // Plus de sous-onglets horizontaux : le rail gère Analyse / Historique / Paramètres.
    return _buildGameLayout(context);
  }

  Widget _buildGameLayout(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 1100;
    final mid = MediaQuery.sizeOf(context).width >= 800;
    final board = ChessBoardView(
      fen: _fen,
      legalUci: (_thinking || _paused) ? const [] : _legal,
      selected: _selected,
      lastFrom: _lastFrom,
      lastTo: _lastTo,
      orientWhite: _humanIsWhite,
      onSquareTap: _onTap,
      interactive: !_thinking && !_paused,
    );

    final left = _LeftPanel(
      whiteName: _whiteName,
      blackName: _blackName,
      whiteClock: _fmtClock(_snap?['white_seconds']),
      blackClock: _fmtClock(_snap?['black_seconds']),
      elo: context.watch<AppState>().elo,
      turn: _snap?['turn']?.toString() ?? 'white',
      san: _san,
      status: _status,
      thinking: _thinking,
      humanIsWhite: _humanIsWhite,
    );

    final right = _EnginePanel(
      analysis: _analysis,
      thinking: _thinking,
      error: _error,
      onAnalyse: _refreshAnalysis,
    );

    final toolbar = _GameToolbar(
      paused: _paused,
      canUndo: _moves.isNotEmpty && !_thinking,
      onNew: _start,
      onUndo: _undo,
      onSave: _save,
      onPause: () => setState(() => _paused = !_paused),
      onAnalyse: () {
        _refreshAnalysis();
      },
    );

    if (wide) {
      return Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          children: [
            Expanded(
              child: Row(
                children: [
                  SizedBox(width: 240, child: left),
                  const SizedBox(width: 10),
                  Expanded(flex: 5, child: board),
                  const SizedBox(width: 10),
                  SizedBox(width: 260, child: right),
                ],
              ),
            ),
            toolbar,
          ],
        ),
      );
    }
    if (mid) {
      return Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          children: [
            Expanded(
              child: Row(
                children: [
                  Expanded(flex: 5, child: board),
                  const SizedBox(width: 8),
                  SizedBox(
                    width: 220,
                    child: Column(
                      children: [
                        Expanded(child: left),
                        const SizedBox(height: 8),
                        Expanded(child: right),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            toolbar,
          ],
        ),
      );
    }
    return Padding(
      padding: const EdgeInsets.all(6),
      child: Column(
        children: [
          SizedBox(height: 64, child: left),
          Expanded(flex: 4, child: board),
          SizedBox(height: 120, child: right),
          toolbar,
        ],
      ),
    );
  }
}

class _LeftPanel extends StatelessWidget {
  const _LeftPanel({
    required this.whiteName,
    required this.blackName,
    required this.whiteClock,
    required this.blackClock,
    required this.elo,
    required this.turn,
    required this.san,
    required this.status,
    required this.thinking,
    required this.humanIsWhite,
  });

  final String whiteName;
  final String blackName;
  final String whiteClock;
  final String blackClock;
  final int elo;
  final String turn;
  final List<String> san;
  final String status;
  final bool thinking;
  final bool humanIsWhite;

  @override
  Widget build(BuildContext context) {
    // Aligné sur l’échiquier : adversaire en haut, joueur en bas.
    final top = humanIsWhite
        ? _PlayerRow(name: blackName, elo: elo, clock: blackClock, active: turn == 'black', colorLabel: 'Noirs')
        : _PlayerRow(name: whiteName, elo: elo, clock: whiteClock, active: turn == 'white', colorLabel: 'Blancs');
    final bottom = humanIsWhite
        ? _PlayerRow(name: whiteName, elo: elo, clock: whiteClock, active: turn == 'white', colorLabel: 'Blancs')
        : _PlayerRow(name: blackName, elo: elo, clock: blackClock, active: turn == 'black', colorLabel: 'Noirs');

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            top,
            const SizedBox(height: 8),
            bottom,
            const Divider(color: D4Theme.line, height: 20),
            Text(status,
                style: TextStyle(
                    color: thinking ? D4Theme.gold : D4Theme.text, fontWeight: FontWeight.w600, fontSize: 13)),
            const SizedBox(height: 8),
            const Text('Historique', style: TextStyle(color: D4Theme.gold, fontSize: 12)),
            const SizedBox(height: 4),
            Expanded(
              child: ListView.builder(
                itemCount: (san.length + 1) ~/ 2,
                itemBuilder: (_, i) {
                  final w = i * 2 < san.length ? san[i * 2] : '';
                  final b = i * 2 + 1 < san.length ? san[i * 2 + 1] : '';
                  return Text('${i + 1}. $w  $b',
                      style: const TextStyle(fontFamily: 'Consolas', fontSize: 12, color: D4Theme.text));
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PlayerRow extends StatelessWidget {
  const _PlayerRow({
    required this.name,
    required this.elo,
    required this.clock,
    required this.active,
    required this.colorLabel,
  });
  final String name;
  final int elo;
  final String clock;
  final bool active;
  final String colorLabel;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: active ? D4Theme.gold.withValues(alpha: 0.12) : D4Theme.surfaceSoft,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: active ? D4Theme.gold : D4Theme.line),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w600)),
                Text('$colorLabel · $elo', style: const TextStyle(color: D4Theme.muted, fontSize: 11)),
              ],
            ),
          ),
          Text(clock,
              style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: active ? D4Theme.goldBright : D4Theme.text,
                  fontFeatures: const [FontFeature.tabularFigures()])),
        ],
      ),
    );
  }
}

class _EnginePanel extends StatelessWidget {
  const _EnginePanel({
    required this.analysis,
    required this.thinking,
    required this.error,
    required this.onAnalyse,
  });
  final Map<String, dynamic>? analysis;
  final bool thinking;
  final String? error;
  final VoidCallback onAnalyse;

  @override
  Widget build(BuildContext context) {
    final a = analysis;
    final lines = (a?['lines'] as List?) ?? const [];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Stockfish', style: TextStyle(color: D4Theme.gold, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Text(a?['eval']?.toString() ?? (thinking ? '…' : '—'),
                style: const TextStyle(fontSize: 28, color: D4Theme.goldBright, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('Profondeur  ${a?['depth'] ?? '—'}', style: const TextStyle(color: D4Theme.muted, fontSize: 12)),
            Text('Meilleur    ${a?['best_move'] ?? '—'}', style: const TextStyle(color: D4Theme.muted, fontSize: 12)),
            const SizedBox(height: 8),
            Expanded(
              child: ListView(
                children: [
                  for (final raw in lines.take(3))
                    Builder(builder: (_) {
                      final line = Map<String, dynamic>.from(raw as Map);
                      final san = (line['pv_san'] as List?)?.cast<String>() ?? const [];
                      final txt = san.isNotEmpty
                          ? san.take(6).join(' ')
                          : ((line['pv_uci'] as List?)?.take(4).join(' ') ?? '');
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Text('${line['multipv']}. ${line['eval']}  $txt',
                            style: const TextStyle(fontSize: 11, height: 1.3)),
                      );
                    }),
                ],
              ),
            ),
            if (error != null) Text(error!, style: const TextStyle(color: D4Theme.offline, fontSize: 11)),
            OutlinedButton(onPressed: onAnalyse, child: const Text('Analyser')),
            TextButton(onPressed: () => context.go('/analyse'), child: const Text('Analyse complète')),
          ],
        ),
      ),
    );
  }
}

class _GameToolbar extends StatelessWidget {
  const _GameToolbar({
    required this.paused,
    required this.canUndo,
    required this.onNew,
    required this.onUndo,
    required this.onSave,
    required this.onPause,
    required this.onAnalyse,
  });
  final bool paused;
  final bool canUndo;
  final VoidCallback onNew;
  final VoidCallback onUndo;
  final VoidCallback onSave;
  final VoidCallback onPause;
  final VoidCallback onAnalyse;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 8, 4, 4),
      child: Wrap(
        spacing: 8,
        runSpacing: 6,
        alignment: WrapAlignment.center,
        children: [
          OutlinedButton(onPressed: onNew, child: const Text('Nouvelle')),
          OutlinedButton(onPressed: canUndo ? onUndo : null, child: const Text('Annuler')),
          OutlinedButton(onPressed: onSave, child: const Text('Sauver')),
          OutlinedButton(onPressed: onPause, child: Text(paused ? 'Reprendre' : 'Pause')),
          OutlinedButton(onPressed: onAnalyse, child: const Text('Analyse')),
        ],
      ),
    );
  }
}

class HotseatGameScreen extends StatefulWidget {
  const HotseatGameScreen({super.key});
  @override
  State<HotseatGameScreen> createState() => _HotseatGameScreenState();
}

class _HotseatGameScreenState extends State<HotseatGameScreen> {
  final _api = ApiClient();
  String? _gameId;
  String _fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  List<String> _legal = [];
  String? _selected;
  String? _lastFrom;
  String? _lastTo;
  String _turn = 'white';
  String? _error;

  @override
  void initState() {
    super.initState();
    _boot();
  }

  Future<void> _boot() async {
    try {
      SoundService.instance.enabled = context.read<AppState>().sounds;
      final g = await _api.newGame(mode: 'pvp');
      setState(() {
        _gameId = g['id'] as String;
        _fen = g['fen'] as String;
        _legal = (g['legal'] as List?)?.cast<String>() ?? [];
        _turn = g['turn'] as String? ?? 'white';
        _lastFrom = null;
        _lastTo = null;
        _selected = null;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = '$e');
    }
  }

  Future<void> _tap(String sq) async {
    if (_gameId == null) return;
    if (_selected == null) {
      if (_legal.any((u) => u.startsWith(sq))) {
        SoundService.instance.enabled = context.read<AppState>().sounds;
        SoundService.instance.click();
        setState(() => _selected = sq);
      }
      return;
    }
    if (_selected == sq) {
      setState(() => _selected = null);
      return;
    }
    final cands = _legal.where((u) => u.startsWith('${_selected!}$sq')).toList();
    if (cands.isEmpty) {
      setState(() => _selected = _legal.any((u) => u.startsWith(sq)) ? sq : null);
      return;
    }
    final uci = cands.first;
    final before = piecesFromFen(_fen);
    final g = await _api.playMove(_gameId!, uci);
    if (!mounted) return;
    setState(() {
      _fen = g['fen'] as String;
      _legal = (g['legal'] as List?)?.cast<String>() ?? [];
      _turn = g['turn'] as String? ?? 'white';
      _selected = null;
      _lastFrom = uci.substring(0, 2);
      _lastTo = uci.substring(2, 4);
    });
    SoundService.instance.enabled = context.read<AppState>().sounds;
    SoundService.instance.playForMove(uci: uci, after: g, piecesBefore: before);
    if (g['result'] != '*' && g['result'] != null && mounted) {
      await showGameOverDialog(
        context,
        title: gameOverTitle(g),
        subtitle: gameOverSubtitle(g),
        onReplay: _boot,
        homeRoute: '/play',
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!, style: const TextStyle(color: D4Theme.offline)),
            ElevatedButton(onPressed: _boot, child: const Text('Réessayer')),
          ],
        ),
      );
    }
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: Text(
            'Tour : ${_turn == 'white' ? 'Blancs' : 'Noirs'}',
            style: const TextStyle(color: D4Theme.goldBright, fontWeight: FontWeight.w600),
          ),
        ),
        Expanded(
          child: ChessBoardView(
            fen: _fen,
            legalUci: _legal,
            selected: _selected,
            lastFrom: _lastFrom,
            lastTo: _lastTo,
            onSquareTap: _tap,
          ),
        ),
      ],
    );
  }
}
