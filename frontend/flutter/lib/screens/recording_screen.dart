import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/recording_api.dart';
import '../app_state.dart';
import '../services/recording_diagnostics.dart';
import '../widgets/recording_diagnostics_panel.dart';

class RecordingScreen extends StatefulWidget {
  const RecordingScreen({super.key});

  @override
  State<RecordingScreen> createState() => _RecordingScreenState();
}

enum _RecordingNoticeLevel { info, warning, error }

class _RecordingScreenState extends State<RecordingScreen> {
  RecordingStatus? _status;
  List<RecordingScreenInfo> _screens = const [];
  bool _loading = true;

  int? _screenIndex;
  int? _screenDisplayId;

  bool _wasRecording = false;
  String? _recordingNotice;
  _RecordingNoticeLevel _recordingNoticeLevel = _RecordingNoticeLevel.info;

  Timer? _pollTimer;
  AppState? _appState;
  int _lastRecordingStatusVersion = -1;
  int _lastCurrentTabIndex = -1;

  @override
  void initState() {
    super.initState();
    _load();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _appState = context.read<AppState>();
      _lastRecordingStatusVersion = _appState!.recordingStatusVersion;
      _lastCurrentTabIndex = _appState!.currentTabIndex;
      _appState!.addListener(_onAppStateChanged);
    });
  }

  @override
  void dispose() {
    _appState?.removeListener(_onAppStateChanged);
    _pollTimer?.cancel();
    super.dispose();
  }

  void _onAppStateChanged() {
    if (!mounted || _appState == null) return;
    final currentTabIndex = _appState!.currentTabIndex;
    if (currentTabIndex != _lastCurrentTabIndex) {
      _lastCurrentTabIndex = currentTabIndex;
      if (currentTabIndex == 0) {
        _load();
      } else {
        _stopPolling();
      }
    }

    final currentVersion = _appState!.recordingStatusVersion;
    if (currentVersion != _lastRecordingStatusVersion) {
      _lastRecordingStatusVersion = currentVersion;
      _load();
    }
  }

  Future<void> _load() async {
    try {
      final appState = context.read<AppState>();
      final status = await appState.loadRecordingStatusForUi();
      await appState.syncRecordingStateFromBackend(status.isRecording);
      final screens = await appState.loadAvailableScreensForUi();
      await appState.refreshPermissionStatus();

      if (!mounted) {
        return;
      }

      setState(() {
        _status = status;
        _screens = screens;
        _loading = false;

        final selected = _resolveSelectedScreen(screens);
        _screenIndex = selected?.index;
        _screenDisplayId = selected?.displayId;
      });

      _wasRecording = status.isRecording;
      if (status.isRecording) {
        _startPolling();
      } else {
        _stopPolling();
      }

      _consumePendingRecordingNotice(showSnackBar: true);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
      });
    }
  }

  RecordingScreenInfo? _resolveSelectedScreen(
      List<RecordingScreenInfo> screens) {
    if (screens.isEmpty) return null;
    if (_screenIndex == null) return null;

    for (final screen in screens) {
      if (screen.index == _screenIndex) {
        return screen;
      }
    }

    final primary = screens.where((screen) => screen.isPrimary);
    if (primary.isNotEmpty) {
      return primary.first;
    }
    return screens.first;
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (_) {
      final appState = _appState;
      if (appState == null || !mounted || appState.currentTabIndex != 0) {
        return;
      }
      _load();
    });
  }

  void _stopPolling() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  _RecordingNoticeLevel _classifyNoticeLevel(String notice) {
    final lower = notice.toLowerCase();
    if (lower.contains('permission') ||
        lower.contains('failed') ||
        lower.contains('did not') ||
        lower.contains('cancelled') ||
        lower.contains('without creating')) {
      return _RecordingNoticeLevel.error;
    }
    if (lower.contains('without audio') ||
        lower.contains('microphone only') ||
        lower.contains('import warning')) {
      return _RecordingNoticeLevel.warning;
    }
    return _RecordingNoticeLevel.info;
  }

  void _showRecordingNotice(String notice, {bool showSnackBar = true}) {
    final trimmed = notice.trim();
    if (trimmed.isEmpty || !mounted) {
      return;
    }
    final level = _classifyNoticeLevel(trimmed);
    setState(() {
      _recordingNotice = trimmed;
      _recordingNoticeLevel = level;
    });

    if (!showSnackBar) {
      return;
    }

    final colorScheme = Theme.of(context).colorScheme;
    final snackColor = switch (level) {
      _RecordingNoticeLevel.error => colorScheme.errorContainer,
      _RecordingNoticeLevel.warning => colorScheme.tertiaryContainer,
      _RecordingNoticeLevel.info => colorScheme.surfaceContainerHighest,
    };
    final textColor = switch (level) {
      _RecordingNoticeLevel.error => colorScheme.onErrorContainer,
      _RecordingNoticeLevel.warning => colorScheme.onTertiaryContainer,
      _RecordingNoticeLevel.info => colorScheme.onSurface,
    };

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: snackColor,
        content: Text(trimmed, style: TextStyle(color: textColor)),
      ),
    );
  }

  void _clearRecordingNotice() {
    if (!mounted) {
      return;
    }
    setState(() {
      _recordingNotice = null;
      _recordingNoticeLevel = _RecordingNoticeLevel.info;
    });
  }

  void _consumePendingRecordingNotice({bool showSnackBar = true}) {
    final notice = context.read<AppState>().consumePendingRecordingNotice();
    if (notice != null && notice.isNotEmpty) {
      _showRecordingNotice(notice, showSnackBar: showSnackBar);
    }
  }

  Future<void> _start() async {
    final appState = context.read<AppState>();

    try {
      if (Theme.of(context).platform == TargetPlatform.macOS &&
          !appState.hasScreenRecordingPermission) {
        await appState.promptScreenRecordingPermissionFlow();
        if (mounted) {
          _showRecordingNotice(
            'Screen Recording permission is required. System Settings has been opened.',
            showSnackBar: true,
          );
        }
        return;
      }

      final mode = _screenIndex == null ? 'fullscreen' : 'fullscreen-single';
      await appState.startRecording(
        duration: appState.recordingDurationSec,
        interval: appState.recordingIntervalSec,
        mode: mode,
        screenIndex: _screenIndex,
        screenDisplayId: _screenDisplayId,
      );

      _consumePendingRecordingNotice(showSnackBar: true);
      _wasRecording = true;
      await _load();
    } catch (e) {
      if (!mounted) return;
      _showRecordingNotice(appState.describeRecordingStartError(e));
    }
  }

  Future<void> _stop() async {
    try {
      await context.read<AppState>().stopRecording();
      _stopPolling();
      _wasRecording = false;
      await _load();
    } catch (e) {
      if (!mounted) return;
      _showRecordingNotice('Failed to stop recording: $e');
    }
  }

  Future<void> _runSmokeCheck() async {
    final appState = context.read<AppState>();
    if (appState.recordingSmokeCheckInProgress ||
        (_status?.isRecording ?? false)) {
      return;
    }
    _clearRecordingNotice();

    try {
      final summary = await appState.runRecordingSmokeCheck(
        screenIndex: _screenIndex,
        screenDisplayId: _screenDisplayId,
      );
      _showRecordingNotice(summary);
      if (appState.recordingSmokeCheckInProgress) {
        _wasRecording = true;
        await _load();
      }
    } catch (e) {
      if (!mounted) return;
      _showRecordingNotice(
        'Smoke check failed to start: ${appState.describeRecordingStartError(e)}',
      );
    }
  }

  String _audioLabel(AppState appState) {
    switch (appState.recordingAudioSource) {
      case 'mixed':
        return 'System + Mic';
      case 'system_audio':
        return 'System only';
      case 'microphone':
        return 'Mic only';
      default:
        return 'Off';
    }
  }

  String _recordingEngineLabel(AppState appState) {
    if (Theme.of(context).platform == TargetPlatform.macOS &&
        appState.useNativeMacOSRecording) {
      return 'Native macOS recorder';
    }
    return 'Backend recorder';
  }

  Widget _buildNoticeCard() {
    final notice = _recordingNotice;
    if (notice == null || notice.isEmpty) {
      return const SizedBox.shrink();
    }

    final colorScheme = Theme.of(context).colorScheme;
    final (bg, fg, icon) = switch (_recordingNoticeLevel) {
      _RecordingNoticeLevel.error => (
          colorScheme.errorContainer,
          colorScheme.onErrorContainer,
          Icons.error_outline,
        ),
      _RecordingNoticeLevel.warning => (
          colorScheme.tertiaryContainer,
          colorScheme.onTertiaryContainer,
          Icons.warning_amber_outlined,
        ),
      _RecordingNoticeLevel.info => (
          colorScheme.surfaceContainerHighest,
          colorScheme.onSurface,
          Icons.info_outline,
        ),
    };

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: fg, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              notice,
              style: TextStyle(color: fg, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _openPath(
    String path, {
    required String label,
    bool revealInFinder = false,
  }) async {
    try {
      if (Platform.isMacOS) {
        final args = revealInFinder ? ['-R', path] : [path];
        final result = await Process.run('open', args);
        if (result.exitCode != 0) {
          throw Exception((result.stderr ?? '').toString().trim());
        }
      } else {
        throw Exception('Open path is only implemented for macOS right now.');
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to open $label: $e')),
      );
    }
  }

  String _recordingTargetLabel() {
    if (_screenIndex == null) {
      return 'All screens';
    }
    final screen = _screens
        .where((s) => s.index == _screenIndex)
        .cast<RecordingScreenInfo?>()
        .firstOrNull;
    if (screen == null) {
      return 'Screen ${_screenIndex! + 1}';
    }
    return '${screen.name} (${screen.width}x${screen.height})';
  }

  RecordingDiagnosticsData _buildDiagnosticsData(AppState appState) {
    final status = _status;
    return buildRecordingDiagnosticsData(
      screenRecordingGranted: appState.hasScreenRecordingPermission,
      engine: _recordingEngineLabel(appState),
      target: _recordingTargetLabel(),
      outputDir: (status?.outputDir ?? '').isNotEmpty
          ? status!.outputDir
          : recordingDefaultOutputDir(),
      isRecording: status?.isRecording ?? false,
      transientNotice: _recordingNotice,
      transientNoticeLevel: switch (_recordingNoticeLevel) {
        _RecordingNoticeLevel.error => RecordingDiagnosticsNoticeLevel.error,
        _RecordingNoticeLevel.warning =>
          RecordingDiagnosticsNoticeLevel.warning,
        _RecordingNoticeLevel.info => RecordingDiagnosticsNoticeLevel.info,
      },
      statusNotice: status?.lastNotice,
      lastFailureKind: status?.lastFailureKind,
      lastFailureMessage: status?.lastFailureMessage,
      lastExitStatus: status?.lastTerminationStatus,
      lastOutputPath: status?.lastOutputPath,
      lastOutputFileSize: status?.lastOutputFileSize,
      smokeCheckAt: appState.lastRecordingSmokeCheckAt,
      smokeCheckSummary: appState.lastRecordingSmokeCheckSummary,
    );
  }

  Future<void> _copyDiagnostics(AppState appState,
      {required bool brief}) async {
    final diagnostics = _buildDiagnosticsData(appState);
    final message = await copyRecordingDiagnosticsToClipboard(
      diagnostics,
      brief: brief,
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Widget _buildDiagnosticsSection(AppState appState) {
    final diagnostics = _buildDiagnosticsData(appState);
    return ExpansionTile(
      tilePadding: const EdgeInsets.symmetric(horizontal: 4),
      childrenPadding: const EdgeInsets.only(bottom: 8),
      title: const Text('Troubleshooting (Advanced)'),
      subtitle: const Text('Smoke check, logs, and diagnostics copy tools'),
      children: [
        RecordingDiagnosticsPanel(
          title: 'Recording diagnostics',
          data: diagnostics,
          headerActions: [
            RecordingDiagnosticsHeaderAction(
              label: 'Copy brief',
              onPressed: () => _copyDiagnostics(appState, brief: true),
            ),
            RecordingDiagnosticsHeaderAction(
              label: 'Copy full',
              onPressed: () => _copyDiagnostics(appState, brief: false),
            ),
          ],
          quickActions: [
            RecordingDiagnosticsQuickAction(
              label: appState.recordingSmokeCheckInProgress
                  ? 'Running check...'
                  : 'Run smoke check',
              icon: Icons.science_outlined,
              onPressed: appState.recordingSmokeCheckInProgress ||
                      (_status?.isRecording ?? false)
                  ? null
                  : _runSmokeCheck,
              isLoading: appState.recordingSmokeCheckInProgress,
            ),
            RecordingDiagnosticsQuickAction(
              label: 'Open output',
              icon: Icons.video_library_outlined,
              onPressed: () => _openPath(
                diagnostics.outputDir,
                label: 'output folder',
              ),
            ),
            RecordingDiagnosticsQuickAction(
              label: 'Open logs',
              icon: Icons.folder_open_outlined,
              onPressed: () => _openPath(
                recordingLogsDirPath(),
                label: 'logs folder',
              ),
            ),
          ],
          showPermissionShortcut:
              Theme.of(context).platform == TargetPlatform.macOS &&
                  !appState.hasScreenRecordingPermission,
          onOpenLastOutput: (diagnostics.lastOutputPath ?? '').trim().isEmpty
              ? null
              : () => _openPath(
                    diagnostics.lastOutputPath!,
                    label: 'last output file',
                  ),
          onOpenScreenRecording: () =>
              appState.openPermissionSettings('screen_recording'),
        ),
      ],
    );
  }

  Widget _buildPermissionHint(AppState appState) {
    if (Theme.of(context).platform != TargetPlatform.macOS ||
        appState.hasScreenRecordingPermission) {
      return const SizedBox.shrink();
    }

    final colorScheme = Theme.of(context).colorScheme;
    final permissionStatus = appState.permissionStatus;
    final runtimePath =
        (permissionStatus?['runtime_executable'] as String?)?.trim() ?? '';
    final appBundleHint =
        (permissionStatus?['app_bundle_hint'] as String?)?.trim() ?? '';
    final effectiveRuntimePath = runtimePath.isNotEmpty
        ? runtimePath
        : '${Platform.environment['HOME'] ?? ''}/.memscreen/runtime/.venv/bin/python';

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Screen Recording permission is required.',
            style: TextStyle(
              color: colorScheme.onErrorContainer,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Allow these entries in macOS System Settings > Privacy & Security > Screen Recording:',
            style: TextStyle(color: colorScheme.onErrorContainer),
          ),
          const SizedBox(height: 6),
          Text(
            '1. $effectiveRuntimePath',
            style: TextStyle(
              color: colorScheme.onErrorContainer,
              fontFamily: 'Menlo',
              fontSize: 12,
            ),
          ),
          if (appBundleHint.isNotEmpty && appBundleHint != effectiveRuntimePath)
            Text(
              '2. $appBundleHint',
              style: TextStyle(
                color: colorScheme.onErrorContainer,
                fontFamily: 'Menlo',
                fontSize: 12,
              ),
            ),
          const SizedBox(height: 6),
          Text(
            'After granting access, completely quit and reopen MemScreen.',
            style: TextStyle(
              color: colorScheme.onErrorContainer,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FilledButton.tonalIcon(
                onPressed: appState.promptScreenRecordingPermissionFlow,
                icon: const Icon(Icons.security_outlined),
                label: const Text('Open Permission Flow'),
              ),
              FilledButton.tonalIcon(
                onPressed: _load,
                icon: const Icon(Icons.refresh),
                label: const Text('I Granted, Recheck'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMainCard(AppState appState) {
    final isRecording = _status?.isRecording ?? false;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Screen Recording',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(
            isRecording ? 'Status: Recording' : 'Status: Ready',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: isRecording
                      ? Theme.of(context).colorScheme.error
                      : Theme.of(context).colorScheme.primary,
                ),
          ),
          const SizedBox(height: 6),
          Text(
            'Engine: ${_recordingEngineLabel(appState)}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 4),
          Text(
            'Duration ${appState.recordingDurationSec}s · Interval ${appState.recordingIntervalSec}s · Audio ${_audioLabel(appState)}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 12),
          _buildPermissionHint(appState),
          if (Theme.of(context).platform == TargetPlatform.macOS &&
              !appState.hasScreenRecordingPermission)
            const SizedBox(height: 12),
          DropdownButtonFormField<int>(
            initialValue: _screenIndex ?? -1,
            decoration: const InputDecoration(
              labelText: 'Display target',
              contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            ),
            items: [
              const DropdownMenuItem<int>(
                value: -1,
                child: Text('All Screens'),
              ),
              ..._screens.map(
                (screen) => DropdownMenuItem<int>(
                  value: screen.index,
                  child: Text(
                    '${screen.name} (${screen.width}x${screen.height})${screen.isPrimary ? " [Primary]" : ""}',
                  ),
                ),
              ),
            ],
            onChanged: isRecording
                ? null
                : (value) {
                    if (value == null) return;
                    setState(() {
                      _screenIndex = value < 0 ? null : value;
                      final selected = _resolveSelectedScreen(_screens);
                      _screenDisplayId = selected?.displayId;
                    });
                  },
          ),
          const SizedBox(height: 12),
          if (isRecording)
            FilledButton.icon(
              onPressed: _stop,
              icon: const Icon(Icons.stop),
              label: const Text('Stop Recording'),
              style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error,
              ),
            )
          else
            FilledButton.icon(
              onPressed: _start,
              icon: const Icon(Icons.fiber_manual_record),
              label: const Text('Start Recording'),
            ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _status == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final appState = context.watch<AppState>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Record'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildMainCard(appState),
                const SizedBox(height: 10),
                _buildNoticeCard(),
                const SizedBox(height: 10),
                _buildDiagnosticsSection(appState),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

extension<T> on Iterable<T> {
  T? get firstOrNull {
    final iterator = this.iterator;
    if (!iterator.moveNext()) return null;
    return iterator.current;
  }
}
