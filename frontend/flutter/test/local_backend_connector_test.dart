import 'package:flutter_test/flutter_test.dart';
import 'package:memscreen_flutter/config/api_config.dart';
import 'package:memscreen_flutter/connection/connection_state.dart';
import 'package:memscreen_flutter/services/local_backend_connector.dart';
import 'package:memscreen_flutter/services/native_runtime_service.dart';

ApiConnectionState _state(ConnectionStatus status, {String? message}) {
  return ApiConnectionState(
    status: status,
    message: message,
    config: ApiConfig(baseUrl: 'http://127.0.0.1:8765'),
  );
}

void main() {
  test('returns immediately when backend is already connected', () async {
    var bootstrapCalls = 0;
    final connectedStates = <ApiConnectionState>[];
    final changedStates = <ApiConnectionState>[];

    final connector = LocalBackendConnector(
      checkConnection: () async => _state(ConnectionStatus.connected),
      onConnected: (state) async => connectedStates.add(state),
      onStateChanged: (state) => changedStates.add(state),
      ensureNativeBackendBootstrap: () async {
        bootstrapCalls += 1;
        return const NativeRuntimeBootstrapResult(ok: true, status: 'ok');
      },
      buildConnectingState: ({String? message}) =>
          _state(ConnectionStatus.connecting, message: message),
      currentConfig: () => ApiConfig(baseUrl: 'http://127.0.0.1:8765'),
      pollInterval: Duration.zero,
      pollAttempts: 3,
    );

    await connector.connectOrBootstrap();

    expect(bootstrapCalls, 0);
    expect(connectedStates, hasLength(1));
    expect(changedStates, isEmpty);
  });

  test('surfaces bootstrap failure without polling', () async {
    final connectedStates = <ApiConnectionState>[];
    final changedStates = <ApiConnectionState>[];

    final connector = LocalBackendConnector(
      checkConnection: () async => _state(ConnectionStatus.error),
      onConnected: (state) async => connectedStates.add(state),
      onStateChanged: (state) => changedStates.add(state),
      ensureNativeBackendBootstrap: () async =>
          const NativeRuntimeBootstrapResult(
        ok: false,
        status: 'launch_failed',
        message: 'bootstrap failed',
      ),
      buildConnectingState: ({String? message}) =>
          _state(ConnectionStatus.connecting, message: message),
      currentConfig: () => ApiConfig(baseUrl: 'http://127.0.0.1:8765'),
      pollInterval: Duration.zero,
      pollAttempts: 3,
    );

    await connector.connectOrBootstrap();

    expect(connectedStates, isEmpty);
    expect(changedStates, hasLength(2));
    expect(changedStates.first.status, ConnectionStatus.connecting);
    expect(changedStates.last.status, ConnectionStatus.error);
    expect(changedStates.last.message, 'bootstrap failed');
  });

  test('polls until backend becomes connected after bootstrap', () async {
    final connectedStates = <ApiConnectionState>[];
    final changedStates = <ApiConnectionState>[];
    var checks = 0;

    final connector = LocalBackendConnector(
      checkConnection: () async {
        checks += 1;
        if (checks >= 3) {
          return _state(ConnectionStatus.connected);
        }
        return _state(ConnectionStatus.error);
      },
      onConnected: (state) async => connectedStates.add(state),
      onStateChanged: (state) => changedStates.add(state),
      ensureNativeBackendBootstrap: () async =>
          const NativeRuntimeBootstrapResult(ok: true, status: 'launched'),
      buildConnectingState: ({String? message}) =>
          _state(ConnectionStatus.connecting, message: message),
      currentConfig: () => ApiConfig(baseUrl: 'http://127.0.0.1:8765'),
      pollInterval: Duration.zero,
      pollAttempts: 4,
    );

    await connector.connectOrBootstrap();

    expect(connectedStates, hasLength(1));
    expect(connectedStates.single.status, ConnectionStatus.connected);
    expect(changedStates.where((s) => s.status == ConnectionStatus.connecting),
        isNotEmpty);
  });

  test('returns timeout error when backend never becomes connected', () async {
    final connectedStates = <ApiConnectionState>[];
    final changedStates = <ApiConnectionState>[];

    final connector = LocalBackendConnector(
      checkConnection: () async => _state(ConnectionStatus.error),
      onConnected: (state) async => connectedStates.add(state),
      onStateChanged: (state) => changedStates.add(state),
      ensureNativeBackendBootstrap: () async =>
          const NativeRuntimeBootstrapResult(ok: true, status: 'launched'),
      buildConnectingState: ({String? message}) =>
          _state(ConnectionStatus.connecting, message: message),
      currentConfig: () => ApiConfig(baseUrl: 'http://127.0.0.1:8765'),
      pollInterval: Duration.zero,
      pollAttempts: 2,
    );

    await connector.connectOrBootstrap();

    expect(connectedStates, isEmpty);
    expect(changedStates.last.status, ConnectionStatus.error);
    expect(
      changedStates.last.message,
      'Local backend is still starting. Retry in a few seconds.',
    );
  });
}
