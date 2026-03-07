import 'dart:async';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'api/api_client.dart';
import 'api/chat_api.dart';
import 'api/config_api.dart';
import 'api/model_api.dart';
import 'api/process_api.dart';
import 'api/recording_api.dart';
import 'api/video_api.dart';
import 'config/api_config.dart';
import 'connection/connection_state.dart';
import 'connection/connection_service.dart';
import 'services/floating_ball_commands.dart';
import 'services/floating_ball_service.dart';
import 'services/native_recording_import_queue.dart';
import 'services/native_recording_service.dart';
import 'services/recording_lifecycle_coordinator.dart';
import 'services/recording_settings_store.dart';
import 'services/recording_tracking_coordinator.dart';

/// Global app state: config, client, connection, API facades.
class AppState extends ChangeNotifier {
  static const List<String> supportedVideoFormats = <String>[
    'mp4',
    'mov',
    'mkv',
    'avi',
  ];
  static const List<String> supportedAudioFormats = <String>[
    'wav',
    'm4a',
    'mp3',
    'aac',
  ];

  AppState() {
    _connection = ConnectionService(config: _config);
    _client = ApiClient(config: _config);
    _chatApi = ChatApi(_client);
    _processApi = ProcessApi(_client);
    _recordingApi = RecordingApi(_client);
    _videoApi = VideoApi(_client);
    _configApi = ConfigApi(_client);
    _modelApi = ModelApi(_client);

    // Setup method channel handler for floating ball
    if (Platform.isMacOS || Platform.isWindows) {
      const channel = MethodChannel('com.memscreen/floating_ball');
      channel.setMethodCallHandler(_handleFloatingBallCall);
    }

    _recordingSettingsStore = RecordingSettingsStore();
    if (Platform.isMacOS) {
      _nativeRecordingService = NativeRecordingService();
      _nativeRecordingImportQueue = NativeRecordingImportQueue();
    }
    _recordingTrackingCoordinator = RecordingTrackingCoordinator(
      processApi: _processApi,
      requestRecordingStatusRefresh: () => requestRecordingStatusRefresh(),
      requestVideoRefresh: () => requestVideoRefresh(),
      updateFloatingBallTracking: updateFloatingBallTracking,
    );
    _recordingLifecycleCoordinator = RecordingLifecycleCoordinator(
      recordingApi: _recordingApi,
      trackingCoordinator: _recordingTrackingCoordinator,
      autoTrackInputWithRecording: () => _autoTrackInputWithRecording,
      recordSystemAudio: () => _recordSystemAudio,
      recordMicrophoneAudio: () => _recordMicrophoneAudio,
      recordingAudioSource: () => recordingAudioSource,
      recordingVideoFormat: () => _recordingVideoFormat,
      recordingAudioFormat: () => _recordingAudioFormat,
      recordingAudioDenoise: () => _recordingAudioDenoise,
      updateFloatingBallState: updateFloatingBallState,
      requestRecordingStatusRefresh: () => requestRecordingStatusRefresh(),
      requestVideoRefresh: () => requestVideoRefresh(),
    );
    _loadRecordingSettings();
  }

  ApiConfig _config = ApiConfig.fromEnvironment();
  late ApiClient _client;
  late ConnectionService _connection;

  ApiConnectionState _connectionState = ApiConnectionState(
    status: ConnectionStatus.unknown,
  );
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

  bool _autoTrackInputWithRecording = false;
  bool get autoTrackInputWithRecording => _autoTrackInputWithRecording;
  String _recordingVideoFormat = 'mp4';
  String get recordingVideoFormat => _recordingVideoFormat;
  String _recordingAudioFormat = 'wav';
  String get recordingAudioFormat => _recordingAudioFormat;
  bool _recordingAudioDenoise = true;
  bool get recordingAudioDenoise => _recordingAudioDenoise;
  final RecordingTrackingState _recordingTrackingState =
      RecordingTrackingState();
  final RecordingLifecycleState _recordingLifecycleState =
      RecordingLifecycleState();
  late final RecordingTrackingCoordinator _recordingTrackingCoordinator;
  late final RecordingLifecycleCoordinator _recordingLifecycleCoordinator;
  late final RecordingSettingsStore _recordingSettingsStore;
  NativeRecordingService? _nativeRecordingService;
  NativeRecordingImportQueue? _nativeRecordingImportQueue;
  Map<String, dynamic>? _permissionStatus;
  Map<String, dynamic>? get permissionStatus => _permissionStatus;

  late ChatApi _chatApi;
  late ProcessApi _processApi;
  late RecordingApi _recordingApi;
  late VideoApi _videoApi;
  late ConfigApi _configApi;
  late ModelApi _modelApi;

