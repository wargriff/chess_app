import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:chess_pro_d4/api/api_client.dart';
import 'package:chess_pro_d4/screens/updates_settings_page.dart';
import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/ui/scrollable_sub_tabs.dart';

/// Système / Paramètres — 5 sous-onglets : Jeu · Réseau · Mise à jour · Aide · À propos
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  int _section = 0;
  late TextEditingController _nameCtrl;
  late TextEditingController _apiCtrl;

  @override
  void initState() {
    super.initState();
    final state = context.read<AppState>();
    _nameCtrl = TextEditingController(text: state.playerName);
    _apiCtrl = TextEditingController(text: ApiClient.defaultBase);
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _apiCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    return SectionScaffold(
      sectionTitle: 'Système',
      index: _section,
      onIndexChanged: (i) => setState(() => _section = i),
      labels: const ['Jeu', 'Réseau', 'Mise à jour', 'Aide', 'À propos'],
      icons: const [
        Icons.sports_esports_outlined,
        Icons.wifi,
        Icons.system_update_alt,
        Icons.help_outline,
        Icons.info_outline,
      ],
      pages: [
        Padding(padding: const EdgeInsets.all(14), child: _jeu(state)),
        Padding(padding: const EdgeInsets.all(14), child: _reseau(state)),
        const Padding(padding: EdgeInsets.all(14), child: UpdatesSettingsPage()),
        Padding(padding: const EdgeInsets.all(14), child: _aide()),
        Padding(padding: const EdgeInsets.all(14), child: _apropos(state)),
      ],
    );
  }

  Widget _jeu(AppState state) => ListView(
        children: [
          const Text('Jeu', style: TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          const Text('Nom du joueur', style: TextStyle(color: D4Theme.muted)),
          const SizedBox(height: 6),
          TextField(controller: _nameCtrl, onSubmitted: state.setPlayerName),
          const SizedBox(height: 8),
          ElevatedButton(onPressed: () => state.setPlayerName(_nameCtrl.text), child: const Text('Enregistrer')),
          const Divider(height: 32, color: D4Theme.line),
          const Text('Préférence de couleur', style: TextStyle(color: D4Theme.gold, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              for (final c in [('white', 'Blancs'), ('black', 'Noirs'), ('random', 'Aléatoire')])
                ChoiceChip(
                  label: Text(c.$2),
                  selected: state.colorPref == c.$1,
                  onSelected: (_) => state.setColorPref(c.$1),
                ),
            ],
          ),
          const SizedBox(height: 16),
          const Text('Chronomètre', style: TextStyle(color: D4Theme.gold, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final t in [
                (0, 0, 'Sans limite'),
                (3, 2, '3+2'),
                (5, 0, '5+0'),
                (10, 0, '10+0'),
                (10, 5, '10+5'),
                (15, 10, '15+10'),
              ])
                ChoiceChip(
                  label: Text(t.$3),
                  selected: state.timeMinutes == t.$1 && state.timeIncrement == t.$2,
                  onSelected: (_) => state.setTimeControl(t.$1, t.$2),
                ),
            ],
          ),
        ],
      );

  Widget _reseau(AppState state) => ListView(
        children: [
          const Text('Réseau', style: TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          TextField(
            controller: _apiCtrl,
            decoration: const InputDecoration(
              labelText: 'URL API backend',
              hintText: 'http://127.0.0.1:3848',
              helperText: 'Le port 3848 est obligatoire pour le QR / join',
            ),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: () {
              final url = _apiCtrl.text.trim().replaceAll(RegExp(r'/$'), '');
              if (url.isEmpty) return;
              ApiClient.defaultBase = url;
              state.setApiBase(url);
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('API → $url')));
            },
            child: const Text('Appliquer'),
          ),
          ListTile(title: const Text('API active'), subtitle: Text(ApiClient.defaultBase)),
          ListTile(title: const Text('IP hôte'), subtitle: Text(state.localIp)),
          ListTile(
            leading: Icon(Icons.circle, size: 12, color: state.connectionColor),
            title: const Text('Backend'),
            subtitle: Text(state.connectionLabel),
          ),
          const ListTile(
            title: Text('QR / lien'),
            subtitle: Text('Format : http://IP:3848/join/CODE — le port est obligatoire.'),
          ),
        ],
      );

  Widget _aide() => ListView(
        children: [
          const Text('Aide', style: TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          const ListTile(
            leading: Icon(Icons.play_arrow, color: D4Theme.gold),
            title: Text('Jouer'),
            subtitle: Text('Contre IA, Local QR, ou 1 vs 1 sur le même PC.'),
          ),
          const ListTile(
            leading: Icon(Icons.qr_code_2, color: D4Theme.gold),
            title: Text('Local'),
            subtitle: Text('Créer une partie, scanner le QR (lien HTTPS mondial).'),
          ),
          const ListTile(
            leading: Icon(Icons.analytics_outlined, color: D4Theme.gold),
            title: Text('Analyse'),
            subtitle: Text('Évaluation Stockfish, MultiPV et navigation coup par coup.'),
          ),
          const ListTile(
            leading: Icon(Icons.update, color: D4Theme.gold),
            title: Text('Mise à jour'),
            subtitle: Text('Utilisez METTRE_A_JOUR.bat puis FLUTTER.bat.'),
          ),
          const ListTile(
            leading: Icon(Icons.palette_outlined, color: D4Theme.gold),
            title: Text('Apparence'),
            subtitle: Text('Thème, échiquier, pièces, son et animations.'),
          ),
        ],
      );

  Widget _apropos(AppState state) => ListView(
        children: [
          const Text('À propos', style: TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          const ListTile(
            title: Text('Chess Pro D4'),
            subtitle: Text('Flutter Desktop + FastAPI + Stockfish UCI\nIdentité : sombre · or · graphite'),
          ),
          ListTile(title: const Text('Backend'), subtitle: Text('${ApiClient.defaultBase} · IP ${state.localIp}')),
          ListTile(title: const Text('Stockfish'), subtitle: Text(state.stockfishLabel)),
        ],
      );
}
