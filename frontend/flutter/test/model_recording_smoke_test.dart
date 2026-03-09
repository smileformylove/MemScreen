import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:memscreen_flutter/api/recording_api.dart';
import 'package:memscreen_flutter/build_info.dart';
import 'package:memscreen_flutter/app_state.dart';
import 'package:memscreen_flutter/connection/connection_state.dart';
import 'package:memscreen_flutter/screens/recording_screen.dart';

class FakeRecordingAppState extends AppState {
  FakeRecordingAppState() : super();

  @override
  bool get hasScreenRecordingPermission => true;

  @override
  bool get useNativeMacOSRecording => true;

  @override
  int get currentTabIndex => 0;

  @override
  ApiConnectionState get connectionState => ApiConnectionState(
        status: ConnectionStatus.connected,
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
  Future<void> refreshPermissionStatus({bool promptSystem = false}) async {}

  @override
  Future<void> openPermissionSettings(String area) async {}

  @override
  String? consumePendingRecordingNotice() {
    return null;
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

class FakePermissionBlockedAppState extends FakeRecordingAppState {
  @override
  bool get hasScreenRecordingPermission => false;

  @override
  Map<String, dynamic>? get permissionStatus => {
        'runtime_executable':
            '/Users/test/Library/Application Support/MemScreen/runtime/bin/python',
        'app_bundle_hint': '/Users/test/Applications/MemScreen.app',
        'screen_recording': {'granted': false},
      };
}

void main() {
  testWidgets('Recording screen keeps primary flow minimal', (tester) async {
    tester.view.physicalSize = const Size(1600, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    BuildInfo.debugBundlePathOverride = '/Users/test/Downloads/MemScreen.app';
    addTearDown(() => BuildInfo.debugBundlePathOverride = null);
    final appState = FakeRecordingAppState();
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          theme: ThemeData(platform: TargetPlatform.macOS),
          home: const RecordingScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Screen Recording'), findsOneWidget);
    expect(find.text('Start Recording'), findsOneWidget);
    expect(find.text('Display target'), findsOneWidget);
    expect(find.text('Troubleshooting (Advanced)'), findsNothing);
    expect(find.byIcon(Icons.fiber_manual_record), findsOneWidget);
  });

  testWidgets('Recording screen shows explicit permission paths when blocked',
      (tester) async {
    final appState = FakePermissionBlockedAppState();
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          theme: ThemeData(platform: TargetPlatform.macOS),
          home: const RecordingScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(
        find.text('Screen Recording permission is required.'), findsOneWidget);
    expect(find.textContaining('/Users/test/Library/Application Support'),
        findsOneWidget);
    expect(find.text('Open Permission Flow'), findsOneWidget);
    expect(find.text('I Granted, Recheck'), findsOneWidget);
  });
}
