import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'package:chess_pro_d4/screens/library_screens.dart';
import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/ui/scrollable_sub_tabs.dart';

class HomeHubScreen extends StatefulWidget {
  const HomeHubScreen({super.key});
  @override
  State<HomeHubScreen> createState() => _HomeHubScreenState();
}

class _HomeHubScreenState extends State<HomeHubScreen> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    return SectionScaffold(
      sectionTitle: 'Accueil',
      index: _index,
      onIndexChanged: (i) => setState(() => _index = i),
      labels: const ['Tableau de bord', 'Statistiques'],
      icons: const [Icons.dashboard_outlined, Icons.bar_chart],
      pages: const [
        _DashboardPage(),
        StatsScreen(),
      ],
    );
  }
}

class _DashboardPage extends StatelessWidget {
  const _DashboardPage();

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final w = MediaQuery.sizeOf(context).width;
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFF12100E), Color(0xFF080605)],
        ),
      ),
      child: Center(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: w > 900 ? 720 : 560),
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 28),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  w < 500 ? 'D4' : 'Chess Pro D4',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: w < 500 ? 34 : 42,
                    color: D4Theme.goldBright,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.1,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Stockfish UCI  ·  Échecs premium',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: D4Theme.muted, fontSize: 14),
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _StatusPill(
                      ok: state.link == BackendLink.online,
                      label: state.link == BackendLink.starting ? 'Démarrage…' : 'Backend',
                    ),
                    const SizedBox(width: 10),
                    _StatusPill(ok: state.stockfishOnline, label: 'Stockfish'),
                    const SizedBox(width: 10),
                    _StatusPill(ok: true, label: 'ELO ${state.elo}'),
                  ],
                ),
                const SizedBox(height: 28),
                _HomeAction(
                  title: 'Jouer contre Stockfish',
                  subtitle: 'Partie UCI réelle · niveaux ELO',
                  primary: true,
                  onTap: () => context.go('/play/stockfish'),
                ),
                const SizedBox(height: 10),
                _HomeAction(
                  title: 'Jouer en local',
                  subtitle: 'QR Code · lien · deux appareils',
                  onTap: () => context.go('/local'),
                ),
                const SizedBox(height: 10),
                _HomeAction(
                  title: 'Analyser une partie',
                  subtitle: 'Évaluation · PV · profondeur',
                  onTap: () => context.go('/analyse'),
                ),
                const SizedBox(height: 10),
                _HomeAction(
                  title: 'Sauvegardes',
                  subtitle: 'Bibliothèque JSON / PGN',
                  onTap: () => context.go('/library'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.ok, required this.label});
  final bool ok;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: D4Theme.surfaceSoft,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: D4Theme.line),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.circle, size: 7, color: ok ? D4Theme.online : D4Theme.offline),
          const SizedBox(width: 6),
          Text(label, style: const TextStyle(color: D4Theme.muted, fontSize: 11)),
        ],
      ),
    );
  }
}

class _HomeAction extends StatelessWidget {
  const _HomeAction({
    required this.title,
    required this.subtitle,
    required this.onTap,
    this.primary = false,
  });
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final bool primary;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: primary ? D4Theme.gold.withValues(alpha: 0.12) : D4Theme.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: primary ? D4Theme.gold : D4Theme.line),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        color: primary ? D4Theme.goldBright : D4Theme.text,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(subtitle, style: const TextStyle(color: D4Theme.muted, fontSize: 12)),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: primary ? D4Theme.gold : D4Theme.muted),
            ],
          ),
        ),
      ),
    );
  }
}
