import 'api_client.dart';

class RecordingApi {
  RecordingApi(this.client);
  final ApiClient client;

  Future<void> start({
    int duration = 60,
    double interval = 2.0,
    String? mode,
    List<double>? region,
    int? screenIndex,
    String? windowTitle,
  }) async {
    final body = <String, dynamic>{
      'duration': duration,
      'interval': interval,
    };
    if (mode != null) body['mode'] = mode;
    if (region != null) body['region'] = region;
    if (screenIndex != null) body['screen_index'] = screenIndex;
    if (windowTitle != null && windowTitle.isNotEmpty) {
      body['window_title'] = windowTitle;
    }
    await client.post('/recording/start', body: body);
  }

  Future<void> stop() async {
    await client.post('/recording/stop');
  }

  Future<RecordingStatus> getStatus() async {
    final m = await client.get('/recording/status');
    List<double>? region;
    if (m['region'] is List) {
      region = (m['region'] as List).map((e) => (e as num).toDouble()).toList();
    }
    return RecordingStatus(
      isRecording: m['is_recording'] as bool? ?? false,
      duration: m['duration'] as int? ?? 0,
      interval: m['interval'] as double? ?? 2.0,
      outputDir: m['output_dir'] as String? ?? '',
      frameCount: m['frame_count'] as int? ?? 0,
      elapsedTime: m['elapsed_time'] as num? ?? 0,
      mode: m['mode'] as String? ?? 'fullscreen',
      region: region,
      screenIndex: m['screen_index'] as int?,
    );
  }

  /// 
  Future<List<RecordingScreenInfo>> getScreens() async {
    final m = await client.get('/recording/screens');
    final list = m['screens'];
    if (list is! List) return [];
    return list.map((e) {
      final x = e as Map<String, dynamic>;
      return RecordingScreenInfo(
        index: x['index'] as int? ?? 0,
        name: x['name'] as String? ?? '',
        width: x['width'] as int? ?? 0,
        height: x['height'] as int? ?? 0,
        isPrimary: x['is_primary'] as bool? ?? false,
      );
    }).toList();
  }
}

class RecordingScreenInfo {
  RecordingScreenInfo({
    required this.index,
    required this.name,
    required this.width,
    required this.height,
    required this.isPrimary,
  });
  final int index;
  final String name;
  final int width;
  final int height;
  final bool isPrimary;
}

class RecordingStatus {
  RecordingStatus({
    required this.isRecording,
    required this.duration,
    required this.interval,
    required this.outputDir,
    required this.frameCount,
    required this.elapsedTime,
    this.mode = 'fullscreen',
    this.region,
    this.screenIndex,
  });
  final bool isRecording;
  final int duration;
  final double interval;
  final String outputDir;
  final int frameCount;
  final num elapsedTime;
  final String mode;
  final List<double>? region;
  final int? screenIndex;
}
