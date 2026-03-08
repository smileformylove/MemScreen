import 'package:flutter_test/flutter_test.dart';
import 'package:memscreen_flutter/api/api_client.dart';
import 'package:memscreen_flutter/app_state.dart';

class FakeSmokeCheckAppState extends AppState {
  FakeSmokeCheckAppState({required this.permissionGranted, this.startError})
      : super();

  final bool permissionGranted;
  final Object? startError;
  bool prompted = false;
  int startCalls = 0;
  int? lastScreenIndex;
  int? lastScreenDisplayId;

  @override
  bool get enforcesScreenRecordingPermissionFlow => true;

  @override
  bool get hasScreenRecordingPermission => permissionGranted;

  @override
  Future<void> promptScreenRecordingPermissionFlow() async {
    prompted = true;
  }

  @override
  Future<void> startRecording({
    required int duration,
    required double interval,
    String? mode,
    List<double>? region,
    int? screenIndex,
    int? screenDisplayId,
    String? windowTitle,
  }) async {
    startCalls += 1;
    lastScreenIndex = screenIndex;
    lastScreenDisplayId = screenDisplayId;
    if (startError != null) {
      throw startError!;
    }
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('runRecordingSmokeCheck prompts when screen permission is missing',
      () async {
    final appState = FakeSmokeCheckAppState(permissionGranted: false);

    final summary = await appState.runRecordingSmokeCheck(
      screenIndex: 2,
      screenDisplayId: 99,
    );

    expect(appState.prompted, isTrue);
    expect(appState.startCalls, 0);
    expect(appState.recordingSmokeCheckInProgress, isFalse);
    expect(appState.lastRecordingSmokeCheckSummary, summary);
    expect(summary, contains('still not active'));
    expect(appState.consumePendingRecordingNotice(), summary);
  });

  test(
      'runRecordingSmokeCheck starts recording and leaves shared state running',
      () async {
    final appState = FakeSmokeCheckAppState(permissionGranted: true);

    final summary = await appState.runRecordingSmokeCheck(
      screenIndex: 1,
      screenDisplayId: 7,
    );

    expect(appState.prompted, isFalse);
    expect(appState.startCalls, 1);
    expect(appState.lastScreenIndex, 1);
    expect(appState.lastScreenDisplayId, 7);
    expect(appState.recordingSmokeCheckInProgress, isTrue);
    expect(summary, contains('2-second recording test has started'));
    expect(appState.consumePendingRecordingNotice(), summary);
  });

  test('runRecordingSmokeCheck records friendly start failures', () async {
    final appState = FakeSmokeCheckAppState(
      permissionGranted: true,
      startError: ApiException('Screen Recording permission is required.'),
    );

    final summary = await appState.runRecordingSmokeCheck();

    expect(appState.startCalls, 1);
    expect(appState.recordingSmokeCheckInProgress, isFalse);
    expect(appState.lastRecordingSmokeCheckSummary, summary);
    expect(summary, contains('Smoke check failed to start'));
    expect(summary, contains('Screen Recording permission is missing'));
    expect(appState.consumePendingRecordingNotice(), summary);
  });
}
