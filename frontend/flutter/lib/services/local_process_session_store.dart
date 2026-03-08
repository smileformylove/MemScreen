import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';

import '../api/process_api.dart';

class LocalProcessSessionStore {
  LocalProcessSessionStore({String? filePath})
      : _filePath = filePath ??
            '${Platform.environment['HOME'] ?? ''}/.memscreen/local_process_sessions.json';

  final String _filePath;

  Future<List<Map<String, dynamic>>> _readAll() async {
    try {
      final file = File(_filePath);
      if (!await file.exists()) return <Map<String, dynamic>>[];
      final raw = await file.readAsString();
      final decoded = jsonDecode(raw);
      if (decoded is! List) return <Map<String, dynamic>>[];
      return decoded
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    } catch (e) {
      debugPrint('[LocalProcessSessionStore] Failed to read cache: $e');
      return <Map<String, dynamic>>[];
    }
  }

  Future<void> _writeAll(List<Map<String, dynamic>> items) async {
    try {
      final file = File(_filePath);
      await file.parent.create(recursive: true);
      await file.writeAsString(jsonEncode(items));
    } catch (e) {
      debugPrint('[LocalProcessSessionStore] Failed to write cache: $e');
    }
  }

  Future<void> appendSession({
    required String startTime,
    required String endTime,
    required List<Map<String, dynamic>> events,
  }) async {
    final items = await _readAll();
    final keystrokes =
        events.where((entry) => entry['type'] == 'keypress').length;
    final clicks = events.where((entry) => entry['type'] == 'click').length;
    items.add({
      'id': DateTime.now().microsecondsSinceEpoch,
      'start_time': startTime,
      'end_time': endTime,
      'event_count': events.length,
      'keystrokes': keystrokes,
      'clicks': clicks,
      'events': events,
      'source': 'local-native',
    });
    await _writeAll(items);
  }

  Future<void> reconcileWithRemote(List<ProcessSession> remoteSessions) async {
    if (remoteSessions.isEmpty) return;
    final remoteKeys = remoteSessions.map(_mergeKeyForSession).toSet();
    final items = await _readAll();
    items.removeWhere((item) => remoteKeys.contains(_mergeKeyForMap(item)));
    await _writeAll(items);
  }

  Future<List<ProcessSession>> listSessions() async {
    final items = await _readAll();
    final sessions = items.map(_sessionFromMap).toList();
    sessions.sort((a, b) => b.startTime.compareTo(a.startTime));
    return sessions;
  }

  Future<ProcessAnalysis?> getAnalysis(int sessionId) async {
    final items = await _readAll();
    final item = items.cast<Map<String, dynamic>?>().firstWhere(
          (entry) => (entry?['id'] as int?) == sessionId,
          orElse: () => null,
        );
    if (item == null) return null;

    final events = (item['events'] as List? ?? const [])
        .whereType<Map>()
        .map((entry) => Map<String, dynamic>.from(entry))
        .toList();
    final actionCounts = <String, int>{};
    for (final event in events) {
      final text = (event['text'] ?? '').toString().trim();
      if (text.isEmpty) continue;
      final key = text.length > 48 ? text.substring(0, 48) : text;
      actionCounts[key] = (actionCounts[key] ?? 0) + 1;
    }
    final topActions = actionCounts.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    final start = _tryParse(item['start_time']?.toString() ?? '');
    final end = _tryParse(item['end_time']?.toString() ?? '');
    final durationSeconds =
        (start != null && end != null) ? end.difference(start).inSeconds : 0;
    final eventCount = item['event_count'] as int? ?? 0;
    final keystrokes = item['keystrokes'] as int? ?? 0;
    final clicks = item['clicks'] as int? ?? 0;
    final minutes = durationSeconds > 0 ? durationSeconds / 60.0 : 0.0;
    final avgEventsPerMinute =
        minutes > 0 ? eventCount / minutes : eventCount.toDouble();

    return ProcessAnalysis(
      categories: {
        'keypress': keystrokes,
        'click': clicks,
        'other': eventCount - keystrokes - clicks,
      },
      patterns: {
        'source': 'local-native',
        'note':
            'Detailed backend analysis is unavailable offline. Showing local summary.',
        'duration_minutes': minutes.toStringAsFixed(1),
        'avg_events_per_minute': avgEventsPerMinute.toStringAsFixed(1),
        'top_action_1': topActions.isNotEmpty
            ? '${topActions[0].key} (${topActions[0].value})'
            : 'n/a',
        'top_action_2': topActions.length > 1
            ? '${topActions[1].key} (${topActions[1].value})'
            : 'n/a',
        'top_action_3': topActions.length > 2
            ? '${topActions[2].key} (${topActions[2].value})'
            : 'n/a',
      },
      eventCount: eventCount,
      keystrokes: keystrokes,
      clicks: clicks,
      startTime: item['start_time'] as String? ?? '',
      endTime: item['end_time'] as String? ?? '',
    );
  }

  ProcessSession _sessionFromMap(Map<String, dynamic> item) {
    return ProcessSession(
      id: item['id'] as int? ?? 0,
      startTime: item['start_time'] as String? ?? '',
      endTime: item['end_time'] as String? ?? '',
      eventCount: item['event_count'] as int? ?? 0,
      keystrokes: item['keystrokes'] as int? ?? 0,
      clicks: item['clicks'] as int? ?? 0,
    );
  }

  String _mergeKeyForSession(ProcessSession session) {
    return '${session.startTime}|${session.endTime}|${session.eventCount}|${session.keystrokes}|${session.clicks}';
  }

  String _mergeKeyForMap(Map<String, dynamic> item) {
    return '${item['start_time'] ?? ''}|${item['end_time'] ?? ''}|${item['event_count'] ?? 0}|${item['keystrokes'] ?? 0}|${item['clicks'] ?? 0}';
  }

  DateTime? _tryParse(String raw) {
    if (raw.isEmpty) return null;
    return DateTime.tryParse(raw.replaceFirst(' ', 'T'));
  }
}
