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
    advice: recordingInstallAdvice(),
  );
}
