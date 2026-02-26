import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final Future<PackageInfo> _packageInfoFuture;
  final TextEditingController _durationController = TextEditingController();
  final TextEditingController _intervalController = TextEditingController();
  final FocusNode _durationFocusNode = FocusNode();
  final FocusNode _intervalFocusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _packageInfoFuture = PackageInfo.fromPlatform();
    final appState = context.read<AppState>();
    _durationController.text = appState.recordingDurationSec.toString();
    _intervalController.text = appState.recordingIntervalSec.toString();
  }

  @override
  void dispose() {
    _durationController.dispose();
    _intervalController.dispose();
    _durationFocusNode.dispose();
    _intervalFocusNode.dispose();
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
  }

  Future<void> _setAutoTrackWithRecording(bool value) async {
    await context.read<AppState>().setAutoTrackInputWithRecording(value);
  }

  Future<void> _setRecordSystemAudio(bool value) async {
    await context.read<AppState>().setRecordSystemAudio(value);
  }

  Future<void> _setRecordMicrophoneAudio(bool value) async {
    await context.read<AppState>().setRecordMicrophoneAudio(value);
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final durationText = appState.recordingDurationSec.toString();
    final intervalText = appState.recordingIntervalSec.toString();
    if (!_durationFocusNode.hasFocus && _durationController.text != durationText) {
      _durationController.text = durationText;
    }
    if (!_intervalFocusNode.hasFocus && _intervalController.text != intervalText) {
      _intervalController.text = intervalText;
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: FutureBuilder<PackageInfo>(
        future: _packageInfoFuture,
        builder: (context, pkgSnap) {
          final appVersion = pkgSnap.data?.version ?? '...';
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _recordingDefaultsCard(appState),
              const SizedBox(height: 12),
              _kv(context, 'Version', appVersion),
            ],
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

  Widget _recordingDefaultsCard(AppState appState) {
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
            title: const Text('System audio'),
            value: appState.recordSystemAudio,
            onChanged: _setRecordSystemAudio,
          ),
          SwitchListTile.adaptive(
            dense: true,
            contentPadding: EdgeInsets.zero,
            title: const Text('Microphone'),
            value: appState.recordMicrophoneAudio,
            onChanged: _setRecordMicrophoneAudio,
          ),
          SwitchListTile.adaptive(
            dense: true,
            contentPadding: EdgeInsets.zero,
            title: const Text('Key-Mouse tracking'),
            value: appState.autoTrackInputWithRecording,
            onChanged: _setAutoTrackWithRecording,
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _durationController,
                  focusNode: _durationFocusNode,
                  decoration: const InputDecoration(labelText: 'Duration (s)'),
                  keyboardType: TextInputType.number,
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _saveRecordingDefaults(),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextField(
                  controller: _intervalController,
                  focusNode: _intervalFocusNode,
                  decoration: const InputDecoration(labelText: 'Interval (s)'),
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _saveRecordingDefaults(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
