import '../api/api_client.dart';
import '../api/health_api.dart';
import '../config/api_config.dart';

enum ConnectionStatus { unknown, connecting, connected, error }

/// Backend connection state (renamed to avoid clash with Flutter's ConnectionState).
class ApiConnectionState {
  ApiConnectionState({
    this.status = ConnectionStatus.unknown,
    this.message,
    this.health,
    this.config,
  });

  final ConnectionStatus status;
  final String? message;
  final HealthResponse? health;
  final ApiConfig? config;

  ApiConnectionState copyWith({
    ConnectionStatus? status,
    String? message,
    HealthResponse? health,
    ApiConfig? config,
  }) =>
      ApiConnectionState(
        status: status ?? this.status,
        message: message ?? this.message,
        health: health ?? this.health,
        config: config ?? this.config,
      );

  bool get isConnected => status == ConnectionStatus.connected;
  bool get isError => status == ConnectionStatus.error;
}
