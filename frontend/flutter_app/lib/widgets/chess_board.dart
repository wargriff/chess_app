import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/theme/catalog.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';

const _unicode = {
  'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
  'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
};

/// Plateau D4 — orientation correcte, coordonnées fiables, animation optionnelle.
class ChessBoardView extends StatefulWidget {
  const ChessBoardView({
    super.key,
    required this.fen,
    required this.legalUci,
    this.selected,
    this.lastFrom,
    this.lastTo,
    this.orientWhite = true,
    this.onSquareTap,
    this.interactive = true,
    this.showCoords,
  });

  final String fen;
  final List<String> legalUci;
  final String? selected;
  final String? lastFrom;
  final String? lastTo;
  final bool orientWhite;
  final ValueChanged<String>? onSquareTap;
  final bool interactive;
  final bool? showCoords;

  static String sq(int file, int rank) => '${String.fromCharCode(97 + file)}${rank + 1}';

  @override
  State<ChessBoardView> createState() => _ChessBoardViewState();
}

class _ChessBoardViewState extends State<ChessBoardView> with SingleTickerProviderStateMixin {
  late final AnimationController _anim;
  Animation<Offset> _slide = const AlwaysStoppedAnimation(Offset.zero);
  String? _flyingPiece;
  String? _hideFrom;
  String? _hideTo;
  Map<String, String> _pieces = {};

  @override
  void initState() {
    super.initState();
    _pieces = _parseFen(widget.fen);
    _anim = AnimationController(vsync: this, duration: const Duration(milliseconds: 180));
    _anim.addStatusListener((s) {
      if (s == AnimationStatus.completed && mounted) {
        setState(() {
          _flyingPiece = null;
          _hideFrom = null;
          _hideTo = null;
          _pieces = _parseFen(widget.fen);
        });
      }
    });
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant ChessBoardView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.orientWhite != widget.orientWhite && _anim.isAnimating) {
      _anim.stop();
      _flyingPiece = null;
      _hideFrom = null;
      _hideTo = null;
    }
    if (oldWidget.fen == widget.fen) return;

    final animate = context.read<AppState>().animations &&
        widget.lastFrom != null &&
        widget.lastTo != null &&
        widget.lastFrom != widget.lastTo;

    if (!animate) {
      _anim.stop();
      setState(() {
        _flyingPiece = null;
        _hideFrom = null;
        _hideTo = null;
        _pieces = _parseFen(widget.fen);
      });
      return;
    }

    final before = _parseFen(oldWidget.fen);
    final piece = before[widget.lastFrom!] ?? _parseFen(widget.fen)[widget.lastTo!];
    if (piece == null) {
      setState(() => _pieces = _parseFen(widget.fen));
      return;
    }

    _slide = Tween<Offset>(
      begin: _squareOffset(widget.lastFrom!),
      end: _squareOffset(widget.lastTo!),
    ).animate(CurvedAnimation(parent: _anim, curve: Curves.easeOutCubic));

