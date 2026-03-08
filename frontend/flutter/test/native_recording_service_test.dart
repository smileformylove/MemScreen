import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:memscreen_flutter/services/native_recording_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const channel = MethodChannel('com.memscreen/native_recording');
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;

  tearDown(() async {
    messenger.setMockMethodCallHandler(channel, null);
  });

  test('consumeFinishedRecordingIfNeeded returns failed finished result',
      () async {
    messenger.setMockMethodCallHandler(channel, (call) async {
      if (call.method == 'consumeFinishedNativeRecording') {
        return <String, dynamic>{
          'consumed': true,
          'ok': false,
          'failureKind': 'permission_denied',
          'error': 'Screen Recording permission is required.',
          'durationSec': 0.0,
          'consumedByCallback': false,
        };
      }
      fail('Unexpected method: ${call.method}');
    });

    final service = NativeRecordingService();
    final result = await service.consumeFinishedRecordingIfNeeded();

    expect(result, isNotNull);
    expect(result!.ok, isFalse);
    expect(result.failureKind, 'permission_denied');
    expect(result.error, contains('Screen Recording permission'));
  });

  test('consumeFinishedRecordingIfNeeded returns null when nothing finished',
      () async {
    messenger.setMockMethodCallHandler(channel, (call) async {
      if (call.method == 'consumeFinishedNativeRecording') {
        return <String, dynamic>{'consumed': false};
      }
      fail('Unexpected method: ${call.method}');
    });

    final service = NativeRecordingService();
    final result = await service.consumeFinishedRecordingIfNeeded();

    expect(result, isNull);
  });

  test('getStatus parses native failure diagnostics', () async {
    messenger.setMockMethodCallHandler(channel, (call) async {
      if (call.method == 'nativeRecordingStatus') {
        return <String, dynamic>{
          'isRecording': false,
          'duration': 2,
          'interval': 2.0,
          'outputDir': '/tmp/videos',
          'frameCount': 0,
          'elapsedTime': 0,
          'mode': 'fullscreen-single',
          'screenIndex': 1,
          'screenDisplayId': 77,
          'lastFailureKind': 'no_output',
          'lastFailureMessage': 'No output file created.',
          'lastOutputPath': '/tmp/videos/test.mov',
          'lastOutputFileSize': 0,
          'lastTerminationStatus': 1,
          'lastNotice': 'No file created.',
        };
      }
      fail('Unexpected method: ${call.method}');
    });

    final service = NativeRecordingService();
    final status = await service.getStatus();

    expect(status.mode, 'fullscreen-single');
    expect(status.screenIndex, 1);
    expect(status.screenDisplayId, 77);
    expect(status.lastFailureKind, 'no_output');
    expect(status.lastFailureMessage, 'No output file created.');
    expect(status.lastOutputPath, '/tmp/videos/test.mov');
    expect(status.lastOutputFileSize, 0);
    expect(status.lastTerminationStatus, 1);
    expect(status.lastNotice, 'No file created.');
  });
}
