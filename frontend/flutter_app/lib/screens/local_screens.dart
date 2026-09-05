import 'dart:convert';
import 'dart:io' show Process;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'package:chess_pro_d4/api/api_client.dart';
import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/ui/scrollable_sub_tabs.dart';
import 'package:chess_pro_d4/widgets/chess_board.dart';

/// Port API Chess Pro D4 (3847 souvent pris → 3848).
const int kApiPort = 3848;

/// Construit toujours une URL join avec le port (jamais port 80 implicite).
String buildJoinUrl({
  required String code,
  String? localIp,
  int? port,
  String? apiBase,
}) {
  var ip = localIp ?? '127.0.0.1';
  var p = port ?? kApiPort;
  if (apiBase != null) {
    final u = Uri.tryParse(apiBase);
    if (u != null && u.host.isNotEmpty) {
      ip = u.host;
      if (u.hasPort) p = u.port;
    }
  }
  final c = code.trim().toUpperCase();
  return 'http://$ip:$p/join/$c';
}

String buildLocalJoinUrl(String code, {int port = kApiPort}) =>
    'http://127.0.0.1:$port/join/${code.trim().toUpperCase()}';

String buildHomeUrl({int port = kApiPort}) => 'http://127.0.0.1:$port/';

class LocalHubScreen extends StatefulWidget {
  const LocalHubScreen({super.key, this.initialIndex = 0});
  final int initialIndex;
  @override
  State<LocalHubScreen> createState() => _LocalHubScreenState();
}

class _LocalHubScreenState extends State<LocalHubScreen> {
  late int _section;

  @override
  void initState() {
    super.initState();
    _section = widget.initialIndex.clamp(0, 2);
  }

  @override
  Widget build(BuildContext context) {
    // Un seul niveau de sous-onglets (pas de double menu Local).
    return SectionScaffold(
      sectionTitle: 'Local',
      index: _section,
      onIndexChanged: (i) => setState(() => _section = i),
      labels: const ['Créer', 'Rejoindre', 'Aide'],
      icons: const [Icons.add_circle_outline, Icons.login, Icons.help_outline],
      pages: [
        _CreateTab(),
        const _JoinTab(),
        const _HelpTab(),
      ],
    );
  }
}

class _CreateTab extends StatefulWidget {
  @override
  State<_CreateTab> createState() => _CreateTabState();
}

class _CreateTabState extends State<_CreateTab> {
  final _api = ApiClient();
  bool _busy = false;
  String? _error;

