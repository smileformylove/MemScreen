import 'dart:io';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'api/api_client.dart';
import 'api/chat_api.dart';
import 'api/config_api.dart';
import 'api/health_api.dart';
import 'api/process_api.dart';
import 'api/recording_api.dart';
import 'api/video_api.dart';
import 'config/api_config.dart';
import 'connection/connection_state.dart';
import 'connection/connection_service.dart';
import 'services/floating_ball_service.dart';

/// Global app state: config, client, connection, API facades.
class AppState extends ChangeNotifier {
  AppState() {
    _connection = ConnectionService(config: _config);
    _client = ApiClient(config: _config);
    _chatApi = ChatApi(_client);
    _processApi = ProcessApi(_client);
    _recordingApi = RecordingApi(_client);
    _videoApi = VideoApi(_client);
    _configApi = ConfigApi(_client);

    // Setup method channel handler for floating ball
    if (Platform.isMacOS || Platform.isWindows) {
      const channel = MethodChannel('com.memscreen/floating_ball');
      channel.setMethodCallHandler(_handleFloatingBallCall);
    }

    _loadRecordingSettings();
  }

  ApiConfig _config = ApiConfig.fromEnvironment();
  late ApiClient _client;
  late ConnectionService _connection;

  ApiConnectionState _connectionState =
      ApiConnectionState(status: ConnectionStatus.unknown);
  ApiConnectionState get connectionState => _connectionState;

  // Desired tab index from floating ball (null = no change requested)
  int? _desiredTabIndex;
  int? get desiredTabIndex => _desiredTabIndex;
  int _videoRefreshVersion = 0;
  int get videoRefreshVersion => _videoRefreshVersion;
  int _recordingStatusVersion = 0;
  int get recordingStatusVersion => _recordingStatusVersion;
  int _recordingDurationSec = 9999;
  int get recordingDurationSec => _recordingDurationSec;
  double _recordingIntervalSec = 2.0;
  double get recordingIntervalSec => _recordingIntervalSec;
  bool _recordSystemAudio = true;
  bool get recordSystemAudio => _recordSystemAudio;
  bool _recordMicrophoneAudio = true;
  bool get recordMicrophoneAudio => _recordMicrophoneAudio;
  bool _recordingAudioUserConfigured = false;
  bool get recordingAudioEnabled =>
      _recordSystemAudio || _recordMicrophoneAudio;
  String get recordingAudioSource {
    if (_recordSystemAudio && _recordMicrophoneAudio) return 'mixed';
    if (_recordSystemAudio) return 'system_audio';
    if (_recordMicrophoneAudio) return 'microphone';
    return 'none';
  }

  bool _autoTrackInputWithRecording = true;
  bool get autoTrackInputWithRecording => _autoTrackInputWithRecording;
  bool _trackingStartedByRecording = false;
  bool _trackingBoundToRecording = false;
  String? _pendingRecordingNotice;
  String get _settingsFilePath =>
      '${Platform.environment['HOME'] ?? ''}/.memscreen/flutter_settings.json';

  late ChatApi _chatApi;
  late ProcessApi _processApi;
  late RecordingApi _recordingApi;
  late VideoApi _videoApi;
  late ConfigApi _configApi;

  ChatApi get chatApi => _chatApi;
  ProcessApi get processApi => _processApi;
  RecordingApi get recordingApi => _recordingApi;
  VideoApi get videoApi => _videoApi;
  ConfigApi get configApi => _configApi;
  ApiClient get client => _client;
  ApiConfig get config => _config;

  /// Check connection (e.g. on startup or retry).
  Future<void> checkConnection() async {
    _connectionState =
        _connectionState.copyWith(status: ConnectionStatus.connecting);
    notifyListeners();
    final state = await _connection.check();
    _connectionState = state;
    notifyListeners();
  }

  /// Retry with optional new base URL (replaces config and client).
  Future<void> reconnectWithBaseUrl(String baseUrl) async {
    _connectionState =
        _connectionState.copyWith(status: ConnectionStatus.connecting);
    notifyListeners();
    final state = await _connection.reconnectWithBaseUrl(baseUrl);
    if (state.config != null) {
      _config = state.config!;
      _client = ApiClient(config: _config);
      _connection = ConnectionService(config: _config);
      _chatApi = ChatApi(_client);
      _processApi = ProcessApi(_client);
      _recordingApi = RecordingApi(_client);
      _videoApi = VideoApi(_client);
      _configApi = ConfigApi(_client);
    }
    _connectionState = state;
    notifyListeners();
  }

