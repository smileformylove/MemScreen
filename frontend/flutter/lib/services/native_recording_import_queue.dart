import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';

import '../api/api_client.dart';

class NativeRecordingImportQueue {
  NativeRecordingImportQueue({String? filePath})
    : _filePath =
          filePath ??
          '${Platform.environment['HOME'] ?? ''}/.memscreen/native_recording_imports.json';

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
      debugPrint('[NativeRecordingImportQueue] Failed to read queue: $e');
      return <Map<String, dynamic>>[];
    }
  }

  Future<void> _writeAll(List<Map<String, dynamic>> items) async {
    try {
      final file = File(_filePath);
      await file.parent.create(recursive: true);
      await file.writeAsString(jsonEncode(items));
    } catch (e) {
      debugPrint('[NativeRecordingImportQueue] Failed to write queue: $e');
    }
  }

  Future<void> enqueue(Map<String, dynamic> item) async {
    final items = await _readAll();
    final filename = (item['filename'] ?? '').toString();
    items.removeWhere((entry) => (entry['filename'] ?? '').toString() == filename);
    items.add(item);
    await _writeAll(items);
  }

  Future<void> flush(ApiClient client) async {
    final items = await _readAll();
    if (items.isEmpty) return;
    final remaining = <Map<String, dynamic>>[];
    for (final item in items) {
      try {
        await client.post('/recording/import', body: item);
      } catch (e) {
        remaining.add(item);
      }
    }
    await _writeAll(remaining);
  }
}
