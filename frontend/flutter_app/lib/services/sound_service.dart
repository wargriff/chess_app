import 'dart:io';

import 'package:ffi/ffi.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:win32/win32.dart';

/// Sons Windows via PlaySound (async) — packs stylés sélectionnables.
class SoundService {
  SoundService._();
  static final SoundService instance = SoundService._();

  bool enabled = true;
  String packId = 'classic';
  final Map<String, String> _cache = {};
  bool _warming = false;

  Future<void> warmUp() async {
    if (_warming) return;
    _warming = true;
    try {
      for (final name in ['move', 'capture', 'check', 'checkmate', 'castle', 'promote', 'click']) {
        await _ensureFile(_assetFor(name));
      }
    } catch (e) {
      debugPrint('SoundService warmUp: $e');
    }
  }

  void setPack(String id) {
    packId = id;
    _warming = false;
    warmUp();
  }

  String _assetFor(String name) {
    // Packs générés : assets/sounds/packs/<id>/<name>.wav
    return 'sounds/packs/$packId/$name.wav';
  }

  Future<String?> _ensureFile(String asset) async {
    final hit = _cache[asset];
    if (hit != null && File(hit).existsSync()) return hit;
    try {
      final data = await rootBundle.load('assets/$asset');
      final bytes = data.buffer.asUint8List();
      final dir = Directory('${Directory.systemTemp.path}${Platform.pathSeparator}chess_pro_d4_snd');
      if (!dir.existsSync()) dir.createSync(recursive: true);
      final fileName = asset.replaceAll('/', '_');
      final file = File('${dir.path}${Platform.pathSeparator}$fileName');
      await file.writeAsBytes(bytes, flush: true);
      _cache[asset] = file.path;
      return file.path;
    } catch (e) {
      // Fallback legacy dossiers
      final fallbacks = <String, List<String>>{
        'move': ['sounds/move/move.wav'],
        'capture': ['sounds/capture/capture.wav'],
        'check': ['sounds/check/check.wav'],
        'checkmate': ['sounds/checkmate/checkmate.wav'],
        'castle': ['sounds/move/castle.wav'],
        'promote': ['sounds/ui/promote.wav'],
        'click': ['sounds/ui/click.wav'],
      };
      final key = asset.split('/').last.replaceAll('.wav', '');
      for (final alt in fallbacks[key] ?? const <String>[]) {
        try {
          final data = await rootBundle.load('assets/$alt');
          final bytes = data.buffer.asUint8List();
          final dir = Directory('${Directory.systemTemp.path}${Platform.pathSeparator}chess_pro_d4_snd');
          if (!dir.existsSync()) dir.createSync(recursive: true);
          final file = File('${dir.path}${Platform.pathSeparator}${alt.replaceAll('/', '_')}');
          await file.writeAsBytes(bytes, flush: true);
          _cache[asset] = file.path;
          return file.path;
        } catch (_) {}
      }
      debugPrint('SoundService cache $asset: $e');
      return null;
    }
  }

  void _play(String name) {
    if (!enabled) return;
    () async {
      try {
        final path = await _ensureFile(_assetFor(name));
        if (path == null) return;
        final ptr = path.toNativeUtf16();
        try {
          PlaySound(PCWSTR(ptr), null, SND_FILENAME | SND_ASYNC | SND_NODEFAULT);
        } finally {
          free(ptr);
        }
      } catch (e) {
        debugPrint('SoundService play: $e');
      }
    }();
  }

  void move() => _play('move');
  void capture() => _play('capture');
  void castle() => _play('castle');
  void check() => _play('check');
  void checkmate() => _play('checkmate');
  void promote() => _play('promote');
  void click() => _play('click');

  void playForMove({
    required String uci,
    required Map<String, dynamic> after,
    required Map<String, String> piecesBefore,
  }) {
    if (!enabled) return;
    if (after['checkmate'] == true) {
      checkmate();
      return;
    }
    if (after['check'] == true) {
      check();
      return;
    }
    if (uci.length >= 5) {
      promote();
      return;
    }
    final from = uci.substring(0, 2);
    final to = uci.substring(2, 4);
    final piece = piecesBefore[from] ?? '';
    final isKing = piece.toUpperCase() == 'K';
    const castleUci = {'e1g1', 'e1c1', 'e8g8', 'e8c8'};
    if (isKing && castleUci.contains(uci.substring(0, 4))) {
      castle();
      return;
    }
    if (piecesBefore.containsKey(to)) {
      capture();
      return;
    }
    if (piece.toUpperCase() == 'P' && from[0] != to[0] && !piecesBefore.containsKey(to)) {
      capture();
      return;
    }
    move();
  }
}

Map<String, String> piecesFromFen(String fen) {
  final map = <String, String>{};
  final placement = fen.split(' ').first;
  var rank = 7;
  var file = 0;
  for (final ch in placement.split('')) {
    if (ch == '/') {
      rank -= 1;
      file = 0;
    } else if (int.tryParse(ch) != null) {
      file += int.parse(ch);
    } else {
      map['${String.fromCharCode(97 + file)}${rank + 1}'] = ch;
      file += 1;
    }
  }
  return map;
}
