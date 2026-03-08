String describeNativeRecordingFailure({
  String? failureKind,
  String? error,
}) {
  final raw = (error ?? '').trim();
  switch (failureKind) {
    case 'permission_denied':
      return 'Permission: Screen Recording access is still not active. Reopen MemScreen after allowing access in System Settings.';
    case 'cancelled':
      return 'Cancelled: Recording was cancelled before a video file was saved.';
    case 'empty_output':
      return 'No file: Recording ended, but the saved file was empty.';
    case 'no_output':
      return 'No file: Recording ended without creating a playable video file.';
    case 'recorder_error':
      return raw.isNotEmpty
          ? 'Recorder error: $raw'
          : 'Recorder error: Native macOS recording failed.';
    default:
      return raw.isNotEmpty ? raw : 'Native macOS recording failed.';
  }
}
