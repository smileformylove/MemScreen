import 'dart:io';

import '../build_info.dart';
import '../widgets/recording_diagnostics_panel.dart';

enum RecordingInstallStatus { applications, nonstandard, unknown }

String recordingLogsDirPath() {
  return '${Platform.environment['HOME'] ?? '~'}/.memscreen/logs';
}

String recordingDefaultOutputDir() {
  return '${Platform.environment['HOME'] ?? '~'}/.memscreen/videos';
}

RecordingInstallStatus detectRecordingInstallStatus() {
  final appPath = BuildInfo.detectAppBundlePath() ?? '';
  if (appPath.isEmpty) {
    return RecordingInstallStatus.unknown;
  }
  if (appPath.startsWith('/Applications/')) {
    return RecordingInstallStatus.applications;
  }
  return RecordingInstallStatus.nonstandard;
}

String recordingInstallStatusLabel() {
  switch (detectRecordingInstallStatus()) {
    case RecordingInstallStatus.applications:
      return 'Applications';
    case RecordingInstallStatus.nonstandard:
      return 'Nonstandard path';
    case RecordingInstallStatus.unknown:
      return 'Unknown';
  }
}

String? recordingInstallAdvice() {
  return detectRecordingInstallStatus() == RecordingInstallStatus.nonstandard
      ? 'Install the latest MemScreen.app into /Applications before testing recording.'
      : null;
}

String? recordingDiagnosticsAdvice({
  required bool screenRecordingGranted,
  String? lastFailureKind,
  String? lastFailureMessage,
}) {
  final installAdvice = recordingInstallAdvice();
  if (installAdvice != null) {
    return installAdvice;
  }
  if (!screenRecordingGranted || lastFailureKind == 'permission_denied') {
    return 'Grant Screen Recording permission, then fully quit and reopen MemScreen before trying again.';
  }
  switch ((lastFailureKind ?? '').trim()) {
    case 'cancelled':
      return 'The recording was cancelled before a file was written. Retry the smoke check and avoid dismissing the system capture flow.';
    case 'empty_output':
      return 'A zero-byte file was created. Retry the smoke check, then inspect the output folder and logs if it happens again.';
    case 'no_output':
      return 'No playable video file was created. Run the smoke check again and compare the exit status and last output path.';
    case 'recorder_error':
      if ((lastFailureMessage ?? '').trim().isNotEmpty) {
        return 'Recorder error detected. Open logs and check the native failure details before retrying.';
      }
      return 'Recorder error detected. Open logs before retrying.';
    default:
      return null;
  }
}

RecordingDiagnosticsData buildRecordingDiagnosticsData({
  required bool screenRecordingGranted,
  required String outputDir,
  required bool isRecording,
  String? engine,
  String? target,
  String? lastResult,
  RecordingDiagnosticsNoticeLevel lastResultLevel =
      RecordingDiagnosticsNoticeLevel.info,
  String? lastFailureKind,
  String? lastFailureMessage,
  int? lastExitStatus,
  String? lastOutputPath,
  int? lastOutputFileSize,
}) {
  return RecordingDiagnosticsData(
    buildLabel: '${BuildInfo.commit} · ${BuildInfo.buildChannel}',
    appPath: BuildInfo.detectAppBundlePath(),
    installStatus: recordingInstallStatusLabel(),
    screenRecordingGranted: screenRecordingGranted,
    engine: engine,
    target: target,
    outputDir: outputDir,
    logsDir: recordingLogsDirPath(),
    isRecording: isRecording,
    lastResult: lastResult,
    lastResultLevel: lastResultLevel,
    lastFailureKind: lastFailureKind,
    lastFailureMessage: lastFailureMessage,
    lastExitStatus: lastExitStatus,
    lastOutputPath: lastOutputPath,
    lastOutputFileSize: lastOutputFileSize,
    advice: recordingDiagnosticsAdvice(
      screenRecordingGranted: screenRecordingGranted,
      lastFailureKind: lastFailureKind,
      lastFailureMessage: lastFailureMessage,
    ),
  );
}
