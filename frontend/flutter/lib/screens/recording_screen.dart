import 'dart:async';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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

  // 录制模式
  String _mode = 'region';
  int? _screenIndex;

  // 区域选择（用比例）
  double _regionLeft = 0.0;
  double _regionTop = 0.0;
  double _regionRight = 1.0;
  double _regionBottom = 1.0;

  // 屏幕尺寸
  double _screenWidth = 1920.0;
  double _screenHeight = 1080.0;

  // 录制参数
  final _durationController = TextEditingController(text: '60');
  final _intervalController = TextEditingController(text: '2.0');

  // 区域输入控制器
  final _regionLeftController = TextEditingController(text: '0');
  final _regionTopController = TextEditingController(text: '0');
  final _regionRightController = TextEditingController(text: '1920');
  final _regionBottomController = TextEditingController(text: '1080');

  // 屏幕截图相关
  ui.Image? _screenshotImage;
  String? _screenshotPath;
  bool _capturing = false;

  @override
  void initState() {
    super.initState();
    _load();

    // 添加监听器实时更新区域显示
    _regionLeftController.addListener(_updateRegionFromControllers);
    _regionTopController.addListener(_updateRegionFromControllers);
    _regionRightController.addListener(_updateRegionFromControllers);
    _regionBottomController.addListener(_updateRegionFromControllers);
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _regionLeftController.dispose();
    _regionTopController.dispose();
    _regionRightController.dispose();
    _regionBottomController.dispose();
    _durationController.dispose();
    _intervalController.dispose();
    super.dispose();
  }

  void _updateRegionFromControllers() {
    setState(() {
      _regionLeft = (double.tryParse(_regionLeftController.text) ?? 0.0) / 100;
      _regionTop = (double.tryParse(_regionTopController.text) ?? 0.0) / 100;
      _regionRight = (double.tryParse(_regionRightController.text) ?? 1920.0) / 100;
      _regionBottom = (double.tryParse(_regionBottomController.text) ?? 1080.0) / 100;
    });
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
          if (screens.isNotEmpty) {
            final primary = screens.firstWhere((s) => s.isPrimary, orElse: () => screens.first);
            _screenWidth = primary.width.toDouble();
            _screenHeight = primary.height.toDouble();
            // 初始化区域为全屏
            _regionLeft = 0.0;
            _regionTop = 0.0;
            _regionRight = 1.0;
            _regionBottom = 1.0;
          }
          if (_mode == 'fullscreen-single' && _screenIndex == null && screens.isNotEmpty) {
            _screenIndex = screens.first.index;
          }
        });
      }
      if (s.isRecording) _startPolling();
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

  // 捕获屏幕截图
  Future<void> _captureScreen() async {
    if (_capturing) return;
    setState(() => _capturing = true);

    try {
      // 使用macOS的screencapture命令截取主屏幕
      final tempDir = Directory.systemTemp;
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final path = '${tempDir.path}/screenshot_$timestamp.png';

      // 执行截图命令（截取主屏幕）
      final result = await Process.run('screencapture', ['-x', '-t', 'png', '-R', '0,0,$_screenWidth,$_screenHeight', path]);

      if (result.exitCode == 0 || File(path).existsSync()) {
        // 读取截图并显示
        final bytes = await File(path).readAsBytes();
        final codec = await ui.instantiateImageCodec(bytes);
        final frame = await codec.getNextFrame();
        final image = frame.image;

        if (mounted) {
          setState(() {
            _screenshotPath = path;
            _screenshotImage = image;
            _capturing = false;
          });
          // 显示区域选择对话框
          _showRegionSelector();
        }
      } else {
        // 如果特定区域失败，尝试全屏截图
        final fullPath = '${tempDir.path}/screenshot_full_$timestamp.png';
        await Process.run('screencapture', ['-x', '-t', 'png', fullPath]);

        if (File(fullPath).existsSync()) {
          final bytes = await File(fullPath).readAsBytes();
          final codec = await ui.instantiateImageCodec(bytes);
          final frame = await codec.getNextFrame();
          final image = frame.image;

          if (mounted) {
            setState(() {
              _screenshotPath = fullPath;
              _screenshotImage = image;
              _capturing = false;
            });
            _showRegionSelector();
          }
        } else {
          if (mounted) setState(() => _capturing = false);
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Failed to capture screen')),
            );
          }
        }
      }
    } catch (e) {
      if (mounted) setState(() => _capturing = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error capturing screen: $e')),
        );
      }
    }
  }

  // 显示区域选择对话框
  void _showRegionSelector() {
    if (_screenshotImage == null) return;

    showDialog(
      context: context,
      builder: (context) => _RegionSelectorDialog(
        screenshotImage: _screenshotImage!,
        screenWidth: _screenWidth,
        screenHeight: _screenHeight,
        initialLeft: _regionLeft,
        initialTop: _regionTop,
        initialRight: _regionRight,
        initialBottom: _regionBottom,
        onRegionSelected: (left, top, right, bottom) {
          setState(() {
            _regionLeft = left;
            _regionTop = top;
            _regionRight = right;
            _regionBottom = bottom;
          });
          Navigator.of(context).pop();
        },
      ),
    );
  }

  Future<void> _start() async {
    final duration = int.tryParse(_durationController.text.trim()) ?? 60;
    final interval = double.tryParse(_intervalController.text.trim()) ?? 2.0;
    String? mode = _mode;
    List<double>? region;
    int? screenIndex;

    if (_mode == 'region') {
      // 将比例转换为实际像素坐标
      final leftPx = (_regionLeft * _screenWidth).round();
      final topPx = (_regionTop * _screenHeight).round();
      final rightPx = (_regionRight * _screenWidth).round();
      final bottomPx = (_regionBottom * _screenHeight).round();
      region = [leftPx.toDouble(), topPx.toDouble(), rightPx.toDouble(), bottomPx.toDouble()];
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
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to start recording: $e')),
        );
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
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to stop recording: $e')),
        );
      }
    }
  }

  List<Widget> _buildModeSelection() {
    return [
      SegmentedButton<String>(
        segments: const [
          ButtonSegment(value: 'fullscreen', label: Text('Full Screen')),
          ButtonSegment(value: 'fullscreen-single', label: Text('Single Screen')),
          ButtonSegment(value: 'region', label: Text('Region')),
        ],
        selected: {_mode},
        onSelectionChanged: (v) => setState(() => _mode = v.first),
      ),
      const SizedBox(height: 16),
    ];
  }

  List<Widget> _buildFullscreenSingleMode() {
    if (_mode != 'fullscreen-single' || _screens.isEmpty) {
      return [];
    }
    return [
      DropdownButtonFormField<int>(
        value: _screenIndex ?? _screens.first.index,
        decoration: const InputDecoration(
          labelText: 'Select Screen',
          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        ),
        items: _screens.map((e) => DropdownMenuItem<int>(
          value: e.index,
          child: Text('${e.name} (${e.width}x${e.height})${e.isPrimary ? " [Primary]" : ""}'),
        )).toList(),
        onChanged: (v) => setState(() => _screenIndex = v),
      ),
    ];
  }

  List<Widget> _buildRegionMode() {
    if (_mode != 'region') {
      return [];
    }

    // 确保status不为null
    final status = _status ?? RecordingStatus(
      isRecording: false,
      duration: 60,
      interval: 2,
      outputDir: '',
      frameCount: 0,
      elapsedTime: 0,
    );

    return [
      // 区域选择标题
      Row(
        children: [
          Text('Recording Region', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const Spacer(),
          if (_mode == 'region') ...[
            OutlinedButton.icon(
              icon: const Icon(Icons.fullscreen),
              label: Text('Full Screen'),
              onPressed: () => setState(() {
                _regionLeft = 0.0;
                _regionTop = 0.0;
                _regionRight = 1.0;
                _regionBottom = 1.0;
              }),
            ),
            const SizedBox(width: 8),
            FilledButton.icon(
              icon: _capturing
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.screenshot),
              label: Text(_capturing ? 'Capturing...' : 'Select on Screen'),
              onPressed: _capturing ? null : _captureScreen,
            ),
          ],
        ],
      ),
      const SizedBox(height: 12),

      // 区域输入行
      Row(
        children: [
          Expanded(
            child: TextField(
              controller: _regionLeftController,
              decoration: const InputDecoration(
                labelText: 'Left (px)',
                isDense: true,
                contentPadding: EdgeInsets.all(8),
              ),
              keyboardType: TextInputType.number,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              controller: _regionTopController,
              decoration: const InputDecoration(
                labelText: 'Top (px)',
                isDense: true,
                contentPadding: EdgeInsets.all(8),
              ),
              keyboardType: TextInputType.number,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              controller: _regionRightController,
              decoration: const InputDecoration(
                labelText: 'Right (px)',
                isDense: true,
                contentPadding: EdgeInsets.all(8),
              ),
              keyboardType: TextInputType.number,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              controller: _regionBottomController,
              decoration: const InputDecoration(
                labelText: 'Bottom (px)',
                isDense: true,
                contentPadding: EdgeInsets.all(8),
              ),
              keyboardType: TextInputType.number,
            ),
          ),
        ],
      ),
      const SizedBox(height: 24),

      // 区域显示（百分比）
      Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.blue.shade50,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.grey.shade300),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Selected Region:', style: TextStyle(fontSize: 12, color: Colors.black87)),
            const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                Text(
                  'Left:   ${(_regionLeft * 100).toStringAsFixed(1)}%',
                  style: TextStyle(fontSize: 11, fontFamily: 'monospace'),
                ),
                Text(
                  'Top:    ${(_regionTop * 100).toStringAsFixed(1)}%',
                  style: TextStyle(fontSize: 11, fontFamily: 'monospace'),
                ),
                Text(
                  'Right:  ${(_regionRight * 100).toStringAsFixed(1)}%',
                  style: TextStyle(fontSize: 11, fontFamily: 'monospace'),
                ),
                Text(
                  'Bottom: ${(_regionBottom * 100).toStringAsFixed(1)}%',
                  style: TextStyle(fontSize: 11, fontFamily: 'monospace'),
                ),
              ],
            ),
          ],
        ),
      ),
      const SizedBox(height: 24),

      // 录制参数设置
      Row(
        children: [
          Expanded(
            child: TextField(
              controller: _durationController,
              decoration: const InputDecoration(
                labelText: 'Duration (seconds)',
                prefixIcon: Icon(Icons.timer, size: 20),
              ),
              keyboardType: TextInputType.number,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: TextField(
              controller: _intervalController,
              decoration: const InputDecoration(
                labelText: 'Interval (seconds)',
                prefixIcon: Icon(Icons.schedule, size: 20),
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
            ),
          ),
        ],
      ),
      const SizedBox(height: 32),

      // 开始/停止按钮
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (!status.isRecording)
            FilledButton.icon(
              onPressed: _start,
              icon: const Icon(Icons.fiber_manual_record),
              label: const Text('Start Recording'),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
              ),
            )
          else
            FilledButton.icon(
              onPressed: _stop,
              icon: const Icon(Icons.stop),
              label: const Text('Stop Recording'),
              style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error,
                padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
              ),
            ),
        ],
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    // 总是提供有效的status对象
    final s = _status ?? RecordingStatus(
          isRecording: false,
          duration: 60,
          interval: 2,
          outputDir: '',
          frameCount: 0,
          elapsedTime: 0,
        );

    if (_loading && _status == null) {
      return Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Screen Recording'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 600),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // 状态显示
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.orange.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.orange.shade300),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.info_outline, color: Colors.blue),
                      const SizedBox(width: 12),
                      Text('区域选择：直接输入像素坐标', style: TextStyle(fontSize: 12, color: Colors.black87)),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        s.isRecording ? Icons.fiber_manual_record : Icons.stop_circle_outlined,
                        size: 48,
                        color: s.isRecording ? Colors.red : Colors.grey,
                      ),
                      const SizedBox(width: 16),
                      Text(
                        s.isRecording ? 'Recording' : 'Not Recording',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      if (s.isRecording) ...[
                        const SizedBox(width: 16),
                        Text(
                          '${s.elapsedTime}s · ${s.frameCount} frames',
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        if (s.outputDir.isNotEmpty)
                          Text('Output: ${s.outputDir}', style: Theme.of(context).textTheme.bodySmall),
                      ],
                    ],
                  ),
                ),

                const SizedBox(height: 24),

                // 录制模式选择
                ..._buildModeSelection(),

                // 屏幕选择或区域设置
                ..._buildFullscreenSingleMode(),
                ..._buildRegionMode(),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// 区域选择对话框
