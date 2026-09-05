import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'package:chess_pro_d4/api/api_client.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/widgets/chess_board.dart';

/// Analyse Stockfish : barre d'eval + MultiPV + navigation coups (sans courses).
class AnalyseScreen extends StatefulWidget {
  const AnalyseScreen({super.key});
  @override
  State<AnalyseScreen> createState() => _AnalyseScreenState();
}

class _AnalyseScreenState extends State<AnalyseScreen> {
  final _api = ApiClient();
  List<String> _moves = [];
  List<String> _san = [];
  int _ply = 0;
  String _fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  Map<String, dynamic>? _analysis;
  String? _error;
  bool _busy = false;
  int _depth = 18;
  int _multipv = 3;
  int _reqId = 0;

  List<String> get _prefixMoves => _moves.take(_ply).toList();

  String? get _bestFrom {
    final bm = _analysis?['best_move']?.toString();
    if (bm == null || bm.length < 4) return null;
    return bm.substring(0, 2);
  }

  String? get _bestTo {
    final bm = _analysis?['best_move']?.toString();
    if (bm == null || bm.length < 4) return null;
    return bm.substring(2, 4);
  }

  Future<void> _syncFen() async {
    try {
      final fen = await _api.fenFromMoves(_prefixMoves);
      if (mounted) setState(() => _fen = fen);
    } catch (_) {}
  }

  Future<void> _run() async {
    final id = ++_reqId;
    setState(() {
      _busy = true;
      _error = null;
    });
    await _syncFen();
    try {
      final a = await _api.analyze(
        moves: _prefixMoves,
        depth: _depth,
        multipv: _multipv,
        movetimeMs: 900,
      );
      if (!mounted || id != _reqId) return;
      setState(() {
        _analysis = a;
        if (a['fen'] is String) _fen = a['fen'] as String;
      });
    } catch (e) {
      if (!mounted || id != _reqId) return;
      setState(() => _error = '$e');
    } finally {
      if (mounted && id == _reqId) setState(() => _busy = false);
    }
  }

  Future<void> _loadLastSave() async {
    try {
      final list = await _api.listSaves();
      final saves = (list['saves'] as List?) ?? [];
      if (saves.isEmpty) {
        setState(() => _error = 'Aucune sauvegarde');
        return;
      }
      final name = (saves.first['path'] ?? saves.first['name'])?.toString();
      if (name == null || name.isEmpty) {
        setState(() => _error = 'Sauvegarde invalide');
        return;
      }
      final data = await _api.loadSave(name);
      final moves = (data['moves'] as List?)?.map((e) => e.toString()).toList() ?? [];
      final san = (data['san'] as List?)?.map((e) => e.toString()).toList() ?? [];
      setState(() {
        _moves = moves;
        _san = san;
        _ply = moves.length;
        _analysis = null;
      });
      await _run();
    } catch (e) {
      setState(() => _error = '$e');
    }
  }

  Future<void> _goPly(int ply) async {
    setState(() {
      _ply = ply.clamp(0, _moves.length);
      _analysis = null;
    });
    await _run();
  }

  void _reset() {
    setState(() {
      _moves = [];
      _san = [];
      _ply = 0;
      _fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
      _analysis = null;
      _error = null;
    });
    _run();
  }

  double get _evalFraction {
    final a = _analysis;
    if (a == null) return 0.5;
    final mate = a['mate'];
    if (mate is num) {
      return mate > 0 ? 0.97 : 0.03;
    }
    final cp = a['score_cp'] ?? a['white_advantage'];
    if (cp is! num) return 0.5;
    final x = (cp / 100.0).clamp(-8.0, 8.0);
    return 1 / (1 + math.exp(-x * 0.7));
  }