  void setConnectionState(ApiConnectionState s) {
    _connectionState = s;
    notifyListeners();
  }

  /// Update floating ball recording state (macOS only)
  void updateFloatingBallState(bool isRecording) {
    if (Platform.isMacOS || Platform.isWindows) {
      FloatingBallService.setRecordingState(isRecording);
    }
  }

  /// Update floating ball paused state (macOS only)
  void updateFloatingBallPaused(bool isPaused) {
    if (Platform.isMacOS || Platform.isWindows) {
      FloatingBallService.setPausedState(isPaused);
    }
  }

  /// Update floating ball keyboard/mouse tracking state (macOS only)
  void updateFloatingBallTracking(bool isTracking) {
    if (Platform.isMacOS || Platform.isWindows) {
      FloatingBallService.setTrackingState(isTracking);
    }
  }

  void requestVideoRefresh({bool notify = true}) {
    _videoRefreshVersion += 1;
    if (notify) {
      notifyListeners();
    }
  }

  void requestRecordingStatusRefresh({bool notify = true}) {
    _recordingStatusVersion += 1;
    if (notify) {
      notifyListeners();
    }
  }

  Future<void> _loadRecordingSettings() async {
    try {
      final file = File(_settingsFilePath);
      if (!await file.exists()) return;
      final raw = await file.readAsString();
      final map = jsonDecode(raw);
      if (map is! Map<String, dynamic>) return;
      final duration = map['recording_duration_sec'];
      final interval = map['recording_interval_sec'];
      final audioSource = map['recording_audio_source'];
      final systemAudioEnabled = map['record_system_audio_enabled'];
      final microphoneAudioEnabled = map['record_microphone_audio_enabled'];
      final audioUserConfigured = map['recording_audio_user_configured'];
      final autoTrack = map['auto_track_input_with_recording'];
      var loadedAudioSource = false;
      if (duration is int && duration > 0) {
        _recordingDurationSec = duration;
      }
      if (interval is num && interval > 0) {
        _recordingIntervalSec = interval.toDouble();
      }
      if (systemAudioEnabled is bool) {
        _recordSystemAudio = systemAudioEnabled;
      }
      if (microphoneAudioEnabled is bool) {
        _recordMicrophoneAudio = microphoneAudioEnabled;
      }
      if (audioUserConfigured is bool) {
        _recordingAudioUserConfigured = audioUserConfigured;
      }
      if (audioSource is String &&
          (audioSource == 'mixed' ||
              audioSource == 'system_audio' ||
              audioSource == 'microphone' ||
              audioSource == 'none')) {
        loadedAudioSource = true;
        if (audioSource == 'mixed') {
          _recordSystemAudio = true;
          _recordMicrophoneAudio = true;
        } else if (audioSource == 'system_audio') {
          _recordSystemAudio = true;
          _recordMicrophoneAudio = false;
        } else if (audioSource == 'microphone') {
          _recordSystemAudio = false;
          _recordMicrophoneAudio = true;
        } else {
          _recordSystemAudio = false;
          _recordMicrophoneAudio = false;
        }
      }
      // Backward-compatibility migration:
      // Older builds could persist "none" while audio switches looked enabled in UI
      // due IndexedStack state caching. If no explicit user-config marker exists,
      // recover to the current default (both enabled).
      final shouldMigrateLegacyAudioOff = audioUserConfigured is! bool &&
          loadedAudioSource &&
          audioSource == 'none' &&
          !_recordSystemAudio &&
          !_recordMicrophoneAudio;
      if (shouldMigrateLegacyAudioOff) {
        _recordSystemAudio = true;
        _recordMicrophoneAudio = true;
        await _persistRecordingSettings();
      }
      if (autoTrack is bool) {
        _autoTrackInputWithRecording = autoTrack;
      }
      notifyListeners();
    } catch (e) {
      debugPrint('[AppState] Failed to load recording settings: $e');
    }
  }

