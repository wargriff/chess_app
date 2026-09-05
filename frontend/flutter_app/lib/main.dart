import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'package:chess_pro_d4/api/api_client.dart';
import 'package:chess_pro_d4/screens/appearance_hub.dart';
import 'package:chess_pro_d4/screens/engine_hub.dart';
import 'package:chess_pro_d4/screens/home_hub.dart';
import 'package:chess_pro_d4/screens/local_screens.dart';
import 'package:chess_pro_d4/screens/play_hub.dart';
import 'package:chess_pro_d4/screens/play_screens.dart';
import 'package:chess_pro_d4/screens/section_hubs.dart';
import 'package:chess_pro_d4/screens/settings_screen.dart';
import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/services/sound_service.dart';
import 'package:chess_pro_d4/theme/catalog.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/ui/shell.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SoundService.instance.warmUp();
  runApp(const ChessProApp());
}

class ChessProApp extends StatefulWidget {
  const ChessProApp({super.key});

  @override
  State<ChessProApp> createState() => _ChessProAppState();
}

class _ChessProAppState extends State<ChessProApp> {
  late final AppState _appState;
  late final GoRouter _router;

  @override
  void initState() {
    super.initState();
    _appState = AppState();
    _router = _buildRouter();
    _pollHealth();
  }

  Future<void> _pollHealth() async {
    final api = ApiClient();
    Future<void> once() async {
      try {
        final h = await api.health();
        _appState.applyHealth(h);
      } catch (e) {
        _appState.setOffline('Backend hors ligne — $e');
      }
    }

    await once();
    while (mounted) {
      await Future<void>.delayed(const Duration(seconds: 5));
      if (!mounted) break;
      await once();
    }
  }

  GoRouter _buildRouter() {
    return GoRouter(
      initialLocation: '/',
      routes: [
        ShellRoute(
          builder: (context, state, child) {
            return AppShell(location: state.uri.toString(), child: child);
          },
          routes: [
            GoRoute(
              path: '/',
              pageBuilder: (c, s) => const NoTransitionPage(child: HomeHubScreen()),
            ),
            GoRoute(
              path: '/play',
              pageBuilder: (c, s) => const NoTransitionPage(child: PlaySectionScreen()),
              routes: [
                GoRoute(
                  path: 'stockfish',
                  pageBuilder: (c, s) => const NoTransitionPage(child: StockfishGameScreen()),
                ),
                GoRoute(
                  path: 'local-hotseat',
                  pageBuilder: (c, s) => const NoTransitionPage(child: HotseatGameScreen()),
                ),
              ],
            ),
            GoRoute(
              path: '/local',
              pageBuilder: (c, s) => const NoTransitionPage(child: LocalHubScreen()),
              routes: [
                GoRoute(
                  path: 'host',
                  pageBuilder: (c, s) {
                    final extra = s.extra;
                    final data = extra is Map<String, dynamic> ? extra : <String, dynamic>{};
                    return NoTransitionPage(child: LocalHostScreen(roomData: data));
                  },
                ),
                GoRoute(
                  path: 'join',
                  pageBuilder: (c, s) {
                    final code = s.uri.queryParameters['code'] ?? '';
                    return NoTransitionPage(child: LocalJoinScreen(code: code.toUpperCase()));
                  },
                ),
              ],
            ),
            GoRoute(
              path: '/analyse',
              pageBuilder: (c, s) => const NoTransitionPage(child: AnalyseHubScreen()),
            ),
            GoRoute(
              path: '/library',
              pageBuilder: (c, s) => const NoTransitionPage(child: LibraryHubScreen()),
            ),
            GoRoute(
              path: '/appearance',
              pageBuilder: (c, s) => const NoTransitionPage(child: AppearanceHubScreen()),
            ),
            GoRoute(
              path: '/engine',
              pageBuilder: (c, s) => const NoTransitionPage(child: EngineHubScreen()),
            ),
            GoRoute(path: '/history', redirect: (c, s) => '/library'),
            GoRoute(path: '/saves', redirect: (c, s) => '/library'),
            GoRoute(path: '/stats', redirect: (c, s) => '/'),
            GoRoute(
              path: '/settings',
              pageBuilder: (c, s) => const NoTransitionPage(child: SettingsScreen()),
            ),
          ],
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider.value(
      value: _appState,
      child: AnimatedBuilder(
        animation: _appState,
        builder: (context, _) {
          final theme = D4Theme.fromAppTheme(appThemeById(_appState.appThemeId));
          return MaterialApp.router(
            title: 'Chess Pro D4',
            debugShowCheckedModeBanner: false,
            theme: theme,
            routerConfig: _router,
          );
        },
      ),
    );
  }
}
