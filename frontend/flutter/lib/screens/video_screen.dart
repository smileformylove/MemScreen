import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/video_api.dart';
import '../app_state.dart';

class VideoScreen extends StatefulWidget {
  const VideoScreen({super.key});

  @override
  State<VideoScreen> createState() => _VideoScreenState();
}

class _VideoScreenState extends State<VideoScreen> {
  List<VideoItem> _videos = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final list = await context.read<AppState>().videoApi.getList();
      if (mounted) setState(() => _videos = list);
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('视频'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _videos.isEmpty
              ? const Center(child: Text('暂无视频'))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _videos.length,
                    itemBuilder: (context, i) {
                      final v = _videos[i];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: const Icon(Icons.video_file),
                          title: Text(v.filename.split('/').last),
                          subtitle: Text('${v.timestamp} · ${v.duration}s · ${v.frameCount} 帧'),
                          onTap: () => _showVideoInfo(context, v),
                        ),
                      );
                    },
                  ),
                ),
    );
  }

  void _showVideoInfo(BuildContext context, VideoItem v) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(v.filename, style: Theme.of(ctx).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text('时间: ${v.timestamp}'),
            Text('时长: ${v.duration}s · 帧数: ${v.frameCount} · FPS: ${v.fps}'),
            Text('大小: ${v.fileSize} bytes'),
            const SizedBox(height: 16),
            const Text('同机桌面端可使用 path 播放；跨机/移动端需后端提供文件流接口。', style: TextStyle(fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