  Future<void> setRecordingDefaults({
    required int durationSec,
    required double intervalSec,
  }) async {
    if (durationSec <= 0 || intervalSec <= 0) return;
    _recordingDurationSec = durationSec;
    _recordingIntervalSec = intervalSec;
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> setAutoTrackInputWithRecording(bool enabled) async {
    _autoTrackInputWithRecording = enabled;
    if (!enabled) {
      _trackingStartedByRecording = false;
      _trackingBoundToRecording = false;
    }
    notifyListeners();
    await _persistRecordingSettings();
  }

  String? consumePendingRecordingNotice() {
    final notice = _pendingRecordingNotice;
    _pendingRecordingNotice = null;
    return notice;
  }

  Future<void> setRecordingAudioSource(String source) async {
    if (source != 'mixed' &&
        source != 'system_audio' &&
        source != 'microphone' &&
        source != 'none') {
      return;
    }
    if (source == 'mixed') {
      _recordSystemAudio = true;
      _recordMicrophoneAudio = true;
    } else if (source == 'system_audio') {
      _recordSystemAudio = true;
      _recordMicrophoneAudio = false;
    } else if (source == 'microphone') {
      _recordSystemAudio = false;
      _recordMicrophoneAudio = true;
    } else {
      _recordSystemAudio = false;
      _recordMicrophoneAudio = false;
    }
    _recordingAudioUserConfigured = true;
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> setRecordingAudioEnabled(bool enabled) async {
    _recordSystemAudio = enabled;
    _recordMicrophoneAudio = enabled;
    _recordingAudioUserConfigured = true;
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> setRecordSystemAudio(bool enabled) async {
    _recordSystemAudio = enabled;
    _recordingAudioUserConfigured = true;
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> setRecordMicrophoneAudio(bool enabled) async {
    _recordMicrophoneAudio = enabled;
    _recordingAudioUserConfigured = true;
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> _persistRecordingSettings() async {
    try {
      final file = File(_settingsFilePath);
      await file.parent.create(recursive: true);
      await file.writeAsString(
        jsonEncode({
          'recording_duration_sec': _recordingDurationSec,
          'recording_interval_sec': _recordingIntervalSec,
          'recording_audio_source': recordingAudioSource,
          'record_system_audio_enabled': _recordSystemAudio,
          'record_microphone_audio_enabled': _recordMicrophoneAudio,
          'recording_audio_user_configured': _recordingAudioUserConfigured,
          'auto_track_input_with_recording': _autoTrackInputWithRecording,
        }),
      );
    } catch (e) {
      debugPrint('[AppState] Failed to persist recording settings: $e');
    }
  }

  Future<void> _maybeStartTrackingForRecording() async {
    _trackingStartedByRecording = false;
    _trackingBoundToRecording = false;
    if (!_autoTrackInputWithRecording) return;
    try {
      final status = await _processApi.getTrackingStatus();
      if (status.isTracking) {
        await _processApi.markTrackingStart();
        _trackingBoundToRecording = true;
        updateFloatingBallTracking(true);
        requestRecordingStatusRefresh();
        return;
      }
      if (!status.isTracking) {
        await _processApi.startTracking();
        _trackingStartedByRecording = true;
        _trackingBoundToRecording = true;
        updateFloatingBallTracking(true);
        requestRecordingStatusRefresh();
      }
    } catch (e) {
      String reason = 'Key-Mouse tracking did not start. Video recording continues.';
      if (e is ApiException) {
        final details = e.message.trim();
        if (details.isNotEmpty) {
          reason = 'Key-Mouse tracking disabled for this recording: $details';
        }
      }
      _pendingRecordingNotice = reason;
      debugPrint('[AppState] Failed to auto-start input tracking: $e');
    }
  }

  Future<void> _saveTrackingSessionForRecording() async {
    await Future.delayed(const Duration(milliseconds: 400));
    try {
      final result = await _processApi.saveSessionFromTracking();
      if (result.eventsSaved > 0) {
        requestVideoRefresh();
      }
    } catch (e) {
      // Ignore "no events"/small interactions; keep logs for diagnostics only.
      debugPrint('[AppState] Error auto-saving tracking session: $e');
    }
  }

  Future<void> _maybeStopTrackingAfterRecording() async {
    if (!_trackingBoundToRecording) return;
    try {
      if (_trackingStartedByRecording) {
        await _processApi.stopTracking();
        updateFloatingBallTracking(false);
        requestRecordingStatusRefresh();
      }
      await _saveTrackingSessionForRecording();
    } catch (e) {
      debugPrint('[AppState] Failed to auto-stop input tracking: $e');
    } finally {
      _trackingStartedByRecording = false;
      _trackingBoundToRecording = false;
    }
  }

  Future<void> startRecording({
    required int duration,
    required double interval,
    String? mode,
    List<double>? region,
    int? screenIndex,
    int? screenDisplayId,
    String? windowTitle,
  }) async {
    await _maybeStartTrackingForRecording();
    final effectiveAudioSource = await _resolveRecordingAudioSourceForStart();
    await _recordingApi.start(
      duration: duration,
      interval: interval,
      mode: mode,
      region: region,
      screenIndex: screenIndex,
      screenDisplayId: screenDisplayId,
      windowTitle: windowTitle,
      audioSource: effectiveAudioSource,
    );
    // Confirm backend entered recording state; if not, surface immediate failure
    // so floating-ball selection flow can recover and allow instant retry.
    await Future.delayed(const Duration(milliseconds: 500));
    final status = await _recordingApi.getStatus();
    if (!status.isRecording) {
      updateFloatingBallState(false);
      requestRecordingStatusRefresh();
      throw Exception(
          'Recording did not start. Please reselect target and retry.');
    }
    updateFloatingBallState(true);
    requestRecordingStatusRefresh();
  }

  Future<String> _resolveRecordingAudioSourceForStart() async {
    final requested = recordingAudioSource;
    if (requested == 'none') return requested;
    try {
      final diagnosis = await _recordingApi.diagnoseAudio(source: requested);
      var useSystem = _recordSystemAudio;
      var useMic = _recordMicrophoneAudio;

      if (useSystem && !diagnosis.systemDeviceAvailable) {
        useSystem = false;
      }
      if (useMic && !diagnosis.microphoneAvailable) {
        useMic = false;
      }

      final resolved = _composeAudioSource(useSystem, useMic);
      if (resolved != requested) {
        debugPrint(
          '[AppState] Audio source fallback: requested=$requested, resolved=$resolved',
        );
      }
      return resolved;
    } catch (e) {
      debugPrint(
        '[AppState] Audio diagnosis failed, using requested source=$requested: $e',
      );
      return requested;
    }
  }

  String _composeAudioSource(bool useSystem, bool useMic) {
    if (useSystem && useMic) return 'mixed';
    if (useSystem) return 'system_audio';
    if (useMic) return 'microphone';
    return 'none';
  }

  Future<void> stopRecording() async {
    await _recordingApi.stop();
    updateFloatingBallState(false);
    requestRecordingStatusRefresh();
    requestVideoRefresh();
    _schedulePostStopRefreshes();
    await _maybeStopTrackingAfterRecording();
  }

  void _schedulePostStopRefreshes() {
    // Video save/merge can take several seconds; refresh in a short window so
    // Videos timeline updates as soon as the new file is persisted.
    for (var sec = 1; sec <= 12; sec++) {
      Future.delayed(Duration(seconds: sec), () {
        requestRecordingStatusRefresh();
        requestVideoRefresh();
      });
    }
  }

  /// Handle method calls from native floating ball
  Future<dynamic> _handleFloatingBallCall(MethodCall call) async {
    debugPrint('[AppState] Received floating ball call: ${call.method}');
    switch (call.method) {
      case 'startRecording':
        try {
          final args =
              call.arguments is Map ? (call.arguments as Map) : const {};
          final rawMode = args['mode'];
          var mode =
              rawMode is String && rawMode.isNotEmpty ? rawMode : 'fullscreen';
          if (mode == 'window') {
            mode = 'region';
          }

          List<double>? region;
          final rawRegion = args['region'];
          if (rawRegion is List) {
            region = rawRegion.map((e) => (e as num).toDouble()).toList();
            if (region.length != 4) {
              region = null;
            }
          }

          int? screenIndex;
          final rawScreenIndex = args['screenIndex'] ?? args['screen_index'];
          if (rawScreenIndex is int) {
            screenIndex = rawScreenIndex;
          } else if (rawScreenIndex is num) {
            screenIndex = rawScreenIndex.toInt();
          }
          int? screenDisplayId;
          final rawScreenDisplayId =
              args['screenDisplayId'] ?? args['screen_display_id'];
          if (rawScreenDisplayId is int) {
            screenDisplayId = rawScreenDisplayId;
          } else if (rawScreenDisplayId is num) {
            screenDisplayId = rawScreenDisplayId.toInt();
          }
          final rawWindowTitle = args['windowTitle'] ?? args['window_title'];
          final windowTitle =
              rawWindowTitle is String && rawWindowTitle.isNotEmpty
                  ? rawWindowTitle
                  : null;

          // Safety fallback: avoid invalid region start when selector payload is missing.
          if (mode == 'region' && (region == null || region.length != 4)) {
            mode = (screenIndex != null || screenDisplayId != null)
                ? 'fullscreen-single'
                : 'fullscreen';
            region = null;
          }

          await startRecording(
            duration: _recordingDurationSec,
            interval: _recordingIntervalSec,
            mode: mode,
            region: region,
            screenIndex: screenIndex,
            screenDisplayId: screenDisplayId,
            windowTitle: windowTitle,
          );
          final notice = consumePendingRecordingNotice();
          if (notice != null && notice.isNotEmpty) {
            debugPrint('[AppState] Recording notice: $notice');
          }
          debugPrint(
            '[AppState] Recording started from floating ball: mode=$mode, region=$region, screen=$screenIndex, displayId=$screenDisplayId, windowTitle=$windowTitle',
          );
          return <String, dynamic>{'ok': true};
        } catch (e) {
          debugPrint('[AppState] Error starting recording: $e');
          updateFloatingBallState(false);
          requestRecordingStatusRefresh();
          return <String, dynamic>{'ok': false, 'error': '$e'};
        }

      case 'stopRecording':
        try {
          await stopRecording();
          debugPrint('[AppState] Recording stopped from floating ball');
          return <String, dynamic>{'ok': true};
        } catch (e) {
          debugPrint('[AppState] Error stopping recording: $e');
          return <String, dynamic>{'ok': false, 'error': '$e'};
        }

      case 'togglePause':
        // Pause/resume functionality to be implemented
        debugPrint('[AppState] Toggle pause called (not fully implemented)');
        return <String, dynamic>{'ok': true};

      case 'toggleTracking':
        try {
          final status = await _processApi.getTrackingStatus();
          if (status.isTracking) {
            await _processApi.stopTracking();
            _trackingStartedByRecording = false;
            updateFloatingBallTracking(false);
            requestVideoRefresh();
            requestRecordingStatusRefresh();
            Future.delayed(const Duration(milliseconds: 400), () async {
              try {
                final result = await _processApi.saveSessionFromTracking();
                if (result.eventsSaved > 0) {
                  requestVideoRefresh();
                }
              } catch (e) {
                debugPrint('[AppState] Error saving tracking session: $e');
              }
            });
            debugPrint('[AppState] Input tracking stopped from floating ball');
          } else {
            await _processApi.startTracking();
            _trackingStartedByRecording = false;
            updateFloatingBallTracking(true);
            requestRecordingStatusRefresh();
            debugPrint('[AppState] Input tracking started from floating ball');
          }
          return <String, dynamic>{'ok': true};
        } catch (e) {
          debugPrint('[AppState] Error toggling input tracking: $e');
          return <String, dynamic>{'ok': false, 'error': '$e'};
        }

      case 'openQuickChat':
        _desiredTabIndex = 3;
        notifyListeners();
        debugPrint('[AppState] Requesting tab switch to Chat (3)');
        return <String, dynamic>{'ok': true};

      case 'openVideos':
        _desiredTabIndex = 1;
        notifyListeners();
        debugPrint('[AppState] Requesting tab switch to Videos (1)');
        return <String, dynamic>{'ok': true};

      case 'openSettings':
        _desiredTabIndex = 4;
        notifyListeners();
        debugPrint('[AppState] Requesting tab switch to Settings (4)');
        return <String, dynamic>{'ok': true};

      case 'quitApp':
        // Exit the application completely
        debugPrint('[AppState] Quitting application...');
        // Give some time for cleanup then exit
        Future.delayed(const Duration(milliseconds: 100), () {
          try {
            // This will trigger the AppDelegate's termination
            if (Platform.isMacOS || Platform.isWindows) {
              FloatingBallService.quitApp();
            }
          } catch (e) {
            debugPrint('[AppState] Error during quit: $e');
          }
        });
        return <String, dynamic>{'ok': true};

      default:
        debugPrint('[AppState] Unknown method: ${call.method}');
        return <String, dynamic>{'ok': false, 'error': 'Unknown method'};
    }
  }

  /// Clear the desired tab index after it has been consumed
  void clearDesiredTab() {
    _desiredTabIndex = null;
  }
}
