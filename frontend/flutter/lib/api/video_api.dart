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

  static VideoItem _itemFromMap(Map<String, dynamic> m) {
    return VideoItem(
      filename: m['filename'] as String? ?? '',
      timestamp: m['timestamp'] as String? ?? '',
      frameCount: m['frame_count'] as int? ?? 0,
      fps: m['fps'] as num? ?? 0,
      duration: m['duration'] as num? ?? 0,
      fileSize: m['file_size'] as int? ?? 0,
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
    this.isPlaying = false,
  });
  final String filename;
  final String timestamp;
  final int frameCount;
  final num fps;
  final num duration;
  final int fileSize;
  bool isPlaying;
}
