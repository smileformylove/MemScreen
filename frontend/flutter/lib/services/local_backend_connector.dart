import '../config/api_config.dart';
import '../connection/connection_state.dart';
import 'native_runtime_service.dart';

typedef ConnectionStateBuilder = ApiConnectionState Function({String? message});

class LocalBackendConnector {
  LocalBackendConnector({
    required this.checkConnection,
    required this.onConnected,
    required this.onStateChanged,
    required this.ensureNativeBackendBootstrap,
    required this.buildConnectingState,
    required this.currentConfig,
    Duration pollInterval = const Duration(seconds: 1),
    int pollAttempts = 8,
  })  : _pollInterval = pollInterval,
        _pollAttempts = pollAttempts;

  final Future<ApiConnectionState> Function() checkConnection;
  final Future<void> Function(ApiConnectionState state) onConnected;
  final void Function(ApiConnectionState state) onStateChanged;
  final Future<NativeRuntimeBootstrapResult?> Function()
      ensureNativeBackendBootstrap;
  final ConnectionStateBuilder buildConnectingState;
  final ApiConfig Function() currentConfig;
  final Duration _pollInterval;
  final int _pollAttempts;

  Future<void> connectOrBootstrap() async {
    final initialState = await checkConnection();
    if (initialState.status == ConnectionStatus.connected) {
      await onConnected(initialState);
      return;
    }

    onStateChanged(buildConnectingState(message: 'Starting local backend...'));
    final bootstrapResult = await ensureNativeBackendBootstrap();
    if (bootstrapResult != null && !bootstrapResult.shouldWaitForBackend) {
      onStateChanged(
        ApiConnectionState(
          status: ConnectionStatus.error,
          message: bootstrapResult.message ??
              'Unable to start the local backend from this app session.',
          config: currentConfig(),
        ),
      );
      return;
    }

    for (var attempt = 0; attempt < _pollAttempts; attempt += 1) {
      if (attempt > 0) {
        await Future<void>.delayed(_pollInterval);
      }
      final polledState = await checkConnection();
      if (polledState.status == ConnectionStatus.connected) {
        await onConnected(polledState);
        return;
      }
      if (attempt < _pollAttempts - 1) {
        onStateChanged(
            buildConnectingState(message: 'Starting local backend...'));
      }
    }

    onStateChanged(
      ApiConnectionState(
        status: ConnectionStatus.error,
        message: 'Local backend is still starting. Retry in a few seconds.',
        config: currentConfig(),
      ),
    );
  }
}
