import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'package:chess_pro_d4/screens/library_screens.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/ui/scrollable_sub_tabs.dart';

/// Jouer — exactement 3 sous-onglets (Local est un onglet principal séparé).
class PlaySectionScreen extends StatefulWidget {
  const PlaySectionScreen({super.key, this.initialIndex = 0});
  final int initialIndex;

  @override
  State<PlaySectionScreen> createState() => _PlaySectionScreenState();
}

class _PlaySectionScreenState extends State<PlaySectionScreen> {
  late int _index;

  @override
  void initState() {
    super.initState();
    _index = widget.initialIndex.clamp(0, 2);
  }

  @override
  Widget build(BuildContext context) {
    return SectionScaffold(
      sectionTitle: 'Jouer',
      index: _index,
      onIndexChanged: (i) => setState(() => _index = i),
      labels: const ['Contre IA', 'Rapide', 'Même PC'],
      icons: const [Icons.smart_toy_outlined, Icons.bolt_outlined, Icons.people_outline],
      pages: [
        _LaunchPage(
          title: 'Contre Stockfish',
          subtitle: 'Moteur UCI · ELO et couleur dans IA / Système',
          action: 'Lancer',
          onTap: () => context.go('/play/stockfish'),
          secondary: 'Réglages IA',
          onSecondary: () => context.go('/engine'),
        ),
        _LaunchPage(
          title: 'Partie rapide 5+0',
          subtitle: 'Blitz classique contre Stockfish',
          action: 'Lancer 5+0',
          onTap: () => context.go('/play/stockfish'),
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 24, 24, 8),
              child: _LaunchCard(
                title: 'Joueur contre Joueur',
                subtitle: 'Hotseat sur le même écran',
                action: 'Lancer',
                onTap: () => context.go('/play/local-hotseat'),
              ),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 24),
              child: Text('Récentes', style: TextStyle(color: D4Theme.gold, fontWeight: FontWeight.w600)),
            ),
            const Expanded(child: SavesScreen()),
          ],
        ),
      ],
    );
  }
}

class _LaunchPage extends StatelessWidget {
  const _LaunchPage({
    required this.title,
    required this.subtitle,
    required this.action,
    required this.onTap,
    this.secondary,
    this.onSecondary,
  });

  final String title;
  final String subtitle;
  final String action;
  final VoidCallback onTap;
  final String? secondary;
  final VoidCallback? onSecondary;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(title, style: const TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Text(subtitle, style: const TextStyle(color: D4Theme.muted)),
        const SizedBox(height: 20),
        _LaunchCard(
          title: title,
          subtitle: subtitle,
          action: action,
          onTap: onTap,
          secondary: secondary,
          onSecondary: onSecondary,
        ),
      ],
    );
  }
}

class _LaunchCard extends StatelessWidget {
  const _LaunchCard({
    required this.title,
    required this.subtitle,
    required this.action,
    required this.onTap,
    this.secondary,
    this.onSecondary,
  });

  final String title;
  final String subtitle;
  final String action;
  final VoidCallback onTap;
  final String? secondary;
  final VoidCallback? onSecondary;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: D4Theme.surfaceSoft,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: D4Theme.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
          const SizedBox(height: 4),
          Text(subtitle, style: const TextStyle(color: D4Theme.muted, fontSize: 13)),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            children: [
              ElevatedButton(onPressed: onTap, child: Text(action)),
              if (secondary != null && onSecondary != null)
                OutlinedButton(onPressed: onSecondary, child: Text(secondary!)),
            ],
          ),
        ],
      ),
    );
  }
}
