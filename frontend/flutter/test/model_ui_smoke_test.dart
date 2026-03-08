import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:provider/provider.dart';
import 'package:memscreen_flutter/api/chat_api.dart';
import 'package:memscreen_flutter/api/model_api.dart';
import 'package:memscreen_flutter/api/recording_api.dart';
import 'package:memscreen_flutter/api/api_client.dart';
import 'package:memscreen_flutter/build_info.dart';
import 'package:memscreen_flutter/app_state.dart';
import 'package:memscreen_flutter/config/api_config.dart';
import 'package:memscreen_flutter/connection/connection_state.dart';
import 'package:memscreen_flutter/screens/chat_screen.dart';
import 'package:memscreen_flutter/screens/settings_screen.dart';
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

class FakeChatApi extends ChatApi {
  FakeChatApi(this._currentModel, this._availableModels)
      : super(ApiClient(config: ApiConfig(baseUrl: 'http://127.0.0.1:0')));

  String _currentModel;
  final List<String> _availableModels;

  @override
  Future<List<String>> getModels() async => _availableModels;

  @override
  Future<String?> getCurrentModel() async => _currentModel;

  @override
  Future<void> setModel(String model) async {
    _currentModel = model;
  }

  @override
  Future<ChatThreadState> getThreads() async {
    return ChatThreadState(
      activeThreadId: 't1',
      threads: [
        ChatThreadSummary(
          id: 't1',
          title: 'Model demo',
          preview: 'hello',
          createdAt: '2026-03-08 10:00:00',
          updatedAt: '2026-03-08 10:05:00',
          messageCount: 1,
          isActive: true,
        ),
      ],
    );
  }

  @override
  Future<List<ChatHistoryMessage>> getHistory({String? threadId}) async {
    return [
      ChatHistoryMessage(
        role: 'assistant',
        content: 'Hi there',
        timestamp: '2026-03-08 10:05:00',
      ),
    ];
  }
}

class FakeAppState extends AppState {
  FakeAppState({
    required LocalModelCatalog catalog,
    required bool backendConnected,
  })  : _catalog = catalog,
        _backendConnected = backendConnected,
        _chatApi = FakeChatApi(
          catalog.currentChatModel ?? '',
          catalog.availableChatModels,
        ),
        super();

  LocalModelCatalog _catalog;
  final bool _backendConnected;
  final FakeChatApi _chatApi;
  int _chatModelRefreshVersionValue = 0;

  @override
  bool get isBackendConnected => _backendConnected;

  @override
  ApiConnectionState get connectionState => ApiConnectionState(
        status: _backendConnected
            ? ConnectionStatus.connected
            : ConnectionStatus.error,
        message: _backendConnected ? null : 'Backend not connected',
      );

  @override
  Future<RecordingStatus> loadRecordingStatusForUi() async {
    return RecordingStatus(
      isRecording: false,
      duration: 2,
      interval: 2.0,
      outputDir: '/Users/test/.memscreen/videos',
      frameCount: 0,
      elapsedTime: 0,
      mode: 'fullscreen',
      lastFailureKind: 'permission_denied',
      lastFailureMessage: 'Screen Recording permission is required.',
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 0,
      lastTerminationStatus: 1,
      lastNotice: 'Permission: Screen Recording access is still not active.',
    );
  }

  @override
  Future<List<RecordingScreenInfo>> loadAvailableScreensForUi() async {
    return [
      RecordingScreenInfo(
        index: 0,
        name: 'Main',
        width: 1,
        height: 1,
        isPrimary: true,
        displayId: 1,
      ),
    ];
  }

  @override
  Future<void> syncRecordingStateFromBackend(bool isRecording) async {}

  @override
  ChatApi get chatApi => _chatApi;

  @override
  int get chatModelRefreshVersion => _chatModelRefreshVersionValue;

  @override
  Future<void> refreshPermissionStatus({bool promptSystem = false}) async {}

  @override
  Future<LocalModelCatalog> loadLocalModelCatalogForUi({
    bool forceRefresh = false,
  }) async {
    return _catalog;
  }

  @override
  Future<SettingsModelSection> loadSettingsModelSectionForUi({
    bool forceRefresh = false,
  }) async {
    return buildSettingsModelSection(_catalog);
  }

  @override
  Future<ChatModelSelection> loadChatModelSelectionForUi({
    bool forceRefresh = false,
  }) async {
    return buildChatModelSelection(_catalog);
  }

  Future<List<String>> loadChatModelsForUi() async =>
      _catalog.availableChatModels;

  Future<String?> loadCurrentChatModelForUi() async =>
      _catalog.currentChatModel;

  @override
  Future<LocalModelCatalog> setChatModelForUi(String modelName) async {
    _chatApi.setModel(modelName);
    _catalog = markCurrentChatModel(_catalog, modelName);
    _chatModelRefreshVersionValue += 1;
    notifyListeners();
    return _catalog;
  }

  @override
  Future<LocalModelCatalog> downloadLocalModelForUi(
    String modelName, {
    Duration timeout = const Duration(minutes: 45),
  }) async {
    _catalog = markDownloadedModel(_catalog, modelName);
    _chatModelRefreshVersionValue += 1;
    notifyListeners();
    return _catalog;
  }

