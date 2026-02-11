/// API base URL for MemScreen backend.
/// Default: http://127.0.0.1:8765 (see docs/API_HTTP.md).
/// Override via [ApiConfig.baseUrl] or environment (e.g. MEMSCREEN_API_URL).
class ApiConfig {
  ApiConfig({String? baseUrl})
      : baseUrl = baseUrl ?? _defaultBaseUrl;

  static const String _defaultBaseUrl = 'http://127.0.0.1:8765';

  /// Base URL without trailing slash, e.g. http://127.0.0.1:8765
  final String baseUrl;

  /// Full URL for a path (e.g. /health -> http://127.0.0.1:8765/health)
  String url(String path) {
    final p = path.startsWith('/') ? path : '/$path';
    return '$baseUrl$p';
  }

  /// Create from environment if needed (e.g. MEMSCREEN_API_URL)
  static ApiConfig fromEnvironment() {
    // Dart has no built-in env map; app can pass --dart-define=API_BASE_URL=...
    // or we read from a config file. For now use default.
    return ApiConfig();
  }
}
