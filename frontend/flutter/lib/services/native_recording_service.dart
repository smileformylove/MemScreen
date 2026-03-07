import 'package:flutter/services.dart';

import '../api/recording_api.dart';

class NativeRecordingStartResult {
  NativeRecordingStartResult({
    required this.ok,
    this.filename,
    this.mode,
    this.audioSourceUsed,
    this.notice,
    this.error,
  });

  final bool ok;
  final String? filename;
  final String? mode;
  final String? audioSourceUsed;
  final String? notice;
  final String? error;
}

class NativeRecordingStopResult {
  NativeRecordingStopResult({
    required this.ok,
    this.filename,
    this.durationSec,
    this.mode,
    this.audioSourceUsed,
    this.notice,
    this.error,
  });

  final bool ok;
  final String? filename;
  final double? durationSec;
  final String? mode;
  final String? audioSourceUsed;
  final String? notice;
  final String? error;
}

class NativeRecordingService {
  static const _channel = MethodChannel('com.memscreen/native_recording');

  Future<NativeRecordingStartResult> start({
    required int duration,
    required double interval,
    String? mode,
    List<double>? region,
    int? screenIndex,
    int? screenDisplayId,
    String? windowTitle,
    String? audioSource,
  }) async {
    final raw = await _channel.invokeMethod<dynamic>('startNativeRecording', {
      'duration': duration,
      'interval': interval,
      'mode': mode,
      'region': region,
      'screenIndex': screenIndex,
      'screenDisplayId': screenDisplayId,
      'windowTitle': windowTitle,
      'audioSource': audioSource,
    });
    final map = (raw is Map
        ? Map<String, dynamic>.from(raw)
        : const <String, dynamic>{});
    return NativeRecordingStartResult(
      ok: map['ok'] as bool? ?? false,
      filename: map['filename'] as String?,
      mode: map['mode'] as String?,
      audioSourceUsed: map['audioSourceUsed'] as String?,
      notice: map['notice'] as String?,
      error: map['error'] as String?,
    );
  }

  Future<NativeRecordingStopResult> stop() async {
    final raw = await _channel.invokeMethod<dynamic>('stopNativeRecording');
    final map = (raw is Map
        ? Map<String, dynamic>.from(raw)
        : const <String, dynamic>{});
    return NativeRecordingStopResult(
      ok: map['ok'] as bool? ?? false,
      filename: map['filename'] as String?,
      durationSec: (map['durationSec'] as num?)?.toDouble(),
      mode: map['mode'] as String?,
      audioSourceUsed: map['audioSourceUsed'] as String?,
      notice: map['notice'] as String?,
      error: map['error'] as String?,
    );
  }

  Future<RecordingStatus> getStatus() async {
    final raw = await _channel.invokeMethod<dynamic>('nativeRecordingStatus');
    final map = (raw is Map
        ? Map<String, dynamic>.from(raw)
        : const <String, dynamic>{});
    List<double>? region;
    if (map['region'] is List) {
      region =
          (map['region'] as List).map((e) => (e as num).toDouble()).toList();
    }
    return RecordingStatus(
      isRecording: map['isRecording'] as bool? ?? false,
      duration: map['duration'] as int? ?? 0,
      interval: (map['interval'] as num?)?.toDouble() ?? 2.0,
      outputDir: map['outputDir'] as String? ?? '',
      frameCount: map['frameCount'] as int? ?? 0,
      elapsedTime: (map['elapsedTime'] as num?) ?? 0,
      mode: map['mode'] as String? ?? 'fullscreen',
      region: region,
      screenIndex: map['screenIndex'] as int?,
      screenDisplayId: map['screenDisplayId'] as int?,
    );
  }
}
