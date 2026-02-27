import 'dart:io';
import 'api_client.dart';

class VideoApi {
  VideoApi(this.client);
  final ApiClient client;

  Future<List<VideoItem>> getList() async {
    final m = await client.get('/video/list');
    final list = m['videos'];
    if (list is! List) return [];
    return list.map((e) => _itemFromMap(e as Map<String, dynamic>)).toList();
  }

  Future<Map<String, dynamic>> reanalyze(String filename) async {
    return client.post('/video/reanalyze', body: {'filename': filename});
  }

  Future<String> resolvePlayablePath(String filename) async {
    final m =
        await client.post('/video/playable', body: {'filename': filename});
    final resolved = m['filename'] as String?;
    if (resolved != null && resolved.trim().isNotEmpty) {
      return resolved.trim();
    }
    return filename;
  }

  static VideoItem _itemFromMap(Map<String, dynamic> m) {
    return VideoItem(
      filename: m['filename'] as String? ?? '',
      timestamp: m['timestamp'] as String? ?? '',
      frameCount: m['frame_count'] as int? ?? 0,
      fps: m['fps'] as num? ?? 0,
      duration: m['duration'] as num? ?? 0,
      fileSize: m['file_size'] as int? ?? 0,
      recordingMode: m['recording_mode'] as String? ?? 'fullscreen',
      windowTitle: m['window_title'] as String?,
      audioSource: m['audio_source'] as String?,
      appName: m['app_name'] as String?,
      tags: (m['tags'] is List)
          ? (m['tags'] as List)
              .whereType<String>()
              .where((x) => x.isNotEmpty)
              .toList()
          : const [],
      contentTags: (m['content_tags'] is List)
          ? (m['content_tags'] as List)
              .whereType<String>()
              .where((x) => x.isNotEmpty)
              .toList()
          : const [],
      contentSummary: m['content_summary'] as String?,
    );
  }

  Future<bool> play(String filename) async {
    try {
      // Expand ~ to home directory if present
      String path = filename;
      if (path.startsWith('~')) {
        final home = Platform.environment['HOME'] ?? '';
        path = path.replaceFirst('~', home);
      }

      print('[VideoApi] Attempting to play: $path');

      // Check if file exists
      final file = File(path);
      if (!await file.exists()) {
        print('[VideoApi] File does not exist: $path');
        return false;
      }

      // Get file size for verification
      final size = await file.length();
      print('[VideoApi] File size: $size bytes');

      if (size == 0) {
        print('[VideoApi] File is empty!');
        return false;
      }

      // Try qlmanage (Quick Look) as it's more reliable in sandboxed apps
      // Falls back to 'open' if Quick Look fails
      var result = await Process.run('qlmanage', ['-p', path]);

      // If qlmanage fails, try regular open command
      if (result.exitCode != 0) {
        result = await Process.run('open', ['-W', path]);
      }

      print('[VideoApi] Playback result:');
      print('  - Exit code: ${result.exitCode}');
      print('  - Stdout: ${result.stdout}');
      print('  - Stderr: ${result.stderr}');

      // open should return 0 on success
      return result.exitCode == 0;
    } catch (e) {
      print('[VideoApi] Error playing video: $e');
      return false;
    }
  }
}

class VideoItem {
  VideoItem({
    required this.filename,
    required this.timestamp,
    required this.frameCount,
    required this.fps,
    required this.duration,
    required this.fileSize,
    this.recordingMode = 'fullscreen',
    this.windowTitle,
    this.audioSource,
    this.appName,
    this.tags = const [],
    this.contentTags = const [],
    this.contentSummary,
    this.isPlaying = false,
  });
  final String filename;
  final String timestamp;
  final int frameCount;
  final num fps;
  final num duration;
  final int fileSize;
  final String recordingMode;
  final String? windowTitle;
  final String? audioSource;
  final String? appName;
  final List<String> tags;
  final List<String> contentTags;
  final String? contentSummary;
  bool isPlaying;
}
