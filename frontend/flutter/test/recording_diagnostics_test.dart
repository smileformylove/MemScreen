import 'package:flutter_test/flutter_test.dart';
import 'package:memscreen_flutter/build_info.dart';
import 'package:memscreen_flutter/services/recording_diagnostics.dart';
import 'package:memscreen_flutter/widgets/recording_diagnostics_panel.dart';

void main() {
  test(
      'recording diagnostics builder includes install advice for nonstandard path',
      () {
    BuildInfo.debugBundlePathOverride = '/Users/test/Downloads/MemScreen.app';
    addTearDown(() => BuildInfo.debugBundlePathOverride = null);

    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: false,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      engine: 'Native macOS recorder',
      target: 'All screens',
      lastResult: 'Permission: Screen Recording access is still not active.',
      lastResultLevel: RecordingDiagnosticsNoticeLevel.error,
      lastFailureKind: 'permission_denied',
      lastFailureMessage: 'Screen Recording permission is required.',
      lastExitStatus: 1,
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 0,
    );

    expect(data.installStatus, 'Nonstandard path');
    expect(data.advice, isNotNull);

    final report = buildRecordingDiagnosticsReport(data);
    expect(report, contains('install_status: Nonstandard path'));
    expect(report, contains('last_failure_kind: permission_denied'));
    expect(report, contains('last_exit_status: 1'));
    expect(report, contains('logs_dir:'));
  });
  test(
      'recording diagnostics advice prioritizes permission over generic failures',
      () {
    BuildInfo.debugBundlePathOverride = '/Applications/MemScreen.app';
    addTearDown(() => BuildInfo.debugBundlePathOverride = null);

    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: false,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastFailureKind: 'no_output',
      lastFailureMessage:
          'Native recording finished without creating a playable video file.',
    );

    expect(data.installStatus, 'Applications');
    expect(data.advice, contains('fully quit and reopen MemScreen'));
  });

  test('recording diagnostics advice explains empty output failures', () {
    BuildInfo.debugBundlePathOverride = '/Applications/MemScreen.app';
    addTearDown(() => BuildInfo.debugBundlePathOverride = null);

    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastFailureKind: 'empty_output',
      lastFailureMessage: 'Recording ended, but the saved file was empty.',
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 0,
    );

    expect(data.advice, contains('zero-byte file'));
  });
}