class _RegionSelectorDialog extends StatefulWidget {
  final ui.Image screenshotImage;
  final double screenWidth;
  final double screenHeight;
  final double initialLeft;
  final double initialTop;
  final double initialRight;
  final double initialBottom;
  final Function(double left, double top, double right, double bottom) onRegionSelected;

  const _RegionSelectorDialog({
    required this.screenshotImage,
    required this.screenWidth,
    required this.screenHeight,
    required this.initialLeft,
    required this.initialTop,
    required this.initialRight,
    required this.initialBottom,
    required this.onRegionSelected,
  });

  @override
  State<_RegionSelectorDialog> createState() => _RegionSelectorDialogState();
}

class _RegionSelectorDialogState extends State<_RegionSelectorDialog> {
  late double _left;
  late double _top;
  late double _right;
  late double _bottom;

  // 拖动状态
  bool _isDragging = false;
  bool _isDraggingLeft = false;
  bool _isDraggingTop = false;
  bool _isDraggingRight = false;
  bool _isDraggingBottom = false;
  bool _isMovingRegion = false;

  // 拖动起始位置
  double _dragStartX = 0;
  double _dragStartY = 0;
  double _dragStartLeft = 0;
  double _dragStartTop = 0;
  double _dragStartRight = 0;
  double _dragStartBottom = 0;

