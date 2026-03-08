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
      transientNotice:
          'Permission: Screen Recording access is still not active.',
      transientNoticeLevel: RecordingDiagnosticsNoticeLevel.error,
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

  test('recording diagnostics advice explains import warnings separately', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      statusNotice:
          'Import warning: Recording saved locally, but adding it to Videos failed.',
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
    );

    expect(data.advice, contains('saved locally'));
  });

  test('recording diagnostics advice uses exit status for no-output failures',
      () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastFailureKind: 'no_output',
      lastExitStatus: 1,
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
    );

    expect(data.advice, contains('Exit status 1'));
  });

  test('recording diagnostics advice highlights zero-byte output paths', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastFailureKind: 'empty_output',
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 0,
    );

    expect(data.advice, contains('last output path'));
  });

  test('recording last output status shows saved size when bytes are present',
      () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 1536,
    );

    expect(data.lastOutputStatus, 'Saved · 1.5 KB');
    expect(data.lastOutputStatusLevel, RecordingDiagnosticsNoticeLevel.info);
  });

  test('recording last output status highlights zero-byte files', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastFailureKind: 'empty_output',
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 0,
    );

    expect(data.lastOutputStatus, 'Zero-byte file');
    expect(data.lastOutputStatusLevel, RecordingDiagnosticsNoticeLevel.warning);

    final report = buildRecordingDiagnosticsReport(data);
    expect(report, contains('last_output_status: Zero-byte file'));
  });

  test('recording problem summary prioritizes permission blockers', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: false,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastFailureKind: 'permission_denied',
    );

    expect(data.problemSummary, 'Blocked by Screen Recording permission.');
    expect(data.problemSummaryLevel, RecordingDiagnosticsNoticeLevel.error);
  });

  test('recording problem summary explains saved local import warnings', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      statusNotice:
          'Import warning: Recording saved locally, but adding it to Videos failed.',
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 2048,
    );

    expect(
      data.problemSummary,
      'Recording saved locally; Videos import is still pending.',
    );
    expect(data.problemSummaryLevel, RecordingDiagnosticsNoticeLevel.warning);

    final report = buildRecordingDiagnosticsReport(data);
    expect(
      report,
      contains(
          'problem_summary: Recording saved locally; Videos import is still pending.'),
    );
  });

  test('recording problem summary falls back to output health', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 1536,
    );

    expect(data.problemSummary, 'Latest output: Saved · 1.5 KB.');
    expect(data.problemSummaryLevel, RecordingDiagnosticsNoticeLevel.info);
  });

  test('recording next step points to restart when permission is blocked', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: false,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastFailureKind: 'permission_denied',
    );

    expect(
      data.nextStep,
      'Quit MemScreen fully, reopen it, then run Smoke check again.',
    );
    expect(data.nextStepLevel, RecordingDiagnosticsNoticeLevel.error);
  });

  test('recording next step points to backend retry for import warnings', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      statusNotice:
          'Import warning: Recording saved locally, but adding it to Videos failed.',
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 2048,
    );

    expect(
      data.nextStep,
      'Open Videos later or reconnect the backend to finish import.',
    );
    expect(data.nextStepLevel, RecordingDiagnosticsNoticeLevel.warning);
  });

  test('recording next step falls back to verifying saved output', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 1536,
    );

    expect(
      data.nextStep,
      'Open the last output file and verify it plays back correctly.',
    );
    expect(data.nextStepLevel, RecordingDiagnosticsNoticeLevel.info);

    final report = buildRecordingDiagnosticsReport(data);
    expect(
      report,
      contains(
          'next_step: Open the last output file and verify it plays back correctly.'),
    );
  });

  test('ordered action labels prioritize screen permission first', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: false,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastFailureKind: 'permission_denied',
    );

    final labels = orderedRecordingDiagnosticsActionLabels(
      data,
      availableActionLabels: const [
        'Run smoke check',
        'Open logs',
        'Open Screen Recording',
      ],
    );

    expect(labels.first, 'Open Screen Recording');
  });

  test('ordered action labels prioritize last output playback when relevant',
      () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 1536,
    );

    final labels = orderedRecordingDiagnosticsActionLabels(
      data,
      availableActionLabels: const [
        'Run smoke check',
        'Open last output',
        'Open logs',
      ],
    );

    expect(labels.first, 'Open last output');
  });

  test('ordered action labels prioritize logs for native recorder failures',
      () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastFailureKind: 'recorder_error',
      lastExitStatus: 1,
    );

    final labels = orderedRecordingDiagnosticsActionLabels(
      data,
      availableActionLabels: const [
        'Run smoke check',
        'Open logs',
        'Open output',
      ],
    );

    expect(labels.first, 'Open logs');
  });
  test('recording diagnostics brief prioritizes summary and next step', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: false,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastFailureKind: 'permission_denied',
    );

    final brief = buildRecordingDiagnosticsBrief(data);
    expect(brief, contains('Summary: Blocked by Screen Recording permission.'));
    expect(
      brief,
      contains(
          'Next: Quit MemScreen fully, reopen it, then run Smoke check again.'),
    );
  });

  test('recording diagnostics report starts with brief summary', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
      lastOutputFileSize: 1536,
    );

    final report = buildRecordingDiagnosticsReport(data).split('\n');
    expect(report[0], 'MemScreen recording diagnostics');
    expect(report[1], contains('Summary: Latest output: Saved · 1.5 KB.'));
  });
  test('recording diagnostics summary falls back to native failure mapping',
      () {
    final summary = recordingDiagnosticsSummary(
      isRecording: false,
      lastFailureKind: 'no_output',
      lastFailureMessage: 'No playable video file created.',
    );

    expect(summary, isNotNull);
    expect(summary!.level, RecordingDiagnosticsNoticeLevel.error);
    expect(summary.message, contains('No file:'));
  });

  test('recording diagnostics summary treats import warnings as warning', () {
    final summary = recordingDiagnosticsSummary(
      isRecording: false,
      statusNotice:
          'Import warning: Recording saved locally, but adding it to Videos failed.',
    );

    expect(summary, isNotNull);
    expect(summary!.level, RecordingDiagnosticsNoticeLevel.warning);
    expect(summary.message, contains('Import warning:'));
  });

  test('recording diagnostics builder uses shared status notice fallback', () {
    final data = buildRecordingDiagnosticsData(
      screenRecordingGranted: true,
      outputDir: '/Users/test/.memscreen/videos',
      isRecording: false,
      statusNotice:
          'Import warning: Recording saved locally, but adding it to Videos failed.',
      lastOutputPath: '/Users/test/.memscreen/videos/native_test.mov',
    );

    expect(data.lastResult,
        'Import warning: Recording saved locally, but adding it to Videos failed.');
    expect(data.lastResultLevel, RecordingDiagnosticsNoticeLevel.warning);
  });
}