  @override
  void initState() {
    super.initState();
    _run();
  }

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 900;
    final a = _analysis;
    final board = ChessBoardView(
      fen: _fen,
      legalUci: const [],
      interactive: false,
      lastFrom: _bestFrom,
      lastTo: _bestTo,
    );
    final panel = _AnalysisPanel(
      analysis: a,
      busy: _busy,
      error: _error,
      depth: _depth,
      multipv: _multipv,
      moves: _moves,
      san: _san,
      ply: _ply,
      evalFraction: _evalFraction,
      onAnalyse: _run,
      onLoadSave: _loadLastSave,
      onReset: _reset,
      onDepth: (d) => setState(() => _depth = d),
      onMulti: (m) => setState(() => _multipv = m),
      onPly: _goPly,
    );

    if (wide) {
      return Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            SizedBox(width: 28, child: _EvalBar(fraction: _evalFraction, evalText: a?['eval']?.toString())),
            const SizedBox(width: 10),
            Expanded(flex: 5, child: board),
            const SizedBox(width: 12),
            Expanded(flex: 4, child: panel),
          ],
        ),
      );
    }

    return Column(
      children: [
        SizedBox(
          height: 240,
          child: Row(
            children: [
              SizedBox(width: 22, child: _EvalBar(fraction: _evalFraction, evalText: a?['eval']?.toString())),
              Expanded(child: Padding(padding: const EdgeInsets.all(6), child: board)),
            ],
          ),
        ),
        Expanded(child: panel),
      ],
    );
  }
}

class _EvalBar extends StatelessWidget {
  const _EvalBar({required this.fraction, this.evalText});
  final double fraction;
  final String? evalText;

  @override
  Widget build(BuildContext context) {
    final f = fraction.clamp(0.02, 0.98);
    return Tooltip(
      message: evalText ?? 'Éval (perspective Blancs)',
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: D4Theme.line),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(5),
          child: Column(
            children: [
              Expanded(flex: ((1 - f) * 1000).round().clamp(1, 999), child: Container(color: const Color(0xFF1A1A1A))),
              Expanded(flex: (f * 1000).round().clamp(1, 999), child: Container(color: const Color(0xFFE8E8E8))),
            ],
          ),
        ),
      ),
    );
  }
}

class _AnalysisPanel extends StatelessWidget {
  const _AnalysisPanel({
    required this.analysis,
    required this.busy,
    required this.error,
    required this.depth,
    required this.multipv,
    required this.moves,
    required this.san,
    required this.ply,
    required this.evalFraction,
    required this.onAnalyse,
    required this.onLoadSave,
    required this.onReset,
    required this.onDepth,
    required this.onMulti,
    required this.onPly,
  });

  final Map<String, dynamic>? analysis;
  final bool busy;
  final String? error;
  final int depth;
  final int multipv;
  final List<String> moves;
  final List<String> san;
  final int ply;
  final double evalFraction;
  final VoidCallback onAnalyse;
  final VoidCallback onLoadSave;
  final VoidCallback onReset;
  final ValueChanged<int> onDepth;
  final ValueChanged<int> onMulti;
  final ValueChanged<int> onPly;

