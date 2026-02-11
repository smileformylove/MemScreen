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
}

class VideoItem {
  VideoItem({
    required this.filename,
    required this.timestamp,
    required this.frameCount,
    required this.fps,
    required this.duration,
    required this.fileSize,
  });
  final String filename;
  final String timestamp;
  final int frameCount;
  final num fps;
  final num duration;
  final int fileSize;
}
