import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../services/recording_failure_messages.dart';

enum RecordingDiagnosticsNoticeLevel { info, warning, error }

class RecordingDiagnosticsData {
  const RecordingDiagnosticsData({
    required this.buildLabel,
    required this.installStatus,
    required this.screenRecordingGranted,
    required this.outputDir,
    required this.logsDir,
    required this.isRecording,
    this.appPath,
    this.engine,
    this.target,
    this.lastResult,
    this.lastResultLevel = RecordingDiagnosticsNoticeLevel.info,
    this.lastFailureKind,
    this.lastFailureMessage,
    this.lastExitStatus,
    this.lastOutputPath,
    this.lastOutputFileSize,
    this.lastOutputStatus,
    this.lastOutputStatusLevel = RecordingDiagnosticsNoticeLevel.info,
    this.problemSummary,
    this.problemSummaryLevel = RecordingDiagnosticsNoticeLevel.info,
    this.nextStep,
    this.nextStepLevel = RecordingDiagnosticsNoticeLevel.info,
    this.smokeCheckAt,
    this.smokeCheckSummary,
    this.advice,
  });

  final String buildLabel;
  final String installStatus;
  final bool screenRecordingGranted;
  final String outputDir;
  final String logsDir;
  final bool isRecording;
  final String? appPath;
  final String? engine;
  final String? target;
  final String? lastResult;
  final RecordingDiagnosticsNoticeLevel lastResultLevel;
  final String? lastFailureKind;
  final String? lastFailureMessage;
  final int? lastExitStatus;
  final String? lastOutputPath;
  final int? lastOutputFileSize;
  final String? lastOutputStatus;
  final RecordingDiagnosticsNoticeLevel lastOutputStatusLevel;
  final String? problemSummary;
  final RecordingDiagnosticsNoticeLevel problemSummaryLevel;
  final String? nextStep;
  final RecordingDiagnosticsNoticeLevel nextStepLevel;
  final String? smokeCheckAt;
  final String? smokeCheckSummary;
  final String? advice;
}

