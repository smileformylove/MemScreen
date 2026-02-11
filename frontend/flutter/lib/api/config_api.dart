import 'api_client.dart';

class ConfigApi {
  ConfigApi(this.client);
  final ApiClient client;

  Future<ConfigInfo> get() async {
    final m = await client.get('/config');
    return ConfigInfo(
      ollamaBaseUrl: m['ollama_base_url'] as String? ?? '',
      dbDir: m['db_dir'] as String? ?? '',
      videosDir: m['videos_dir'] as String? ?? '',
    );
  }
}

class ConfigInfo {
  ConfigInfo({
    required this.ollamaBaseUrl,
    required this.dbDir,
    required this.videosDir,
  });
  final String ollamaBaseUrl;
  final String dbDir;
  final String videosDir;
}
