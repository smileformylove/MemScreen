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

void main() {
  testWidgets('Recording screen shows diagnostics summary controls',
      (tester) async {
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
        child: const MaterialApp(home: RecordingScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Recording diagnostics'), findsOneWidget);
    expect(find.text('Capture target'), findsOneWidget);
    expect(find.text('Start recording here'), findsOneWidget);
    expect(find.text('Ready here'), findsOneWidget);
    expect(find.text('Pick region'), findsOneWidget);
    expect(find.text('Pick window'), findsOneWidget);
    expect(find.text('Ready to record'), findsOneWidget);
    expect(find.text('Starts immediately from this page.'), findsOneWidget);
    expect(find.textContaining('Mode:'), findsWidgets);
    expect(find.textContaining('Flow:'), findsWidgets);
    expect(find.textContaining('Target:'), findsWidgets);
    expect(find.byIcon(Icons.commit), findsWidgets);
    expect(find.byIcon(Icons.videocam_outlined), findsWidgets);
    expect(find.byIcon(Icons.bug_report_outlined), findsWidgets);
    expect(find.byIcon(Icons.terminal), findsWidgets);
    expect(find.byIcon(Icons.insert_drive_file_outlined), findsWidgets);
    expect(find.text('Run smoke check'), findsOneWidget);
    expect(find.text('Open output'), findsOneWidget);
    expect(find.text('Open logs'), findsOneWidget);
    expect(find.text('Open last output'), findsOneWidget);
    expect(find.text('Reveal in Finder'), findsOneWidget);
    expect(find.text('Copy brief'), findsOneWidget);
    expect(find.text('Copy full'), findsOneWidget);
    expect(find.text('Refresh'), findsOneWidget);
    expect(find.byIcon(Icons.install_desktop_outlined), findsWidgets);
  });
}
