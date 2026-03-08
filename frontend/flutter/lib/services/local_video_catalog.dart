import 'dart:io';

import '../api/video_api.dart';

class LocalVideoCatalog {
  LocalVideoCatalog({String? videosDir})
      : _videosDir = videosDir ??
            '${Platform.environment['HOME'] ?? ''}/.memscreen/videos';

  final String _videosDir;

  Future<List<VideoItem>> list() async {
    final dir = Directory(_videosDir);
    if (!await dir.exists()) return const [];

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
    }).toList();

    final items = <VideoItem>[];
    for (final file in entries) {
      try {
        final stat = await file.stat();
        final timestamp = _formatTimestamp(stat.modified);
        final mode = file.path.toLowerCase().contains('native_')
            ? 'fullscreen'
            : 'fullscreen';
        items.add(
          VideoItem(
            filename: file.path,
            timestamp: timestamp,
            frameCount: 0,
            fps: 0,
            duration: 0,
            fileSize: stat.size,
            recordingMode: mode,
            windowTitle: null,
            audioSource: null,
            appName: 'local-video',
            tags: const ['source:local-fallback'],
            contentTags: const [],
            contentKeywords: const [],
            contentSummary: 'Local video file',
            analysisStatus: 'offline',
          ),
        );
      } catch (_) {}
    }

    items.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    return items;
  }

  static String _formatTimestamp(DateTime value) {
    String two(int n) => n.toString().padLeft(2, '0');
    return '${value.year.toString().padLeft(4, '0')}-'
        '${two(value.month)}-${two(value.day)} '
        '${two(value.hour)}:${two(value.minute)}:${two(value.second)}';
  }
}