  Future<void> _create() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final name = context.read<AppState>().playerName;
      final fallbackIp = context.read<AppState>().localIp;
      final r = await _api.createRoom(hostName: name);
      final code = r['code']?.toString() ?? '';
      final ip = r['local_ip']?.toString() ?? fallbackIp;
      final port = r['port'] is int ? r['port'] as int : kApiPort;
      final public = r['join_url_public']?.toString() ??
          (r['worldwide'] == true ? r['join_url']?.toString() : null);
      final joinLan = r['join_url_lan']?.toString() ??
          buildJoinUrl(code: code, localIp: ip, port: port);
      final joinLocal = r['join_url_local']?.toString() ??
          buildLocalJoinUrl(code, port: port);
      // QR = lien mondial si dispo (LA / autres pays), sinon LAN
      final primary = (public != null && public.startsWith('http'))
          ? public
          : (r['qr_payload']?.toString() ?? r['join_url']?.toString() ?? joinLan);
      r['join_url'] = primary;
      r['web_url'] = primary;
      r['qr_payload'] = primary;
      r['join_url_local'] = joinLocal;
      r['join_url_lan'] = joinLan;
      r['join_url_public'] = public;
      r['home_url'] = r['home_url'] ?? buildHomeUrl(port: port);
      r['port'] = port;
      r['local_ip'] = ip;
      r['worldwide'] = r['worldwide'] == true || (public?.startsWith('https://') ?? false);
      if (!mounted) return;
      context.go('/local/host', extra: r);
    } catch (e) {
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('PARTIE LOCALE',
                  style: TextStyle(fontSize: 24, color: D4Theme.goldBright, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text(
                'Créez une partie : le QR utilise un lien HTTPS mondial\n'
                '(Los Angeles, Europe, etc.). Le PC hôte doit rester allumé.',
                textAlign: TextAlign.center,
                style: TextStyle(color: D4Theme.muted),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _busy ? null : _create,
                child: Text(_busy ? 'Création…' : 'Créer une partie'),
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: D4Theme.offline)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _JoinTab extends StatefulWidget {
  const _JoinTab();
  @override
  State<_JoinTab> createState() => _JoinTabState();
}

class _JoinTabState extends State<_JoinTab> {
  final _ctrl = TextEditingController();
  final _apiCtrl = TextEditingController(text: ApiClient.defaultBase);
  final _linkCtrl = TextEditingController();

  @override
  void dispose() {
    _ctrl.dispose();
    _apiCtrl.dispose();
    _linkCtrl.dispose();
    super.dispose();
  }

  void _join() {
    var code = _ctrl.text.trim().toUpperCase();
    final link = _linkCtrl.text.trim();
    if (link.isNotEmpty) {
      var fixed = link;
      // Si lien sans port → injecter 3848
      final uri = Uri.tryParse(fixed);
      if (uri != null && uri.host.isNotEmpty && !uri.hasPort) {
        fixed = 'http://${uri.host}:3848${uri.path}${uri.hasQuery ? '?${uri.query}' : ''}';
      }
      final u = Uri.tryParse(fixed);
      if (u != null) {
        if (u.host.isNotEmpty) {
          final port = u.hasPort ? u.port : 3848;
          ApiClient.defaultBase = 'http://${u.host}:$port';
        }
        final segs = u.pathSegments;
        if (segs.isNotEmpty && segs.last.length >= 4) code = segs.last.toUpperCase();
        final q = u.queryParameters['code'];
        if (q != null && q.isNotEmpty) code = q.toUpperCase();
      }
    }
    final api = _apiCtrl.text.trim().replaceAll(RegExp(r'/$'), '');
    if (api.isNotEmpty) ApiClient.defaultBase = api;
    if (code.length < 4) return;
    context.go('/local/join?code=$code');
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const Text('Rejoindre', style: TextStyle(fontSize: 22, color: D4Theme.goldBright)),
        const SizedBox(height: 12),
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 440),
          child: Column(
            children: [
              TextField(
                controller: _apiCtrl,
                decoration: const InputDecoration(
                  labelText: 'API hôte',
                  hintText: 'http://192.168.1.10:3848',
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _linkCtrl,
                decoration: const InputDecoration(
                  labelText: 'Coller le lien',
                  hintText: 'http://IP:3848/join/CODE',
                ),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _ctrl,
                textCapitalization: TextCapitalization.characters,
                decoration: const InputDecoration(labelText: 'Code de partie'),
              ),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: _join, child: const Text('Rejoindre la partie')),
            ],
          ),
        ),
        const SizedBox(height: 28),
        const Text('Salles disponibles', style: TextStyle(color: D4Theme.gold, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        const SizedBox(height: 280, child: _RoomsTab()),
      ],
    );
  }
}

class _RoomsTab extends StatefulWidget {
  const _RoomsTab();
  @override
  State<_RoomsTab> createState() => _RoomsTabState();
}

class _RoomsTabState extends State<_RoomsTab> {
  final _api = ApiClient();
  List<dynamic> _rooms = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final r = await _api.listRooms();
      setState(() {
        _rooms = (r['rooms'] as List?) ?? [];
        _error = null;
      });
    } catch (e) {
      setState(() => _error = '$e');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: D4Theme.offline)));
    }
    if (_rooms.isEmpty) {
      return const Center(child: Text('Aucune partie en attente', style: TextStyle(color: D4Theme.muted)));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        itemCount: _rooms.length,
        itemBuilder: (_, i) {
          final r = _rooms[i] as Map<String, dynamic>;
          return ListTile(
            title: Text('Code ${r['code']}', style: const TextStyle(color: D4Theme.text)),
            subtitle: Text('Hôte : ${r['host']} · joueurs ${r['players']}',
                style: const TextStyle(color: D4Theme.muted)),
            trailing: const Icon(Icons.login, color: D4Theme.gold),
            onTap: () => context.go('/local/join?code=${r['code']}'),
          );
        },
      ),
    );
  }
}

