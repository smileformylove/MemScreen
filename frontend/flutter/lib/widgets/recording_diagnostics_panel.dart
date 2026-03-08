import 'package:flutter/material.dart';

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

String buildRecordingDiagnosticsReport(RecordingDiagnosticsData data) {
  final lines = <String>[
    'MemScreen recording diagnostics',
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
  if ((data.lastResult ?? '').isNotEmpty) {
    lines.add('last_notice: ${data.lastResult!}');
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
    this.showPermissionShortcut = false,
    this.onOpenScreenRecording,
  });

  final String title;
  final RecordingDiagnosticsData data;
  final List<RecordingDiagnosticsHeaderAction> headerActions;
  final List<RecordingDiagnosticsQuickAction> quickActions;
  final bool showPermissionShortcut;
  final VoidCallback? onOpenScreenRecording;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final installOk = data.installStatus == 'Applications';
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
          _diagnosticRow(
            context,
            icon: Icons.commit,
            label: 'Build',
            value: data.buildLabel,
          ),
          if ((data.appPath ?? '').isNotEmpty)
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
          if ((data.advice ?? '').isNotEmpty)
            _diagnosticRow(
              context,
              icon: Icons.warning_amber_outlined,
              label: 'Advice',
              value: data.advice!,
              valueColor: theme.colorScheme.error,
            ),
          if ((data.engine ?? '').isNotEmpty)
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
          if ((data.target ?? '').isNotEmpty)
            _diagnosticRow(
              context,
              icon: Icons.filter_center_focus_outlined,
              label: 'Target',
              value: data.target!,
            ),
          _diagnosticRow(
            context,
            icon: Icons.folder_open_outlined,
            label: 'Output',
            value: data.outputDir,
          ),
          _diagnosticRow(
            context,
            icon: Icons.receipt_long_outlined,
            label: 'Logs',
            value: data.logsDir,
          ),
          if ((data.lastResult ?? '').isNotEmpty)
            _diagnosticRow(
              context,
              icon: Icons.info_outline,
              label: 'Last result',
              value: data.lastResult!,
              valueColor: switch (data.lastResultLevel) {
                RecordingDiagnosticsNoticeLevel.error =>
                  theme.colorScheme.error,
                RecordingDiagnosticsNoticeLevel.warning =>
                  theme.colorScheme.onTertiaryContainer,
                RecordingDiagnosticsNoticeLevel.info =>
                  theme.colorScheme.onSurface,
              },
            ),
          if ((data.lastFailureKind ?? '').isNotEmpty)
            _diagnosticRow(
              context,
              icon: Icons.bug_report_outlined,
              label: 'Failure kind',
              value: data.lastFailureKind!,
              valueColor: theme.colorScheme.error,
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
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final action in quickActions)
                OutlinedButton.icon(
                  onPressed: action.isLoading ? null : action.onPressed,
                  icon: action.isLoading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Icon(action.icon),
                  label: Text(action.label),
                ),
              if (showPermissionShortcut)
                OutlinedButton.icon(
                  onPressed: onOpenScreenRecording,
                  icon: const Icon(Icons.open_in_new),
                  label: const Text('Open Screen Recording'),
                ),
            ],
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
}
