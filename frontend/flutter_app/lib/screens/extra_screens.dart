import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'package:chess_pro_d4/api/api_client.dart';
import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/widgets/chess_board.dart';

export 'package:chess_pro_d4/screens/settings_screen.dart';
export 'package:chess_pro_d4/screens/analyse_screen.dart';

class SavesScreen extends StatefulWidget {
  const SavesScreen({super.key});
  @override
  State<SavesScreen> createState() => _SavesScreenState();
}

class _SavesScreenState extends State<SavesScreen> {
  final _api = ApiClient();
  final _search = TextEditingController();
  List<dynamic> _items = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final r = await _api.listSaves();
      setState(() {
        _items = (r['saves'] as List?) ?? [];
        _error = null;
      });
    } catch (e) {
      setState(() => _error = '$e');
    }
  }

  List<dynamic> get _filtered {
    final q = _search.text.trim().toLowerCase();
    if (q.isEmpty) return _items;
    return _items.where((s) {
      final label = '${s['label']}${s['white']}${s['black']}${s['path']}'.toLowerCase();
      return label.contains(q);
    }).toList();
  }

  Future<void> _delete(String name) async {
    await _api.deleteSave(name);
    await _load();
  }

  Future<void> _export(String name) async {
    try {
      final pgn = await _api.exportPgn(name);
      await Clipboard.setData(ClipboardData(text: pgn));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('PGN copiù dans le presse-papiers')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Center(
        child: Text('Backend requis (port 3848)\n$_error',
            textAlign: TextAlign.center, style: const TextStyle(color: D4Theme.offline)),
      );
    }
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 6),
          child: TextField(
            controller: _search,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search, color: D4Theme.muted),
              hintText: 'Rechercher une partieù',
            ),
          ),
        ),
        Expanded(
          child: _filtered.isEmpty
              ? const Center(child: Text('Aucune partie sauvegardùe', style: TextStyle(color: D4Theme.muted)))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.separated(
                    itemCount: _filtered.length,
                    separatorBuilder: (_, __) => const Divider(color: D4Theme.line, height: 1),
                    itemBuilder: (_, i) {
                      final s = _filtered[i] as Map<String, dynamic>;
                      final path = s['path'] as String;
                      return ListTile(
                        title: Text(s['label']?.toString() ?? path, style: const TextStyle(color: D4Theme.text)),
                        subtitle: Text(
                          '${s['saved_at']} ù ${s['white']} vs ${s['black']} ù ${s['result']} ù ${s['ply']} coups',
                          style: const TextStyle(color: D4Theme.muted, fontSize: 12),
                        ),
                        trailing: Wrap(
                          children: [
                            IconButton(
                              tooltip: 'Exporter PGN',
                              icon: const Icon(Icons.copy_all_outlined, color: D4Theme.muted),
                              onPressed: () => _export(path),
                            ),
                            IconButton(
                              tooltip: 'Analyser',
                              icon: const Icon(Icons.analytics_outlined, color: D4Theme.muted),
                              onPressed: () => context.go('/analyse'),
                            ),
                            IconButton(
                              tooltip: 'Supprimer',
                              icon: const Icon(Icons.delete_outline, color: D4Theme.muted),
                              onPressed: () => _delete(path),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
        ),
      ],
    );
  }
}

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});
  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final _api = ApiClient();
  final _search = TextEditingController();
  List<dynamic> _items = [];
  String _filter = 'all';
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final r = await _api.listSaves();
      setState(() {
        _items = (r['saves'] as List?) ?? [];
        _error = null;
      });
    } catch (e) {
      setState(() => _error = '$e');
    }
  }

  List<dynamic> get _filtered {
    var list = _items;
    final q = _search.text.trim().toLowerCase();
    if (q.isNotEmpty) {
      list = list.where((s) => '${s['white']}${s['black']}${s['label']}'.toLowerCase().contains(q)).toList();
    }
    switch (_filter) {
      case 'win':
        return list.where((s) => s['result']?.toString() == '1-0').toList();
      case 'loss':
        return list.where((s) => s['result']?.toString() == '0-1').toList();
      case 'draw':
        return list.where((s) => s['result']?.toString() == '1/2-1/2').toList();
      case 'pve':
        return list.where((s) {
          final m = (s['mode']?.toString() ?? '').toUpperCase();
          return m.contains('PVE') || m.contains('STOCK');
        }).toList();
      case 'local':
        return list.where((s) {
          final m = (s['mode']?.toString() ?? '').toUpperCase();
          return m.contains('LOCAL') || m.contains('PVP');
        }).toList();
      default:
        return list;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: D4Theme.offline)));
    }
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 4),
          child: TextField(
            controller: _search,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              hintText: 'Rechercher une partieù',
            ),
          ),
        ),
        SizedBox(
          height: 44,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 8),
            children: [
              for (final f in [
                ('all', 'Toutes'),
                ('win', 'Victoires'),
                ('loss', 'Dùfaites'),
                ('draw', 'Nulles'),
                ('local', 'Local'),
                ('pve', 'Stockfish'),
              ])
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 6),
                  child: ChoiceChip(
                    label: Text(f.$2),
                    selected: _filter == f.$1,
                    onSelected: (_) => setState(() => _filter = f.$1),
                    selectedColor: D4Theme.surfaceSoft,
                    labelStyle: TextStyle(color: _filter == f.$1 ? D4Theme.goldBright : D4Theme.muted),
                  ),
                ),
            ],
          ),
        ),
        Expanded(
          child: _filtered.isEmpty
              ? const Center(child: Text('Aucune partie', style: TextStyle(color: D4Theme.muted)))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.separated(
                    itemCount: _filtered.length,
                    separatorBuilder: (_, __) => const Divider(color: D4Theme.line, height: 1),
                    itemBuilder: (_, i) {
                      final s = _filtered[i] as Map<String, dynamic>;
                      return ListTile(
                        title: Text('${s['white'] ?? '?'} vs ${s['black'] ?? '?'}',
                            style: const TextStyle(color: D4Theme.text)),
                        subtitle: Text(
                          '${s['saved_at']} ù ${s['mode']} ù ${s['result']} ù ELO ${s['elo'] ?? 'ù'} ù ${s['ply']} coups',
                          style: const TextStyle(color: D4Theme.muted, fontSize: 12),
                        ),
                        trailing: Wrap(
                          spacing: 4,
                          children: [
                            TextButton(onPressed: () => context.go('/analyse'), child: const Text('Analyser')),
                            TextButton(onPressed: () => context.go('/play/stockfish'), child: const Text('Rejouer')),
                          ],
                        ),
                      );
                    },
                  ),
                ),
        ),
      ],
    );
  }
}