  @override
  Future<String> runRecordingSmokeCheck({
    int? screenIndex,
    int? screenDisplayId,
  }) async {
    markRecordingSmokeCheckStarted();
    const summary = 'Smoke check: 2-second recording test started.';
    return summary;
  }
}

Widget wrapWithScaffold(AppState appState, Widget child) {
  return ChangeNotifierProvider<AppState>.value(
    value: appState,
    child: MaterialApp(
      home: Scaffold(body: child),
    ),
  );
}

Widget wrapAsHome(AppState appState, Widget child) {
  return ChangeNotifierProvider<AppState>.value(
    value: appState,
    child: MaterialApp(home: child),
  );
}

void main() {
  setUpAll(() {
    PackageInfo.setMockInitialValues(
      appName: 'MemScreen',
      packageName: 'com.memscreen.test',
      version: '0.6.3',
      buildNumber: '1',
      buildSignature: '',
    );
  });

  testWidgets('Chat screen shows current and recommended model actions',
      (tester) async {
    final catalog = makeCatalog(
      currentChatModel: 'qwen3.5:2b',
      recommendedChatModel: 'qwen3.5:4b',
      availableChatModels: const ['qwen3.5:4b', 'qwen3.5:2b', 'qwen3.5:0.8b'],
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
          name: 'qwen3.5:2b',
          installedName: 'qwen3.5:2b',
          sizeLabel: '2b',
          recommendedUse: 'fast',
          supportsVision: true,
        ),
        makeEntry(
          name: 'qwen3.5:0.8b',
          installedName: 'qwen3.5:0.8b',
          sizeLabel: '0.8b',
          recommendedUse: 'ultra_light',
          supportsVision: true,
        ),
      ],
    );

    final appState = FakeAppState(catalog: catalog, backendConnected: true);
    await tester.pumpWidget(wrapWithScaffold(appState, const ChatScreen()));
    await tester.pumpAndSettle();

    expect(find.text('qwen3.5:2b'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.tune));
    await tester.pumpAndSettle();

    expect(find.text('Current: qwen3.5:2b'), findsOneWidget);
    expect(find.text('Recommended: qwen3.5:4b'), findsOneWidget);
    expect(find.text('Use recommended'), findsOneWidget);
    expect(find.text('Recommended'), findsWidgets);
  });

  testWidgets('Settings screen shows grouped model recommendations',
      (tester) async {
    final catalog = makeCatalog(
      currentChatModel: 'qwen3.5:2b',
      recommendedChatModel: 'qwen3.5:4b',
      availableChatModels: const ['qwen3.5:4b', 'qwen3.5:2b', 'qwen3.5:0.8b'],
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
          name: 'qwen3.5:2b',
          installedName: 'qwen3.5:2b',
          sizeLabel: '2b',
          recommendedUse: 'fast',
          supportsVision: true,
        ),
        makeEntry(
          name: 'qwen3.5:0.8b',
          installedName: 'qwen3.5:0.8b',
          sizeLabel: '0.8b',
          recommendedUse: 'ultra_light',
          supportsVision: true,
        ),
      ],
    );

    final appState = FakeAppState(catalog: catalog, backendConnected: true);
    await tester.pumpWidget(wrapAsHome(appState, const SettingsScreen()));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    await tester.drag(find.byType(ListView).first, const Offset(0, -600));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Recommended chat model: qwen3.5:4b'), findsOneWidget);
    expect(find.text('Use recommended'), findsOneWidget);
    expect(find.text('Recommended'), findsWidgets);
    expect(find.text('Fast / Light'), findsOneWidget);
    expect(find.textContaining('Model storage (external):'), findsOneWidget);

    final useRecommended = find.text('Use recommended').first;
    await tester.ensureVisible(useRecommended);
    await tester.pump();
    await tester.tap(useRecommended, warnIfMissed: false);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Current chat model: qwen3.5:4b'), findsOneWidget);
  });

  testWidgets('Settings screen shows recording diagnostics actions',
      (tester) async {
    BuildInfo.debugBundlePathOverride = '/Users/test/Downloads/MemScreen.app';
    addTearDown(() => BuildInfo.debugBundlePathOverride = null);

    final catalog = makeCatalog(
      currentChatModel: 'qwen3.5:2b',
      recommendedChatModel: 'qwen3.5:4b',
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
      ],
    );

    final appState = FakeAppState(catalog: catalog, backendConnected: true);
    await tester.pumpWidget(wrapAsHome(appState, const SettingsScreen()));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    await tester.drag(find.byType(ListView).first, const Offset(0, -400));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Recording diagnostics'), findsOneWidget);
    expect(find.text('Run smoke check'), findsOneWidget);
    expect(find.text('Open output'), findsOneWidget);
    expect(find.text('Open logs'), findsOneWidget);
    expect(find.text('Copy'), findsWidgets);
    expect(find.byIcon(Icons.install_desktop_outlined), findsWidgets);
    expect(find.byIcon(Icons.bug_report_outlined), findsWidgets);
  });
}
