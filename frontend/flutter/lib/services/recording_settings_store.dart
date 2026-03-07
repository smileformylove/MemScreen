import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';

class RecordingSettingsStore {
  RecordingSettingsStore({String? filePath})
    : _filePath =
          filePath ??
          '${Platform.environment['HOME'] ?? ''}/.memscreen/flutter_settings.json';

  final String _filePath;

  Future<Map<String, dynamic>?> load() async {
    try {
      final file = File(_filePath);
      if (!await file.exists()) return null;
      final raw = await file.readAsString();
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) {
        return decoded;
      }
      if (decoded is Map) {
        return Map<String, dynamic>.from(decoded);
      }
      return null;
    } catch (e) {
      debugPrint('[RecordingSettingsStore] Failed to load settings: $e');
      return null;
    }
  }

  Future<void> save(Map<String, dynamic> data) async {
    try {
      final file = File(_filePath);
      await file.parent.create(recursive: true);
      await file.writeAsString(jsonEncode(data));
    } catch (e) {
      debugPrint('[RecordingSettingsStore] Failed to persist settings: $e');
    }
  }
}