class RecordingDiagnosticsHeaderAction {
  const RecordingDiagnosticsHeaderAction({
    required this.label,
    required this.onPressed,
    this.isLoading = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;
}

class RecordingDiagnosticsQuickAction {
  const RecordingDiagnosticsQuickAction({
    required this.label,
    required this.icon,
    required this.onPressed,
    this.isLoading = false,
  });

  final String label;
  final IconData icon;
  final VoidCallback? onPressed;
  final bool isLoading;
}

class RecordingDiagnosticsBanner {
  const RecordingDiagnosticsBanner({
    required this.label,
    required this.value,
    required this.level,
    required this.icon,
  });

  final String label;
  final String value;
  final RecordingDiagnosticsNoticeLevel level;
  final IconData icon;
}

List<RecordingDiagnosticsBanner> buildRecordingDiagnosticsBanners(
  RecordingDiagnosticsData data,
) {
  final banners = <RecordingDiagnosticsBanner>[];
  final seen = <String>{};

  void addBanner({
    required String label,
    required String? value,
    required RecordingDiagnosticsNoticeLevel level,
    required IconData icon,
  }) {
    final normalized = (value ?? '').trim();
    if (normalized.isEmpty) return;
    final dedupeKey = normalized.toLowerCase();
    if (!seen.add(dedupeKey)) return;
    banners.add(
      RecordingDiagnosticsBanner(
        label: label,
        value: normalized,
        level: level,
        icon: icon,
      ),
    );
  }

  addBanner(
    label: 'Problem summary',
    value: data.problemSummary,
    level: data.problemSummaryLevel,
    icon: switch (data.problemSummaryLevel) {
      RecordingDiagnosticsNoticeLevel.error => Icons.error_outline,
      RecordingDiagnosticsNoticeLevel.warning => Icons.warning_amber_outlined,
      RecordingDiagnosticsNoticeLevel.info => Icons.check_circle_outline,
    },
  );

  addBanner(
    label: 'Next step',
    value: data.nextStep,
    level: data.nextStepLevel,
    icon: switch (data.nextStepLevel) {
      RecordingDiagnosticsNoticeLevel.error => Icons.arrow_forward,
      RecordingDiagnosticsNoticeLevel.warning => Icons.double_arrow_outlined,
      RecordingDiagnosticsNoticeLevel.info => Icons.play_arrow_outlined,
    },
  );

  final detailCandidates = <RecordingDiagnosticsBanner>[];
  final preferOutputDetail = (data.problemSummary ?? '').trim().isNotEmpty ||
      (data.nextStep ?? '').trim().isNotEmpty;

  void addOutputDetail() {
    if ((data.lastOutputStatus ?? '').trim().isEmpty) return;
    detailCandidates.add(
      RecordingDiagnosticsBanner(
        label: 'Output file',
        value: data.lastOutputStatus!.trim(),
        level: data.lastOutputStatusLevel,
        icon: data.lastOutputStatusLevel == RecordingDiagnosticsNoticeLevel.info
            ? Icons.check_circle_outline
            : data.lastOutputStatusLevel ==
                    RecordingDiagnosticsNoticeLevel.warning
                ? Icons.warning_amber_outlined
                : Icons.error_outline,
      ),
    );
  }

  void addLastResultDetail() {
    if ((data.lastResult ?? '').trim().isEmpty) return;
    detailCandidates.add(
      RecordingDiagnosticsBanner(
        label: 'Last result',
        value: data.lastResult!.trim(),
        level: data.lastResultLevel,
        icon: switch (data.lastResultLevel) {
          RecordingDiagnosticsNoticeLevel.error => Icons.error_outline,
          RecordingDiagnosticsNoticeLevel.warning =>
            Icons.warning_amber_outlined,
          RecordingDiagnosticsNoticeLevel.info => Icons.info_outline,
        },
      ),
    );
  }

  void addAdviceDetail() {
    if ((data.advice ?? '').trim().isEmpty) return;
    detailCandidates.add(
      RecordingDiagnosticsBanner(
        label: 'Advice',
        value: data.advice!.trim(),
        level: data.screenRecordingGranted
            ? RecordingDiagnosticsNoticeLevel.warning
            : RecordingDiagnosticsNoticeLevel.error,
        icon: Icons.tips_and_updates_outlined,
      ),
    );
  }

  if (preferOutputDetail) {
    addOutputDetail();
    addLastResultDetail();
    addAdviceDetail();
  } else {
    addLastResultDetail();
    addAdviceDetail();
    addOutputDetail();
  }

  for (final candidate in detailCandidates) {
    final normalized = candidate.value.trim().toLowerCase();
    if (seen.contains(normalized)) {
      continue;
    }
    banners.add(candidate);
    break;
  }

  return banners;
}

Future<String> copyRecordingDiagnosticsToClipboard(
  RecordingDiagnosticsData data, {
  required bool brief,
}) async {
  final text = brief
      ? buildRecordingDiagnosticsBrief(data)
      : buildRecordingDiagnosticsReport(data);
  await Clipboard.setData(ClipboardData(text: text));
  return brief
      ? 'Recording diagnostics brief copied'
      : 'Recording diagnostics report copied';
}

String buildRecordingDiagnosticsBrief(RecordingDiagnosticsData data) {
  final parts = <String>[];
  if ((data.problemSummary ?? '').isNotEmpty) {
    parts.add('Summary: ${data.problemSummary!}');
  }
  if ((data.nextStep ?? '').isNotEmpty) {
    parts.add('Next: ${data.nextStep!}');
  }
  if ((data.lastOutputStatus ?? '').isNotEmpty) {
    parts.add('Output: ${data.lastOutputStatus!}');
  }
  if (parts.isEmpty) {
    parts.add('Summary: No immediate recording issue detected.');
  }
  return parts.join(' | ');
}

List<String> orderedRecordingDiagnosticsActionLabels(
  RecordingDiagnosticsData data, {
  required Iterable<String> availableActionLabels,
}) {
  final labels = availableActionLabels.toList();
  final next = (data.nextStep ?? '').toLowerCase();
  final advice = (data.advice ?? '').toLowerCase();
  final outputStatus = (data.lastOutputStatus ?? '').toLowerCase();
  final indexed = labels.indexed.toList();
  int priorityFor(String label) {
    switch (label) {
      case 'Open Screen Recording':
        return data.screenRecordingGranted ? 90 : 0;
      case 'Run smoke check':
        if (next.contains('smoke check')) return 1;
        return 20;
      case 'Open last output':
        if (next.contains('last output') || next.contains('plays back')) {
          return 1;
        }
        return 30;
      case 'Reveal in Finder':
        if (next.contains('finder') || next.contains('delete')) return 2;
        if (outputStatus.contains('zero-byte')) return 3;
        return 31;
      case 'Open logs':
        if (next.contains('open logs') || advice.contains('open logs')) {
          return 2;
        }
        return 40;
      case 'Open output':
        return 50;
      default:
        return 60;
    }
  }

  indexed.sort((a, b) {
    final pa = priorityFor(a.$2);
    final pb = priorityFor(b.$2);
    if (pa != pb) return pa.compareTo(pb);
    return a.$1.compareTo(b.$1);
  });
  return indexed.map((entry) => entry.$2).toList(growable: false);
}

String buildRecordingDiagnosticsReport(RecordingDiagnosticsData data) {
  final lines = <String>[
    'MemScreen recording diagnostics',
    buildRecordingDiagnosticsBrief(data),
    'build: ${data.buildLabel}',
    'install_status: ${data.installStatus}',
    'screen_recording_permission: ${data.screenRecordingGranted ? 'granted' : 'missing'}',
    'output_dir: ${data.outputDir}',
    'logs_dir: ${data.logsDir}',
    'is_recording: ${data.isRecording}',
  ];
  if ((data.appPath ?? '').isNotEmpty) {
    lines.add('app_path: ${data.appPath!}');
  }
  if ((data.engine ?? '').isNotEmpty) {
    lines.add('engine: ${data.engine!}');
  }
  if ((data.target ?? '').isNotEmpty) {
    lines.add('target: ${data.target!}');
  }
  if ((data.lastFailureKind ?? '').isNotEmpty) {
    lines.add('last_failure_kind: ${data.lastFailureKind!}');
  }
  if ((data.lastFailureMessage ?? '').isNotEmpty) {
    lines.add('last_failure_message: ${data.lastFailureMessage!}');
  }
  if (data.lastExitStatus != null) {
    lines.add('last_exit_status: ${data.lastExitStatus}');
  }
  if ((data.lastOutputPath ?? '').isNotEmpty) {
    lines.add('last_output_path: ${data.lastOutputPath!}');
  }
  if (data.lastOutputFileSize != null) {
    lines.add('last_output_file_size: ${data.lastOutputFileSize}');
  }
  if ((data.lastOutputStatus ?? '').isNotEmpty) {
    lines.add('last_output_status: ${data.lastOutputStatus!}');
  }
  if ((data.problemSummary ?? '').isNotEmpty) {
    lines.add('problem_summary: ${data.problemSummary!}');
  }
  if ((data.nextStep ?? '').isNotEmpty) {
    lines.add('next_step: ${data.nextStep!}');
  }
  if ((data.lastResult ?? '').isNotEmpty) {
    lines.add('last_notice: ${data.lastResult!}');
  }
  if ((data.smokeCheckAt ?? '').isNotEmpty) {
    lines.add('last_smoke_check_at: ${data.smokeCheckAt!}');
  }
  if ((data.smokeCheckSummary ?? '').isNotEmpty) {
    lines.add('last_smoke_check_summary: ${data.smokeCheckSummary!}');
  }
  if ((data.advice ?? '').isNotEmpty) {
    lines.add('advice: ${data.advice!}');
  }
  return lines.join('\n');
}

class RecordingDiagnosticsPanel extends StatelessWidget {
  const RecordingDiagnosticsPanel({
    super.key,
    required this.title,
    required this.data,
    this.headerActions = const <RecordingDiagnosticsHeaderAction>[],
    this.quickActions = const <RecordingDiagnosticsQuickAction>[],
    this.compactMode = false,
    this.showPermissionShortcut = false,
    this.onOpenLastOutput,
    this.onRevealLastOutput,
    this.onOpenScreenRecording,
  });

  final String title;
  final RecordingDiagnosticsData data;
  final List<RecordingDiagnosticsHeaderAction> headerActions;
  final List<RecordingDiagnosticsQuickAction> quickActions;
  final bool compactMode;
  final bool showPermissionShortcut;
  final VoidCallback? onOpenLastOutput;
  final VoidCallback? onRevealLastOutput;
  final VoidCallback? onOpenScreenRecording;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final installOk = data.installStatus == 'Applications';
    final lastOutputAvailable = (data.lastOutputPath ?? '').trim().isNotEmpty;
    final showFullMetadata = !compactMode;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Text(title)),
              for (final action in headerActions)
                TextButton(
                  onPressed: action.isLoading ? null : action.onPressed,
                  child: action.isLoading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(action.label),
                ),
            ],
          ),
          if (showFullMetadata)
            _diagnosticRow(
              context,
              icon: Icons.commit,
              label: 'Build',
              value: data.buildLabel,
            ),
          if (showFullMetadata && (data.appPath ?? '').isNotEmpty)
            _diagnosticRow(
              context,
              icon: Icons.apps_outlined,
              label: 'App Path',
              value: data.appPath!,
            ),
          _diagnosticRow(
            context,
            icon: Icons.install_desktop_outlined,
            label: 'Install',
            value: data.installStatus,
            valueColor: installOk ? Colors.green : theme.colorScheme.error,
          ),
          for (final banner in buildRecordingDiagnosticsBanners(data))
            _noticeBanner(
              context,
              icon: banner.icon,
              label: banner.label,
              value: banner.value,
              level: banner.level,
            ),
          if (showFullMetadata && (data.engine ?? '').isNotEmpty)
            _diagnosticRow(
              context,
              icon: Icons.videocam_outlined,
              label: 'Engine',
              value: data.engine!,
            ),
          _diagnosticRow(
            context,
            icon: Icons.privacy_tip_outlined,
            label: 'Screen Recording',
            value: data.screenRecordingGranted ? 'Granted' : 'Missing',
            valueColor: data.screenRecordingGranted
                ? Colors.green
                : theme.colorScheme.error,
          ),
          if (showFullMetadata && (data.target ?? '').isNotEmpty)
            _diagnosticRow(
              context,
              icon: Icons.filter_center_focus_outlined,
              label: 'Target',
              value: data.target!,
            ),
          if (showFullMetadata)
            _diagnosticRow(
              context,
              icon: Icons.folder_open_outlined,
              label: 'Output',
              value: data.outputDir,
            ),
          if (showFullMetadata)
            _diagnosticRow(
              context,
              icon: Icons.receipt_long_outlined,
              label: 'Logs',
              value: data.logsDir,
            ),
          if ((data.lastFailureKind ?? '').isNotEmpty)
            _diagnosticRow(
              context,
              icon: Icons.bug_report_outlined,
              label: 'Failure kind',
              value: formatRecordingFailureKind(data.lastFailureKind),
              valueColor: recordingFailureKindIsWarning(data.lastFailureKind)
                  ? theme.colorScheme.onTertiaryContainer
                  : theme.colorScheme.error,
            ),
          if (data.lastExitStatus != null)
            _diagnosticRow(
              context,
              icon: Icons.terminal,
              label: 'Exit status',
              value: data.lastExitStatus.toString(),
            ),
          if ((data.lastOutputPath ?? '').isNotEmpty)
            _diagnosticRow(
              context,
              icon: Icons.insert_drive_file_outlined,
              label: 'Last output',
              value: data.lastOutputPath!,
            ),
          if ((data.smokeCheckSummary ?? '').isNotEmpty)
            _diagnosticRow(
              context,
              icon: Icons.science_outlined,
              label: 'Smoke check',
              value: data.smokeCheckAt == null
                  ? data.smokeCheckSummary!
                  : '${data.smokeCheckSummary!} · ${data.smokeCheckAt!}',
            ),
          const SizedBox(height: 8),
          Builder(
            builder: (context) {
              final actionMap = <String, RecordingDiagnosticsQuickAction>{
                for (final action in quickActions) action.label: action,
              };
              if (lastOutputAvailable) {
                actionMap['Open last output'] = RecordingDiagnosticsQuickAction(
                  label: 'Open last output',
                  icon: Icons.play_circle_outline,
                  onPressed: onOpenLastOutput,
                );
                actionMap['Reveal in Finder'] = RecordingDiagnosticsQuickAction(
                  label: 'Reveal in Finder',
                  icon: Icons.folder_open,
                  onPressed: onRevealLastOutput,
                );
              }
              if (showPermissionShortcut) {
                actionMap['Open Screen Recording'] =
                    RecordingDiagnosticsQuickAction(
                  label: 'Open Screen Recording',
                  icon: Icons.open_in_new,
                  onPressed: onOpenScreenRecording,
                );
              }
              final orderedLabels = orderedRecordingDiagnosticsActionLabels(
                data,
                availableActionLabels: actionMap.keys,
              );
              return Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final label in orderedLabels)
                    OutlinedButton.icon(
                      onPressed: actionMap[label]!.isLoading
                          ? null
                          : actionMap[label]!.onPressed,
                      icon: actionMap[label]!.isLoading
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Icon(actionMap[label]!.icon),
                      label: Text(actionMap[label]!.label),
                    ),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _diagnosticRow(
    BuildContext context, {
    required IconData icon,
    required String label,
    required String value,
    Color? valueColor,
  }) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: theme.colorScheme.onSurfaceVariant),
          const SizedBox(width: 8),
          Expanded(
            child: RichText(
              text: TextSpan(
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                children: [
                  TextSpan(text: '$label: '),
                  TextSpan(
                    text: value,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: valueColor ?? theme.colorScheme.onSurface,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _noticeBanner(
    BuildContext context, {
    required IconData icon,
    required String label,
    required String value,
    required RecordingDiagnosticsNoticeLevel level,
  }) {
    final theme = Theme.of(context);
    final (background, foreground) = switch (level) {
      RecordingDiagnosticsNoticeLevel.error => (
          theme.colorScheme.errorContainer,
          theme.colorScheme.onErrorContainer,
        ),
      RecordingDiagnosticsNoticeLevel.warning => (
          theme.colorScheme.tertiaryContainer,
          theme.colorScheme.onTertiaryContainer,
        ),
      RecordingDiagnosticsNoticeLevel.info => (
          theme.colorScheme.secondaryContainer,
          theme.colorScheme.onSecondaryContainer,
        ),
    };
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: foreground),
          const SizedBox(width: 8),
          Expanded(
            child: RichText(
              text: TextSpan(
                style: theme.textTheme.bodySmall?.copyWith(color: foreground),
                children: [
                  TextSpan(
                    text: '$label: ',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: foreground,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  TextSpan(text: value),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
