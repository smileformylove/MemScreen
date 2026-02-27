import 'api_client.dart';

class ModelApi {
  ModelApi(this.client);
  final ApiClient client;

  Future<LocalModelCatalog> getCatalog() async {
    final m = await client.get('/models/catalog');
    final list = m['models'];
    final models = <LocalModelEntry>[];
    if (list is List) {
      for (final item in list) {
        if (item is! Map<String, dynamic>) continue;
        models.add(
          LocalModelEntry(
            name: item['name'] as String? ?? '',
            purpose: item['purpose'] as String? ?? '',
            required: item['required'] as bool? ?? false,
            installed: item['installed'] as bool? ?? false,
            installedName: item['installed_name'] as String?,
          ),
        );
      }
    }
    return LocalModelCatalog(
      baseUrl: m['base_url'] as String? ?? '',
      runtimeReady: m['runtime_ready'] as bool? ?? false,
      runtimeError: m['runtime_error'] as String?,
      modelsDisabled: m['models_disabled'] as bool? ?? false,
      models: models,
    );
  }

  Future<void> downloadModel(
    String modelName, {
    Duration timeout = const Duration(minutes: 45),
  }) async {
    await client.post(
      '/models/download',
      body: {
        'model': modelName,
        'timeout_sec': timeout.inSeconds,
      },
      timeout: timeout,
    );
  }
}

class LocalModelCatalog {
  LocalModelCatalog({
    required this.baseUrl,
    required this.runtimeReady,
    required this.runtimeError,
    required this.modelsDisabled,
    required this.models,
  });

  final String baseUrl;
  final bool runtimeReady;
  final String? runtimeError;
  final bool modelsDisabled;
  final List<LocalModelEntry> models;
}

class LocalModelEntry {
  LocalModelEntry({
    required this.name,
    required this.purpose,
    required this.required,
    required this.installed,
    this.installedName,
  });

  final String name;
  final String purpose;
  final bool required;
  final bool installed;
  final String? installedName;
}
