import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';

class LocalVideoCatalogStore {
  LocalVideoCatalogStore({String? filePath})
      : _filePath = filePath ??
            '${Platform.environment['HOME'] ?? ''}/.memscreen/local_video_catalog.json';

  final String _filePath;

  Future<List<Map<String, dynamic>>> load() async {
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
      debugPrint('[LocalVideoCatalogStore] Failed to load cache: $e');
      return <Map<String, dynamic>>[];
    }
  }

  Future<void> upsert(Map<String, dynamic> item) async {
    try {
      final items = await load();
      final filename = (item['filename'] ?? '').toString();
      items.removeWhere(
          (entry) => (entry['filename'] ?? '').toString() == filename);
      items.add(item);
      final file = File(_filePath);
      await file.parent.create(recursive: true);
      await file.writeAsString(jsonEncode(items));
    } catch (e) {
      debugPrint('[LocalVideoCatalogStore] Failed to update cache: $e');
    }
  }
}