  // 显示尺寸
  double get _displayWidth => 800;
  double get _displayHeight => _displayWidth * (widget.screenHeight / widget.screenWidth);

  // 转换系数
  double get _scale => _displayWidth / widget.screenWidth;

  @override
  void initState() {
    super.initState();
    _left = widget.initialLeft;
    _top = widget.initialTop;
    _right = widget.initialRight;
    _bottom = widget.initialBottom;
  }

  // 处理拖动开始
  void _handleDragStart(DragStartDetails details) {
    final localPosition = details.localPosition;
    final dx = localPosition.dx;
    final dy = localPosition.dy;

    final leftPx = _left * _displayWidth;
    final topPx = _top * _displayHeight;
    final rightPx = _right * _displayWidth;
    final bottomPx = _bottom * _displayHeight;

    // 检查是否点击了边框或角落
    const handleSize = 20.0;
    _isDraggingLeft = (dx - leftPx).abs() < handleSize;
    _isDraggingTop = (dy - topPx).abs() < handleSize;
    _isDraggingRight = (dx - rightPx).abs() < handleSize;
    _isDraggingBottom = (dy - bottomPx).abs() < handleSize;

    // 检查是否在区域内
    if (!_isDraggingLeft && !_isDraggingTop && !_isDraggingRight && !_isDraggingBottom) {
      if (dx > leftPx && dx < rightPx && dy > topPx && dy < bottomPx) {
        _isMovingRegion = true;
      }
    }

    if (_isDraggingLeft || _isDraggingTop || _isDraggingRight || _isDraggingBottom || _isMovingRegion) {
      setState(() {
        _isDragging = true;
        _dragStartX = dx;
        _dragStartY = dy;
        _dragStartLeft = _left;
        _dragStartTop = _top;
        _dragStartRight = _right;
        _dragStartBottom = _bottom;
      });
    }
  }

