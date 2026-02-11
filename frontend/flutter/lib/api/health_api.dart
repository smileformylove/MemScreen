import 'api_client.dart';

/// GET /health — status, ollama, db.
class HealthApi {
  HealthApi(this.client);
  final ApiClient client;

  Future<HealthResponse> get() async {
    final m = await client.get('/health');
    return HealthResponse(
      status: m['status'] as String? ?? 'unknown',
      ollama: m['ollama'] as String? ?? 'unknown',
      db: m['db'] as String? ?? 'unknown',
    );
  }
}

class HealthResponse {
  HealthResponse({required this.status, required this.ollama, required this.db});
  final String status;
  final String ollama;
  final String db;

  bool get isOk => status == 'ok';
}