class StatsScreen extends StatelessWidget {
  const StatsScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return FutureBuilder(
      future: ApiClient().listSaves(),
      builder: (context, snap) {
        if (snap.hasError) {
          return Center(child: Text('${snap.error}', style: const TextStyle(color: D4Theme.offline)));
        }
        if (!snap.hasData) {
          return const Center(child: CircularProgressIndicator(color: D4Theme.gold));
        }
        final saves = (snap.data!['saves'] as List?) ?? [];
        final count = saves.length;
        var wins = 0, losses = 0, draws = 0;
        for (final s in saves) {
          final r = s['result']?.toString();
          if (r == '1-0') wins++;
          if (r == '0-1') losses++;
          if (r == '1/2-1/2') draws++;
        }
        final rate = count == 0 ? 0.0 : wins / count * 100;
        final elo = context.watch<AppState>().elo;
        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 720),
              child: Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  _StatCard(label: 'Parties', value: '$count'),
                  _StatCard(label: 'Victoires', value: '$wins'),
                  _StatCard(label: 'Dùfaites', value: '$losses'),
                  _StatCard(label: 'Nulles', value: '$draws'),
                  _StatCard(label: 'Taux de victoire', value: '${rate.toStringAsFixed(0)}%'),
                  _StatCard(label: 'ELO actuel', value: '$elo'),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 160,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Text(value,
                  style: const TextStyle(fontSize: 28, color: D4Theme.goldBright, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text(label, style: const TextStyle(color: D4Theme.muted, fontSize: 12)),
            ],
          ),
        ),
      ),
    );
  }
}

