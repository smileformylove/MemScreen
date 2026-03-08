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
            family: item['family'] as String? ?? 'other',
            sizeLabel: item['size_label'] as String?,
            supportsChat: item['supports_chat'] as bool? ?? false,
            supportsVision: item['supports_vision'] as bool? ?? false,
            recommendedUse: item['recommended_use'] as String? ?? 'general',
            chatSelectable: item['chat_selectable'] as bool? ?? false,
            recommendedChatDefault:
                item['recommended_chat_default'] as bool? ?? false,
          ),
        );
      }
    }
    return LocalModelCatalog(
      baseUrl: m['base_url'] as String? ?? '',
      modelsDir: m['models_dir'] as String?,
      modelsDirExternal: m['models_dir_external'] as bool? ?? false,
      currentChatModel: m['current_chat_model'] as String?,
      recommendedChatModel: m['recommended_chat_model'] as String?,
      availableChatModels: (m['available_chat_models'] is List)
          ? (m['available_chat_models'] as List)
              .map((e) => e.toString())
              .toList()
          : const <String>[],
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
    required this.modelsDir,
    required this.modelsDirExternal,
    required this.currentChatModel,
    required this.recommendedChatModel,
    required this.availableChatModels,
    required this.runtimeReady,
    required this.runtimeError,
    required this.modelsDisabled,
    required this.models,
  });

  final String baseUrl;
  final String? modelsDir;
  final bool modelsDirExternal;
  final String? currentChatModel;
  final String? recommendedChatModel;
  final List<String> availableChatModels;
  final bool runtimeReady;
  final String? runtimeError;
  final bool modelsDisabled;
  final List<LocalModelEntry> models;

  LocalModelCatalog copyWith({
    String? currentChatModel,
    String? recommendedChatModel,
    List<String>? availableChatModels,
    List<LocalModelEntry>? models,
  }) {
    return LocalModelCatalog(
      baseUrl: baseUrl,
      modelsDir: modelsDir,
      modelsDirExternal: modelsDirExternal,
      currentChatModel: currentChatModel ?? this.currentChatModel,
      recommendedChatModel: recommendedChatModel ?? this.recommendedChatModel,
      availableChatModels: availableChatModels ?? this.availableChatModels,
      runtimeReady: runtimeReady,
      runtimeError: runtimeError,
      modelsDisabled: modelsDisabled,
      models: models ?? this.models,
    );
  }
}

class LocalModelEntry {
  LocalModelEntry({
    required this.name,
    required this.purpose,
    required this.required,
    required this.installed,
    required this.family,
    required this.sizeLabel,
    required this.supportsChat,
    required this.supportsVision,
    required this.recommendedUse,
    required this.chatSelectable,
    required this.recommendedChatDefault,
    this.installedName,
  });

  final String name;
  final String purpose;
  final bool required;
  final bool installed;
  final String? installedName;
  final String family;
  final String? sizeLabel;
  final bool supportsChat;
  final bool supportsVision;
  final String recommendedUse;
  final bool chatSelectable;
  final bool recommendedChatDefault;

  LocalModelEntry copyWith({
    bool? installed,
    String? installedName,
    bool? chatSelectable,
    bool? recommendedChatDefault,
  }) {
    return LocalModelEntry(
      name: name,
      purpose: purpose,
      required: required,
      installed: installed ?? this.installed,
      installedName: installedName ?? this.installedName,
      family: family,
      sizeLabel: sizeLabel,
      supportsChat: supportsChat,
      supportsVision: supportsVision,
      recommendedUse: recommendedUse,
      chatSelectable: chatSelectable ?? this.chatSelectable,
      recommendedChatDefault:
          recommendedChatDefault ?? this.recommendedChatDefault,
    );
  }
}
