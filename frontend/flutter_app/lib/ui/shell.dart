import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';

/// 8 onglets principaux — chacun a exactement 3 sous-onglets dans son hub.
class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.child, required this.location});
  final Widget child;
  final String location;

  static const destinations = [
    ('/', 'Accueil', Icons.home_outlined),
    ('/play', 'Jouer', Icons.sports_esports_outlined),
    ('/local', 'Local', Icons.qr_code_2),
    ('/analyse', 'Analyse', Icons.analytics_outlined),
    ('/library', 'Bibliothèque', Icons.folder_outlined),
    ('/appearance', 'Apparence', Icons.palette_outlined),
    ('/engine', 'IA', Icons.smart_toy_outlined),
    ('/settings', 'Système', Icons.settings_outlined),
  ];

  int _indexFromLoc(String loc) {
    if (loc.startsWith('/play')) return 1;
    if (loc.startsWith('/local')) return 2;
    if (loc.startsWith('/analyse')) return 3;
    if (loc.startsWith('/library') || loc.startsWith('/history') || loc.startsWith('/saves')) return 4;
    if (loc.startsWith('/appearance')) return 5;
    if (loc.startsWith('/engine')) return 6;
    if (loc.startsWith('/settings') || loc.startsWith('/stats')) return 7;
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final useRail = width >= 900;
    final state = context.watch<AppState>();
    final idx = _indexFromLoc(location);

    return Scaffold(
      body: Row(
        children: [
          if (useRail) _MainRail(index: idx),
          if (useRail) const VerticalDivider(width: 1, color: D4Theme.line),
          Expanded(
            child: Column(
              children: [
                _HeaderBar(state: state),
                if (!useRail)
                  Material(
                    color: D4Theme.surface,
                    child: SizedBox(
                      height: 50,
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                        children: [
                          for (var i = 0; i < destinations.length; i++)
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 3),
                              child: ChoiceChip(
                                label: Text(destinations[i].$2, style: const TextStyle(fontSize: 12)),
                                selected: idx == i,
                                onSelected: (_) => context.go(destinations[i].$1),
                                selectedColor: D4Theme.gold.withValues(alpha: 0.18),
                                labelStyle: TextStyle(
                                  color: idx == i ? D4Theme.goldBright : D4Theme.muted,
                                  fontWeight: idx == i ? FontWeight.w600 : FontWeight.w500,
                                ),
                                side: BorderSide(color: idx == i ? D4Theme.gold : D4Theme.line),
                                visualDensity: VisualDensity.compact,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                Expanded(child: child),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Rail défilable (8 onglets) — évite le débordement NavigationRail.
class _MainRail extends StatelessWidget {
  const _MainRail({required this.index});
  final int index;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: D4Theme.surface,
      child: SizedBox(
        width: 88,
        child: Column(
          children: [
            const Padding(
              padding: EdgeInsets.only(top: 14, bottom: 8),
              child: Text('♞', style: TextStyle(color: D4Theme.goldBright, fontSize: 24)),
            ),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                itemCount: AppShell.destinations.length,
                itemBuilder: (context, i) {
                  final d = AppShell.destinations[i];
                  final selected = i == index;
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Material(
                      color: selected ? D4Theme.gold.withValues(alpha: 0.14) : Colors.transparent,
                      borderRadius: BorderRadius.circular(10),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(10),
                        onTap: () => context.go(d.$1),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          child: Column(
                            children: [
                              Icon(
                                d.$3,
                                size: 22,
                                color: selected ? D4Theme.goldBright : D4Theme.muted,
                              ),
                              const SizedBox(height: 4),
                              Text(
                                d.$2,
                                textAlign: TextAlign.center,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontSize: 10,
                                  height: 1.1,
                                  fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
                                  color: selected ? D4Theme.goldBright : D4Theme.muted,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HeaderBar extends StatelessWidget {
  const _HeaderBar({required this.state});
  final AppState state;

  @override
  Widget build(BuildContext context) {
    final w = MediaQuery.sizeOf(context).width;
    final title = w < 520 ? 'D4' : (w < 900 ? 'Chess Pro' : 'Chess Pro D4');
    return Container(
      height: 52,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: const BoxDecoration(
        color: D4Theme.surface,
        border: Border(bottom: BorderSide(color: D4Theme.line)),
      ),
      child: Row(
        children: [
          Text(
            title,
            style: const TextStyle(
              color: D4Theme.goldBright,
              fontSize: 18,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.4,
            ),
          ),
          const SizedBox(width: 14),
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(color: state.connectionColor, shape: BoxShape.circle),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              state.connectionLabel,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: D4Theme.muted, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}
