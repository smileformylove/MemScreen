import 'package:flutter/services.dart';

import '../api/process_api.dart';

class NativeInputTrackingStatus extends TrackingStatus {
  NativeInputTrackingStatus({
    required bool isTracking,
    required int eventCount,
    required this.accessibilityGranted,
    required this.inputMonitoringGranted,
  }) : super(isTracking: isTracking, eventCount: eventCount);

  final bool accessibilityGranted;
  final bool inputMonitoringGranted;
}

class NativeTrackingSessionPayload {
  NativeTrackingSessionPayload({
    required this.events,
    required this.eventsSaved,
    required this.startTime,
    required this.endTime,
  });

  final List<Map<String, dynamic>> events;
  final int eventsSaved;
  final String startTime;
  final String endTime;
}

class NativeInputTrackingService {
  static const _channel = MethodChannel('com.memscreen/native_input_tracking');

  Future<NativeInputTrackingStatus> getStatus() async {
    final raw = await _channel.invokeMethod<dynamic>('nativeTrackingStatus');
    final map =
        raw is Map ? Map<String, dynamic>.from(raw) : const <String, dynamic>{};
    return NativeInputTrackingStatus(
      isTracking: map['isTracking'] as bool? ?? false,
      eventCount: map['eventCount'] as int? ?? 0,
      accessibilityGranted: map['accessibilityGranted'] as bool? ?? false,
      inputMonitoringGranted: map['inputMonitoringGranted'] as bool? ?? false,
    );
  }

  Future<void> start() async {
    final raw = await _channel.invokeMethod<dynamic>('startNativeTracking');
    final map =
        raw is Map ? Map<String, dynamic>.from(raw) : const <String, dynamic>{};
    if (map['ok'] != true) {
      throw PlatformException(
        code: 'NATIVE_TRACKING_START_FAILED',
        message: (map['error'] ?? 'Failed to start native tracking').toString(),
      );
    }
  }

  Future<void> stop() async {
    await _channel.invokeMethod<dynamic>('stopNativeTracking');
  }

  Future<NativeTrackingSessionPayload> captureSessionPayload() async {
    final raw =
        await _channel.invokeMethod<dynamic>('saveNativeTrackingSession');
    final map = raw is Map<String, dynamic>
        ? raw
        : Map<String, dynamic>.from(raw as Map);
    if (map['ok'] != true) {
      throw PlatformException(
        code: 'NATIVE_TRACKING_SAVE_FAILED',
        message: (map['error'] ?? 'No events to save').toString(),
      );
    }
    final events = (map['events'] as List? ?? const [])
        .map((entry) => Map<String, dynamic>.from(entry as Map))
        .toList();
    final startTime = map['startTime'] as String? ?? '';
    final endTime = map['endTime'] as String? ?? startTime;
    return NativeTrackingSessionPayload(
      events: events,
      eventsSaved: map['eventsSaved'] as int? ?? events.length,
      startTime: startTime,
      endTime: endTime,
    );
  }

  Future<SaveFromTrackingResult> saveSession(
    ProcessApi processApi,
    NativeTrackingSessionPayload payload,
  ) async {
    await processApi.saveSession(
      events: payload.events,
      startTime: payload.startTime,
      endTime: payload.endTime,
    );
    return SaveFromTrackingResult(
      eventsSaved: payload.eventsSaved,
      startTime: payload.startTime,
      endTime: payload.endTime,
    );
  }
}
