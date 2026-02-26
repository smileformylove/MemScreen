import 'api_client.dart';

class ProcessApi {
  ProcessApi(this.client);
  final ApiClient client;

  Future<List<ProcessSession>> getSessions({int limit = 20}) async {
    final m = await client.get('/process/sessions?limit=$limit');
    final list = m['sessions'];
    if (list is! List) return [];
    return list.map((e) => _sessionFromMap(e as Map<String, dynamic>)).toList();
  }

  Future<ProcessSession?> saveSession({
    required List<Map<String, dynamic>> events,
    required String startTime,
    required String endTime,
  }) async {
    final m = await client.post('/process/sessions', body: {
      'events': events,
      'start_time': startTime,
      'end_time': endTime,
    });
    final s = m['session'];
    if (s is Map<String, dynamic>) return _sessionFromMap(s);
    return null;
  }

  Future<List<Map<String, dynamic>>> getSessionEvents(String id) async {
    final m = await client.get('/process/sessions/$id');
    final list = m['events'];
    if (list is List) return list.map((e) => e as Map<String, dynamic>).toList();
    return [];
  }

  Future<ProcessAnalysis?> getSessionAnalysis(String id) async {
    final m = await client.get('/process/sessions/$id/analysis');
    return ProcessAnalysis(
      categories: m['categories'] as Map<String, dynamic>? ?? {},
      patterns: m['patterns'] as Map<String, dynamic>? ?? {},
      eventCount: m['event_count'] as int? ?? 0,
      keystrokes: m['keystrokes'] as int? ?? 0,
      clicks: m['clicks'] as int? ?? 0,
      startTime: m['start_time'] as String? ?? '',
      endTime: m['end_time'] as String? ?? '',
    );
  }

  Future<int> deleteSession(String id) async {
    final m = await client.delete('/process/sessions/$id');
    return m['deleted'] as int? ?? 0;
  }

  Future<int> deleteAllSessions() async {
    final m = await client.delete('/process/sessions');
    return m['deleted'] as int? ?? 0;
  }

  /// /
  Future<void> startTracking() async {
    await client.post('/process/tracking/start');
  }

  /// 
  Future<void> stopTracking() async {
    await client.post('/process/tracking/stop');
  }

  Future<void> markTrackingStart() async {
    await client.post('/process/tracking/mark-start');
  }

  /// 
  Future<TrackingStatus> getTrackingStatus() async {
    final m = await client.get('/process/tracking/status');
    return TrackingStatus(
      isTracking: m['is_tracking'] as bool? ?? false,
      eventCount: m['event_count'] as int? ?? 0,
    );
  }

  /// 
  Future<SaveFromTrackingResult> saveSessionFromTracking() async {
    final m = await client.post('/process/sessions/from-tracking');
    return SaveFromTrackingResult(
      eventsSaved: m['events_saved'] as int? ?? 0,
      startTime: m['start_time'] as String? ?? '',
      endTime: m['end_time'] as String? ?? '',
    );
  }

  static ProcessSession _sessionFromMap(Map<String, dynamic> m) {
    return ProcessSession(
      id: m['id'] as int? ?? 0,
      startTime: m['start_time'] as String? ?? '',
      endTime: m['end_time'] as String? ?? '',
      eventCount: m['event_count'] as int? ?? 0,
      keystrokes: m['keystrokes'] as int? ?? 0,
      clicks: m['clicks'] as int? ?? 0,
    );
  }
}

class TrackingStatus {
  TrackingStatus({required this.isTracking, required this.eventCount});
  final bool isTracking;
  final int eventCount;
}

class SaveFromTrackingResult {
  SaveFromTrackingResult({
    required this.eventsSaved,
    required this.startTime,
    required this.endTime,
  });
  final int eventsSaved;
  final String startTime;
  final String endTime;
}

class ProcessSession {
  ProcessSession({
    required this.id,
    required this.startTime,
    required this.endTime,
    required this.eventCount,
    required this.keystrokes,
    required this.clicks,
  });
  final int id;
  final String startTime;
  final String endTime;
  final int eventCount;
  final int keystrokes;
  final int clicks;
}

class ProcessAnalysis {
  ProcessAnalysis({
    required this.categories,
    required this.patterns,
    required this.eventCount,
    required this.keystrokes,
    required this.clicks,
    required this.startTime,
    required this.endTime,
  });
  final Map<String, dynamic> categories;
  final Map<String, dynamic> patterns;
  final int eventCount;
  final int keystrokes;
  final int clicks;
  final String startTime;
  final String endTime;
}
