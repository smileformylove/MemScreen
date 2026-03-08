import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/recording_api.dart';
import '../app_state.dart';
import '../services/floating_ball_service.dart';
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
  List<RecordingScreenInfo> _screens = [];
  bool _loading = true;
  Timer? _pollTimer;

  //
  String _mode = 'fullscreen';
  int? _screenIndex;
  int? _screenDisplayId;

  bool _wasRecording = false;
  String? _recordingNotice;
  _RecordingNoticeLevel _recordingNoticeLevel = _RecordingNoticeLevel.info;
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

    //
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
    if (showSnackBar) {
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

  Future<void> _load() async {
    try {
      final appState = context.read<AppState>();
      final s = await appState.loadRecordingStatusForUi();
      await appState.syncRecordingStateFromBackend(s.isRecording);
      final screens = await appState.loadAvailableScreensForUi();
      final justStopped = _wasRecording && !s.isRecording;
      if (mounted) {
        setState(() {
          _status = s;
          if (justStopped) {
            _mode = 'fullscreen';
            _screenIndex = null;
            _screenDisplayId = null;
          }
          _screens = screens;
          _loading = false;
          if (screens.isNotEmpty) {
            final selected = _findScreenByIndex(_screenIndex) ??
                screens.firstWhere((x) => x.isPrimary,
                    orElse: () => screens.first);
            _screenDisplayId =
                (_screenIndex == null) ? null : selected.displayId;
          }
        });
      }
      _wasRecording = s.isRecording;
      if (s.isRecording) {
        _startPolling();
      } else {
        _stopPolling();
      }
      _consumePendingRecordingNotice(showSnackBar: true);
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
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

  //
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
      _showRecordingNotice(summary, showSnackBar: true);
      if (appState.recordingSmokeCheckInProgress) {
        _wasRecording = true;
        await _load();
      }
    } catch (e) {
      if (mounted) {
        final summary = 'Smoke check failed to start: '
            '${appState.describeRecordingStartError(e)}';
        _showRecordingNotice(summary, showSnackBar: true);
      }
    }
  }

  Future<void> _start() async {
    final appState = context.read<AppState>();
    final duration = appState.recordingDurationSec;
    final interval = appState.recordingIntervalSec;
    // "Screen" button should always start screen recording from dropdown selection.
    String? mode = 'fullscreen';
    List<double>? region;
    int? screenIndex;
    int? screenDisplayId;

    if (_screenIndex != null) {
      mode = 'fullscreen-single';
      screenIndex = _screenIndex;
      screenDisplayId = _screenDisplayId;
    }

    try {
      if (Theme.of(context).platform == TargetPlatform.macOS &&
          !appState.hasScreenRecordingPermission) {
        await appState.promptScreenRecordingPermissionFlow();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(
                'Screen Recording permission is required. System Settings has been opened.',
              ),
            ),
          );
        }
        return;
      }

      final requestedAudioSource = appState.recordingAudioSource;
      if (!appState.useNativeMacOSRecording && requestedAudioSource != 'none') {
        final diagnosis = await appState.recordingApi
            .diagnoseAudio(source: requestedAudioSource);

        var useSystem = appState.recordSystemAudio;
        var useMic = appState.recordMicrophoneAudio;
        final notes = <String>[];

        if (useMic && !diagnosis.microphoneAvailable) {
          useMic = false;
          notes.add('Microphone not ready. Microphone recording is disabled.');
        }

        if (useSystem && !diagnosis.systemDeviceAvailable) {
          useSystem = false;
          notes.add(
              'System audio not ready. System audio recording is disabled.');
        }

        final resolvedAudioSource = _resolveAudioSource(useSystem, useMic);
        if (resolvedAudioSource == 'none' &&
            requestedAudioSource != 'none' &&
            notes.isEmpty) {
          notes.add(
              'No available audio input. Recording will continue without audio.');
        }

        if (notes.isNotEmpty && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(notes.join('\n'))),
          );
        }
      }
      if (_mode == 'fullscreen') {
        await FloatingBallService.show();
        await FloatingBallService.prepareScreenRecording(
          screenIndex: _screenIndex,
          screenDisplayId: _screenDisplayId,
        );
      }
      await appState.startRecording(
        duration: duration,
        interval: interval,
        mode: mode,
        region: region,
        screenIndex: screenIndex,
        screenDisplayId: screenDisplayId,
      );
      _consumePendingRecordingNotice(showSnackBar: true);
      _wasRecording = true;
      _load();
    } catch (e) {
      if (mounted) {
        _showRecordingNotice(
          _friendlyRecordingStartError(e),
          showSnackBar: true,
        );
      }
    }
  }

  String _friendlyRecordingStartError(Object error) {
    return context.read<AppState>().describeRecordingStartError(error);
  }

  String _resolveAudioSource(bool useSystem, bool useMic) {
    if (useSystem && useMic) return 'mixed';
    if (useSystem) return 'system_audio';
    if (useMic) return 'microphone';
    return 'none';
  }

  Future<void> _selectRegionWithFloatingBall() async {
    try {
      await FloatingBallService.show();
      await FloatingBallService.prepareRegionSelection(
          screenIndex: _screenIndex, screenDisplayId: _screenDisplayId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Main window minimized. Select region on screen, then start from floating ball.',
          ),
          duration: Duration(seconds: 3),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to select region: $e')),
      );
    }
  }

  Future<void> _selectWindowWithFloatingBall() async {
    try {
      await FloatingBallService.show();
      await FloatingBallService.prepareWindowSelection(
          screenIndex: _screenIndex, screenDisplayId: _screenDisplayId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Main window minimized. Click a window, then confirm recording.',
          ),
          duration: Duration(seconds: 3),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to select window: $e')),
      );
    }
  }

  Future<void> _stop() async {
    try {
      await context.read<AppState>().stopRecording();
      _stopPolling();
      if (mounted) {
        setState(() {
          _mode = 'fullscreen';
          _screenIndex = null;
          _screenDisplayId = null;
        });
      }
      _wasRecording = false;
      _load();
    } catch (e) {
      if (mounted) {
        _showRecordingNotice('Failed to stop recording: $e',
            showSnackBar: true);
      }
    }
  }

  String _selectedModeLabel() {
    switch (_mode) {
      case 'region':
        return 'Region';
      case 'window':
        return 'Window';
      default:
        return 'Full screen';
    }
  }

  String _selectedModeHelpText() {
    if ((_status?.isRecording ?? false)) {
      return 'Recording is already active. Stop it before changing capture target.';
    }
    switch (_mode) {
      case 'region':
        return 'Pick a region from the floating ball, then start recording from the overlay.';
      case 'window':
        return 'Pick a window from the floating ball, then confirm recording from the overlay.';
      default:
        return 'Choose a display target, then start recording directly from this page.';
    }
  }

  String _recordingSetupSummary(AppState appState) {
    final duration = appState.recordingDurationSec;
    final interval = appState.recordingIntervalSec;
    final audio = switch (appState.recordingAudioSource) {
      'mixed' => 'system + mic',
      'system_audio' => 'system audio',
      'microphone' => 'microphone',
      _ => 'silent',
    };
    return 'Duration ${duration}s · Interval ${interval.toStringAsFixed(interval == interval.roundToDouble() ? 0 : 1)}s · Audio $audio';
  }

  IconData _selectedModeIcon() {
    switch (_mode) {
      case 'region':
        return Icons.crop_free;
      case 'window':
        return Icons.web_asset;
      default:
        return Icons.desktop_windows_outlined;
    }
  }

  String _captureFlowLabel() {
    switch (_mode) {
      case 'region':
        return 'Pick the region from the floating ball overlay';
      case 'window':
        return 'Pick the window from the floating ball overlay';
      default:
        return 'Ready to start directly from this page';
    }
  }

  bool get _requiresOverlayFlow => _mode == 'region' || _mode == 'window';

  IconData _primaryActionIcon(bool isRecording) {
    if (isRecording) {
      return Icons.stop_circle_outlined;
    }
    return _requiresOverlayFlow ? Icons.open_in_new : Icons.fiber_manual_record;
  }

  String _primaryActionHintText(bool isRecording) {
    if (isRecording) {
      return 'Recording is active on the current target.';
    }
    if (_requiresOverlayFlow) {
      return 'Requires overlay selection before recording can begin.';
    }
    return 'Starts immediately from this page.';
  }

  ({String label, String detail, ColorScheme Function(BuildContext) colors})
      _captureStatePresentation() {
    final isRecording = _status?.isRecording ?? false;
    if (isRecording) {
      return (
        label: 'Recording live',
        detail: 'Capture is already running. Stop it before changing target.',
        colors: (context) => Theme.of(context).colorScheme,
      );
    }
    switch (_mode) {
      case 'region':
        return (
          label: 'Overlay required',
          detail: 'Use the floating ball to mark the region before recording.',
          colors: (context) => Theme.of(context).colorScheme,
        );
      case 'window':
        return (
          label: 'Overlay required',
          detail: 'Use the floating ball to pick a window before recording.',
          colors: (context) => Theme.of(context).colorScheme,
        );
      default:
        return (
          label: 'Ready here',
          detail: 'You can start recording directly from this page.',
          colors: (context) => Theme.of(context).colorScheme,
        );
    }
  }

  Widget _summaryChip({
    required IconData icon,
    required String label,
    required String value,
  }) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: theme.colorScheme.onSurfaceVariant),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              '$label: $value',
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCaptureControlCard(AppState appState) {
    final isRecording = _status?.isRecording ?? false;
    final targetLabel = _recordingTargetLabel();
    final primaryActionLabel = switch (_mode) {
      'region' => 'Open region selector',
      'window' => 'Open window picker',
      _ => 'Start recording here',
    };
    final captureState = _captureStatePresentation();
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
            'Capture target',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 6),
          Text(
            _selectedModeHelpText(),
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: (_status?.isRecording ?? false)
                  ? Theme.of(context).colorScheme.errorContainer
                  : _mode == 'fullscreen'
                      ? Theme.of(context).colorScheme.secondaryContainer
                      : Theme.of(context).colorScheme.tertiaryContainer,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  (_status?.isRecording ?? false)
                      ? Icons.fiber_manual_record
                      : _mode == 'fullscreen'
                          ? Icons.play_circle_outline
                          : Icons.touch_app_outlined,
                  color: (_status?.isRecording ?? false)
                      ? Theme.of(context).colorScheme.onErrorContainer
                      : _mode == 'fullscreen'
                          ? Theme.of(context).colorScheme.onSecondaryContainer
                          : Theme.of(context).colorScheme.onTertiaryContainer,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        captureState.label,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w700,
                              color: (_status?.isRecording ?? false)
                                  ? Theme.of(context)
                                      .colorScheme
                                      .onErrorContainer
                                  : _mode == 'fullscreen'
                                      ? Theme.of(context)
                                          .colorScheme
                                          .onSecondaryContainer
                                      : Theme.of(context)
                                          .colorScheme
                                          .onTertiaryContainer,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        captureState.detail,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: (_status?.isRecording ?? false)
                                  ? Theme.of(context)
                                      .colorScheme
                                      .onErrorContainer
                                  : _mode == 'fullscreen'
                                      ? Theme.of(context)
                                          .colorScheme
                                          .onSecondaryContainer
                                      : Theme.of(context)
                                          .colorScheme
                                          .onTertiaryContainer,
                            ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ChoiceChip(
                avatar: const Icon(Icons.desktop_windows_outlined, size: 16),
                label: const Text('Full screen'),
                selected: _mode == 'fullscreen',
                onSelected: isRecording
                    ? null
                    : (_) => _onFullscreenSelected(_screenIndex ?? -1),
              ),
              ChoiceChip(
                avatar: const Icon(Icons.crop_free, size: 16),
                label: const Text('Pick region'),
                selected: _mode == 'region',
                onSelected:
                    isRecording ? null : (_) => _onModeChanged('region'),
              ),
              ChoiceChip(
                avatar: const Icon(Icons.web_asset, size: 16),
                label: const Text('Pick window'),
                selected: _mode == 'window',
                onSelected:
                    isRecording ? null : (_) => _onModeChanged('window'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (_mode == 'fullscreen')
            DropdownButtonFormField<int>(
              value: _screenIndex ?? -1,
              decoration: const InputDecoration(
                labelText: 'Display target',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
              items: [
                const DropdownMenuItem<int>(
                  value: -1,
                  child: Text('All Screens'),
                ),
                ..._screens.map((e) => DropdownMenuItem<int>(
                      value: e.index,
                      child: Text(
                          '${e.name} (${e.width}x${e.height})${e.isPrimary ? " [Primary]" : ""}'),
                    )),
              ],
              onChanged: isRecording
                  ? null
                  : (v) {
                      _onFullscreenSelected(v);
                    },
            ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Ready to record',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    _summaryChip(
                      icon: _selectedModeIcon(),
                      label: 'Mode',
                      value: _selectedModeLabel(),
                    ),
                    _summaryChip(
                      icon: Icons.filter_center_focus_outlined,
                      label: 'Target',
                      value: targetLabel,
                    ),
                    _summaryChip(
                      icon: Icons.route_outlined,
                      label: 'Flow',
                      value: _captureFlowLabel(),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  _recordingSetupSummary(appState),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: isRecording
                  ? Theme.of(context).colorScheme.errorContainer
                  : _requiresOverlayFlow
                      ? Theme.of(context).colorScheme.tertiaryContainer
                      : Theme.of(context).colorScheme.secondaryContainer,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  _primaryActionIcon(isRecording),
                  size: 18,
                  color: isRecording
                      ? Theme.of(context).colorScheme.onErrorContainer
                      : _requiresOverlayFlow
                          ? Theme.of(context).colorScheme.onTertiaryContainer
                          : Theme.of(context).colorScheme.onSecondaryContainer,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _primaryActionHintText(isRecording),
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: isRecording
                              ? Theme.of(context).colorScheme.onErrorContainer
                              : _requiresOverlayFlow
                                  ? Theme.of(context)
                                      .colorScheme
                                      .onTertiaryContainer
                                  : Theme.of(context)
                                      .colorScheme
                                      .onSecondaryContainer,
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          if (isRecording)
            FilledButton.icon(
              onPressed: _stop,
              icon: const Icon(Icons.stop),
              label: const Text('Stop recording'),
              style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error,
              ),
            )
          else if (_mode == 'fullscreen')
            FilledButton.icon(
              onPressed: _start,
              icon: Icon(_primaryActionIcon(false)),
              label: Text(primaryActionLabel),
            )
          else
            FilledButton.tonalIcon(
              onPressed: _mode == 'region'
                  ? _selectRegionWithFloatingBall
                  : _selectWindowWithFloatingBall,
              icon: Icon(_primaryActionIcon(false)),
              label: Text(primaryActionLabel),
            ),
        ],
      ),
    );
  }

  Future<void> _onModeChanged(String nextMode) async {
    final isRecording = _status?.isRecording ?? false;
    if (isRecording) return;

    // Allow repeated taps on Region/Window to re-open selector after cancel.
    if (nextMode == 'region') {
      setState(() => _mode = nextMode);
      await _selectRegionWithFloatingBall();
      return;
    }
    if (nextMode == 'window') {
      setState(() => _mode = nextMode);
      await _selectWindowWithFloatingBall();
      return;
    }

    if (_mode == nextMode) return;
    setState(() => _mode = nextMode);

    if (nextMode == 'region') {
      await _selectRegionWithFloatingBall();
    } else if (nextMode == 'window') {
      await _selectWindowWithFloatingBall();
    }
  }

  Future<void> _onFullscreenSelected(int? value) async {
    if (value == null) return;
    final screenIndex = value < 0 ? null : value;
    setState(() {
      _mode = 'fullscreen';
      _screenIndex = screenIndex;
      final selected = _findScreenByIndex(screenIndex);
      if (selected != null) {
        _screenDisplayId = selected.displayId;
      } else if (_screens.isNotEmpty) {
        final primary = _screens.firstWhere(
          (x) => x.isPrimary,
          orElse: () => _screens.first,
        );
        _screenDisplayId = (screenIndex == null) ? null : primary.displayId;
      } else {
        _screenDisplayId = null;
      }
    });
  }

  RecordingScreenInfo? _findScreenByIndex(int? index) {
    if (index == null) return null;
    for (final s in _screens) {
      if (s.index == index) return s;
    }
    return null;
  }

  String _recordingEngineLabel(AppState appState) {
    if (Theme.of(context).platform == TargetPlatform.macOS &&
        appState.useNativeMacOSRecording) {
      return 'Native macOS recorder';
    }
    return 'Backend recorder';
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
    if (_mode == 'region') {
      return 'Region selection';
    }
    if (_mode == 'window') {
      return 'Window selection';
    }
    if (_screenIndex == null) {
      return 'All screens';
    }
    final screen = _findScreenByIndex(_screenIndex);
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

  Future<void> _copyDiagnostics(
    AppState appState, {
    required bool brief,
  }) async {
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

  Widget _buildDiagnosticsCard(AppState appState) {
    final hasPermission = Theme.of(context).platform != TargetPlatform.macOS ||
        appState.hasScreenRecordingPermission;
    final smokeCheckRunning = appState.recordingSmokeCheckInProgress;
    return RecordingDiagnosticsPanel(
      title: 'Recording diagnostics',
      data: _buildDiagnosticsData(appState),
      headerActions: [
        RecordingDiagnosticsHeaderAction(
          label: 'Copy brief',
          onPressed: smokeCheckRunning
              ? null
              : () => _copyDiagnostics(appState, brief: true),
        ),
        RecordingDiagnosticsHeaderAction(
          label: 'Copy full',
          onPressed: smokeCheckRunning
              ? null
              : () => _copyDiagnostics(appState, brief: false),
        ),
        RecordingDiagnosticsHeaderAction(
          label: 'Refresh',
          onPressed: smokeCheckRunning
              ? null
              : () async {
                  await appState.refreshPermissionStatus();
                  await _load();
                },
        ),
      ],
      quickActions: [
        RecordingDiagnosticsQuickAction(
          label: smokeCheckRunning ? 'Running check...' : 'Run smoke check',
          icon: Icons.science_outlined,
          onPressed: smokeCheckRunning || (_status?.isRecording ?? false)
              ? null
              : _runSmokeCheck,
          isLoading: smokeCheckRunning,
        ),
        RecordingDiagnosticsQuickAction(
          label: 'Open output',
          icon: Icons.video_library_outlined,
          onPressed: () => _openPath(
            _buildDiagnosticsData(appState).outputDir,
            label: 'output folder',
          ),
        ),
        RecordingDiagnosticsQuickAction(
          label: 'Open logs',
          icon: Icons.folder_open_outlined,
          onPressed: () =>
              _openPath(recordingLogsDirPath(), label: 'logs folder'),
        ),
      ],
      showPermissionShortcut:
          Theme.of(context).platform == TargetPlatform.macOS && !hasPermission,
      onOpenLastOutput:
          (_buildDiagnosticsData(appState).lastOutputPath ?? '').trim().isEmpty
              ? null
              : () => _openPath(
                    _buildDiagnosticsData(appState).lastOutputPath!,
                    label: 'last output file',
                  ),
      onOpenScreenRecording: () =>
          appState.openPermissionSettings('screen_recording'),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _status == null) {
      return Scaffold(
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
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildCaptureControlCard(appState),
                const SizedBox(height: 12),
                _buildDiagnosticsCard(appState),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
