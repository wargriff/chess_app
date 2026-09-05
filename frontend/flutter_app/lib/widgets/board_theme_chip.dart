import 'package:flutter/material.dart';

import 'package:chess_pro_d4/theme/catalog.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';

/// Aperçu échiquier — taille fixe (remplit la cellule de grille).
class BoardThemeChip extends StatelessWidget {
  const BoardThemeChip({
    super.key,
    required this.info,
    required this.selected,
    required this.onTap,
  });

  final BoardThemeInfo info;
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
          padding: const EdgeInsets.fromLTRB(8, 8, 8, 8),
          decoration: BoxDecoration(
            color: const Color(0xFF1A1814),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: selected ? D4Theme.goldBright : D4Theme.line,
              width: selected ? 2.2 : 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: CustomPaint(
                    painter: _BoardPreviewPainter(
                        light: info.light, dark: info.dark),
                    child: const SizedBox.expand(),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                info.label,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
                  color:
                      selected ? D4Theme.goldBright : const Color(0xFFF0E6D4),
                ),
              ),
              SizedBox(
                height: 16,
                child: selected
                    ? const Center(
                        child: Icon(Icons.check_circle,
                            size: 14, color: D4Theme.gold),
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

class _BoardPreviewPainter extends CustomPainter {
  _BoardPreviewPainter({required this.light, required this.dark});
  final Color light;
  final Color dark;

  @override
  void paint(Canvas canvas, Size size) {
    const n = 4;
    final w = size.width / n;
    final h = size.height / n;
    final lightPaint = Paint()..color = light;
    final darkPaint = Paint()..color = dark;
    for (var r = 0; r < n; r++) {
      for (var c = 0; c < n; c++) {
        final paint = (r + c).isEven ? lightPaint : darkPaint;
        canvas.drawRect(
            Rect.fromLTWH(c * w, r * h, w + 0.5, h + 0.5), paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _BoardPreviewPainter old) =>
      old.light != light || old.dark != dark;
}
