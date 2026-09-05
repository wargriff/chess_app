import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

/// Client HTTP/WS — Chess Pro D4 (port dédié 3848).
class ApiClient {
  ApiClient({String? baseUrl}) : _override = baseUrl;

  static String defaultBase = const String.fromEnvironment(
    'CHESS_API',
    defaultValue: 'http://127.0.0.1:3848',
  );

  final String? _override;
  String get baseUrl => _override ?? defaultBase;

  Uri _u(String path, [Map<String, String>? q]) =>
      Uri.parse('$baseUrl$path').replace(queryParameters: q);

  String _err(http.Response r) {
    try {
      final j = jsonDecode(r.body);
      if (j is Map && j['detail'] != null) return j['detail'].toString();
    } catch (_) {}
    return 'HTTP ${r.statusCode}: ${r.body}';
  }

  Future<Map<String, dynamic>> health() async {
    // /health d'abord (spécifié) puis /api/health
    try {
      final r = await http.get(_u('/health')).timeout(const Duration(seconds: 2));
      if (r.statusCode == 200) return jsonDecode(r.body) as Map<String, dynamic>;
    } catch (_) {}
    final r = await http.get(_u('/api/health')).timeout(const Duration(seconds: 2));
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> engineStatus() async {
    final r = await http.get(_u('/api/engine/status'));
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> newGame({
    String mode = 'pve',
    int elo = 1200,
    String color = 'white',
    int timeMinutes = 10,
    String whiteName = 'Joueur',
    String blackName = 'Stockfish',
  }) async {
    final r = await http.post(
      _u('/api/game/new'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'mode': mode,
        'elo': elo,
        'color': color,
        'time_minutes': timeMinutes,
        'white_name': whiteName,
        'black_name': blackName,
      }),
    );
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> playMove(String gameId, String uci) async {
    final r = await http.post(
      _u('/api/game/$gameId/move'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'uci': uci}),
    );
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> undoPair(String gameId) async {
    final r = await http.post(_u('/api/game/$gameId/undo_pair'));
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> undoOne(String gameId) async {
    final r = await http.post(_u('/api/game/$gameId/undo'));
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> enginePlay({
    required List<String> moves,
    int elo = 1200,
    int? movetimeMs,
  }) async {
    final r = await http.post(
      _u('/api/engine/play'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'fen': '',
        'moves': moves,
        'elo': elo,
        if (movetimeMs != null) 'movetime_ms': movetimeMs,
      }),
    );
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> analyze({
    required List<String> moves,
    int depth = 15,
    int multipv = 3,
    int? movetimeMs,
  }) async {
    final r = await http.post(
      _u('/api/engine/analyze'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'fen': '',
        'moves': moves,
        'depth': depth,
        'multipv': multipv,
        if (movetimeMs != null) 'movetime_ms': movetimeMs,
      }),
    );
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<String> fenFromMoves(List<String> moves) async {
    final r = await http.post(
      _u('/api/board/fen'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'fen': '', 'moves': moves}),
    );
    if (r.statusCode >= 400) throw Exception(_err(r));
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    return j['fen']?.toString() ??
        'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  }

  Future<Map<String, dynamic>> engineLevels() async {
    final r = await http.get(_u('/api/engine/levels'));
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> configureEngine({required int elo}) async {
    final r = await http.post(
      _u('/api/engine/configure'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'elo': elo}),
    );
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> listSaves() async {
    final r = await http.get(_u('/api/saves'));
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> saveGame(Map<String, dynamic> body) async {
    final r = await http.post(
      _u('/api/saves'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> loadSave(String name) async {
    final r = await http.get(_u('/api/saves/$name'));
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<String> exportPgn(String name) async {
    final r = await http.get(_u('/api/saves/$name/pgn'));
    if (r.statusCode >= 400) throw Exception(_err(r));
    final j = jsonDecode(r.body) as Map<String, dynamic>;
    return j['pgn']?.toString() ?? '';
  }

  Future<void> deleteSave(String name) async {
    final r = await http.delete(_u('/api/saves/$name'));
    if (r.statusCode >= 400) throw Exception(_err(r));
  }

  Future<Map<String, dynamic>> createRoom({
    String hostName = 'Joueur 1',
    int timeMinutes = 10,
  }) async {
    final r = await http.post(
      _u('/api/rooms'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'host_name': hostName, 'time_minutes': timeMinutes}),
    );
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getRoom(String code) async {
    final r = await http.get(_u('/api/rooms/${code.toUpperCase()}'));
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> listRooms() async {
    final r = await http.get(_u('/api/rooms'));
    if (r.statusCode >= 400) throw Exception(_err(r));
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  WebSocketChannel connectRoom({
    required String code,
    required String playerId,
    required String name,
    required String role,
  }) {
    final wsBase =
        baseUrl.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://');
    final uri = Uri.parse(
      '$wsBase/ws/room/${code.toUpperCase()}?player_id=$playerId&name=${Uri.encodeComponent(name)}&role=$role',
    );
    return WebSocketChannel.connect(uri);
  }
}
