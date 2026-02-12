import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:video_player/video_player.dart';

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
  VideoPlayerController? _controller;
  VideoItem? _currentVideo;

  String _positionLabel = '0:00';
  double _sliderValue = 0.0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final minutes = twoDigits(duration.inMinutes.remainder(60));
    final seconds = twoDigits(duration.inSeconds.remainder(60));
    return '$minutes:$seconds';
  }

  void _updatePosition() {
    if (_controller != null && _controller!.value.isInitialized) {
      final position = _controller!.value.position;
      final duration = _controller!.value.duration;
      setState(() {
        _positionLabel = _formatDuration(position);
        if (duration.inMilliseconds > 0) {
          _sliderValue = position.inMilliseconds / duration.inMilliseconds;
        } else {
          _sliderValue = 0.0;
        }
      });
    }
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final list = await context.read<AppState>().videoApi.getList();
      if (mounted) {
        setState(() {
          _videos = list;
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _playVideo(VideoItem v) async {
    _controller?.dispose();

    final path = v.filename.startsWith('/')
        ? v.filename
        : '/Users/jixiangluo/.memscreen/videos/${v.filename}';
    final file = File(path);

    if (!await file.exists()) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Video file not found')),
        );
      }
      return;
    }

    try {
      final controller = VideoPlayerController.file(file);
      _controller = controller;
      setState(() {
        _currentVideo = v;
        _sliderValue = 0.0;
        _positionLabel = '0:00';
      });

      await controller.initialize();
      controller.addListener(_updatePosition);

      await controller.play();
      if (mounted) {
        setState(() {});
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to play video: $e')),
        );
        setState(() => _currentVideo = null);
      }
    }
  }

  void _closeVideo() {
    _controller?.pause();
    _controller?.removeListener(_updatePosition);
    _controller?.dispose();
    _controller = null;
    setState(() => _currentVideo = null);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Videos'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // 视频录制时间轴 - 始终显示
                _buildTimeline(),
                // 视频播放器或列表区域
                Expanded(
                  child: _currentVideo != null
                      ? _buildVideoPlayer()
                      : _buildVideoList(),
                ),
              ],
            ),
    );
  }

  // 构建时间轴（显示所有录制的视频）
  Widget _buildTimeline() {
    final theme = Theme.of(context);

    if (_videos.isEmpty) {
      return Container(
        height: 50,
        decoration: BoxDecoration(
          color: theme.colorScheme.surfaceContainerHighest,
          border: Border(
            bottom: BorderSide(color: theme.dividerColor, width: 1),
          ),
        ),
        child: Center(
          child: Text(
            '暂无录制视频',
            style: TextStyle(
              color: theme.colorScheme.onSurfaceVariant,
              fontSize: 12,
            ),
          ),
        ),
      );
    }

    return Container(
      height: 50,
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        border: Border(
          bottom: BorderSide(color: theme.dividerColor, width: 1),
        ),
      ),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        itemCount: _videos.length,
        itemBuilder: (context, index) {
          final video = _videos[index];
          final isPlaying = _currentVideo?.filename == video.filename;
          return _buildVideoTimelineNode(video, isPlaying);
        },
      ),
    );
  }

  // 视频时间轴节点 - 圆形设计
  Widget _buildVideoTimelineNode(VideoItem video, bool isPlaying) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6),
      child: GestureDetector(
        onTap: () => _playVideo(video),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 圆形节点
            Container(
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: isPlaying
                    ? LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [
                          theme.colorScheme.primary,
                          theme.colorScheme.primary.withOpacity(0.7),
                        ],
                      )
                    : null,
                color: isPlaying ? null : theme.colorScheme.surfaceContainerLow,
                border: Border.all(
                  color: isPlaying ? theme.colorScheme.primary : theme.dividerColor,
                  width: isPlaying ? 2 : 1,
                ),
                boxShadow: isPlaying
                    ? [
                        BoxShadow(
                          color: theme.colorScheme.primary.withOpacity(0.4),
                          blurRadius: 8,
                          spreadRadius: 1,
                        ),
                      ]
                    : null,
              ),
              child: Icon(
                isPlaying ? Icons.play_arrow : Icons.circle,
                color: isPlaying
                    ? theme.colorScheme.onPrimary
                    : theme.colorScheme.onSurfaceVariant,
                size: 12,
              ),
            ),
            const SizedBox(height: 2),
            // 时间标签 - 更小的字体
            Text(
              video.timestamp,
              style: TextStyle(
                fontSize: 5,
                color: isPlaying
                    ? theme.colorScheme.primary
                    : theme.colorScheme.onSurfaceVariant,
                fontWeight: isPlaying ? FontWeight.bold : FontWeight.normal,
              ),
              maxLines: 1,
              textAlign: TextAlign.center,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  // 视频列表
  Widget _buildVideoList() {
    final theme = Theme.of(context);

    if (_videos.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.video_library, size: 64, color: theme.colorScheme.onSurfaceVariant),
            const SizedBox(height: 16),
            Text(
              '暂无录制视频',
              style: TextStyle(color: theme.colorScheme.onSurfaceVariant, fontSize: 16),
            ),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _videos.length,
      separatorBuilder: (context, index) => Divider(
        height: 1,
        color: theme.dividerColor,
      ),
      itemBuilder: (context, index) {
        final v = _videos[index];
        final isPlaying = _currentVideo?.filename == v.filename;

        return Container(
          decoration: BoxDecoration(
            color: isPlaying
                ? theme.colorScheme.primaryContainer.withOpacity(0.3)
                : Colors.transparent,
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                color: isPlaying
                    ? theme.colorScheme.primaryContainer
                    : theme.colorScheme.surfaceContainerLow,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: isPlaying ? theme.colorScheme.primary : theme.dividerColor,
                  width: 1,
                ),
              ),
              child: Icon(
                Icons.movie,
                color: isPlaying
                    ? theme.colorScheme.primary
                    : theme.colorScheme.onSurfaceVariant,
                size: 24,
              ),
            ),
            title: Text(
              v.filename.split('/').last,
              style: TextStyle(
                color: isPlaying
                    ? theme.colorScheme.primary
                    : theme.colorScheme.onSurface,
                fontWeight: isPlaying ? FontWeight.bold : FontWeight.normal,
                fontSize: 14,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Row(
              children: [
                Icon(Icons.access_time, size: 12, color: theme.colorScheme.onSurfaceVariant),
                const SizedBox(width: 4),
                Text(
                  v.timestamp,
                  style: TextStyle(color: theme.colorScheme.onSurfaceVariant, fontSize: 12),
                ),
                const SizedBox(width: 12),
                Text(
                  '${v.duration}s',
                  style: TextStyle(
                    color: theme.colorScheme.onSurfaceVariant,
                    fontSize: 12,
                    fontFamily: 'monospace',
                  ),
                ),
              ],
            ),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                // 播放按钮
                IconButton(
                  icon: Icon(
                    isPlaying ? Icons.pause : Icons.play_arrow,
                    color: isPlaying
                        ? theme.colorScheme.primary
                        : theme.colorScheme.onSurfaceVariant,
                  ),
                  onPressed: () => _playVideo(v),
                  tooltip: '播放',
                ),
                // 删除按钮
                IconButton(
                  icon: Icon(Icons.delete_outline, color: theme.colorScheme.error),
                  onPressed: () => _deleteVideo(v, index),
                  tooltip: '删除',
                ),
              ],
            ),
            onTap: () => _playVideo(v),
          ),
        );
      },
    );
  }

  // 删除视频
  Future<void> _deleteVideo(VideoItem video, int index) async {
    final theme = Theme.of(context);

    // 确认删除
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: theme.colorScheme.surfaceContainerHigh,
        title: Text('删除视频', style: TextStyle(color: theme.colorScheme.onSurface)),
        content: Text(
          '确定要删除这个视频吗？\n${video.filename.split('/').last}',
          style: TextStyle(color: theme.colorScheme.onSurfaceVariant),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('取消', style: TextStyle(color: theme.colorScheme.onSurfaceVariant)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('删除', style: TextStyle(color: theme.colorScheme.error)),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      try {
        // 删除文件
        final path = video.filename.startsWith('/')
            ? video.filename
            : '/Users/jixiangluo/.memscreen/videos/${video.filename}';
        final file = File(path);
        if (await file.exists()) {
          await file.delete();
        }

        // 如果正在播放这个视频，先关闭
        if (_currentVideo?.filename == video.filename) {
          _closeVideo();
        }

        // 刷新列表
        await _load();

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('视频已删除'),
              duration: Duration(seconds: 2),
            ),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('删除失败: $e'),
              backgroundColor: Colors.red.shade700,
            ),
          );
        }
      }
    }
  }

  // 视频播放器
  Widget _buildVideoPlayer() {
    final theme = Theme.of(context);

    if (_controller == null || !_controller!.value.isInitialized) {
      return Container(
        color: theme.colorScheme.surface,
        child: const Center(child: CircularProgressIndicator()),
      );
    }

    return Stack(
      alignment: Alignment.center,
      children: [
        // 视频显示
        Center(
          child: AspectRatio(
            aspectRatio: _controller!.value.aspectRatio,
            child: VideoPlayer(_controller!),
          ),
        ),

        // 控制面板
        Positioned(
          bottom: 0,
          left: 0,
          right: 0,
          child: Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.transparent,
                  theme.colorScheme.surfaceContainerLow.withOpacity(0.8),
                  theme.colorScheme.surfaceContainerLow.withOpacity(0.95),
                ],
              ),
            ),
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // 进度条
                Row(
                  children: [
                    Text(
                      _positionLabel,
                      style: TextStyle(color: theme.colorScheme.onSurface, fontSize: 13, fontFamily: 'monospace'),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Slider(
                        value: _sliderValue,
                        min: 0.0,
                        max: 1.0,
                        activeColor: theme.colorScheme.primary,
                        inactiveColor: theme.colorScheme.onSurface.withOpacity(0.2),
                        onChanged: (value) {
                          if (_controller != null && _controller!.value.isInitialized) {
                            final position = Duration(
                              milliseconds: (value * _controller!.value.duration.inMilliseconds).toInt(),
                            );
                            _controller!.seekTo(position);
                          }
                        },
                      ),
                    ),
                    Text(
                      _formatDuration(_controller!.value.duration),
                      style: TextStyle(color: theme.colorScheme.onSurfaceVariant, fontSize: 13, fontFamily: 'monospace'),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // 控制按钮
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    IconButton(
                      icon: Icon(
                        _controller!.value.isPlaying ? Icons.pause : Icons.play_arrow,
                        color: theme.colorScheme.onSurface,
                      ),
                      onPressed: () {
                        setState(() {});
                        if (_controller!.value.isPlaying) {
                          _controller!.pause();
                        } else {
                          _controller!.play();
                        }
                      },
                    ),
                    const SizedBox(width: 32),
                    IconButton(
                      icon: Icon(Icons.close, color: theme.colorScheme.onSurfaceVariant),
                      onPressed: _closeVideo,
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                // 视频信息
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.movie, size: 16, color: theme.colorScheme.primary),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _currentVideo?.filename.split('/').last ?? '',
                          style: TextStyle(color: theme.colorScheme.onSurfaceVariant, fontSize: 11),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
