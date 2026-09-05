import 'package:flutter/material.dart';

import 'package:chess_pro_d4/screens/analyse_screen.dart';
import 'package:chess_pro_d4/screens/library_screens.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/ui/scrollable_sub_tabs.dart';

class AnalyseHubScreen extends StatefulWidget {
  const AnalyseHubScreen({super.key});
  @override
  State<AnalyseHubScreen> createState() => _AnalyseHubScreenState();
}

class _AnalyseHubScreenState extends State<AnalyseHubScreen> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    return SectionScaffold(
      sectionTitle: 'Analyse',
      index: _index,
      onIndexChanged: (i) => setState(() => _index = i),
      labels: const ['Analyse IA', 'Sauvegardes', 'Historique'],
      icons: const [
        Icons.psychology_outlined,
        Icons.save_outlined,
        Icons.history,
      ],
      pages: const [
        AnalyseScreen(),
        SavesScreen(),
        HistoryScreen(),
      ],
    );
  }
}

class LibraryHubScreen extends StatefulWidget {
  const LibraryHubScreen({super.key});
  @override
  State<LibraryHubScreen> createState() => _LibraryHubScreenState();
}

class _LibraryHubScreenState extends State<LibraryHubScreen> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    return SectionScaffold(
      sectionTitle: 'Bibliothèque',
      index: _index,
      onIndexChanged: (i) => setState(() => _index = i),
      labels: const ['Sauvegardes', 'Historique', 'Favoris', 'Statistiques', 'Export'],
      icons: const [
        Icons.folder_outlined,
        Icons.history,
        Icons.star_outline,
        Icons.bar_chart,
        Icons.copy_all_outlined,
      ],
      pages: const [
        SavesScreen(),
        HistoryScreen(),
        _FavoritesLibraryPage(),
        StatsScreen(),
        _ExportLibraryPage(),
      ],
    );
  }
}

class _FavoritesLibraryPage extends StatelessWidget {
  const _FavoritesLibraryPage();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: const [
        Text('Favoris', style: TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
        SizedBox(height: 12),
        Text(
          'Aucun favori pour le moment.\n\n'
          'Utilisez cet espace pour retrouver plus tard vos parties marquées '
          '(indépendant de l’historique).',
          style: TextStyle(color: D4Theme.muted, height: 1.45),
        ),
        SizedBox(height: 20),
        ListTile(
          leading: Icon(Icons.star_outline, color: D4Theme.gold),
          title: Text('Astuce'),
          subtitle: Text('Depuis Sauvegardes, vous pourrez épingler une partie ici.'),
        ),
      ],
    );
  }
}

class _ExportLibraryPage extends StatelessWidget {
  const _ExportLibraryPage();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Export', style: TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
              SizedBox(height: 6),
              Text(
                'Ouvrez une sauvegarde et utilisez l’action Export / Copier PGN.',
                style: TextStyle(color: D4Theme.muted, fontSize: 13),
              ),
            ],
          ),
        ),
        const Expanded(child: SavesScreen()),
      ],
    );
  }
}

