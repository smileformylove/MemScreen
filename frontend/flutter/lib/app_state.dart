import 'dart:io';

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
  }

  ApiConfig _config = ApiConfig.fromEnvironment();
  late ApiClient _client;
  late ConnectionService _connection;

  ApiConnectionState _connectionState = ApiConnectionState(status: ConnectionStatus.unknown);
  ApiConnectionState get connectionState => _connectionState;

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
    _connectionState = _connectionState.copyWith(status: ConnectionStatus.connecting);
    notifyListeners();
    final state = await _connection.check();
    _connectionState = state;
    notifyListeners();
  }

  /// Retry with optional new base URL (replaces config and client).
  Future<void> reconnectWithBaseUrl(String baseUrl) async {
    _connectionState = _connectionState.copyWith(status: ConnectionStatus.connecting);
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

  /// Handle method calls from native floating ball
  Future<dynamic> _handleFloatingBallCall(MethodCall call) async {
    debugPrint('[AppState] Received floating ball call: ${call.method}');
    switch (call.method) {
      case 'startRecording':
        try {
          await _recordingApi.start(
            duration: 60,
            interval: 2.0,
            mode: 'fullscreen',
            region: null,
            screenIndex: null,
          );
          updateFloatingBallState(true);
          debugPrint('[AppState] Recording started from floating ball');
        } catch (e) {
          debugPrint('[AppState] Error starting recording: $e');
        }
        break;

      case 'stopRecording':
        try {
          await _recordingApi.stop();
          updateFloatingBallState(false);
          debugPrint('[AppState] Recording stopped from floating ball');
        } catch (e) {
          debugPrint('[AppState] Error stopping recording: $e');
        }
        break;

      case 'togglePause':
        // Pause/resume functionality to be implemented
        debugPrint('[AppState] Toggle pause called (not fully implemented)');
        break;

      default:
        debugPrint('[AppState] Unknown method: ${call.method}');
    }
  }
}
