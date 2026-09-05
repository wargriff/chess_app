import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import 'package:chess_pro_d4/api/api_client.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';

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
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('PGN copié dans le presse-papiers')),
        );
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
        child: Text(
          'Backend requis (port 3848)\n$_error',
          textAlign: TextAlign.center,
          style: const TextStyle(color: D4Theme.offline),
        ),
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
              hintText: 'Rechercher une partie…',
            ),
          ),
        ),
        Expanded(
          child: _filtered.isEmpty
              ? const Center(child: Text('Aucune partie sauvegardée', style: TextStyle(color: D4Theme.muted)))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.separated(
                    itemCount: _filtered.length,
                    separatorBuilder: (_, _) => const Divider(color: D4Theme.line, height: 1),
                    itemBuilder: (_, i) {
                      final s = _filtered[i] as Map<String, dynamic>;
                      final path = s['path'] as String;
                      return ListTile(
                        title: Text(s['label']?.toString() ?? path, style: const TextStyle(color: D4Theme.text)),
                        subtitle: Text(
                          '${s['saved_at']} · ${s['white']} vs ${s['black']} · ${s['result']} · ${s['ply']} coups',
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
  String? _error;
  String _filter = 'all';

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
      list = list.where((s) {
        final label = '${s['label']}${s['white']}${s['black']}${s['result']}'.toLowerCase();
        return label.contains(q);
      }).toList();
    }
    switch (_filter) {
      case 'win':
        return list.where((s) => (s['result']?.toString() ?? '').contains('1-0')).toList();
      case 'loss':
        return list.where((s) => (s['result']?.toString() ?? '').contains('0-1')).toList();
      case 'draw':
        return list.where((s) {
          final r = s['result']?.toString() ?? '';
          return r.contains('1/2') || r == '*';
        }).toList();
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
              hintText: 'Rechercher une partie…',
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
                ('loss', 'Défaites'),
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
                    side: BorderSide(color: _filter == f.$1 ? D4Theme.gold : D4Theme.line),
                    visualDensity: VisualDensity.compact,
                  ),
                ),
            ],
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: _load,
            child: _filtered.isEmpty
                ? ListView(children: const [
                    SizedBox(height: 80),
                    Center(child: Text('Aucune partie', style: TextStyle(color: D4Theme.muted))),
                  ])
                : ListView.builder(
                    itemCount: _filtered.length,
                    itemBuilder: (_, i) {
                      final s = _filtered[i] as Map<String, dynamic>;
                      return ListTile(
                        leading: const Icon(Icons.history, color: D4Theme.gold),
                        title: Text('${s['white']} vs ${s['black']}', style: const TextStyle(color: D4Theme.text)),
                        subtitle: Text(
                          '${s['saved_at']} · ${s['result']} · ${s['mode'] ?? ''}',
                          style: const TextStyle(color: D4Theme.muted, fontSize: 12),
                        ),
                        onTap: () => context.go('/analyse'),
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
    return FutureBuilder<Map<String, dynamic>>(
      future: ApiClient().listSaves(),
      builder: (context, snap) {
        if (snap.hasError) {
          return Center(child: Text('${snap.error}', style: const TextStyle(color: D4Theme.offline)));
        }
        if (!snap.hasData) {
          return const Center(child: CircularProgressIndicator(color: D4Theme.gold));
        }
        final saves = (snap.data!['saves'] as List?) ?? [];
        var wins = 0, losses = 0, draws = 0;
        for (final s in saves) {
          final r = s['result']?.toString() ?? '';
          if (r.startsWith('1-0')) {
            wins++;
          } else if (r.startsWith('0-1')) {
            losses++;
          } else {
            draws++;
          }
        }
        final total = saves.length;
        return ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const Text('Statistiques', style: TextStyle(fontSize: 22, color: D4Theme.goldBright, fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                _StatCard(label: 'Parties', value: '$total'),
                _StatCard(label: 'Victoires', value: '$wins'),
                _StatCard(label: 'Défaites', value: '$losses'),
                _StatCard(label: 'Nulles', value: '$draws'),
              ],
            ),
            const SizedBox(height: 20),
            Text(
              total == 0
                  ? 'Jouez des parties pour alimenter vos statistiques.'
                  : 'Taux de victoire : ${total == 0 ? 0 : ((wins / total) * 100).toStringAsFixed(0)} %',
              style: const TextStyle(color: D4Theme.muted),
            ),
          ],
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
    return Container(
      width: 140,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: D4Theme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: D4Theme.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: D4Theme.muted, fontSize: 12)),
          const SizedBox(height: 6),
          Text(value, style: const TextStyle(color: D4Theme.goldBright, fontSize: 28, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