class _HelpTab extends StatelessWidget {
  const _HelpTab();
  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(24),
      child: Text(
        '1. FLUTTER.bat (backend + tunnel HTTPS).\n'
        '2. Local → Créer → QR = lien https://….trycloudflare.com/join/CODE\n'
        '3. Marche depuis Los Angeles / n’importe où (hôte en ligne).\n'
        '4. Même Wi‑Fi : lien LAN en secours.\n'
        '5. PC : http://127.0.0.1:3848/',
        style: TextStyle(color: D4Theme.muted, height: 1.5),
      ),
    );
  }
}

class LocalHostScreen extends StatefulWidget {
  const LocalHostScreen({super.key, required this.roomData});
  final Map<String, dynamic> roomData;

  @override
  State<LocalHostScreen> createState() => _LocalHostScreenState();
}

class _LocalHostScreenState extends State<LocalHostScreen> {
  late final String _code;
  late final String _hostId;
  late String _qr;
  late String _link;
  late String _localLink;
  late String _lanLink;
  late String _homeUrl;
  late bool _worldwide;
  late String _hostColor;
  WebSocketChannel? _ch;
  Map<String, dynamic>? _room;
  String? _myColor;
  String? _selected;
  bool _connected = false;

  @override
  void initState() {
    super.initState();
    _code = widget.roomData['code'] as String? ?? '';
    _hostId = widget.roomData['host_id'] as String? ?? '';
    final ip = widget.roomData['local_ip']?.toString() ??
        Uri.tryParse(widget.roomData['api_base']?.toString() ?? '')?.host ??
        '127.0.0.1';
    final port = widget.roomData['port'] is int
        ? widget.roomData['port'] as int
        : int.tryParse('${widget.roomData['port'] ?? ''}') ?? kApiPort;
    _homeUrl = widget.roomData['home_url']?.toString() ?? buildHomeUrl(port: port);
    _localLink = widget.roomData['join_url_local']?.toString() ??
        buildLocalJoinUrl(_code, port: port);
    _lanLink = widget.roomData['join_url_lan']?.toString() ??
        buildJoinUrl(code: _code, localIp: ip, port: port);
    final public = widget.roomData['join_url_public']?.toString();
    final qr = widget.roomData['qr_payload']?.toString() ??
        widget.roomData['join_url']?.toString();
    _worldwide = widget.roomData['worldwide'] == true ||
        (qr != null && qr.startsWith('https://')) ||
        (public != null && public.startsWith('https://'));
    _link = (public != null && public.startsWith('http'))
        ? public
        : (qr ?? _lanLink);
    _qr = _link;
    _hostColor = widget.roomData['host_color']?.toString() ?? 'white';
    _myColor = _hostColor;
    _room = widget.roomData['room'] as Map<String, dynamic>?;
    WidgetsBinding.instance.addPostFrameCallback((_) => _connect());
  }

  void _connect() {
    if (_code.isEmpty || _hostId.isEmpty) return;
    final api = ApiClient();
    final name = context.read<AppState>().playerName;
    _ch = api.connectRoom(code: _code, playerId: _hostId, name: name, role: 'host');
    _ch!.stream.listen((raw) {
      final msg = jsonDecode(raw as String) as Map<String, dynamic>;
      final type = msg['type'];
      if (!mounted) return;
      if (type == 'welcome') {
        setState(() {
          _connected = true;
          _myColor = msg['color'] as String?;
          _room = msg['room'] as Map<String, dynamic>?;
        });
      } else if (type == 'state' || type == 'move' || type == 'player_left' || type == 'resign') {
        setState(() => _room = msg['room'] as Map<String, dynamic>?);
      }
    }, onError: (_) {
      if (mounted) setState(() => _connected = false);
    });
  }