    setState(() {
      _flyingPiece = piece;
      _hideFrom = widget.lastFrom;
      _hideTo = widget.lastTo;
      _pieces = before;
    });
    _anim.forward(from: 0);
  }

  Map<String, String> _parseFen(String fen) {
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
        map[ChessBoardView.sq(file, rank)] = ch;
        file += 1;
      }
    }
    return map;
  }

  Offset _squareOffset(String name) {
    final file = name.codeUnitAt(0) - 97;
    final rank = int.parse(name[1]) - 1;
    final col = widget.orientWhite ? file : 7 - file;
    final row = widget.orientWhite ? 7 - rank : rank;
    return Offset(col / 8, row / 8);
  }

  Set<String> _targetsFrom(String from) {
    final out = <String>{};
    for (final u in widget.legalUci) {
      if (u.length >= 4 && u.substring(0, 2) == from) out.add(u.substring(2, 4));
    }
    return out;
  }

  String _assetFor(String piece, String setId) {
    final color = piece == piece.toUpperCase() ? 'w' : 'b';
    return 'assets/pieces/$setId/$color${piece.toUpperCase()}.png';
  }

  Widget _pieceImage(String piece, double sqSize, AppState state) {
    return Padding(
      padding: EdgeInsets.all(sqSize * 0.04),
      child: Image.asset(
        _assetFor(piece, state.pieceSetId),
        fit: BoxFit.contain,
        filterQuality: FilterQuality.high,
        gaplessPlayback: true,
        errorBuilder: (_, _, _) => Center(
          child: Text(
            _unicode[piece] ?? piece,
            style: TextStyle(
              fontSize: sqSize * 0.72,
              height: 1,
              color: piece == piece.toUpperCase() ? const Color(0xFFFAF6EE) : const Color(0xFF111111),
              shadows: const [Shadow(blurRadius: 2, color: Colors.black54)],
            ),
          ),
        ),
      ),
    );
  }

  Widget _square({
    required int row,
    required int col,
    required double sqSize,
    required Map<String, String> activePieces,
    required Set<String> targets,
    required bool coords,
    required bool hints,
    required bool last,
    required double scale,
    required BoardThemeInfo board,
    required AppState state,
  }) {
    final file = widget.orientWhite ? col : 7 - col;
    final rank = widget.orientWhite ? 7 - row : row;
    final name = ChessBoardView.sq(file, rank);
    final light = (file + rank).isEven;
    final piece = activePieces[name];
    final hide = name == _hideFrom || name == _hideTo;
    final isSelected = widget.selected == name;
    final isLast = last && (name == widget.lastFrom || name == widget.lastTo);
    final isTarget = hints && targets.contains(name);
    final isCapture = isTarget && piece != null && !hide;

    Color bg = light ? board.light : board.dark;
    if (isLast) bg = Color.lerp(bg, D4Theme.gold, 0.28)!;
    if (isSelected) bg = Color.lerp(bg, D4Theme.goldBright, 0.38)!;

    return Positioned(
      left: col * sqSize,
      top: row * sqSize,
      width: sqSize,
      height: sqSize,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: widget.interactive && widget.onSquareTap != null ? () => widget.onSquareTap!(name) : null,
        child: ColoredBox(
          color: bg,
          child: Stack(
            fit: StackFit.expand,
            children: [
              if (isTarget && !isCapture)
                Center(
                  child: Container(
                    width: sqSize * 0.22,
                    height: sqSize * 0.22,
                    decoration: BoxDecoration(
                      color: D4Theme.gold.withValues(alpha: 0.55),
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              if (isCapture)
                Container(
                  margin: EdgeInsets.all(sqSize * 0.06),
                  decoration: BoxDecoration(
                    border: Border.all(color: D4Theme.gold.withValues(alpha: 0.8), width: 2.5),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              if (piece != null && !hide)
                Transform.scale(scale: scale, child: _pieceImage(piece, sqSize, state)),
              if (coords && col == 0)
                Positioned(
                  left: 3,
                  top: 2,
                  child: Text(
                    '${rank + 1}',
                    style: TextStyle(
                      fontSize: (sqSize * 0.18).clamp(9.0, 14.0),
                      fontWeight: FontWeight.w700,
                      color: (light ? board.dark : board.light).withValues(alpha: 0.9),
                    ),
                  ),
                ),
              if (coords && row == 7)
                Positioned(
                  right: 3,
                  bottom: 2,
                  child: Text(
                    String.fromCharCode(97 + file),
                    style: TextStyle(
                      fontSize: (sqSize * 0.18).clamp(9.0, 14.0),
                      fontWeight: FontWeight.w700,
                      color: (light ? board.dark : board.light).withValues(alpha: 0.9),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final board = boardById(state.boardThemeId);
    final activePieces = _anim.isAnimating ? _pieces : _parseFen(widget.fen);
    final targets = widget.selected == null ? <String>{} : _targetsFrom(widget.selected!);
    final coords = widget.showCoords ?? state.showCoordinates;
    final hints = state.showHints;
    final last = state.showLastMove;
    final scale = state.pieceScale.clamp(0.75, 1.25);

    return LayoutBuilder(
      builder: (context, c) {
        final side = (c.maxWidth < c.maxHeight ? c.maxWidth : c.maxHeight).clamp(120.0, 2000.0);
        final sqSize = side / 8;
        return Center(
          child: SizedBox(
            width: side,
            height: side,
            child: Stack(
              children: [
                for (var row = 0; row < 8; row++)
                  for (var col = 0; col < 8; col++)
                    _square(
                      row: row,
                      col: col,
                      sqSize: sqSize,
                      activePieces: activePieces,
                      targets: targets,
                      coords: coords,
                      hints: hints,
                      last: last,
                      scale: scale,
                      board: board,
                      state: state,
                    ),
                if (_flyingPiece != null)
                  AnimatedBuilder(
                    animation: _slide,
                    builder: (context, child) => Positioned(
                      left: _slide.value.dx * side,
                      top: _slide.value.dy * side,
                      width: sqSize,
                      height: sqSize,
                      child: child!,
                    ),
                    child: Transform.scale(
                      scale: scale,
                      child: _pieceImage(_flyingPiece!, sqSize, state),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}
