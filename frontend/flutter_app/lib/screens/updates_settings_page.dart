import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:chess_pro_d4/api/api_client.dart';
import 'package:chess_pro_d4/state/app_state.dart';
import 'package:chess_pro_d4/theme/d4_theme.dart';
import 'package:chess_pro_d4/version.dart';

/// Sous-onglet Mises à jour — pas de faux update auto.
/// Affiche la version réelle + état backend. Mise à jour = METTRE_A_JOUR.bat / git.
class UpdatesSettingsPage extends StatefulWidget {
  const UpdatesSettingsPage({super.key, this.embedded = false});

  /// Quand true : Column (pas ListView) pour être placé dans une autre liste.
  final bool embedded;

  @override
  State<UpdatesSettingsPage> createState() => _UpdatesSettingsPageState();
}

class _UpdatesSettingsPageState extends State<UpdatesSettingsPage> {
  bool _checking = false;
  DateTime? _lastCheck;
  String? _message;
  bool _backendOk = false;
  String? _backendApp;

  Future<void> _check() async {
    setState(() {
      _checking = true;
      _message = null;
    });
    try {
      final h = await ApiClient().health();
      if (!mounted) return;
      context.read<AppState>().applyHealth(h);
      setState(() {
        _backendOk = h['ok'] == true;
        _backendApp = h['app']?.toString();
        _lastCheck = DateTime.now();
        _message =
            'Aucun canal de mise à jour automatique n’est configuré.\n'
            'Version client : ${AppVersion.full}\n'
            'Backend : ${_backendOk ? (_backendApp ?? "OK") : "hors ligne"}\n\n'
            'Pour mettre à jour le projet : lancez METTRE_A_JOUR.bat '
            '(ou git pull) puis relancez FLUTTER.bat.';
      });
    } catch (e) {
      setState(() {
        _backendOk = false;
        _lastCheck = DateTime.now();
        _message =
            'Vérification locale uniquement.\n'
            'Version client : ${AppVersion.full}\n'
            'Backend injoignable : $e\n\n'
            '✓ Pas de déploiement auto. Utilisez METTRE_A_JOUR.bat pour synchroniser le code.';
      });
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final last = _lastCheck == null
        ? 'Jamais'
        : '${_lastCheck!.hour.toString().padLeft(2, '0')}:${_lastCheck!.minute.toString().padLeft(2, '0')}';

    final body = <Widget>[
      if (!widget.embedded) ...[
        const Text('Mises à jour', style: TextStyle(fontSize: 18, color: D4Theme.goldBright, fontWeight: FontWeight.w600)),
        const SizedBox(height: 16),
      ],
      Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _kv('Version actuelle', AppVersion.full),
              _kv('Version disponible', '— (pas de serveur de release)'),
              _kv('Dernière vérification', last),
              _kv('Backend', _backendOk ? 'Connecté' : 'Non vérifié / hors ligne'),
            ],
          ),
        ),
      ),
      const SizedBox(height: 16),
      ElevatedButton.icon(
        onPressed: _checking ? null : _check,
        icon: _checking
            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
            : const Icon(Icons.refresh),
        label: Text(_checking ? 'Vérification…' : 'Vérifier les mises à jour'),
      ),
      const SizedBox(height: 16),
      Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: D4Theme.surfaceSoft,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: D4Theme.line),
        ),
        child: Text(
          _message ??
              '✓ Votre application est à la version ${AppVersion.full}.\n'
                  'Aucune mise à jour automatique n’est branchée : l’interface ne simule pas de patch.',
          style: const TextStyle(color: D4Theme.muted, height: 1.45),
        ),
      ),
    ];

    if (widget.embedded) {
      return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: body);
    }
    return ListView(children: body);
  }

  Widget _kv(String k, String v) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Row(
          children: [
            SizedBox(width: 160, child: Text(k, style: const TextStyle(color: D4Theme.muted))),
            Expanded(child: Text(v, style: const TextStyle(fontWeight: FontWeight.w600))),
          ],
        ),
      );
}
