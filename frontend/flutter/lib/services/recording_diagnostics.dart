import 'dart:io';

import '../build_info.dart';
import 'recording_failure_messages.dart';
import '../widgets/recording_diagnostics_panel.dart';

enum RecordingInstallStatus { applications, nonstandard, unknown }

class RecordingDiagnosticsSummary {
  const RecordingDiagnosticsSummary({
    required this.message,
    required this.level,
  });

  final String message;
  final RecordingDiagnosticsNoticeLevel level;
}

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

String _formatByteCount(int bytes) {
  const units = <String>['B', 'KB', 'MB', 'GB'];
  var value = bytes.toDouble();
  var unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  final decimals = unitIndex == 0 || value >= 10 ? 0 : 1;
  return '${value.toStringAsFixed(decimals)} ${units[unitIndex]}';
}

String? recordingLastOutputStatus({
  String? lastOutputPath,
  int? lastOutputFileSize,
  String? lastFailureKind,
}) {
  final hasOutputPath = (lastOutputPath ?? '').trim().isNotEmpty;
  if (lastOutputFileSize != null && lastOutputFileSize > 0) {
    return 'Saved · ${_formatByteCount(lastOutputFileSize)}';
  }
  if (hasOutputPath && lastOutputFileSize != null && lastOutputFileSize <= 0) {
    return 'Zero-byte file';
  }
  switch ((lastFailureKind ?? '').trim()) {
    case 'no_output':
      return hasOutputPath ? 'Not playable yet' : 'No file created';
    case 'empty_output':
      return hasOutputPath ? 'Empty file written' : 'Empty output';
    case 'cancelled':
      return 'Cancelled before save';
    case 'permission_denied':
      return 'Blocked before save';
    default:
      if (hasOutputPath) {
        return 'Path recorded';
      }
      return null;
  }
}

RecordingDiagnosticsNoticeLevel recordingLastOutputStatusLevel({
  String? lastOutputPath,
  int? lastOutputFileSize,
  String? lastFailureKind,
}) {
  final hasOutputPath = (lastOutputPath ?? '').trim().isNotEmpty;
  if (lastOutputFileSize != null && lastOutputFileSize > 0) {
    return RecordingDiagnosticsNoticeLevel.info;
  }
  if (hasOutputPath && lastOutputFileSize != null && lastOutputFileSize <= 0) {
    return RecordingDiagnosticsNoticeLevel.warning;
  }
  switch ((lastFailureKind ?? '').trim()) {
    case 'cancelled':
      return RecordingDiagnosticsNoticeLevel.warning;
    case 'permission_denied':
    case 'no_output':
    case 'empty_output':
    case 'recorder_error':
      return RecordingDiagnosticsNoticeLevel.error;
    default:
      return RecordingDiagnosticsNoticeLevel.info;
  }
}

String? recordingDiagnosticsAdvice({
  required bool screenRecordingGranted,
  String? statusNotice,
  String? lastFailureKind,
  String? lastFailureMessage,
  int? lastExitStatus,
  int? lastOutputFileSize,
  String? lastOutputPath,
}) {
  final installAdvice = recordingInstallAdvice();
  if (installAdvice != null) {
    return installAdvice;
  }

  final normalizedNotice = (statusNotice ?? '').trim();
  if (normalizedNotice.startsWith('Import warning:')) {
    return 'The recording file was saved locally. Reconnect the backend or open Videos later to let import retry.';
  }

  if (!screenRecordingGranted || lastFailureKind == 'permission_denied') {
    return 'Grant Screen Recording permission, then fully quit and reopen MemScreen before trying again.';
  }

  final hasOutputPath = (lastOutputPath ?? '').trim().isNotEmpty;
  final hasZeroByteOutput =
      lastOutputFileSize != null && lastOutputFileSize <= 0 && hasOutputPath;

  switch ((lastFailureKind ?? '').trim()) {
    case 'cancelled':
      return 'The recording was cancelled before a file was written. Retry the smoke check and avoid dismissing the system capture flow.';
    case 'empty_output':
      if (hasZeroByteOutput) {
        return 'A zero-byte file was created at the last output path. Delete that file if needed, then retry the smoke check and inspect logs if it happens again.';
      }
      return 'A zero-byte file was created. Retry the smoke check, then inspect the output folder and logs if it happens again.';
    case 'no_output':
      if (lastExitStatus == 0) {
        return 'Native capture exited with status 0 but no playable file was created. Run the smoke check again and compare the output folder and last output path.';
      }
      if (lastExitStatus != null) {
        return 'No playable video file was created. Exit status $lastExitStatus suggests native capture failed before writing output. Open logs and retry.';
      }
      return 'No playable video file was created. Run the smoke check again and compare the exit status and last output path.';
    case 'recorder_error':
      if (lastExitStatus != null) {
        return 'Recorder error detected (exit status $lastExitStatus). Open logs and check the native failure details before retrying.';
      }
      if ((lastFailureMessage ?? '').trim().isNotEmpty) {
        return 'Recorder error detected. Open logs and check the native failure details before retrying.';
      }
      return 'Recorder error detected. Open logs before retrying.';
    default:
      if (hasZeroByteOutput) {
        return 'A zero-byte file exists at the last output path. Retry the smoke check and inspect logs if the file stays empty.';
      }
      return null;
  }
}