  Future<void> _openLocalLink() async {
    await Clipboard.setData(ClipboardData(text: _localLink));
    try {
      await Process.run('cmd', ['/c', 'start', '', _localLink]);
    } catch (_) {}
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Navigateur : $_localLink')),
    );
  }

  @override
  void dispose() {
    _ch?.sink.close();
    super.dispose();
  }

  Future<void> _copy() async {
    await Clipboard.setData(ClipboardData(text: _link));
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Lien QR copié : $_link')));
    }
  }

  void _sendMove(String uci) {
    _ch?.sink.add(jsonEncode({'type': 'move', 'uci': uci}));
  }

  void _onTap(String sq) {
    final room = _room;
    if (room == null || room['status'] != 'playing') return;
    if (_myColor != room['turn']) return;
    final legal = (room['legal'] as List?)?.cast<String>() ?? [];
    if (_selected == null) {
      if (legal.any((u) => u.startsWith(sq))) setState(() => _selected = sq);
      return;
    }
    final cands = legal.where((u) => u.startsWith('${_selected!}$sq')).toList();
    if (cands.isEmpty) {
      setState(() => _selected = legal.any((u) => u.startsWith(sq)) ? sq : null);
      return;
    }
    setState(() => _selected = null);
    _sendMove(cands.first);
  }

  @override
  Widget build(BuildContext context) {
    if (_code.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Aucune partie créée', style: TextStyle(color: D4Theme.offline)),
            ElevatedButton(onPressed: () => context.go('/local'), child: const Text('Retour')),
          ],
        ),
      );
    }
    final room = _room;
    final waiting = room == null || room['status'] == 'waiting';
    final fen = room?['fen'] as String? ?? 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
    final legal = (room?['legal'] as List?)?.cast<String>() ?? [];
    final players = room?['players'] ?? 1;

    if (waiting) {
      final linkOk = _link.startsWith('https://') ||
          _link.contains(':$kApiPort/') ||
          RegExp(r':\d+/join/').hasMatch(_link);
      return Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              Text(
                _worldwide
                    ? 'QR mondial — marche depuis Los Angeles & partout'
                    : 'En attente… (lien local — tunnel mondial indisponible)',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _worldwide ? D4Theme.online : D4Theme.goldBright,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Text('Code : $_code',
                  style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, letterSpacing: 4)),
              const SizedBox(height: 6),
              Text(
                'Vous jouez les ${_hostColor == 'black' ? 'Noirs' : 'Blancs'} (tirage aléatoire)',
                style: const TextStyle(color: D4Theme.goldBright, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              Text('Joueurs : $players/2 · WS ${_connected ? 'OK' : '…'}',
                  style: const TextStyle(color: D4Theme.muted)),
              if (!linkOk)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: Text('ERREUR : lien invalide — recréez la partie',
                      style: TextStyle(color: D4Theme.offline, fontWeight: FontWeight.bold)),
                ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: QrImageView(data: _qr, size: 220, backgroundColor: Colors.white),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                _worldwide ? 'Lien QR (monde entier · HTTPS)' : 'Lien QR',
                style: const TextStyle(color: D4Theme.muted, fontSize: 12),
              ),
              SelectableText(_link,
                  style: const TextStyle(color: D4Theme.goldBright, fontSize: 13, fontWeight: FontWeight.w700)),
              const SizedBox(height: 10),
              const Text('Sur ce PC', style: TextStyle(color: D4Theme.muted, fontSize: 12)),
              SelectableText(_localLink, style: const TextStyle(color: D4Theme.muted, fontSize: 12)),
              SelectableText(_homeUrl, style: const TextStyle(color: D4Theme.muted, fontSize: 11)),
              if (_lanLink != _link) ...[
                const SizedBox(height: 6),
                const Text('Même Wi‑Fi seulement', style: TextStyle(color: D4Theme.muted, fontSize: 12)),
                SelectableText(_lanLink, style: const TextStyle(color: D4Theme.muted, fontSize: 11)),
              ],
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  ElevatedButton(onPressed: _copy, child: const Text('Copier le lien QR')),
                  OutlinedButton(onPressed: _openLocalLink, child: const Text('Ouvrir local')),
                  OutlinedButton(onPressed: () => context.go('/local'), child: const Text('Retour')),
                ],
              ),
            ],
          ),
        ),
      );
    }

    final white = room['white_name'] ?? 'Blancs';
    final black = room['black_name'] ?? 'Noirs';
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: Text('$black  vs  $white  ·  vous=${_myColor ?? '?'}  ·  tour=${room['turn']}',
              style: const TextStyle(color: D4Theme.muted)),
        ),
        Expanded(
          child: ChessBoardView(
            fen: fen,
            legalUci: (_myColor == room['turn']) ? legal : const [],
            selected: _selected,
            orientWhite: _myColor != 'black',
            onSquareTap: _onTap,
          ),
        ),
      ],
    );
  }
}

