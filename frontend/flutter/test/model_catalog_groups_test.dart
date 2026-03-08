import 'package:flutter_test/flutter_test.dart';
import 'package:memscreen_flutter/api/model_api.dart';
import 'package:memscreen_flutter/services/model_catalog_groups.dart';

LocalModelEntry makeEntry({
  required String name,
  String purpose = 'Test',
  bool required = false,
  bool installed = true,
  String? installedName,
  String family = 'qwen3.5',
  String? sizeLabel,
  bool supportsChat = true,
  bool supportsVision = false,
  String recommendedUse = 'general',
  bool chatSelectable = true,
  bool recommendedChatDefault = false,
}) {
  return LocalModelEntry(
    name: name,
    purpose: purpose,
    required: required,
    installed: installed,
    installedName: installedName,
    family: family,
    sizeLabel: sizeLabel,
    supportsChat: supportsChat,
    supportsVision: supportsVision,
    recommendedUse: recommendedUse,
    chatSelectable: chatSelectable,
    recommendedChatDefault: recommendedChatDefault,
  );
}

LocalModelCatalog makeCatalog({
  String? currentChatModel,
  String? recommendedChatModel,
  List<String> availableChatModels = const <String>[],
  required List<LocalModelEntry> models,
}) {
  return LocalModelCatalog(
    baseUrl: 'http://127.0.0.1:11434',
    modelsDir: '/Volumes/TestDrive/models/ollama',
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
  test('computeRecommendedChatModel prefers balanced qwen3.5 model', () {
    final catalog = makeCatalog(
      currentChatModel: 'qwen3.5:2b',
      availableChatModels: const ['qwen3.5:2b', 'qwen3.5:4b', 'qwen3.5:9b'],
      models: [
        makeEntry(
          name: 'qwen3.5:2b',
          installedName: 'qwen3.5:2b',
          sizeLabel: '2b',
          recommendedUse: 'fast',
        ),
        makeEntry(
          name: 'qwen3.5:4b',
          installedName: 'qwen3.5:4b',
          sizeLabel: '4b',
          recommendedUse: 'balanced',
          supportsVision: true,
        ),
        makeEntry(
          name: 'qwen3.5:9b',
          installedName: 'qwen3.5:9b',
          sizeLabel: '9b',
          recommendedUse: 'advanced',
        ),
      ],
    );

    expect(computeRecommendedChatModel(catalog), 'qwen3.5:4b');
  });

  test('markDownloadedModel updates installed and recommended flags locally',
      () {
    final catalog = makeCatalog(
      availableChatModels: const ['qwen3.5:2b'],
      models: [
        makeEntry(
          name: 'qwen3.5:2b',
          installedName: 'qwen3.5:2b',
          sizeLabel: '2b',
          recommendedUse: 'fast',
          recommendedChatDefault: true,
        ),
        makeEntry(
          name: 'qwen3.5:4b',
          installed: false,
          sizeLabel: '4b',
          recommendedUse: 'balanced',
          supportsVision: true,
          chatSelectable: false,
        ),
      ],
    );

    final updated = markDownloadedModel(catalog, 'qwen3.5:4b');
    final downloaded = updated.models.firstWhere((m) => m.name == 'qwen3.5:4b');

    expect(downloaded.installed, isTrue);
    expect(downloaded.installedName, 'qwen3.5:4b');
    expect(downloaded.chatSelectable, isTrue);
    expect(updated.availableChatModels, contains('qwen3.5:4b'));
    expect(updated.recommendedChatModel, 'qwen3.5:4b');
    expect(downloaded.recommendedChatDefault, isTrue);
  });

  test('buildCatalogModelGroups separates recommended fast and vision groups',
      () {
    final groups = buildCatalogModelGroups([
      makeEntry(
        name: 'qwen3.5:4b',
        sizeLabel: '4b',
        recommendedUse: 'balanced',
        recommendedChatDefault: true,
        supportsVision: true,
      ),
      makeEntry(
        name: 'qwen3.5:0.8b',
        sizeLabel: '0.8b',
        recommendedUse: 'ultra_light',
      ),
      makeEntry(
        name: 'qwen3-vl:4b',
        family: 'qwen3-vl',
        sizeLabel: '4b',
        recommendedUse: 'vision_fallback',
        supportsVision: true,
      ),
      makeEntry(
        name: 'gemma2:9b',
        family: 'other',
        sizeLabel: '9b',
        recommendedUse: 'general',
        supportsVision: false,
      ),
    ]);

    expect(
        groups.map((g) => g.label),
        containsAll(<String>[
          'Recommended',
          'Fast / Light',
          'Vision / Multimodal',
          'Other',
        ]));
    expect(
        groups.firstWhere((g) => g.label == 'Recommended').entries.single.name,
        'qwen3.5:4b');
    expect(
        groups.firstWhere((g) => g.label == 'Fast / Light').entries.single.name,
        'qwen3.5:0.8b');
  });

  test('catalog helper rules resolve current and chat-usable entries', () {
    final catalog = makeCatalog(
      currentChatModel: 'qwen3.5:4b',
      availableChatModels: const ['qwen3.5:4b', 'qwen3.5:2b'],
      models: [
        makeEntry(
          name: 'qwen3.5:4b',
          installedName: 'qwen3.5:4b',
          sizeLabel: '4b',
          recommendedUse: 'balanced',
          supportsVision: true,
          recommendedChatDefault: true,
        ),
        makeEntry(
          name: 'mxbai-embed-large',
          installedName: 'mxbai-embed-large',
          family: 'embedding',
          supportsChat: false,
          supportsVision: false,
          recommendedUse: 'embedding',
          chatSelectable: false,
        ),
      ],
    );

    final currentEntry = findCatalogEntryByModelName(catalog, 'qwen3.5:4b');
    final embeddingEntry =
        findCatalogEntryByModelName(catalog, 'mxbai-embed-large');

    expect(currentEntry, isNotNull);
    expect(isCurrentCatalogEntry(catalog, currentEntry!), isTrue);
    expect(canUseCatalogEntryForChat(catalog, currentEntry), isTrue);
    expect(embeddingEntry, isNotNull);
    expect(canUseCatalogEntryForChat(catalog, embeddingEntry!), isFalse);
  });
  test('buildChatModelSelection maps installed aliases to entry details', () {
    final catalog = makeCatalog(
      currentChatModel: 'qwen3.5:4b',
      recommendedChatModel: 'qwen3.5:4b',
      availableChatModels: const ['qwen3.5:4b'],
      models: [
        makeEntry(
          name: 'qwen3.5:4b',
          installedName: 'qwen3.5:4b',
          sizeLabel: '4b',
          recommendedUse: 'balanced',
          supportsVision: true,
          recommendedChatDefault: true,
        ),
      ],
    );

    final selection = buildChatModelSelection(catalog);
    expect(selection.currentModel, 'qwen3.5:4b');
    expect(selection.recommendedModel, 'qwen3.5:4b');
    expect(
        selection.detailsByModel['qwen3.5:4b']?.recommendedChatDefault, isTrue);
  });
}
