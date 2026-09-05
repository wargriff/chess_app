import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:chess_pro_d4/services/sound_service.dart';
import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/theme/catalog.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/ui/scrollable_sub_tabs.dart';
import 'package:chess_pro_d4/widgets/board_theme_chip.dart';

/// Apparence — 5 sous-onglets : Thème · Échiquier · Pièces · Son · Animations
class AppearanceHubScreen extends StatefulWidget {
  const AppearanceHubScreen({super.key});
  @override
  State<AppearanceHubScreen> createState() => _AppearanceHubScreenState();
}

class _AppearanceHubScreenState extends State<AppearanceHubScreen> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    return SectionScaffold(
      sectionTitle: 'Apparence',
      index: _index,
      onIndexChanged: (i) => setState(() => _index = i),
      labels: const ['Thème', 'Échiquier', 'Pièces', 'Son', 'Animations'],
      icons: const [
        Icons.color_lens_outlined,
        Icons.grid_on,
        Icons.extension_outlined,
        Icons.volume_up_outlined,
        Icons.animation,
      ],
      pages: [
        _pad(_themePage(state)),
        _pad(_boardPage(state)),
        _pad(_piecesPage(state)),
        _pad(_soundPage(state)),
        _pad(_animPage(state)),
      ],
    );
  }

  Widget _pad(Widget child) =>
      Padding(padding: const EdgeInsets.all(14), child: child);

  /// Grille uniforme : toutes les cartes ont exactement la même taille.
  Widget _equalGrid({
    required int itemCount,
    required double minTileWidth,
    required double childAspectRatio,
    required IndexedWidgetBuilder itemBuilder,
  }) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final maxW = constraints.maxWidth;
        final cols = (maxW / minTileWidth).floor().clamp(2, 8);
        return GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: itemCount,
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: cols,
            mainAxisSpacing: 10,
            crossAxisSpacing: 10,
            childAspectRatio: childAspectRatio,
          ),
          itemBuilder: itemBuilder,
        );
      },
    );
  }

  Widget _themePage(AppState state) => ListView(
        children: [
          const Text('Thème',
              style: TextStyle(
                  fontSize: 18,
                  color: D4Theme.goldBright,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          _equalGrid(
            itemCount: appThemes.length,
            minTileWidth: 130,
            childAspectRatio: 1.35,
            itemBuilder: (_, i) => _themeChip(state, appThemes[i]),
          ),
        ],
      );

  Widget _boardPage(AppState state) => ListView(
        children: [
          const Text('Échiquier',
              style: TextStyle(
                  fontSize: 18,
                  color: D4Theme.goldBright,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text(
            '${boardThemes.length} plateaux — aperçu des cases claires / foncées.',
            style: const TextStyle(color: D4Theme.muted, fontSize: 13),
          ),
          const SizedBox(height: 14),
          _equalGrid(
            itemCount: boardThemes.length,
            minTileWidth: 140,
            childAspectRatio: 0.95,
            itemBuilder: (_, i) {
              final b = boardThemes[i];
              return BoardThemeChip(
                info: b,
                selected: state.boardThemeId == b.id,
                onTap: () => state.setBoardTheme(b.id),
              );
            },
          ),
          const SizedBox(height: 16),
          SwitchListTile(
              title: const Text('Coordonnées'),
              value: state.showCoordinates,
              onChanged: state.setShowCoordinates),
          SwitchListTile(
              title: const Text('Dernier coup'),
              value: state.showLastMove,
              onChanged: state.setShowLastMove),
          SwitchListTile(
              title: const Text('Coups possibles'),
              value: state.showHints,
              onChanged: state.setShowHints),
        ],
      );

  Widget _piecesPage(AppState state) => ListView(
        children: [
          const Text('Pièces',
              style: TextStyle(
                  fontSize: 18,
                  color: D4Theme.goldBright,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text('${pieceSets.length} styles de pièces',
              style: const TextStyle(color: D4Theme.muted, fontSize: 13)),
          const SizedBox(height: 12),
          _equalGrid(
            itemCount: pieceSets.length,
            minTileWidth: 168,
            childAspectRatio: 1.55,
            itemBuilder: (_, i) => _pieceChip(state, pieceSets[i]),
          ),
          ListTile(
              title: Text('Taille : ${state.pieceScale.toStringAsFixed(2)}')),
          Slider(
              value: state.pieceScale,
              min: 0.8,
              max: 1.25,
              onChanged: state.setPieceScale),
        ],
      );

  Widget _soundPage(AppState state) => ListView(
        children: [
          const Text('Son',
              style: TextStyle(
                  fontSize: 18,
                  color: D4Theme.goldBright,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text(
              '${soundPacks.length} packs stylés — touchez pour préécouter',
              style: const TextStyle(color: D4Theme.muted, fontSize: 13)),
          const SizedBox(height: 12),
          SwitchListTile(
            title: const Text('Activer les sons'),
            subtitle: const Text('Coups, captures, échec, mat'),
            value: state.sounds,
            onChanged: (v) {
              state.setSounds(v);
              if (v) SoundService.instance.move();
            },
          ),
          const Divider(height: 24, color: D4Theme.line),
          const Text('Pack sonore',
              style:
                  TextStyle(color: D4Theme.gold, fontWeight: FontWeight.w600)),
          const SizedBox(height: 10),
          _equalGrid(
            itemCount: soundPacks.length,
            minTileWidth: 150,
            childAspectRatio: 1.15,
            itemBuilder: (_, i) {
              final pack = soundPacks[i];
              return _SoundPackChip(
                pack: pack,
                selected: state.soundPackId == pack.id,
                onTap: () {
                  state.setSoundPack(pack.id);
                  SoundService.instance.enabled = state.sounds;
                  SoundService.instance.move();
                },
              );
            },
          ),
        ],
      );

  Widget _animPage(AppState state) => ListView(
        children: [
          const Text('Animations',
              style: TextStyle(
                  fontSize: 18,
                  color: D4Theme.goldBright,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),
          SwitchListTile(
            title: const Text('Animations'),
            subtitle: const Text('Transitions et effets sur l’échiquier'),
            value: state.animations,
            onChanged: state.setAnimations,
          ),
          const ListTile(
            title: Text('Performance'),
            subtitle: Text('Désactivez les animations sur machine lente.'),
          ),
        ],
      );

  Widget _themeChip(AppState state, AppThemeInfo t) {
    final sel = state.appThemeId == t.id;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => state.setAppTheme(t.id),
        borderRadius: BorderRadius.circular(10),
        child: Ink(
          decoration: BoxDecoration(
            color: t.surface,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
                color: sel ? t.gold : D4Theme.line, width: sel ? 2 : 1),
          ),
          child: Padding(
            padding: const EdgeInsets.all(10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(
                  flex: 2,
                  child: Container(
                    decoration: BoxDecoration(
                      color: t.bg,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  height: 8,
                  width: 40,
                  alignment: Alignment.centerLeft,
                  child: Container(
                    width: 40,
                    height: 8,
                    decoration: BoxDecoration(
                      color: t.gold,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  t.label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: t.gold,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                SizedBox(
                  height: 16,
                  child: sel
                      ? const Align(
                          alignment: Alignment.centerLeft,
                          child: Icon(Icons.check_circle,
                              size: 14, color: D4Theme.gold),
                        )
                      : null,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _pieceChip(AppState state, PieceSetInfo p) {
    final sel = state.pieceSetId == p.id;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => state.setPieceSet(p.id),
        borderRadius: BorderRadius.circular(10),
        child: Ink(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
                color: sel ? D4Theme.gold : D4Theme.line, width: sel ? 2 : 1),
            color: D4Theme.surfaceSoft,
          ),
          child: Padding(
            padding: const EdgeInsets.all(10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  p.label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: sel ? D4Theme.goldBright : D4Theme.text,
                  ),
                ),
                Text(
                  p.desc,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 10, color: D4Theme.muted),
                ),
                const SizedBox(height: 8),
                Expanded(
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      for (final code in ['wK', 'wQ', 'wR', 'wB', 'wN', 'wP'])
                        Expanded(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 1),
                            child: AspectRatio(
                              aspectRatio: 1,
                              child: Image.asset(
                                'assets/pieces/${p.id}/$code.png',
                                fit: BoxFit.contain,
                                errorBuilder: (_, _, _) => const Center(
                                    child: Text('·',
                                        textAlign: TextAlign.center)),
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                SizedBox(
                  height: 16,
                  child: sel
                      ? const Align(
                          alignment: Alignment.centerRight,
                          child: Icon(Icons.check_circle,
                              size: 14, color: D4Theme.gold),
                        )
                      : null,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SoundPackChip extends StatelessWidget {
  const _SoundPackChip({
    required this.pack,
    required this.selected,
    required this.onTap,
  });

  final SoundPackInfo pack;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: selected
                ? D4Theme.gold.withValues(alpha: 0.14)
                : D4Theme.surfaceSoft,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: selected ? D4Theme.goldBright : D4Theme.line,
              width: selected ? 2 : 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(pack.icon,
                  color: selected ? D4Theme.goldBright : D4Theme.muted,
                  size: 22),
              const SizedBox(height: 8),
              Text(
                pack.label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontWeight: FontWeight.w700,
                  color: selected ? D4Theme.goldBright : D4Theme.text,
                ),
              ),
              const SizedBox(height: 4),
              Expanded(
                child: Text(
                  pack.desc,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      fontSize: 11, color: D4Theme.muted, height: 1.25),
                ),
              ),
              SizedBox(
                height: 18,
                child: selected
                    ? const Align(
                        alignment: Alignment.centerLeft,
                        child: Icon(Icons.check_circle,
                            size: 16, color: D4Theme.gold),
                      )
                    : null,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
