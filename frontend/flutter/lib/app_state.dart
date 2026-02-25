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
      final autoTrack = map['auto_track_input_with_recording'];
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
      if (audioSource is String &&
          (audioSource == 'mixed' ||
              audioSource == 'system_audio' ||
              audioSource == 'microphone' ||
              audioSource == 'none')) {
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
    notifyListeners();
    await _persistRecordingSettings();
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
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> setRecordingAudioEnabled(bool enabled) async {
    _recordSystemAudio = enabled;
    _recordMicrophoneAudio = enabled;
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> setRecordSystemAudio(bool enabled) async {
    _recordSystemAudio = enabled;
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> setRecordMicrophoneAudio(bool enabled) async {
    _recordMicrophoneAudio = enabled;
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
          'auto_track_input_with_recording': _autoTrackInputWithRecording,
        }),
      );
    } catch (e) {
      debugPrint('[AppState] Failed to persist recording settings: $e');
    }
  }

  Future<void> _maybeStartTrackingForRecording() async {
    if (!_autoTrackInputWithRecording) return;
    try {
      final status = await _processApi.getTrackingStatus();
      if (!status.isTracking) {
        await _processApi.startTracking();
        _trackingStartedByRecording = true;
        updateFloatingBallTracking(true);
        requestRecordingStatusRefresh();
      }
    } catch (e) {
      debugPrint('[AppState] Failed to auto-start input tracking: $e');
    }
  }

  Future<void> _maybeStopTrackingAfterRecording() async {
    if (!_trackingStartedByRecording) return;
    try {
      await _processApi.stopTracking();
      updateFloatingBallTracking(false);
      requestRecordingStatusRefresh();
      _trackingStartedByRecording = false;
      Future.delayed(const Duration(milliseconds: 400), () async {
        try {
          final result = await _processApi.saveSessionFromTracking();
          if (result.eventsSaved > 0) {
            requestVideoRefresh();
          }
        } catch (e) {
          debugPrint('[AppState] Error auto-saving tracking session: $e');
        }
      });
    } catch (e) {
      debugPrint('[AppState] Failed to auto-stop input tracking: $e');
    }
  }

  Future<void> startRecording({
    required int duration,
    required double interval,
    String? mode,
    List<double>? region,
    int? screenIndex,
    String? windowTitle,
  }) async {
    await _maybeStartTrackingForRecording();
    await _recordingApi.start(
      duration: duration,
      interval: interval,
      mode: mode,
      region: region,
      screenIndex: screenIndex,
      windowTitle: windowTitle,
      audioSource: recordingAudioSource,
    );
    updateFloatingBallState(true);
    requestRecordingStatusRefresh();
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
          final rawWindowTitle = args['windowTitle'] ?? args['window_title'];
          final windowTitle =
              rawWindowTitle is String && rawWindowTitle.isNotEmpty
                  ? rawWindowTitle
                  : null;

          // Safety fallback: avoid invalid region start when selector payload is missing.
          if (mode == 'region' && (region == null || region.length != 4)) {
            mode = (screenIndex != null) ? 'fullscreen-single' : 'fullscreen';
            region = null;
          }

          await startRecording(
            duration: _recordingDurationSec,
            interval: _recordingIntervalSec,
            mode: mode,
            region: region,
            screenIndex: screenIndex,
            windowTitle: windowTitle,
          );
          debugPrint(
            '[AppState] Recording started from floating ball: mode=$mode, region=$region, screen=$screenIndex, windowTitle=$windowTitle',
          );
        } catch (e) {
          debugPrint('[AppState] Error starting recording: $e');
          updateFloatingBallState(false);
          requestRecordingStatusRefresh();
        }
        break;

      case 'stopRecording':
        try {
          await stopRecording();
          debugPrint('[AppState] Recording stopped from floating ball');
        } catch (e) {
          debugPrint('[AppState] Error stopping recording: $e');
        }
        break;

      case 'togglePause':
        // Pause/resume functionality to be implemented
        debugPrint('[AppState] Toggle pause called (not fully implemented)');
        break;

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
        } catch (e) {
          debugPrint('[AppState] Error toggling input tracking: $e');
        }
        break;

      case 'openQuickChat':
        _desiredTabIndex = 3;
        notifyListeners();
        debugPrint('[AppState] Requesting tab switch to Chat (3)');
        break;

      case 'openVideos':
        _desiredTabIndex = 1;
        notifyListeners();
        debugPrint('[AppState] Requesting tab switch to Videos (1)');
        break;

      case 'openSettings':
        _desiredTabIndex = 4;
        notifyListeners();
        debugPrint('[AppState] Requesting tab switch to Settings (4)');
        break;

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
        break;

      default:
        debugPrint('[AppState] Unknown method: ${call.method}');
    }
  }

  /// Clear the desired tab index after it has been consumed
  void clearDesiredTab() {
    _desiredTabIndex = null;
  }
}
