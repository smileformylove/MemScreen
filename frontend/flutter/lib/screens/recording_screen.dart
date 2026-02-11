import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/recording_api.dart';
import '../app_state.dart';

class RecordingScreen extends StatefulWidget {
  const RecordingScreen({super.key});

  @override
  State<RecordingScreen> createState() => _RecordingScreenState();
}

class _RecordingScreenState extends State<RecordingScreen> {
  RecordingStatus? _status;
  List<RecordingScreenInfo> _screens = [];
  bool _loading = true;
  Timer? _pollTimer;

  // 录制前选项（与后端 set_recording_mode 一致）
  String _mode = 'fullscreen';
  int? _screenIndex;
  final _regionLeft = TextEditingController(text: '0');
  final _regionTop = TextEditingController(text: '0');
  final _regionRight = TextEditingController(text: '400');
  final _regionBottom = TextEditingController(text: '300');
  final _durationController = TextEditingController(text: '60');
  final _intervalController = TextEditingController(text: '2.0');

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _regionLeft.dispose();
    _regionTop.dispose();
    _regionRight.dispose();
    _regionBottom.dispose();
    _durationController.dispose();
    _intervalController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final api = context.read<AppState>().recordingApi;
      final s = await api.getStatus();
      final screens = await api.getScreens();
      if (mounted) {
        setState(() {
          _status = s;
          _screens = screens;
          _loading = false;
          if (_mode == 'fullscreen-single' && _screenIndex == null && screens.isNotEmpty) {
            _screenIndex = screens.first.index;
          }
        });
        if (s.isRecording) _startPolling();
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 2), (_) => _load());
  }

  void _stopPolling() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  Future<void> _start() async {
    final duration = int.tryParse(_durationController.text.trim()) ?? 60;
    final interval = double.tryParse(_intervalController.text.trim()) ?? 2.0;
    String? mode = _mode;
    List<double>? region;
    int? screenIndex;
    if (_mode == 'region') {
      final l = double.tryParse(_regionLeft.text.trim()) ?? 0;
      final t = double.tryParse(_regionTop.text.trim()) ?? 0;
      final r = double.tryParse(_regionRight.text.trim()) ?? 400;
      final b = double.tryParse(_regionBottom.text.trim()) ?? 300;
      region = [l, t, r, b];
    } else if (_mode == 'fullscreen-single' && _screenIndex != null) {
      screenIndex = _screenIndex;
    }
    try {
      await context.read<AppState>().recordingApi.start(
            duration: duration,
            interval: interval,
            mode: mode,
            region: region,
            screenIndex: screenIndex,
          );
      _load();
      _startPolling();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('启动录制失败: $e')));
      }
    }
  }

  Future<void> _stop() async {
    try {
      await context.read<AppState>().recordingApi.stop();
      _stopPolling();
      _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('停止录制失败: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _status == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final s = _status ?? RecordingStatus(
          isRecording: false,
          duration: 60,
          interval: 2,
          outputDir: '',
          frameCount: 0,
          elapsedTime: 0,
        );
    return Scaffold(
      appBar: AppBar(title: const Text('录制')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  s.isRecording ? Icons.fiber_manual_record : Icons.stop_circle_outlined,
                  size: 80,
                  color: s.isRecording ? Colors.red : null,
                ),
                const SizedBox(height: 24),
                Text(
                  s.isRecording ? '正在录制' : '未在录制',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                if (s.isRecording) ...[
                  const SizedBox(height: 8),
                  Text('已录制 ${s.elapsedTime} 秒 · ${s.frameCount} 帧'),
                  if (s.outputDir.isNotEmpty) Text('输出: ${s.outputDir}', style: Theme.of(context).textTheme.bodySmall),
                ],
                if (!s.isRecording) ...[
                  const SizedBox(height: 24),
                  const Divider(),
                  Text('录制范围', style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  SegmentedButton<String>(
                    segments: const [
                      ButtonSegment(value: 'fullscreen', label: Text('全屏'), icon: Icon(Icons.desktop_windows)),
                      ButtonSegment(value: 'fullscreen-single', label: Text('单屏'), icon: Icon(Icons.monitor)),
                      ButtonSegment(value: 'region', label: Text('区域'), icon: Icon(Icons.crop_square)),
                    ],
                    selected: {_mode},
                    onSelectionChanged: (v) => setState(() => _mode = v.first),
                  ),
                  if (_mode == 'fullscreen-single') ...[
                    const SizedBox(height: 8),
                    if (_screens.isEmpty)
                      const Text('暂无屏幕列表', style: TextStyle(fontSize: 12))
                    else
                      DropdownButtonFormField<int>(
                        value: _screenIndex ?? _screens.first.index,
                        decoration: const InputDecoration(labelText: '选择屏幕'),
                        items: _screens.map((e) => DropdownMenuItem(value: e.index, child: Text('${e.name} (${e.width}x${e.height})${e.isPrimary ? " [主]" : ""}'))).toList(),
                        onChanged: (v) => setState(() => _screenIndex = v),
                      ),
                  ],
                  if (_mode == 'region') ...[
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(child: TextField(controller: _regionLeft, decoration: const InputDecoration(labelText: '左'), keyboardType: TextInputType.number)),
                        const SizedBox(width: 8),
                        Expanded(child: TextField(controller: _regionTop, decoration: const InputDecoration(labelText: '上'), keyboardType: TextInputType.number)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(child: TextField(controller: _regionRight, decoration: const InputDecoration(labelText: '右'), keyboardType: TextInputType.number)),
                        const SizedBox(width: 8),
                        Expanded(child: TextField(controller: _regionBottom, decoration: const InputDecoration(labelText: '下'), keyboardType: TextInputType.number)),
                      ],
                    ),
                    Text('区域为 (left, top, right, bottom) 像素坐标', style: Theme.of(context).textTheme.bodySmall),
                  ],
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(child: TextField(controller: _durationController, decoration: const InputDecoration(labelText: '时长(秒)'), keyboardType: TextInputType.number)),
                      const SizedBox(width: 16),
                      Expanded(child: TextField(controller: _intervalController, decoration: const InputDecoration(labelText: '间隔(秒)'), keyboardType: const TextInputType.numberWithOptions(decimal: true))),
                    ],
                  ),
                  const SizedBox(height: 24),
                ],
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (!s.isRecording)
                      FilledButton.icon(
                        onPressed: _start,
                        icon: const Icon(Icons.fiber_manual_record),
                        label: const Text('开始录制'),
                      )
                    else
                      FilledButton.icon(
                        onPressed: _stop,
                        icon: const Icon(Icons.stop),
                        label: const Text('停止录制'),
                        style: FilledButton.styleFrom(backgroundColor: Theme.of(context).colorScheme.error),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
