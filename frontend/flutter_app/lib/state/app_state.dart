import 'package:flutter/material.dart';

import 'package:chess_pro_d4/services/sound_service.dart';

enum BackendLink { offline, wrongService, starting, online }

/// Préférences + état connexion — identité D4.
class AppState extends ChangeNotifier {
  BackendLink link = BackendLink.offline;
  bool stockfishOnline = false;
  String stockfishLabel = 'Stockfish…';
  String localIp = '127.0.0.1';
  String statusDetail = 'Connexion…';
  int elo = 1200;
  String playerName = 'Joueur';

  // Apparence (catalogue Pygame)
  String appThemeId = 'd4_gold';
  String pieceSetId = 'cburnett';
  String boardThemeId = 'sanctum';
  double pieceScale = 1.08;
  bool showCoordinates = true;
  bool showLastMove = true;
  bool showHints = true;
  bool animations = true;
  bool sounds = true;
  String soundPackId = 'classic';
  int timeMinutes = 10;
  int timeIncrement = 0;
  String colorPref = 'random';

  bool get backendOnline => link == BackendLink.online || link == BackendLink.starting;

  String get connectionLabel {
    switch (link) {
      case BackendLink.offline:
        return 'Backend hors ligne — lancez FLUTTER.bat ou BACKEND.bat (port 3848)';
      case BackendLink.wrongService:
        return 'Port occupé par un autre service — Chess Pro utilise 3848';
      case BackendLink.starting:
        return 'Backend en démarrage… Stockfish charge';
      case BackendLink.online:
        return stockfishOnline ? stockfishLabel : 'Backend OK · Stockfish hors ligne';
    }
  }

  Color get connectionColor {
    switch (link) {
      case BackendLink.online:
        return stockfishOnline ? const Color(0xFF50BE6E) : const Color(0xFFE6BE6E);
      case BackendLink.starting:
        return const Color(0xFFE6BE6E);
      case BackendLink.wrongService:
        return const Color(0xFFC85046);
      case BackendLink.offline:
        return const Color(0xFFC85046);
    }
  }

  void applyHealth(Map<String, dynamic> h) {
    final app = h['app']?.toString() ?? '';
    final ok = h['ok'] == true;
    // Autre service sur le port (ex. ancien 8765) : pas "Chess Pro D4"
    if (!ok && app.isEmpty && h.containsKey('version') && !h.containsKey('stockfish')) {
      link = BackendLink.wrongService;
      stockfishOnline = false;
      stockfishLabel = 'Mauvais service';
      statusDetail = 'Réponse inconnue sur ${ApiBase.hint}';
      notifyListeners();
      return;
    }
    if (app.isNotEmpty && app != 'Chess Pro D4') {
      link = BackendLink.wrongService;
      stockfishOnline = false;
      notifyListeners();
      return;
    }
    stockfishOnline = h['stockfish'] == true;
    stockfishLabel = h['stockfish_label']?.toString() ?? 'Stockfish';
    localIp = h['local_ip']?.toString() ?? localIp;
    final st = h['status']?.toString() ?? '';
    if (ok && stockfishOnline) {
      link = BackendLink.online;
    } else if (ok || st == 'starting') {
      link = BackendLink.starting;
    } else {
      link = BackendLink.offline;
    }
    statusDetail = connectionLabel;
    notifyListeners();
  }

  void setOffline([String? detail]) {
    link = BackendLink.offline;
    stockfishOnline = false;
    statusDetail = detail ?? connectionLabel;
    notifyListeners();
  }

  void setElo(int v) {
    elo = v;
    notifyListeners();
  }

  void setPlayerName(String n) {
    playerName = n.trim().isEmpty ? 'Joueur' : n.trim();
    notifyListeners();
  }

  void setPieceSet(String id) {
    pieceSetId = id;
    notifyListeners();
  }

  void setBoardTheme(String id) {
    boardThemeId = id;
    notifyListeners();
  }

  void setAppTheme(String id) {
    appThemeId = id;
    notifyListeners();
  }

  void setPieceScale(double v) {
    pieceScale = v.clamp(0.7, 1.3);
    notifyListeners();
  }

  void setShowCoordinates(bool v) {
    showCoordinates = v;
    notifyListeners();
  }

  void setShowLastMove(bool v) {
    showLastMove = v;
    notifyListeners();
  }

  void setShowHints(bool v) {
    showHints = v;
    notifyListeners();
  }

  void setAnimations(bool v) {
    animations = v;
    notifyListeners();
  }

  void setSounds(bool v) {
    sounds = v;
    SoundService.instance.enabled = v;
    notifyListeners();
  }

  void setSoundPack(String id) {
    soundPackId = id;
    SoundService.instance.setPack(id);
    notifyListeners();
  }

  void setTimeControl(int minutes, int increment) {
    timeMinutes = minutes;
    timeIncrement = increment;
    notifyListeners();
  }

  void setColorPref(String v) {
    colorPref = v;
    notifyListeners();
  }

  void setApiBase(String url) {
    notifyListeners();
  }
}

class ApiBase {
  static String get hint => 'http://127.0.0.1:3848';
}