  ChatApi get chatApi => _chatApi;
  ProcessApi get processApi => _processApi;
  RecordingApi get recordingApi => _recordingApi;
  VideoApi get videoApi => _videoApi;
  ConfigApi get configApi => _configApi;
  ModelApi get modelApi => _modelApi;
  ApiClient get client => _client;
  ApiConfig get config => _config;

  bool get useNativeMacOSRecording =>
      Platform.isMacOS && _nativeRecordingService != null;

  Future<RecordingStatus> loadRecordingStatusForUi() async {
    if (useNativeMacOSRecording) {
      return _nativeRecordingService!.getStatus();
    }
    return _recordingApi.getStatus();
  }

  Future<List<RecordingScreenInfo>> loadAvailableScreensForUi() async {
    if (useNativeMacOSRecording) {
      return _nativeRecordingService!.getScreens();
    }
    return _recordingApi.getScreens();
  }

  /// Check connection (e.g. on startup or retry).
  Future<void> checkConnection() async {
    _connectionState = _connectionState.copyWith(
      status: ConnectionStatus.connecting,
    );
    notifyListeners();
    final state = await _connection.check();
    _connectionState = state;
    notifyListeners();
    if (state.status == ConnectionStatus.connected) {
      await refreshPermissionStatus();
      await _flushPendingNativeImports();
    }
  }

