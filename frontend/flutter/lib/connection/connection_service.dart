import '../api/api_client.dart';
import '../api/health_api.dart';
import '../config/api_config.dart';
import 'connection_state.dart';

/// Checks backend reachability and exposes connection state.
class ConnectionService {
  ConnectionService({ApiConfig? config})
      : _config = config ?? ApiConfig.fromEnvironment(),
        _client = ApiClient(config: config ?? ApiConfig.fromEnvironment());

  final ApiConfig _config;
  final ApiClient _client;

  ApiConfig get config => _config;

  /// Returns current connection state (checks /health).
  Future<ApiConnectionState> check() async {
    try {
      final healthApi = HealthApi(_client);
      final health = await healthApi.get();
      return ApiConnectionState(
        status: health.isOk ? ConnectionStatus.connected : ConnectionStatus.error,
        message: health.isOk ? null : 'Backend: ${health.ollama}; DB: ${health.db}',
        health: health,
        config: _config,
      );
    } on ApiException catch (e) {
      return ApiConnectionState(
        status: ConnectionStatus.error,
        message: e.message,
        config: _config,
      );
    } catch (e) {
      return ApiConnectionState(
        status: ConnectionStatus.error,
        message: e.toString(),
        config: _config,
      );
    }
  }

  /// Use a new base URL and re-check (for "configure URL" flow).
  Future<ApiConnectionState> reconnectWithBaseUrl(String baseUrl) async {
    final newConfig = ApiConfig(baseUrl: baseUrl);
    final newClient = ApiClient(config: newConfig);
    try {
      final health = await HealthApi(newClient).get();
      return ApiConnectionState(
        status: health.isOk ? ConnectionStatus.connected : ConnectionStatus.error,
        message: health.isOk ? null : '${health.ollama}; ${health.db}',
        health: health,
        config: newConfig,
      );
    } on ApiException catch (e) {
      return ApiConnectionState(
        status: ConnectionStatus.error,
        message: e.message,
        config: newConfig,
      );
    } catch (e) {
      return ApiConnectionState(
        status: ConnectionStatus.error,
        message: e.toString(),
        config: newConfig,
      );
    }
  }

  ApiClient get client => _client;
}
