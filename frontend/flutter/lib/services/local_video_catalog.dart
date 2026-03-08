import 'dart:io';

import '../api/video_api.dart';
import 'local_video_catalog_store.dart';

class LocalVideoCatalog {
  LocalVideoCatalog({String? videosDir, LocalVideoCatalogStore? store})
      : _videosDir = videosDir ??
            '${Platform.environment['HOME'] ?? ''}/.memscreen/videos',
        _store = store ?? LocalVideoCatalogStore();

  final String _videosDir;
  final LocalVideoCatalogStore _store;

  Future<List<VideoItem>> list() async {
    final dir = Directory(_videosDir);
    if (!await dir.exists()) return const [];

    final cacheRows = await _store.load();
    final cacheByFilename = <String, Map<String, dynamic>>{
      for (final row in cacheRows)
        (row['filename'] ?? '').toString(): row,
    };

    final entries = await dir
        .list()
        .where((entity) => entity is File)
        .cast<File>()
        .where((file) {
          final lower = file.path.toLowerCase();
          return lower.endsWith('.mp4') ||
              lower.endsWith('.mov') ||
              lower.endsWith('.mkv') ||
              lower.endsWith('.avi');
        })
        .toList();

    final items = <VideoItem>[];
    for (final file in entries) {
      try {
        final stat = await file.stat();
        final row = cacheByFilename[file.path];
        final timestamp = row?['timestamp']?.toString().isNotEmpty == true
            ? _normalizeTimestamp(row!['timestamp'].toString())
            : _formatTimestamp(stat.modified);
        items.add(
          VideoItem(
            filename: file.path,
            timestamp: timestamp,
            frameCount: (row?['frame_count'] as int?) ?? 0,
            fps: (row?['fps'] as num?) ?? 0,
            duration: (row?['duration'] as num?) ?? 0,
            fileSize: (row?['file_size'] as int?) ?? stat.size,
            recordingMode: (row?['recording_mode'] as String?) ?? 'fullscreen',
            windowTitle: row?['window_title'] as String?,
            audioSource: row?['audio_source'] as String?,
            appName: row?['app_name'] as String? ?? 'local-video',
            tags: (row?['tags'] is List)
                ? (row!['tags'] as List).whereType<String>().toList()
                : const ['source:local-fallback'],
            contentTags: (row?['content_tags'] is List)
                ? (row!['content_tags'] as List).whereType<String>().toList()
                : const [],
            contentKeywords: (row?['content_keywords'] is List)
                ? (row!['content_keywords'] as List)
                    .whereType<String>()
                    .toList()
                : const [],
            contentSummary:
                row?['content_summary'] as String? ?? 'Local video file',
            analysisStatus: row?['analysis_status'] as String? ?? 'offline',
          ),
        );
      } catch (_) {}
    }

    items.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    return items;
  }

  static String _normalizeTimestamp(String raw) {
    final parsed = DateTime.tryParse(raw);
    if (parsed == null) return raw;
    return _formatTimestamp(parsed);
  }

  static String _formatTimestamp(DateTime value) {
    String two(int n) => n.toString().padLeft(2, '0');
    return '${value.year.toString().padLeft(4, '0')}-'
        '${two(value.month)}-${two(value.day)} '
        '${two(value.hour)}:${two(value.minute)}:${two(value.second)}';
  }
}