RecordingDiagnosticsSummary? recordingDiagnosticsSummary({
  required bool isRecording,
  String? transientNotice,
  RecordingDiagnosticsNoticeLevel transientNoticeLevel =
      RecordingDiagnosticsNoticeLevel.info,
  String? statusNotice,
  String? lastFailureKind,
  String? lastFailureMessage,
  String? smokeCheckSummary,
}) {
  final inlineNotice = (transientNotice ?? '').trim();
  if (inlineNotice.isNotEmpty) {
    return RecordingDiagnosticsSummary(
      message: inlineNotice,
      level: transientNoticeLevel,
    );
  }

  if (isRecording) {
    return const RecordingDiagnosticsSummary(
      message: 'Recording is active.',
      level: RecordingDiagnosticsNoticeLevel.info,
    );
  }

  final nativeNotice = (statusNotice ?? '').trim();
  if (nativeNotice.isNotEmpty) {
    if (nativeNotice.startsWith('Import warning:')) {
      return RecordingDiagnosticsSummary(
        message: nativeNotice,
        level: RecordingDiagnosticsNoticeLevel.warning,
      );
    }
    if ((lastFailureKind ?? '').trim().isNotEmpty) {
      return RecordingDiagnosticsSummary(
        message: nativeNotice,
        level: RecordingDiagnosticsNoticeLevel.error,
      );
    }
    return RecordingDiagnosticsSummary(
      message: nativeNotice,
      level: RecordingDiagnosticsNoticeLevel.info,
    );
  }

  if ((lastFailureKind ?? '').trim().isNotEmpty) {
    return RecordingDiagnosticsSummary(
      message: describeNativeRecordingFailure(
        failureKind: lastFailureKind,
        error: lastFailureMessage,
      ),
      level: RecordingDiagnosticsNoticeLevel.error,
    );
  }

  final smokeSummary = (smokeCheckSummary ?? '').trim();
  if (smokeSummary.isNotEmpty) {
    final lower = smokeSummary.toLowerCase();
    final level = lower.contains('failed') ||
            lower.contains('still not active') ||
            lower.contains('permission:')
        ? RecordingDiagnosticsNoticeLevel.error
        : lower.contains('warning')
            ? RecordingDiagnosticsNoticeLevel.warning
            : RecordingDiagnosticsNoticeLevel.info;
    return RecordingDiagnosticsSummary(message: smokeSummary, level: level);
  }

  return null;
}

RecordingDiagnosticsData buildRecordingDiagnosticsData({
  required bool screenRecordingGranted,
  required String outputDir,
  required bool isRecording,
  String? engine,
  String? target,
  String? transientNotice,
  RecordingDiagnosticsNoticeLevel transientNoticeLevel =
      RecordingDiagnosticsNoticeLevel.info,
  String? statusNotice,
  String? lastFailureKind,
  String? lastFailureMessage,
  int? lastExitStatus,
  String? lastOutputPath,
  int? lastOutputFileSize,
  String? smokeCheckAt,
  String? smokeCheckSummary,
}) {
  final summary = recordingDiagnosticsSummary(
    isRecording: isRecording,
    transientNotice: transientNotice,
    transientNoticeLevel: transientNoticeLevel,
    statusNotice: statusNotice,
    lastFailureKind: lastFailureKind,
    lastFailureMessage: lastFailureMessage,
    smokeCheckSummary: smokeCheckSummary,
  );
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
    lastResult: summary?.message,
    lastResultLevel: summary?.level ?? RecordingDiagnosticsNoticeLevel.info,
    lastFailureKind: lastFailureKind,
    lastFailureMessage: lastFailureMessage,
    lastExitStatus: lastExitStatus,
    lastOutputPath: lastOutputPath,
    lastOutputFileSize: lastOutputFileSize,
    lastOutputStatus: recordingLastOutputStatus(
      lastOutputPath: lastOutputPath,
      lastOutputFileSize: lastOutputFileSize,
      lastFailureKind: lastFailureKind,
    ),
    lastOutputStatusLevel: recordingLastOutputStatusLevel(
      lastOutputPath: lastOutputPath,
      lastOutputFileSize: lastOutputFileSize,
      lastFailureKind: lastFailureKind,
    ),
    smokeCheckAt: smokeCheckAt,
    smokeCheckSummary: smokeCheckSummary,
    advice: recordingDiagnosticsAdvice(
      screenRecordingGranted: screenRecordingGranted,
      statusNotice: statusNotice,
      lastFailureKind: lastFailureKind,
      lastFailureMessage: lastFailureMessage,
      lastExitStatus: lastExitStatus,
      lastOutputFileSize: lastOutputFileSize,
      lastOutputPath: lastOutputPath,
    ),
  );
}
