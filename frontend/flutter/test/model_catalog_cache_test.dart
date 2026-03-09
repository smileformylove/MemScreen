import 'package:flutter_test/flutter_test.dart';
import 'package:memscreen_flutter/api/model_api.dart';
import 'package:memscreen_flutter/services/model_catalog_cache.dart';

LocalModelEntry _entry({
  required String name,
  bool installed = true,
  String? installedName,
  bool supportsChat = true,
  String recommendedUse = 'general',
  bool chatSelectable = true,
  bool recommendedChatDefault = false,
}) {
  return LocalModelEntry(
    name: name,
    purpose: 'Test',
    required: false,
    installed: installed,
    installedName: installedName,
    family: 'qwen3.5',
    sizeLabel: '4b',
    supportsChat: supportsChat,
    supportsVision: false,
    recommendedUse: recommendedUse,
    chatSelectable: chatSelectable,
    recommendedChatDefault: recommendedChatDefault,
  );
}

LocalModelCatalog _catalog({
  String? currentChatModel,
  String? recommendedChatModel,
  List<String> availableChatModels = const <String>[],
  required List<LocalModelEntry> models,
}) {
  return LocalModelCatalog(
    baseUrl: 'http://127.0.0.1:11434',
    modelsDir: '/tmp/models',
    modelsDirExternal: true,
    currentChatModel: currentChatModel,
    recommendedChatModel: recommendedChatModel,
    availableChatModels: availableChatModels,
    runtimeReady: true,
    runtimeError: null,
    modelsDisabled: false,
    models: models,
  );
}

void main() {
  test('returns cached snapshot while within TTL window', () {
    final cache = ModelCatalogCache(ttl: const Duration(seconds: 10));
    final now = DateTime(2026, 3, 9, 12, 0, 0);
    final catalog = _catalog(
      currentChatModel: 'qwen3.5:2b',
      availableChatModels: const <String>['qwen3.5:2b'],
      models: [_entry(name: 'qwen3.5:2b', installedName: 'qwen3.5:2b')],
    );
    cache.store(catalog, at: now);

    final cached = cache.readFresh(now.add(const Duration(seconds: 9)));

    expect(cached, isNotNull);
    expect(cached!.currentChatModel, 'qwen3.5:2b');
  });

  test('expires cached snapshot after TTL window', () {
    final cache = ModelCatalogCache(ttl: const Duration(seconds: 10));
    final now = DateTime(2026, 3, 9, 12, 0, 0);
    cache.store(
      _catalog(
        currentChatModel: 'qwen3.5:2b',
        availableChatModels: const <String>['qwen3.5:2b'],
        models: [_entry(name: 'qwen3.5:2b', installedName: 'qwen3.5:2b')],
      ),
      at: now,
    );

    final cached = cache.readFresh(now.add(const Duration(seconds: 11)));

    expect(cached, isNull);
  });

  test('marks current chat model in cached snapshot', () {
    final cache = ModelCatalogCache(ttl: const Duration(seconds: 10));
    cache.store(
      _catalog(
        currentChatModel: 'qwen3.5:2b',
        availableChatModels: const <String>['qwen3.5:2b', 'qwen3.5:4b'],
        models: [
          _entry(
            name: 'qwen3.5:2b',
            installedName: 'qwen3.5:2b',
            recommendedUse: 'fast',
          ),
          _entry(
            name: 'qwen3.5:4b',
            installedName: 'qwen3.5:4b',
            recommendedUse: 'balanced',
          ),
        ],
      ),
    );

    cache.markCurrentChatModel('qwen3.5:4b');
    final snapshot = cache.snapshot;

    expect(snapshot, isNotNull);
    expect(snapshot!.currentChatModel, 'qwen3.5:4b');
    expect(snapshot.recommendedChatModel, 'qwen3.5:4b');
  });

  test('marks downloaded model and updates available chat models', () {
    final cache = ModelCatalogCache(ttl: const Duration(seconds: 10));
    cache.store(
      _catalog(
        availableChatModels: const <String>['qwen3.5:2b'],
        models: [
          _entry(
            name: 'qwen3.5:2b',
            installedName: 'qwen3.5:2b',
            recommendedUse: 'fast',
          ),
          _entry(
            name: 'qwen3.5:4b',
            installed: false,
            chatSelectable: false,
            recommendedUse: 'balanced',
          ),
        ],
      ),
    );

    cache.markDownloadedModel('qwen3.5:4b');
    final snapshot = cache.snapshot;

    expect(snapshot, isNotNull);
    expect(snapshot!.availableChatModels, contains('qwen3.5:4b'));
    final downloaded =
        snapshot.models.firstWhere((m) => m.name == 'qwen3.5:4b');
    expect(downloaded.installed, isTrue);
    expect(downloaded.chatSelectable, isTrue);
  });
}
