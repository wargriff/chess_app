import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'package:chess_pro_d4/theme/d4_theme.dart';

Future<void> showGameOverDialog(
  BuildContext context, {
  required String title,
  required String subtitle,
  required VoidCallback onReplay,
  String homeRoute = '/',
}) {
  return showDialog<void>(
    context: context,
    barrierDismissible: false,
    builder: (ctx) {
      return AlertDialog(
        backgroundColor: D4Theme.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: D4Theme.line),
        ),
        title: Text(
          title,
          style: const TextStyle(color: D4Theme.goldBright, fontWeight: FontWeight.w700),
        ),
        content: Text(subtitle, style: const TextStyle(color: D4Theme.muted, height: 1.4)),
        actionsAlignment: MainAxisAlignment.spaceBetween,
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              context.go(homeRoute);
            },
            child: const Text('Menu principal'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              onReplay();
            },
            child: const Text('Rejouer'),
          ),
        ],
      );
    },
  );
}

String gameOverTitle(Map<String, dynamic> g, {bool? humanIsWhite}) {
  if (g['checkmate'] == true) {
    final result = g['result']?.toString() ?? '';
    if (humanIsWhite == null) {
      return result == '1-0' ? 'Échec et mat — Blancs' : 'Échec et mat — Noirs';
    }
    final humanWon = (humanIsWhite && result == '1-0') || (!humanIsWhite && result == '0-1');
    return humanWon ? 'Victoire !' : 'Échec et mat';
  }
  if (g['stalemate'] == true) return 'Pat';
  final r = g['result']?.toString() ?? '*';
  if (r == '1/2-1/2') return 'Partie nulle';
  return 'Partie terminée';
}

String gameOverSubtitle(Map<String, dynamic> g) {
  final r = g['result']?.toString() ?? '*';
  if (g['checkmate'] == true) return 'Résultat : $r';
  if (g['stalemate'] == true) return 'Aucun coup légal — nulle.';
  return 'Résultat : $r';
}
