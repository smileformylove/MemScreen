import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:provider/provider.dart';

import '../api/config_api.dart';
import '../app_state.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final Future<ConfigInfo> _configFuture;
  late final Future<PackageInfo> _packageInfoFuture;
  final TextEditingController _durationController = TextEditingController();
  final TextEditingController _intervalController = TextEditingController();
  bool _autoTrackWithRecording = true;

  @override
  void initState() {
    super.initState();
    _configFuture = context.read<AppState>().configApi.get();
    _packageInfoFuture = PackageInfo.fromPlatform();
    final appState = context.read<AppState>();
    _durationController.text = appState.recordingDurationSec.toString();
    _intervalController.text = appState.recordingIntervalSec.toString();
    _autoTrackWithRecording = appState.autoTrackInputWithRecording;
  }

  @override
  void dispose() {
    _durationController.dispose();
    _intervalController.dispose();
    super.dispose();
  }

  Future<void> _saveRecordingDefaults() async {
    final duration = int.tryParse(_durationController.text.trim());
    final interval = double.tryParse(_intervalController.text.trim());
    if (duration == null ||
        interval == null ||
        duration <= 0 ||
        interval <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Invalid Duration/Interval')),
      );
      return;
    }
    await context.read<AppState>().setRecordingDefaults(
          durationSec: duration,
          intervalSec: interval,
        );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Recording defaults updated')),
    );
  }

  Future<void> _setAutoTrackWithRecording(bool value) async {
    setState(() => _autoTrackWithRecording = value);
    await context.read<AppState>().setAutoTrackInputWithRecording(value);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          value
              ? 'Auto input tracking with recording enabled'
              : 'Auto input tracking with recording disabled',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: FutureBuilder<ConfigInfo>(
        future: _configFuture,
        builder: (context, configSnap) {
          return FutureBuilder<PackageInfo>(
            future: _packageInfoFuture,
            builder: (context, pkgSnap) {
              final config = configSnap.data;
              final pkg = pkgSnap.data;
              final appVersion = pkg?.version ?? '...';

              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _recordingDefaultsCard(),
                  const SizedBox(height: 8),
                  if (config != null) ...[
                    _kv(context, 'DB', config.dbDir),
                    const SizedBox(height: 8),
                    _kv(context, 'Videos', config.videosDir),
                  ],
                  const SizedBox(height: 16),
                  const Divider(height: 1),
                  const SizedBox(height: 16),
                  _kv(context, 'App', 'MemScreen'),
                  const SizedBox(height: 8),
                  _kv(context, 'Version', appVersion),
                ],
              );
            },
          );
        },
      ),
    );
  }

  Widget _kv(BuildContext context, String key, String value) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 72,
            child: Text(
              key,
              style: TextStyle(
                color: theme.colorScheme.onSurfaceVariant,
                fontSize: 12,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              value,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Widget _recordingDefaultsCard() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        children: [
          SwitchListTile.adaptive(
            dense: true,
            contentPadding: EdgeInsets.zero,
            title: const Text('Auto start input tracking when recording'),
            value: _autoTrackWithRecording,
            onChanged: _setAutoTrackWithRecording,
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _durationController,
                  decoration: const InputDecoration(labelText: 'Duration (s)'),
                  keyboardType: TextInputType.number,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _intervalController,
                  decoration: const InputDecoration(labelText: 'Interval (s)'),
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton.tonal(
              onPressed: _saveRecordingDefaults,
              child: const Text('Save'),
            ),
          ),
        ],
      ),
    );
  }
}
