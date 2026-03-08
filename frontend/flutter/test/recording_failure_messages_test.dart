import 'package:flutter_test/flutter_test.dart';
import 'package:memscreen_flutter/services/recording_failure_messages.dart';

void main() {
  test('describeNativeRecordingFailure maps permission failures clearly', () {
    final message = describeNativeRecordingFailure(
      failureKind: 'permission_denied',
      error: 'Screen Recording permission is required.',
    );

    expect(message, contains('Screen Recording access is still not active'));
  });

  test('describeNativeRecordingFailure prefers recorder error details', () {
    final message = describeNativeRecordingFailure(
      failureKind: 'recorder_error',
      error: 'screencapture exited with status 1',
    );

    expect(message, 'Recorder error: screencapture exited with status 1');
  });

  test('describeNativeRecordingFailure falls back to generic message', () {
    final message = describeNativeRecordingFailure();

    expect(message, 'Native macOS recording failed.');
  });
}