  // 处理拖动更新
  void _handleDragUpdate(DragUpdateDetails details) {
    if (!_isDragging) return;

    final deltaX = (details.localPosition.dx - _dragStartX) / _displayWidth;
    final deltaY = (details.localPosition.dy - _dragStartY) / _displayHeight;

    setState(() {
      if (_isDraggingLeft) {
        _left = (_dragStartLeft + deltaX).clamp(0.0, _right - 0.05);
      }
      if (_isDraggingTop) {
        _top = (_dragStartTop + deltaY).clamp(0.0, _bottom - 0.05);
      }
      if (_isDraggingRight) {
        _right = (_dragStartRight + deltaX).clamp(_left + 0.05, 1.0);
      }
      if (_isDraggingBottom) {
        _bottom = (_dragStartBottom + deltaY).clamp(_top + 0.05, 1.0);
      }
      if (_isMovingRegion) {
        final width = _dragStartRight - _dragStartLeft;
        final height = _dragStartBottom - _dragStartTop;
        _left = (_dragStartLeft + deltaX).clamp(0.0, 1.0 - width);
        _top = (_dragStartTop + deltaY).clamp(0.0, 1.0 - height);
        _right = _left + width;
        _bottom = _top + height;
      }
    });
  }

  // 处理拖动结束
  void _handleDragEnd(DragEndDetails details) {
    setState(() {
      _isDragging = false;
      _isDraggingLeft = false;
      _isDraggingTop = false;
      _isDraggingRight = false;
      _isDraggingBottom = false;
      _isMovingRegion = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final leftPx = _left * _displayWidth;
    final topPx = _top * _displayHeight;
    final rightPx = _right * _displayWidth;
    final bottomPx = _bottom * _displayHeight;
    final widthPx = rightPx - leftPx;
    final heightPx = bottomPx - topPx;

    return Dialog(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: _displayWidth + 40),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Select Recording Region',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              Text(
                'Drag the corners or edges to adjust the region',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey.shade600),
              ),
              const SizedBox(height: 16),
              // 截图显示区域
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: GestureDetector(
                  onPanStart: _handleDragStart,
                  onPanUpdate: _handleDragUpdate,
                  onPanEnd: _handleDragEnd,
                  child: CustomPaint(
                    size: Size(_displayWidth, _displayHeight),
                    painter: _ScreenshotPainter(
                      image: widget.screenshotImage,
                      left: _left,
                      top: _top,
                      right: _right,
                      bottom: _bottom,
                      displayWidth: _displayWidth,
                      displayHeight: _displayHeight,
                    ),
                    child: SizedBox(width: _displayWidth, height: _displayHeight),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              // 区域信息显示
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blue.shade300),
                ),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        Text('Region Size:', style: TextStyle(fontWeight: FontWeight.bold)),
                        Text(
                          '${((widthPx / _scale).round()).toString()} × ${((heightPx / _scale).round()).toString()}',
                          style: TextStyle(fontFamily: 'monospace', color: Colors.blue.shade700),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        Text('Position:', style: TextStyle(fontWeight: FontWeight.bold)),
                        Text(
                          '(${(_left * 100).toStringAsFixed(1)}%, ${(_top * 100).toStringAsFixed(1)}%)',
                          style: TextStyle(fontFamily: 'monospace', color: Colors.blue.shade700),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              // 按钮行
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton.icon(
                    icon: const Icon(Icons.fullscreen),
                    label: const Text('Full Screen'),
                    onPressed: () {
                      setState(() {
                        _left = 0.0;
                        _top = 0.0;
                        _right = 1.0;
                        _bottom = 1.0;
                      });
                    },
                  ),
                  const SizedBox(width: 8),
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('Cancel'),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    onPressed: () => widget.onRegionSelected(_left, _top, _right, _bottom),
                    child: const Text('Confirm'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// 截图画家，绘制图片和区域选择框
class _ScreenshotPainter extends CustomPainter {
  final ui.Image image;
  final double left;
  final double top;
  final double right;
  final double bottom;
  final double displayWidth;
  final double displayHeight;

  _ScreenshotPainter({
    required this.image,
    required this.left,
    required this.top,
    required this.right,
    required this.bottom,
    required this.displayWidth,
    required this.displayHeight,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // 绘制截图
    final srcRect = Rect.fromLTWH(0, 0, image.width.toDouble(), image.height.toDouble());
    final dstRect = Rect.fromLTWH(0, 0, displayWidth, displayHeight);
    canvas.drawImageRect(image, srcRect, dstRect, Paint());

    // 计算区域位置
    final leftPx = left * displayWidth;
    final topPx = top * displayHeight;
    final rightPx = right * displayWidth;
    final bottomPx = bottom * displayHeight;

    // 绘制半透明遮罩（区域外部）
    final maskPaint = Paint()..color = Colors.black.withOpacity(0.5);

    // 顶部遮罩
    canvas.drawRect(Rect.fromLTWH(0, 0, displayWidth, topPx), maskPaint);
    // 底部遮罩
    canvas.drawRect(Rect.fromLTWH(0, bottomPx, displayWidth, displayHeight - bottomPx), maskPaint);
    // 左侧遮罩
    canvas.drawRect(Rect.fromLTWH(0, topPx, leftPx, bottomPx - topPx), maskPaint);
    // 右侧遮罩
    canvas.drawRect(Rect.fromLTWH(rightPx, topPx, displayWidth - rightPx, bottomPx - topPx), maskPaint);

    // 绘制选择框
    final borderPaint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    canvas.drawRect(Rect.fromLTWH(leftPx, topPx, rightPx - leftPx, bottomPx - topPx), borderPaint);

    // 绘制角落手柄
    final handlePaint = Paint()..color = Colors.red;
    const handleSize = 8.0;

    // 左上角
    canvas.drawRect(Rect.fromLTWH(leftPx - handleSize / 2, topPx - handleSize / 2, handleSize, handleSize), handlePaint);
    // 右上角
    canvas.drawRect(Rect.fromLTWH(rightPx - handleSize / 2, topPx - handleSize / 2, handleSize, handleSize), handlePaint);
    // 左下角
    canvas.drawRect(Rect.fromLTWH(leftPx - handleSize / 2, bottomPx - handleSize / 2, handleSize, handleSize), handlePaint);
    // 右下角
    canvas.drawRect(Rect.fromLTWH(rightPx - handleSize / 2, bottomPx - handleSize / 2, handleSize, handleSize), handlePaint);
  }

  @override
  bool shouldRepaint(_ScreenshotPainter oldDelegate) {
    return image != oldDelegate.image ||
        left != oldDelegate.left ||
        top != oldDelegate.top ||
        right != oldDelegate.right ||
        bottom != oldDelegate.bottom;
  }
}