  @override
  Widget build(BuildContext context) {
    final a = analysis;
    final lines = (a?['lines'] as List?) ?? const [];
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Text(
                  a?['eval']?.toString() ?? (busy ? '…' : '—'),
                  style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: D4Theme.goldBright),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    busy
                        ? 'Stockfish calcule…'
                        : 'Coup $ply / ${moves.length} · profondeur ${a?['depth'] ?? depth} · MultiPV $multipv',
                    style: const TextStyle(color: D4Theme.muted, fontSize: 12),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ElevatedButton(
                  onPressed: busy ? null : onAnalyse,
                  child: Text(busy ? 'Analyse…' : 'Analyser'),
                ),
                OutlinedButton(onPressed: busy ? null : onLoadSave, child: const Text('Dernière sauvegarde')),
                OutlinedButton(onPressed: busy ? null : onReset, child: const Text('Position initiale')),
                OutlinedButton(
                  onPressed: ply > 0 && !busy ? () => onPly(ply - 1) : null,
                  child: const Text('◀'),
                ),
                OutlinedButton(
                  onPressed: ply < moves.length && !busy ? () => onPly(ply + 1) : null,
                  child: const Text('▶'),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Text('Depth', style: TextStyle(color: D4Theme.muted, fontSize: 12)),
                Expanded(
                  child: Slider(
                    value: depth.toDouble(),
                    min: 12,
                    max: 24,
                    divisions: 6,
                    label: '$depth',
                    onChanged: busy ? null : (v) => onDepth(v.round()),
                  ),
                ),
                Text('$depth', style: const TextStyle(color: D4Theme.gold)),
              ],
            ),
            Row(
              children: [
                const Text('Lignes', style: TextStyle(color: D4Theme.muted, fontSize: 12)),
                Expanded(
                  child: Slider(
                    value: multipv.toDouble(),
                    min: 1,
                    max: 5,
                    divisions: 4,
                    label: '$multipv',
                    onChanged: busy ? null : (v) => onMulti(v.round()),
                  ),
                ),
                Text('$multipv', style: const TextStyle(color: D4Theme.gold)),
              ],
            ),
            if (error != null) Text(error!, style: const TextStyle(color: D4Theme.offline)),
            const Divider(color: D4Theme.line),
            const Text('Variantes Stockfish', style: TextStyle(color: D4Theme.gold, fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            Expanded(
              child: ListView(
                children: [
                  if (lines.isEmpty && !busy)
                    const Text('Lancez une analyse ou chargez une partie.', style: TextStyle(color: D4Theme.muted)),
                  for (final raw in lines)
                    if (raw is Map) _LineTile(line: Map<String, dynamic>.from(raw)),
                  if (san.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    const Text('Coups de la partie', style: TextStyle(color: D4Theme.gold, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 4,
                      runSpacing: 4,
                      children: [
                        ChoiceChip(
                          label: const Text('0. Début', style: TextStyle(fontSize: 12)),
                          selected: ply == 0,
                          onSelected: busy ? null : (_) => onPly(0),
                          visualDensity: VisualDensity.compact,
                        ),
                        for (var i = 0; i < san.length; i++)
                          ChoiceChip(
                            label: Text(
                              i.isEven ? '${i ~/ 2 + 1}. ${san[i]}' : san[i],
                              style: const TextStyle(fontSize: 12),
                            ),
                            selected: ply == i + 1,
                            onSelected: busy ? null : (_) => onPly(i + 1),
                            visualDensity: VisualDensity.compact,
                          ),
                      ],
                    ),
                  ],
                  const SizedBox(height: 12),
                  Text(
                    'Nœuds ${a?['nodes'] ?? '—'} · NPS ${a?['nps'] ?? '—'} · ${a?['time_ms'] ?? '—'} ms',
                    style: const TextStyle(color: D4Theme.muted, fontSize: 11),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LineTile extends StatelessWidget {
  const _LineTile({required this.line});
  final Map<String, dynamic> line;

  @override
  Widget build(BuildContext context) {
    final n = line['multipv'] ?? '?';
    final ev = line['eval'] ?? '—';
    final san = (line['pv_san'] as List?)?.map((e) => e.toString()).toList() ?? const [];
    final uci = (line['pv_uci'] is List)
        ? (line['pv_uci'] as List).map((e) => e.toString()).toList()
        : (line['pv_uci']?.toString().split(' ') ?? const <String>[]);
    final pv = san.isNotEmpty ? san.take(12).join(' ') : uci.take(8).join(' ');
    final best = line['best_move'] ?? '';
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: D4Theme.surfaceSoft,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: n == 1 ? D4Theme.gold : D4Theme.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 22,
                height: 22,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: n == 1 ? D4Theme.gold : D4Theme.line,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text('$n', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: n == 1 ? Colors.black : D4Theme.text)),
              ),
              const SizedBox(width: 8),
              Text('$ev', style: const TextStyle(fontWeight: FontWeight.w700, color: D4Theme.goldBright, fontSize: 16)),
              const SizedBox(width: 8),
              Text('$best', style: const TextStyle(color: D4Theme.muted, fontFamily: 'Consolas')),
            ],
          ),
          const SizedBox(height: 4),
          Text(pv.isEmpty ? '—' : pv, style: const TextStyle(height: 1.35, fontSize: 13)),
        ],
      ),
    );
  }
}