  /// Retry with optional new base URL (replaces config and client).
  Future<void> reconnectWithBaseUrl(String baseUrl) async {
    _connectionState = _connectionState.copyWith(
      status: ConnectionStatus.connecting,
    );
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
      _modelApi = ModelApi(_client);
    }
    _connectionState = state;
    notifyListeners();
    if (state.status == ConnectionStatus.connected) {
      await refreshPermissionStatus();
      await _flushPendingNativeImports();
    }
  }

  void setConnectionState(ApiConnectionState s) {
    _connectionState = s;
    notifyListeners();
  }

  void setDesiredTabIndex(int index) {
    _desiredTabIndex = index;
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

  Future<void> refreshPermissionStatus({bool promptSystem = false}) async {
    try {
      _permissionStatus = await _client.get(
        '/permissions/status?prompt=${promptSystem ? 'true' : 'false'}',
      );
      notifyListeners();
    } catch (e) {
      debugPrint('[AppState] Failed to refresh permission status: $e');
    }
  }

  Future<void> openPermissionSettings(String area) async {
    try {
      await _client.post('/permissions/open-settings?area=$area');
    } catch (e) {
      debugPrint('[AppState] Failed to open permission settings: $e');
    }
  }

  Future<void> _flushPendingNativeImports() async {
    if (!useNativeMacOSRecording || _nativeRecordingImportQueue == null) {
      return;
    }
    try {
      await _nativeRecordingImportQueue!.flush(_client);
      requestVideoRefresh();
    } catch (e) {
      debugPrint('[AppState] Failed to flush pending native imports: $e');
    }
  }

  Future<void> _loadRecordingSettings() async {
    try {
      final map = await _recordingSettingsStore.load();
      if (map == null) return;
      final duration = map['recording_duration_sec'];
      final interval = map['recording_interval_sec'];
      final audioSource = map['recording_audio_source'];
      final systemAudioEnabled = map['record_system_audio_enabled'];
      final microphoneAudioEnabled = map['record_microphone_audio_enabled'];
      final audioUserConfigured = map['recording_audio_user_configured'];
      final autoTrack = map['auto_track_input_with_recording'];
      final videoFormat = map['recording_video_format'];
      final audioFormat = map['recording_audio_format'];
      final audioDenoise = map['recording_audio_denoise'];
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
      if (videoFormat is String &&
          supportedVideoFormats.contains(videoFormat.toLowerCase())) {
        _recordingVideoFormat = videoFormat.toLowerCase();
      }
      if (audioFormat is String &&
          supportedAudioFormats.contains(audioFormat.toLowerCase())) {
        _recordingAudioFormat = audioFormat.toLowerCase();
      }
      if (audioDenoise is bool) {
        _recordingAudioDenoise = audioDenoise;
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
      _recordingTrackingState.startedByRecording = false;
      _recordingTrackingState.boundToRecording = false;
    }
    notifyListeners();
    await _persistRecordingSettings();
  }

  String? consumePendingRecordingNotice() {
    final notice = _recordingTrackingState.pendingRecordingNotice;
    _recordingTrackingState.pendingRecordingNotice = null;
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

  Future<void> setRecordingVideoFormat(String format) async {
    final normalized = format.trim().toLowerCase();
    if (!supportedVideoFormats.contains(normalized)) return;
    if (_recordingVideoFormat == normalized) return;
    _recordingVideoFormat = normalized;
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> setRecordingAudioFormat(String format) async {
    final normalized = format.trim().toLowerCase();
    if (!supportedAudioFormats.contains(normalized)) return;
    if (_recordingAudioFormat == normalized) return;
    _recordingAudioFormat = normalized;
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> setRecordingAudioDenoise(bool enabled) async {
    if (_recordingAudioDenoise == enabled) return;
    _recordingAudioDenoise = enabled;
    notifyListeners();
    await _persistRecordingSettings();
  }

  Future<void> _persistRecordingSettings() async {
    await _recordingSettingsStore.save({
      'recording_duration_sec': _recordingDurationSec,
      'recording_interval_sec': _recordingIntervalSec,
      'recording_audio_source': recordingAudioSource,
      'record_system_audio_enabled': _recordSystemAudio,
      'record_microphone_audio_enabled': _recordMicrophoneAudio,
      'recording_audio_user_configured': _recordingAudioUserConfigured,
      'auto_track_input_with_recording': _autoTrackInputWithRecording,
      'recording_video_format': _recordingVideoFormat,
      'recording_audio_format': _recordingAudioFormat,
      'recording_audio_denoise': _recordingAudioDenoise,
    });
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
    if (useNativeMacOSRecording) {
      final result = await _nativeRecordingService!.start(
        duration: duration,
        interval: interval,
        mode: mode,
        region: region,
        screenIndex: screenIndex,
        screenDisplayId: screenDisplayId,
        windowTitle: windowTitle,
        audioSource: recordingAudioSource,
      );
      if (!result.ok) {
        throw Exception(result.error ?? 'Failed to start native recording');
      }
      if ((result.notice ?? '').isNotEmpty) {
        _recordingTrackingState.pendingRecordingNotice = result.notice;
      }
      updateFloatingBallState(true);
      requestRecordingStatusRefresh();
      return;
    }

    await _recordingLifecycleCoordinator.start(
      lifecycleState: _recordingLifecycleState,
      trackingState: _recordingTrackingState,
      duration: duration,
      interval: interval,
      mode: mode,
      region: region,
      screenIndex: screenIndex,
      screenDisplayId: screenDisplayId,
      windowTitle: windowTitle,
    );
  }

  Future<void> stopRecording() async {
    if (useNativeMacOSRecording) {
      final result = await _nativeRecordingService!.stop();
      updateFloatingBallState(false);
      requestRecordingStatusRefresh();
      if ((result.notice ?? '').isNotEmpty) {
        _recordingTrackingState.pendingRecordingNotice = result.notice;
      }
      final filename = result.filename;
      if (result.ok && filename != null && filename.isNotEmpty) {
        final payload = {
          'filename': filename,
          'duration_sec': result.durationSec,
          'mode': result.mode,
          'audio_source': result.audioSourceUsed,
        };
        try {
          await _client.post('/recording/import', body: payload);
          requestVideoRefresh();
        } catch (e) {
          debugPrint('[AppState] Failed to import native recording: $e');
          await _nativeRecordingImportQueue?.enqueue(payload);
          _recordingTrackingState.pendingRecordingNotice =
              'Recording saved locally. It will appear in Videos after backend reconnects.';
        }
      }
      return;
    }

    await _recordingLifecycleCoordinator.stop(
      lifecycleState: _recordingLifecycleState,
      trackingState: _recordingTrackingState,
    );
  }

  Future<void> syncRecordingStateFromBackend(bool isRecording) async {
    if (useNativeMacOSRecording) {
      return;
    }
    await _recordingLifecycleCoordinator.syncFromBackend(
      isRecording: isRecording,
      lifecycleState: _recordingLifecycleState,
      trackingState: _recordingTrackingState,
    );
  }

  /// Handle method calls from native floating ball
  Future<dynamic> _handleFloatingBallCall(MethodCall call) async {
    debugPrint('[AppState] Received floating ball call: ${call.method}');
    switch (call.method) {
      case 'startRecording':
        try {
          final request = FloatingBallStartRecordingRequest.fromArguments(
            call.arguments,
          );

          await startRecording(
            duration: _recordingDurationSec,
            interval: _recordingIntervalSec,
            mode: request.mode,
            region: request.region,
            screenIndex: request.screenIndex,
            screenDisplayId: request.screenDisplayId,
            windowTitle: request.windowTitle,
          );
          final notice = consumePendingRecordingNotice();
          if (notice != null && notice.isNotEmpty) {
            debugPrint('[AppState] Recording notice: $notice');
          }
          debugPrint(
            '[AppState] Recording started from floating ball: '
            'mode=${request.mode}, region=${request.region}, '
            'screen=${request.screenIndex}, '
            'displayId=${request.screenDisplayId}, '
            'windowTitle=${request.windowTitle}',
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
          await _recordingTrackingCoordinator.toggleTrackingFromFloatingBall(
            state: _recordingTrackingState,
          );
          debugPrint('[AppState] Input tracking toggled from floating ball');
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

  @override
  void dispose() {
    _recordingLifecycleCoordinator.dispose(_recordingLifecycleState);
    super.dispose();
  }
}
