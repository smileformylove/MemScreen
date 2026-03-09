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
import 'services/local_process_session_store.dart';
import 'services/local_backend_connector.dart';
import 'services/local_video_catalog.dart';
import 'services/local_video_catalog_store.dart';
import 'services/model_catalog_cache.dart';
import 'services/model_catalog_groups.dart';
import 'services/native_input_tracking_service.dart';
import 'services/native_permission_service.dart';
import 'services/native_recording_import_queue.dart';
import 'services/native_tracking_session_queue.dart';
import 'services/native_recording_service.dart';
import 'services/native_runtime_service.dart';
import 'services/recording_failure_messages.dart';
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
  static const Duration _modelCatalogCacheTtl = Duration(seconds: 10);

  AppState() {
    _rebindApiServices(_config);

    // Setup method channel handler for floating ball
    if (Platform.isMacOS || Platform.isWindows) {
      const channel = MethodChannel('com.memscreen/floating_ball');
      channel.setMethodCallHandler(_handleFloatingBallCall);
    }

    _recordingSettingsStore = RecordingSettingsStore();
    _modelCatalogCache = ModelCatalogCache(ttl: _modelCatalogCacheTtl);
    _localBackendConnector = LocalBackendConnector(
      checkConnection: () => _connection.check(),
      onConnected: (state) => _handleConnectedState(state),
      onStateChanged: (state) {
        _connectionState = state;
        notifyListeners();
      },
      ensureNativeBackendBootstrap: () => _ensureNativeBackendBootstrap(),
      buildConnectingState: ({String? message}) =>
          _connectingState(message: message),
      currentConfig: () => _config,
    );
    if (Platform.isMacOS) {
      _nativeRecordingService = NativeRecordingService();
      _nativeRecordingImportQueue = NativeRecordingImportQueue();
      _nativeInputTrackingService = NativeInputTrackingService();
      _nativePermissionService = NativePermissionService();
      _nativeRuntimeService = NativeRuntimeService();
      _nativeTrackingSessionQueue = NativeTrackingSessionQueue();
      _localVideoCatalogStore = LocalVideoCatalogStore();
      _localVideoCatalog = LocalVideoCatalog(store: _localVideoCatalogStore);
      _localProcessSessionStore = LocalProcessSessionStore();
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

  bool get isBackendConnected =>
      _connectionState.status == ConnectionStatus.connected;

  // Desired tab index from floating ball (null = no change requested)
  int? _desiredTabIndex;
  int? get desiredTabIndex => _desiredTabIndex;
  int _currentTabIndex = 0;
  int get currentTabIndex => _currentTabIndex;
  int _videoRefreshVersion = 0;
  int get videoRefreshVersion => _videoRefreshVersion;
  int _recordingStatusVersion = 0;
  int get recordingStatusVersion => _recordingStatusVersion;
  int _processRefreshVersion = 0;
  int get processRefreshVersion => _processRefreshVersion;
  int _chatModelRefreshVersion = 0;
  int get chatModelRefreshVersion => _chatModelRefreshVersion;
  String? _lastRecordingSmokeCheckAt;
  String? get lastRecordingSmokeCheckAt => _lastRecordingSmokeCheckAt;
  String? _lastRecordingSmokeCheckSummary;
  String? get lastRecordingSmokeCheckSummary => _lastRecordingSmokeCheckSummary;
  bool _recordingSmokeCheckInProgress = false;
  bool get recordingSmokeCheckInProgress => _recordingSmokeCheckInProgress;
  late final ModelCatalogCache _modelCatalogCache;
  late final LocalBackendConnector _localBackendConnector;
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
  Timer? _nativeRecordingMonitorTimer;
  NativeRecordingService? _nativeRecordingService;
  NativeRecordingImportQueue? _nativeRecordingImportQueue;
  NativeInputTrackingService? _nativeInputTrackingService;
  NativePermissionService? _nativePermissionService;
  NativeRuntimeService? _nativeRuntimeService;
  NativeTrackingSessionQueue? _nativeTrackingSessionQueue;
  LocalVideoCatalogStore? _localVideoCatalogStore;
  LocalVideoCatalog? _localVideoCatalog;
  LocalProcessSessionStore? _localProcessSessionStore;
  Map<String, dynamic>? _permissionStatus;
  bool _backendCheckInFlight = false;
  DateTime? _lastBackendCheckAt;
  bool _nativeRuntimeBootstrapRequested = false;
  bool _backendActivationRequestedByUser = false;
  bool _nativeRecordingFallbackToBackend = false;
  Map<String, dynamic>? get permissionStatus => _permissionStatus;
  bool get hasRequestedBackendActivation => _backendActivationRequestedByUser;
  bool get usingBackendRecordingFallback => _nativeRecordingFallbackToBackend;

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

  bool get useNativeMacOSTracking =>
      Platform.isMacOS && _nativeInputTrackingService != null;

  bool get useNativeMacOSPermissions =>
      Platform.isMacOS && _nativePermissionService != null;

  bool get useNativeMacOSRuntime =>
      Platform.isMacOS && _nativeRuntimeService != null;

  @visibleForTesting
  bool get enforcesScreenRecordingPermissionFlow => Platform.isMacOS;

  bool get supportsLocalFirstCoreFeatures =>
      useNativeMacOSRecording && useNativeMacOSTracking;

  bool get _usesLocalEmbeddedBackend {
    final uri = Uri.tryParse(_config.baseUrl);
    final host = uri?.host.toLowerCase();
    return host == '127.0.0.1' || host == 'localhost' || host == '::1';
  }

  ApiConnectionState _connectingState({String? message}) => ApiConnectionState(
        status: ConnectionStatus.connecting,
        message: message,
        health: _connectionState.health,
        config: _connectionState.config ?? _config,
      );

  void _rebindApiServices(ApiConfig config) {
    _config = config;
    _connection = ConnectionService(config: _config);
    _client = ApiClient(config: _config);
    _chatApi = ChatApi(_client);
    _processApi = ProcessApi(_client);
    _recordingApi = RecordingApi(_client);
    _videoApi = VideoApi(_client);
    _configApi = ConfigApi(_client);
    _modelApi = ModelApi(_client);
  }

  Future<void> _handleConnectedState(ApiConnectionState state) async {
    _connectionState = state;
    notifyListeners();
    _nativeRuntimeBootstrapRequested = false;
    await refreshPermissionStatus();
    await _flushPendingNativeImports();
    await _flushPendingTrackingSessions();
  }

  bool _permissionGranted(String key) {
    final section = _permissionStatus?[key];
    return section is Map<String, dynamic> && section['granted'] == true;
  }

  bool get hasScreenRecordingPermission =>
      _permissionGranted('screen_recording');
  bool get hasAccessibilityPermission => _permissionGranted('accessibility');
  bool get hasInputMonitoringPermission =>
      _permissionGranted('input_monitoring');

  String _processSessionMergeKey(ProcessSession session) {
    return '${session.startTime}|${session.endTime}|${session.eventCount}|${session.keystrokes}|${session.clicks}';
  }

  Future<RecordingStatus> loadRecordingStatusForUi() async {
    if (useNativeMacOSRecording && !_nativeRecordingFallbackToBackend) {
      final status = await _nativeRecordingService!.getStatus();
      if (!status.isRecording) {
        final finished =
            await _nativeRecordingService!.consumeFinishedRecordingIfNeeded();
        if (finished != null) {
          await _handleFinishedNativeRecording(finished);
        }
      }
      return _nativeRecordingService!.getStatus();
    }
    try {
      return await _recordingApi.getStatus();
    } catch (_) {
      if (useNativeMacOSRecording) {
        return _nativeRecordingService!.getStatus();
      }
      rethrow;
    }
  }

  Future<List<RecordingScreenInfo>> loadAvailableScreensForUi() async {
    if (useNativeMacOSRecording && !_nativeRecordingFallbackToBackend) {
      return _nativeRecordingService!.getScreens();
    }
    try {
      return await _recordingApi.getScreens();
    } catch (_) {
      if (useNativeMacOSRecording) {
        return _nativeRecordingService!.getScreens();
      }
      rethrow;
    }
  }

  Future<void> deleteVideoForUi(String filename) async {
    try {
      final normalized = filename.startsWith('/')
          ? filename
          : '${Platform.environment['HOME'] ?? ''}/.memscreen/videos/$filename';
      final file = File(normalized);
      if (await file.exists()) {
        await file.delete();
      }
      await _localVideoCatalogStore?.deleteByFilename(normalized);
      requestVideoRefresh();
    } catch (e) {
      rethrow;
    }
  }

  Future<String> resolvePlayableVideoPathForUi(String filename) async {
    var normalized = filename.trim();
    if (normalized.startsWith('~')) {
      final home = Platform.environment['HOME'] ?? '';
      normalized = normalized.replaceFirst('~', home);
    }
    if (!isBackendConnected) {
      return normalized;
    }
    try {
      return await _videoApi.resolvePlayablePath(normalized);
    } catch (_) {
      return normalized;
    }
  }

  Future<Map<String, dynamic>> reanalyzeVideoForUi(String filename) async {
    if (!isBackendConnected) {
      throw ApiException('Video analysis requires backend connection.');
    }
    final result = await _videoApi.reanalyze(filename);
    requestVideoRefresh();
    return result;
  }

  void _invalidateModelCatalogCache() {
    _modelCatalogCache.invalidate();
  }

  void _cacheCurrentChatModel(String modelName) {
    _modelCatalogCache.markCurrentChatModel(modelName);
  }

  void _cacheDownloadedModel(String modelName) {
    _modelCatalogCache.markDownloadedModel(modelName);
  }

  Future<LocalModelCatalog> _ensureModelCatalogSnapshotAfterMutation() async {
    final snapshot = _modelCatalogCache.snapshot;
    if (snapshot != null) {
      return snapshot;
    }
    return loadLocalModelCatalogForUi(forceRefresh: true);
  }

  Future<SettingsModelSection> loadSettingsModelSectionForUi({
    bool forceRefresh = false,
  }) async {
    final catalog =
        await loadLocalModelCatalogForUi(forceRefresh: forceRefresh);
    return buildSettingsModelSection(catalog);
  }

  Future<LocalModelCatalog> loadLocalModelCatalogForUi({
    bool forceRefresh = false,
  }) async {
    if (!forceRefresh) {
      final cached = _modelCatalogCache.readFresh(DateTime.now());
      if (cached != null) {
        return cached;
      }
    }
    final catalog = await _modelApi.getCatalog();
    _modelCatalogCache.store(catalog);
    return catalog;
  }

  Future<LocalModelCatalog> downloadLocalModelForUi(
    String modelName, {
    Duration timeout = const Duration(minutes: 45),
  }) async {
    await _modelApi.downloadModel(modelName, timeout: timeout);
    _cacheDownloadedModel(modelName);
    requestChatModelRefresh(invalidateCache: false);
    return _ensureModelCatalogSnapshotAfterMutation();
  }

  Future<ChatModelSelection> loadChatModelSelectionForUi({
    bool forceRefresh = false,
  }) async {
    final catalog =
        await loadLocalModelCatalogForUi(forceRefresh: forceRefresh);
    var availableModels = catalog.availableChatModels;
    var currentModel = catalog.currentChatModel;
    if (availableModels.isEmpty) {
      availableModels = await _chatApi.getModels();
    }
    if ((currentModel ?? '').isEmpty) {
      currentModel = await _chatApi.getCurrentModel();
    }
    return buildChatModelSelection(
      catalog,
      availableModels: availableModels,
      currentModel: currentModel,
    );
  }

  Future<LocalModelCatalog> setChatModelForUi(String modelName) async {
    await _chatApi.setModel(modelName);
    _cacheCurrentChatModel(modelName);
    requestChatModelRefresh(invalidateCache: false);
    return _ensureModelCatalogSnapshotAfterMutation();
  }

  Future<List<VideoItem>> loadVideosForUi() async {
    final localList = await _localVideoCatalog?.list() ?? const <VideoItem>[];
    if (!isBackendConnected) {
      return localList;
    }
    try {
      final remoteList = await _videoApi.getList();
      await _localVideoCatalog?.reconcileWithRemote(remoteList);
      final byFilename = <String, VideoItem>{
        for (final item in localList) item.filename: item,
      };
      for (final item in remoteList) {
        byFilename[item.filename] = item;
      }
      return byFilename.values.toList();
    } catch (_) {
      return localList;
    }
  }

  Future<TrackingStatus> loadTrackingStatusForUi() async {
    if (useNativeMacOSTracking) {
      final status = await _nativeInputTrackingService!.getStatus();
      _permissionStatus = {
        ...?_permissionStatus,
        'accessibility': {
          'granted': status.accessibilityGranted,
          'message': status.accessibilityGranted
              ? 'Accessibility permission granted'
              : 'Accessibility permission is required for native tracking.',
        },
        'input_monitoring': {
          'granted': status.inputMonitoringGranted,
          'message': status.inputMonitoringGranted
              ? 'Input Monitoring permission granted'
              : 'Input Monitoring permission is required for native tracking.',
        },
      };
      notifyListeners();
      return status;
    }
    return _processApi.getTrackingStatus();
  }

  Future<List<ProcessSession>> loadProcessSessionsForUi(
      {int limit = 20}) async {
    final local = await _localProcessSessionStore?.listSessions() ??
        const <ProcessSession>[];
    if (!isBackendConnected) {
      return local;
    }
    try {
      final remote = await _processApi.getSessions(limit: limit);
      final byKey = <String, ProcessSession>{
        for (final session in local) _processSessionMergeKey(session): session,
      };
      for (final session in remote) {
        byKey[_processSessionMergeKey(session)] = session;
      }
      await _localProcessSessionStore?.reconcileWithRemote(remote);
      final merged = byKey.values.toList()
        ..sort((a, b) => b.startTime.compareTo(a.startTime));
      return merged;
    } catch (_) {
      return local;
    }
  }

  Future<ProcessAnalysis?> loadProcessAnalysisForUi(int sessionId) async {
    if (!isBackendConnected) {
      return await _localProcessSessionStore?.getAnalysis(sessionId);
    }
    try {
      return await _processApi.getSessionAnalysis(sessionId.toString());
    } catch (_) {
      return await _localProcessSessionStore?.getAnalysis(sessionId);
    }
  }

  Future<void> saveProcessSessionForUi({
    required List<Map<String, dynamic>> events,
    required String startTime,
    required String endTime,
  }) async {
    var savedRemote = false;
    if (isBackendConnected) {
      try {
        await _processApi.saveSession(
          events: events,
          startTime: startTime,
          endTime: endTime,
        );
        savedRemote = true;
      } catch (_) {}
    }

    await _localProcessSessionStore?.appendSession(
      startTime: startTime,
      endTime: endTime,
      events: events,
    );

    if (savedRemote) {
      final remote = await _processApi.getSessions(limit: 50);
      await _localProcessSessionStore?.reconcileWithRemote(remote);
    }
    requestProcessRefresh();
  }

  Future<int> deleteProcessSessionForUi(int sessionId) async {
    var deleted = 0;
    try {
      deleted = await _processApi.deleteSession(sessionId.toString());
    } catch (_) {}
    deleted += await _localProcessSessionStore?.deleteSession(sessionId) ?? 0;
    requestProcessRefresh();
    return deleted;
  }

  Future<int> deleteAllProcessSessionsForUi() async {
    var deleted = 0;
    try {
      deleted = await _processApi.deleteAllSessions();
    } catch (_) {}
    deleted += await _localProcessSessionStore?.deleteAllSessions() ?? 0;
    requestProcessRefresh();
    return deleted;
  }

  Future<void> startInputTracking() async {
    if (useNativeMacOSTracking) {
      await _nativeInputTrackingService!.start();
      updateFloatingBallTracking(true);
      requestRecordingStatusRefresh();
      requestProcessRefresh();
      return;
    }
    await _processApi.startTracking();
    updateFloatingBallTracking(true);
    requestRecordingStatusRefresh();
    requestProcessRefresh();
  }

  Future<void> stopInputTracking() async {
    if (useNativeMacOSTracking) {
      await _nativeInputTrackingService!.stop();
      updateFloatingBallTracking(false);
      requestRecordingStatusRefresh();
      requestProcessRefresh();
      return;
    }
    await _processApi.stopTracking();
    updateFloatingBallTracking(false);
    requestRecordingStatusRefresh();
    requestProcessRefresh();
  }

  Future<SaveFromTrackingResult> saveTrackingSessionForUi() async {
    if (useNativeMacOSTracking) {
      try {
        final payload =
            await _nativeInputTrackingService!.captureSessionPayload();
        final result = await _nativeInputTrackingService!
            .saveSession(_processApi, payload);
        await _localProcessSessionStore?.appendSession(
          startTime: payload.startTime,
          endTime: payload.endTime,
          events: payload.events,
        );
        requestProcessRefresh();
        return result;
      } catch (e) {
        if (_nativeTrackingSessionQueue != null) {
          final payload =
              await _nativeInputTrackingService!.captureSessionPayload();
          await _nativeTrackingSessionQueue!.enqueue({
            'events': payload.events,
            'start_time': payload.startTime,
            'end_time': payload.endTime,
          });
          await _localProcessSessionStore?.appendSession(
            startTime: payload.startTime,
            endTime: payload.endTime,
            events: payload.events,
          );
          return SaveFromTrackingResult(
            eventsSaved: payload.eventsSaved,
            startTime: payload.startTime,
            endTime: payload.endTime,
          );
        }
        rethrow;
      }
    }
    return _processApi.saveSessionFromTracking();
  }

  /// Check connection (e.g. on startup or retry).
  Future<void> checkConnection() async {
    _connectionState = _connectingState();
    notifyListeners();
    final state = await _connection.check();
    if (state.status == ConnectionStatus.connected) {
      await _handleConnectedState(state);
    } else {
      _connectionState = state;
      notifyListeners();
      if (_usesLocalEmbeddedBackend) {
        await _ensureNativeBackendBootstrap();
      }
    }
  }

  /// Retry with optional new base URL (replaces config and client).
  Future<void> reconnectWithBaseUrl(String baseUrl) async {
    _backendActivationRequestedByUser = true;
    _connectionState = _connectingState(message: 'Connecting to backend...');
    notifyListeners();
    final state = await _connection.reconnectWithBaseUrl(baseUrl);
    if (state.config != null) {
      _rebindApiServices(state.config!);
      _invalidateModelCatalogCache();
      requestChatModelRefresh(notify: false, invalidateCache: false);
    }
    if (state.status == ConnectionStatus.connected) {
      await _handleConnectedState(state);
    } else {
      _connectionState = state;
      notifyListeners();
      if (_usesLocalEmbeddedBackend) {
        await _ensureNativeBackendBootstrap();
      }
    }
  }

  void setConnectionState(ApiConnectionState s) {
    _connectionState = s;
    notifyListeners();
  }

  Future<void> ensureBackendConnection({bool force = false}) async {
    if (force) {
      _backendActivationRequestedByUser = true;
    }
    if (!force && _connectionState.status == ConnectionStatus.connected) {
      return;
    }
    if (_backendCheckInFlight) {
      return;
    }
    final now = DateTime.now();
    if (!force &&
        _lastBackendCheckAt != null &&
        now.difference(_lastBackendCheckAt!) < const Duration(seconds: 5)) {
      return;
    }
    _backendCheckInFlight = true;
    _lastBackendCheckAt = now;
    try {
      if (force && _usesLocalEmbeddedBackend && useNativeMacOSRuntime) {
        await _localBackendConnector.connectOrBootstrap();
      } else {
        await checkConnection();
      }
    } finally {
      _backendCheckInFlight = false;
    }
  }

  void setDesiredTabIndex(int index) {
    _desiredTabIndex = index;
    notifyListeners();
  }

  void setCurrentTabIndex(int index) {
    if (_currentTabIndex == index) {
      return;
    }
    _currentTabIndex = index;
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

  void requestProcessRefresh({bool notify = true}) {
    _processRefreshVersion += 1;
    if (notify) {
      notifyListeners();
    }
  }

  void markRecordingSmokeCheckStarted() {
    _recordingSmokeCheckInProgress = true;
    _lastRecordingSmokeCheckAt = DateTime.now().toIso8601String();
    _lastRecordingSmokeCheckSummary = 'Running 2-second smoke check...';
    requestRecordingStatusRefresh();
  }

  void markRecordingSmokeCheckFinished({required String summary}) {
    _recordingSmokeCheckInProgress = false;
    _lastRecordingSmokeCheckAt = DateTime.now().toIso8601String();
    _lastRecordingSmokeCheckSummary = summary;
    requestRecordingStatusRefresh();
  }

  String describeRecordingStartError(Object error) {
    final raw = error is ApiException ? error.message : error.toString();
    final lower = raw.toLowerCase();
    if (lower.contains('screen recording permission')) {
      return 'Screen Recording permission is missing. In macOS System Settings, allow both MemScreen.app and ~/.memscreen/runtime/.venv/bin/python under Screen Recording, then restart the app.';
    }
    if (lower.contains('accessibility') || lower.contains('input monitoring')) {
      return 'Keyboard/Mouse permission is missing. Allow ~/.memscreen/runtime/.venv/bin/python in Accessibility and Input Monitoring, then restart the app.';
    }
    return 'Failed to start recording: $raw';
  }

  Future<String> runRecordingSmokeCheck({
    int? screenIndex,
    int? screenDisplayId,
  }) async {
    if (_recordingSmokeCheckInProgress) {
      return _lastRecordingSmokeCheckSummary ??
          'Running 2-second smoke check...';
    }
    if (enforcesScreenRecordingPermissionFlow &&
        !hasScreenRecordingPermission) {
      await promptScreenRecordingPermissionFlow();
      const summary =
          'Permission: Screen Recording is still not active, so the smoke check cannot start.';
      markRecordingSmokeCheckStarted();
      markRecordingSmokeCheckFinished(summary: summary);
      _recordingTrackingState.pendingRecordingNotice = summary;
      return summary;
    }

    markRecordingSmokeCheckStarted();
    try {
      final smokeMode =
          screenIndex == null ? 'fullscreen' : 'fullscreen-single';
      await startRecording(
        duration: 2,
        interval: recordingIntervalSec,
        mode: smokeMode,
        screenIndex: screenIndex,
        screenDisplayId: screenDisplayId,
      );
      const summary =
          'Smoke check: A 2-second recording test has started. Wait for it to finish and review Last result below.';
      _recordingTrackingState.pendingRecordingNotice = summary;
      requestRecordingStatusRefresh();
      return summary;
    } catch (e) {
      final summary =
          'Smoke check failed to start: ${describeRecordingStartError(e)}';
      markRecordingSmokeCheckFinished(summary: summary);
      _recordingTrackingState.pendingRecordingNotice = summary;
      return summary;
    }
  }

  void requestChatModelRefresh({
    bool notify = true,
    bool invalidateCache = true,
  }) {
    if (invalidateCache) {
      _invalidateModelCatalogCache();
    }
    _chatModelRefreshVersion += 1;
    if (notify) {
      notifyListeners();
    }
  }

  Future<void> refreshPermissionStatus({bool promptSystem = false}) async {
    try {
      if (useNativeMacOSPermissions) {
        _permissionStatus = await _nativePermissionService!.getStatus(
          prompt: promptSystem,
        );
      } else {
        _permissionStatus = await _client.get(
          '/permissions/status?prompt=${promptSystem ? 'true' : 'false'}',
        );
      }
      if (_nativeRecordingFallbackToBackend &&
          hasScreenRecordingPermission &&
          !_recordingLifecycleState.expectedActive) {
        _nativeRecordingFallbackToBackend = false;
      }
      notifyListeners();
    } catch (e) {
      debugPrint('[AppState] Failed to refresh permission status: $e');
    }
  }

  Future<void> openPermissionSettings(String area) async {
    try {
      if (useNativeMacOSPermissions) {
        await _nativePermissionService!.openSettings(area);
      } else {
        await _client.post('/permissions/open-settings?area=$area');
      }
    } catch (e) {
      debugPrint('[AppState] Failed to open permission settings: $e');
    }
  }

  Future<NativeRuntimeBootstrapResult?> _ensureNativeBackendBootstrap() async {
    if (!useNativeMacOSRuntime || !_usesLocalEmbeddedBackend) {
      return null;
    }
    if (_nativeRuntimeBootstrapRequested) {
      return const NativeRuntimeBootstrapResult(
        ok: true,
        status: 'already_requested',
      );
    }
    try {
      final result = await _nativeRuntimeService!.ensureBackendBootstrap();
      _nativeRuntimeBootstrapRequested = result.shouldWaitForBackend;
      return result;
    } catch (e) {
      _nativeRuntimeBootstrapRequested = false;
      debugPrint('[AppState] Failed to ensure native backend bootstrap: $e');
      return NativeRuntimeBootstrapResult(
        ok: false,
        status: 'channel_error',
        message: 'Failed to trigger local backend startup: $e',
      );
    }
  }

  Future<void> promptScreenRecordingPermissionFlow() async {
    await refreshPermissionStatus(promptSystem: true);
    await openPermissionSettings('screen_recording');
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

  Future<void> _flushPendingTrackingSessions() async {
    if (!useNativeMacOSTracking || _nativeTrackingSessionQueue == null) {
      return;
    }
    try {
      await _nativeTrackingSessionQueue!.flush(_processApi);
      requestProcessRefresh();
    } catch (e) {
      debugPrint('[AppState] Failed to flush pending tracking sessions: $e');
    }
  }

  void _stopNativeRecordingMonitor() {
    _nativeRecordingMonitorTimer?.cancel();
    _nativeRecordingMonitorTimer = null;
  }

  String _describeNativeRecordingFailure(NativeRecordingStopResult result) {
    return describeNativeRecordingFailure(
      failureKind: result.failureKind,
      error: result.error,
    );
  }

  Future<void> _handleFinishedNativeRecording(
    NativeRecordingStopResult result,
  ) async {
    _stopNativeRecordingMonitor();
    updateFloatingBallState(false);
    requestRecordingStatusRefresh();
    if ((result.notice ?? '').isNotEmpty) {
      _recordingTrackingState.pendingRecordingNotice = result.notice;
    }
    if (!result.ok) {
      final failureSummary = _describeNativeRecordingFailure(result);
      _recordingTrackingState.pendingRecordingNotice = failureSummary;
      if (_recordingSmokeCheckInProgress) {
        markRecordingSmokeCheckFinished(summary: failureSummary);
      }
      return;
    }
    final filename = result.filename;
    if (result.ok && filename != null && filename.isNotEmpty) {
      final file = File(filename);
      final fileSize = await file.exists() ? await file.length() : 0;
      await _localVideoCatalogStore?.upsert({
        'filename': filename,
        'timestamp': DateTime.now().toIso8601String(),
        'duration': result.durationSec,
        'file_size': fileSize,
        'recording_mode': result.mode,
        'audio_source': result.audioSourceUsed,
        'content_summary': 'Native macOS recording',
        'analysis_status': 'pending-sync',
      });
      final payload = {
        'filename': filename,
        'duration_sec': result.durationSec,
        'mode': result.mode,
        'audio_source': result.audioSourceUsed,
      };
      if (_recordingSmokeCheckInProgress) {
        markRecordingSmokeCheckFinished(
          summary:
              'Passed: 2-second recording created a playable file successfully.',
        );
      }
      try {
        await _client.post('/recording/import', body: payload);
        requestVideoRefresh();
      } catch (e) {
        debugPrint('[AppState] Failed to import native recording: $e');
        await _nativeRecordingImportQueue?.enqueue(payload);
        _recordingTrackingState.pendingRecordingNotice =
            'Import warning: Recording saved locally, but adding it to Videos failed. It will retry after backend reconnects.';
        if (_recordingSmokeCheckInProgress) {
          markRecordingSmokeCheckFinished(
            summary:
                'Warning: Smoke check recorded a file, but importing it into Videos failed. See logs for details.',
          );
        }
      }
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
    if (useNativeMacOSRecording && !_nativeRecordingFallbackToBackend) {
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
        final errorText = result.error ?? 'Failed to start native recording';
        if (_shouldFallbackToBackendRecorder(errorText) && isBackendConnected) {
          _nativeRecordingFallbackToBackend = true;
          _recordingTrackingState.pendingRecordingNotice =
              'Native recorder is blocked by permission. '
              'Switched to backend recorder fallback.';
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
          return;
        }
        throw Exception(errorText);
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
    if (useNativeMacOSRecording && !_nativeRecordingFallbackToBackend) {
      final result = await _nativeRecordingService!.stop();
      await _handleFinishedNativeRecording(result);
      return;
    }

    await _recordingLifecycleCoordinator.stop(
      lifecycleState: _recordingLifecycleState,
      trackingState: _recordingTrackingState,
    );
    if (hasScreenRecordingPermission) {
      _nativeRecordingFallbackToBackend = false;
    }
  }

  Future<void> syncRecordingStateFromBackend(bool isRecording) async {
    if (useNativeMacOSRecording && !_nativeRecordingFallbackToBackend) {
      return;
    }
    await _recordingLifecycleCoordinator.syncFromBackend(
      isRecording: isRecording,
      lifecycleState: _recordingLifecycleState,
      trackingState: _recordingTrackingState,
    );
    if (!isRecording && hasScreenRecordingPermission) {
      _nativeRecordingFallbackToBackend = false;
    }
  }

  bool _shouldFallbackToBackendRecorder(String errorText) {
    final lower = errorText.toLowerCase();
    return lower.contains('permission') ||
        lower.contains('not permitted') ||
        lower.contains('screen recording');
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

          if (Platform.isMacOS && !hasScreenRecordingPermission) {
            await promptScreenRecordingPermissionFlow();
            _recordingTrackingState.pendingRecordingNotice =
                'Screen Recording permission is missing. '
                'Trying backend recorder fallback.';
          }

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

      case 'nativeRecordingEnded':
        try {
          final args = call.arguments is Map
              ? Map<String, dynamic>.from(call.arguments as Map)
              : const <String, dynamic>{};
          final result = NativeRecordingStopResult(
            ok: args['ok'] as bool? ?? true,
            filename: args['filename'] as String?,
            durationSec: (args['durationSec'] as num?)?.toDouble(),
            mode: args['mode'] as String?,
            audioSourceUsed: args['audioSourceUsed'] as String?,
            notice: args['notice'] as String?,
            error: args['error'] as String?,
            failureKind: args['failureKind'] as String?,
            consumedByCallback: args['consumedByCallback'] as bool? ?? true,
          );
          await _handleFinishedNativeRecording(result);
          debugPrint('[AppState] Native recording finished callback handled');
          return <String, dynamic>{'ok': true};
        } catch (e) {
          debugPrint('[AppState] Error handling native recording finish: $e');
          return <String, dynamic>{'ok': false, 'error': '$e'};
        }

      case 'nativeRecordingStateChanged':
        final args = call.arguments is Map
            ? Map<String, dynamic>.from(call.arguments as Map)
            : const <String, dynamic>{};
        final isRecording = args['isRecording'] as bool? ?? false;
        updateFloatingBallState(isRecording);
        requestRecordingStatusRefresh();
        return <String, dynamic>{'ok': true};

      case 'nativeTrackingStateChanged':
        final args = call.arguments is Map
            ? Map<String, dynamic>.from(call.arguments as Map)
            : const <String, dynamic>{};
        final isTracking = args['isTracking'] as bool? ?? false;
        updateFloatingBallTracking(isTracking);
        requestProcessRefresh();
        return <String, dynamic>{'ok': true};

      case 'nativeTrackingEnded':
        try {
          final args = call.arguments is Map
              ? Map<String, dynamic>.from(call.arguments as Map)
              : const <String, dynamic>{};
          if ((args['ok'] as bool? ?? false) == true) {
            final events = (args['events'] as List? ?? const [])
                .map((entry) => Map<String, dynamic>.from(entry as Map))
                .toList();
            final startTime = args['startTime'] as String? ?? '';
            final endTime = args['endTime'] as String? ?? startTime;
            await saveProcessSessionForUi(
              events: events,
              startTime: startTime,
              endTime: endTime,
            );
          }
          updateFloatingBallTracking(false);
          requestProcessRefresh();
          return <String, dynamic>{'ok': true};
        } catch (e) {
          debugPrint('[AppState] Error handling native tracking finish: $e');
          return <String, dynamic>{'ok': false, 'error': '$e'};
        }

      case 'togglePause':
        // Pause/resume functionality to be implemented
        debugPrint('[AppState] Toggle pause called (not fully implemented)');
        return <String, dynamic>{'ok': true};

      case 'toggleTracking':
        try {
          final status = await loadTrackingStatusForUi();
          if (status.isTracking) {
            await stopInputTracking();
            try {
              final result = await saveTrackingSessionForUi();
              if (result.eventsSaved > 0) {
                requestProcessRefresh();
              }
            } catch (e) {
              debugPrint('[AppState] Error saving tracking session: $e');
            }
          } else {
            if (Platform.isMacOS &&
                (!hasAccessibilityPermission ||
                    !hasInputMonitoringPermission)) {
              setDesiredTabIndex(4);
              if (!hasAccessibilityPermission) {
                await openPermissionSettings('accessibility');
              } else {
                await openPermissionSettings('input_monitoring');
              }
              return <String, dynamic>{
                'ok': false,
                'error':
                    'Tracking permission is required. Opened Settings for authorization.',
              };
            }
            await startInputTracking();
          }
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
    _stopNativeRecordingMonitor();
    _recordingLifecycleCoordinator.dispose(_recordingLifecycleState);
    super.dispose();
  }
}
