import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:chess_pro_d4/api/api_client.dart';
import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/ui/scrollable_sub_tabs.dart';

/// IA — 3 sous-onglets : Niveau · Test · Infos
class EngineHubScreen extends StatefulWidget {
  const EngineHubScreen({super.key});
  @override
  State<EngineHubScreen> createState() => _EngineHubScreenState();
}

class _EngineHubScreenState extends State<EngineHubScreen> {
  int _index = 0;
  List<Map<String, dynamic>> _levels = [];

  @override
  void initState() {
    super.initState();
    _loadLevels();
  }

  Future<void> _loadLevels() async {
    try {
      final r = await ApiClient().engineLevels();
      final list = (r['levels'] as List?) ?? [];
      setState(() {
        _levels = list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      });
    } catch (_) {
      setState(() {
        _levels = [
          for (final e in [400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200])
            {'elo': e, 'label': '$e'},
        ];
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    return SectionScaffold(
      sectionTitle: 'IA',
      index: _index,
      onIndexChanged: (i) => setState(() => _index = i),
      labels: const ['Niveau', 'Test', 'Infos'],
      icons: const [Icons.speed, Icons.science_outlined, Icons.info_outline],
      pages: [
        Padding(padding: const EdgeInsets.all(14), child: _levelsPage(state)),
        Padding(padding: const EdgeInsets.all(14), child: _testPage(state)),
        Padding(padding: const EdgeInsets.all(14), child: _infoPage(state)),
      ],
    );
  }

  Widget _levelsPage(AppState state) => ListView(
        children: [
          const Text('Niveau Stockfish', style: TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text('Actuel : ${state.elo}', style: const TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          const Text(
            'Configure Skill / UCI_Elo / temps / threads côté moteur.',
            style: TextStyle(color: D4Theme.muted, fontSize: 12),
          ),
          const SizedBox(height: 8),
          for (final lvl in _levels)
            ListTile(
              dense: true,
              title: Text('${lvl['elo']} — ${lvl['label']}'),
              subtitle: Text(
                'temps ${lvl['movetime_ms'] ?? '—'} ms · threads ${lvl['threads'] ?? '—'}',
                style: const TextStyle(fontSize: 11),
              ),
              trailing: state.elo == lvl['elo'] ? const Icon(Icons.check, color: D4Theme.gold) : null,
              onTap: () async {
                final elo = lvl['elo'] as int;
                state.setElo(elo);
                try {
                  await ApiClient().configureEngine(elo: elo);
                } catch (_) {}
              },
            ),
        ],
      );

  Widget _testPage(AppState state) => ListView(
        children: [
          const Text('Test moteur', style: TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          ListTile(
            leading: Icon(Icons.circle, size: 12, color: state.stockfishOnline ? D4Theme.online : D4Theme.offline),
            title: Text(state.stockfishOnline ? 'Stockfish en ligne' : 'Stockfish hors ligne'),
            subtitle: Text(state.stockfishLabel),
          ),
          ElevatedButton(
            onPressed: () async {
              try {
                final h = await ApiClient().health();
                state.applyHealth(h);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(h['stockfish'] == true ? 'Stockfish OK' : 'Stockfish hors ligne')),
                  );
                }
              } catch (e) {
                state.setOffline('$e');
              }
            },
            child: const Text('Tester Stockfish'),
          ),
        ],
      );

  Widget _infoPage(AppState state) => ListView(
        children: [
          const Text('Infos IA', style: TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          ListTile(title: const Text('Moteur'), subtitle: Text(state.stockfishLabel)),
          ListTile(title: const Text('ELO'), subtitle: Text('${state.elo}')),
          const ListTile(
            title: Text('Couleur de départ'),
            subtitle: Text('Réglable dans Système → Jeu (Blancs / Noirs / Aléatoire).'),
          ),
        ],
      );
}