class LocalJoinScreen extends StatefulWidget {
  const LocalJoinScreen({super.key, required this.code});
  final String code;

  @override
  State<LocalJoinScreen> createState() => _LocalJoinScreenState();
}

class _LocalJoinScreenState extends State<LocalJoinScreen> {
  final _api = ApiClient();
  WebSocketChannel? _ch;
  Map<String, dynamic>? _room;
  String? _myColor;
  String? _selected;
  String? _error;

  @override
  void initState() {
    super.initState();
    _boot();
  }

  Future<void> _boot() async {
    try {
      if (widget.code.isEmpty) {
        setState(() => _error = 'Code manquant');
        return;
      }
      await _api.getRoom(widget.code);
      if (!mounted) return;
      final id = DateTime.now().millisecondsSinceEpoch.toString();
      final name = context.read<AppState>().playerName;
      _ch = _api.connectRoom(code: widget.code, playerId: id, name: name, role: 'guest');
      _ch!.stream.listen((raw) {
        final msg = jsonDecode(raw as String) as Map<String, dynamic>;
        final type = msg['type'];
        if (!mounted) return;
        if (type == 'error') {
          setState(() => _error = msg['message']?.toString());
          return;
        }
        if (type == 'welcome') {
          setState(() {
            _myColor = msg['color'] as String?;
            _room = msg['room'] as Map<String, dynamic>?;
          });
        } else if (type == 'state' || type == 'move' || type == 'resign') {
          setState(() => _room = msg['room'] as Map<String, dynamic>?);
        }
      });
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    }
  }

  @override
  void dispose() {
    _ch?.sink.close();
    super.dispose();
  }

  void _onTap(String sq) {
    final room = _room;
    if (room == null || room['status'] != 'playing') return;
    if (_myColor != room['turn']) return;
    final legal = (room['legal'] as List?)?.cast<String>() ?? [];
    if (_selected == null) {
      if (legal.any((u) => u.startsWith(sq))) setState(() => _selected = sq);
      return;
    }
    final cands = legal.where((u) => u.startsWith('${_selected!}$sq')).toList();
    if (cands.isEmpty) {
      setState(() => _selected = legal.any((u) => u.startsWith(sq)) ? sq : null);
      return;
    }
    setState(() => _selected = null);
    _ch?.sink.add(jsonEncode({'type': 'move', 'uci': cands.first}));
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: D4Theme.offline)));
    }
    final room = _room;
    if (room == null) {
      return const Center(child: CircularProgressIndicator(color: D4Theme.gold));
    }
    if (room['status'] == 'waiting') {
      return Center(
        child: Text('Connecté — en attente… (${room['players']}/2)',
            style: const TextStyle(color: D4Theme.muted)),
      );
    }
    final fen = room['fen'] as String;
    final legal = (room['legal'] as List?)?.cast<String>() ?? [];
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: Text('Code ${widget.code} · vous=${_myColor ?? '?'} · tour=${room['turn']}',
              style: const TextStyle(color: D4Theme.muted)),
        ),
        Expanded(
          child: ChessBoardView(
            fen: fen,
            legalUci: (_myColor == room['turn']) ? legal : const [],
            selected: _selected,
            orientWhite: _myColor != 'black',
            onSquareTap: _onTap,
          ),
        ),
      ],
    );
  }
}
