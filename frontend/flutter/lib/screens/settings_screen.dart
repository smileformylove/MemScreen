import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:provider/provider.dart';

import '../app_state.dart';
import '../api/api_client.dart';
import '../api/model_api.dart';
import '../connection/connection_state.dart';

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
  LocalModelCatalog? _modelCatalog;
  bool _loadingModelCatalog = false;
  bool _loadingPermissions = false;
  bool _requestedModelHydration = false;
  String? _downloadingModelName;

  @override
  void initState() {
    super.initState();
    _packageInfoFuture = PackageInfo.fromPlatform();
    final appState = context.read<AppState>();
    _durationController.text = appState.recordingDurationSec.toString();
    _intervalController.text = appState.recordingIntervalSec.toString();
    if (appState.isBackendConnected) {
      _requestedModelHydration = true;
      _loadModelCatalog();
    }
    _loadPermissionStatus();
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

  Future<void> _setVideoFormat(String value) async {
    await context.read<AppState>().setRecordingVideoFormat(value);
  }

  Future<void> _setAudioFormat(String value) async {
    await context.read<AppState>().setRecordingAudioFormat(value);
  }

  Future<void> _setAudioDenoise(bool value) async {
    await context.read<AppState>().setRecordingAudioDenoise(value);
  }

  Future<void> _loadPermissionStatus({
    bool showError = false,
    bool promptSystem = false,
  }) async {
    if (!mounted) return;
    setState(() => _loadingPermissions = true);
    try {
      await context.read<AppState>().refreshPermissionStatus(
            promptSystem: promptSystem,
          );
    } catch (e) {
      if (showError && mounted) {
        final msg = e is ApiException ? e.message : e.toString();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load permissions: $msg')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _loadingPermissions = false);
      }
    }
  }

  void _maybeHydrateAfterBackendConnect(AppState appState) {
    if (!appState.isBackendConnected) {
      _requestedModelHydration = false;
      return;
    }
    if (_requestedModelHydration ||
        _loadingModelCatalog ||
        _modelCatalog != null) {
      return;
    }
    _requestedModelHydration = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      _loadModelCatalog();
    });
  }

  Future<void> _loadModelCatalog({bool showError = false}) async {
    if (!mounted) return;
    setState(() => _loadingModelCatalog = true);
    try {
      final appState = context.read<AppState>();
      if (!appState.isBackendConnected) {
        return;
      }
      final catalog = await appState.modelApi.getCatalog();
      if (!mounted) return;
      setState(() => _modelCatalog = catalog);
    } catch (e) {
      if (showError && mounted) {
        final msg = e is ApiException ? e.message : e.toString();
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Failed to load models: $msg')));
      }
    } finally {
      if (mounted) {
        setState(() => _loadingModelCatalog = false);
      }
    }
  }

  Future<void> _downloadModel(LocalModelEntry entry) async {
    if (_downloadingModelName != null) return;
    setState(() => _downloadingModelName = entry.name);
    try {
      await context.read<AppState>().modelApi.downloadModel(entry.name);
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Downloaded ${entry.name}')));
      }
      await _loadModelCatalog();
    } catch (e) {
      if (mounted) {
        final msg = e is ApiException ? e.message : e.toString();
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Download failed: $msg')));
      }
    } finally {
      if (mounted) {
        setState(() => _downloadingModelName = null);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    _maybeHydrateAfterBackendConnect(appState);
    final durationText = appState.recordingDurationSec.toString();
    final intervalText = appState.recordingIntervalSec.toString();
    if (!_durationFocusNode.hasFocus &&
        _durationController.text != durationText) {
      _durationController.text = durationText;
    }
    if (!_intervalFocusNode.hasFocus &&
        _intervalController.text != intervalText) {
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
              _permissionsCard(),
              const SizedBox(height: 12),
              _modelsCard(),
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
          SwitchListTile.adaptive(
            dense: true,
            contentPadding: EdgeInsets.zero,
            title: const Text('Basic noise reduction'),
            value: appState.recordingAudioDenoise,
            onChanged: _setAudioDenoise,
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: appState.recordingVideoFormat,
                  decoration: const InputDecoration(labelText: 'Video format'),
                  items: AppState.supportedVideoFormats
                      .map(
                        (f) => DropdownMenuItem<String>(
                          value: f,
                          child: Text(f.toUpperCase()),
                        ),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value == null) return;
                    _setVideoFormat(value);
                  },
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: appState.recordingAudioFormat,
                  decoration: const InputDecoration(labelText: 'Audio format'),
                  items: AppState.supportedAudioFormats
                      .map(
                        (f) => DropdownMenuItem<String>(
                          value: f,
                          child: Text(f.toUpperCase()),
                        ),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value == null) return;
                    _setAudioFormat(value);
                  },
                ),
              ),
            ],
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

  Widget _permissionsCard() {
    final theme = Theme.of(context);
    final permissionStatus = context.watch<AppState>().permissionStatus;
    final runtimePath = (permissionStatus?['runtime_executable'] ??
            '~/.memscreen/runtime/.venv/bin/python')
        .toString();

    Widget rowFor(String title, String key) {
      final section = permissionStatus?[key];
      final granted = section is Map && section['granted'] == true;
      final message =
          section is Map ? (section['message'] ?? '').toString() : '';
      return Padding(
        padding: const EdgeInsets.only(top: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              granted ? Icons.check_circle : Icons.error_outline,
              size: 16,
              color: granted ? Colors.green : theme.colorScheme.error,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title),
                  if (message.isNotEmpty)
                    Text(
                      message,
                      style: TextStyle(
                        color: theme.colorScheme.onSurfaceVariant,
                        fontSize: 11,
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(child: Text('macOS permissions')),
              IconButton(
                tooltip: 'Refresh',
                onPressed: _loadingPermissions
                    ? null
                    : () => _loadPermissionStatus(showError: true),
                icon: const Icon(Icons.refresh, size: 18),
              ),
              TextButton(
                onPressed: _loadingPermissions
                    ? null
                    : () => _loadPermissionStatus(
                          showError: true,
                          promptSystem: true,
                        ),
                child: const Text('Check / Prompt'),
              ),
            ],
          ),
          Text(
            'Required runtime path: $runtimePath',
            style: TextStyle(
              color: theme.colorScheme.onSurfaceVariant,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 8),
          rowFor('Screen Recording', 'screen_recording'),
          rowFor('Accessibility', 'accessibility'),
          rowFor('Input Monitoring', 'input_monitoring'),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton(
                onPressed: () => context
                    .read<AppState>()
                    .openPermissionSettings('screen_recording'),
                child: const Text('Open Screen Recording'),
              ),
              OutlinedButton(
                onPressed: () => context
                    .read<AppState>()
                    .openPermissionSettings('accessibility'),
                child: const Text('Open Accessibility'),
              ),
              OutlinedButton(
                onPressed: () => context
                    .read<AppState>()
                    .openPermissionSettings('input_monitoring'),
                child: const Text('Open Input Monitoring'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Allow both MemScreen.app and the runtime path above where relevant, then quit and reopen MemScreen.',
            style: TextStyle(
              color: theme.colorScheme.onSurfaceVariant,
              fontSize: 12,
            ),
          ),
          if (_loadingPermissions) ...[
            const SizedBox(height: 8),
            const LinearProgressIndicator(minHeight: 2),
          ],
        ],
      ),
    );
  }

  Widget _modelsCard() {
    final appState = context.watch<AppState>();
    final catalog = _modelCatalog;
    final theme = Theme.of(context);

    if (!appState.isBackendConnected) {
      final isStarting =
          appState.connectionState.status == ConnectionStatus.connecting;
      return Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: theme.colorScheme.surfaceContainerLow,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Local models'),
            const SizedBox(height: 8),
            Text(
              'Model catalog requires the local backend. Core local features continue to work without it.',
              style: TextStyle(
                color: theme.colorScheme.onSurfaceVariant,
                fontSize: 12,
              ),
            ),
            if (appState.connectionState.status == ConnectionStatus.error &&
                (appState.connectionState.message?.isNotEmpty ?? false)) ...[
              const SizedBox(height: 8),
              Text(
                appState.connectionState.message!,
                style: TextStyle(
                  color: theme.colorScheme.error,
                  fontSize: 12,
                ),
              ),
            ],
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: isStarting
                  ? null
                  : () async {
                      await appState.ensureBackendConnection(force: true);
                      if (appState.isBackendConnected) {
                        await _loadModelCatalog(showError: true);
                      }
                    },
              icon: isStarting
                  ? SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: theme.colorScheme.onPrimary,
                      ),
                    )
                  : const Icon(Icons.play_arrow),
              label: Text(isStarting ? 'Starting Backend...' : 'Start Backend'),
            ),
          ],
        ),
      );
    }
    final runtimeReady = catalog?.runtimeReady ?? false;
    final runtimeText = runtimeReady ? 'Runtime ready' : 'Runtime unavailable';
    final statusColor = runtimeReady ? Colors.green : theme.colorScheme.error;
    final modelsDir = catalog?.modelsDir;
    final modelsDirExternal = catalog?.modelsDirExternal ?? false;
    final models = catalog?.models ?? const <LocalModelEntry>[];
    final disableDownloads = _loadingModelCatalog;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        children: [
          Row(
            children: [
              const Expanded(child: Text('Local models')),
              IconButton(
                tooltip: 'Refresh',
                onPressed: _loadingModelCatalog
                    ? null
                    : () => _loadModelCatalog(showError: true),
                icon: const Icon(Icons.refresh, size: 18),
              ),
            ],
          ),
          Row(
            children: [
              Icon(Icons.circle, size: 8, color: statusColor),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  runtimeText,
                  style: TextStyle(
                    color: theme.colorScheme.onSurfaceVariant,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          if (_loadingModelCatalog) ...[
            const SizedBox(height: 8),
            const LinearProgressIndicator(minHeight: 2),
          ],
          if ((modelsDir ?? '').isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              modelsDirExternal
                  ? 'Model storage (external): $modelsDir'
                  : 'Model storage: $modelsDir',
              style: TextStyle(
                color: theme.colorScheme.onSurfaceVariant,
                fontSize: 12,
              ),
            ),
          ],
          if (catalog?.modelsDisabled == true) ...[
            const SizedBox(height: 8),
            Text(
              'Model features are disabled in current runtime config.',
              style: TextStyle(
                color: theme.colorScheme.onSurfaceVariant,
                fontSize: 12,
              ),
            ),
          ],
          if (!runtimeReady && (catalog?.runtimeError ?? '').isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              catalog!.runtimeError!,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                color: theme.colorScheme.onSurfaceVariant,
                fontSize: 11,
              ),
            ),
          ],
          if (models.isNotEmpty) ...[
            const SizedBox(height: 8),
            for (var i = 0; i < models.length; i++) ...[
              _modelRow(models[i], disableDownloads: disableDownloads),
              if (i != models.length - 1) const Divider(height: 14),
            ],
          ],
        ],
      ),
    );
  }

  Widget _modelRow(
    LocalModelEntry entry, {
    required bool disableDownloads,
  }) {
    final theme = Theme.of(context);
    final downloading = _downloadingModelName == entry.name;

    Widget trailing;
    if (entry.installed) {
      trailing = Row(
        mainAxisSize: MainAxisSize.min,
        children: const [
          Icon(Icons.check_circle, size: 16, color: Colors.green),
          SizedBox(width: 4),
          Text('Installed'),
        ],
      );
    } else if (downloading) {
      trailing = const SizedBox(
        width: 16,
        height: 16,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    } else {
      trailing = TextButton(
        onPressed: disableDownloads ? null : () => _downloadModel(entry),
        child: const Text('Download'),
      );
    }

    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                entry.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              Text(
                entry.required ? entry.purpose : '${entry.purpose} · Optional',
                style: TextStyle(
                  color: theme.colorScheme.onSurfaceVariant,
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        trailing,
      ],
    );
  }
}
