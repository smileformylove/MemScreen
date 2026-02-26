import 'dart:async';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/recording_api.dart';
import '../app_state.dart';
import '../services/floating_ball_service.dart';

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

  //
  String _mode = 'fullscreen';
  int? _screenIndex;
  int? _screenDisplayId;

  //
  double _regionLeft = 0.0;
  double _regionTop = 0.0;
  double _regionRight = 1.0;
  double _regionBottom = 1.0;

  //
  double _screenWidth = 1920.0;
  double _screenHeight = 1080.0;

  //
  final _regionLeftController = TextEditingController(text: '0');
  final _regionTopController = TextEditingController(text: '0');
  final _regionRightController = TextEditingController(text: '1920');
  final _regionBottomController = TextEditingController(text: '1080');

  //
  ui.Image? _screenshotImage;
  String? _screenshotPath;
  bool _capturing = false;
  bool _wasRecording = false;
  AppState? _appState;
  int _lastRecordingStatusVersion = -1;

  @override
  void initState() {
    super.initState();
    _load();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _appState = context.read<AppState>();
      _lastRecordingStatusVersion = _appState!.recordingStatusVersion;
      _appState!.addListener(_onAppStateChanged);
    });

    //
    _regionLeftController.addListener(_updateRegionFromControllers);
    _regionTopController.addListener(_updateRegionFromControllers);
    _regionRightController.addListener(_updateRegionFromControllers);
    _regionBottomController.addListener(_updateRegionFromControllers);
  }

  @override
  void dispose() {
    _appState?.removeListener(_onAppStateChanged);
    _pollTimer?.cancel();
    _regionLeftController.dispose();
    _regionTopController.dispose();
    _regionRightController.dispose();
    _regionBottomController.dispose();
    super.dispose();
  }

  void _onAppStateChanged() {
    if (!mounted || _appState == null) return;
    final currentVersion = _appState!.recordingStatusVersion;
    if (currentVersion != _lastRecordingStatusVersion) {
      _lastRecordingStatusVersion = currentVersion;
      _load();
    }
  }

  void _updateRegionFromControllers() {
    setState(() {
      _regionLeft = (double.tryParse(_regionLeftController.text) ?? 0.0) / 100;
      _regionTop = (double.tryParse(_regionTopController.text) ?? 0.0) / 100;
      _regionRight =
          (double.tryParse(_regionRightController.text) ?? 1920.0) / 100;
      _regionBottom =
          (double.tryParse(_regionBottomController.text) ?? 1080.0) / 100;
    });
  }

  Future<void> _load() async {
    try {
      final api = context.read<AppState>().recordingApi;
      final s = await api.getStatus();
      final screens = await api.getScreens();
      final justStopped = _wasRecording && !s.isRecording;
      if (mounted) {
        setState(() {
          _status = s;
          if (justStopped) {
            _mode = 'fullscreen';
            _screenIndex = null;
            _screenDisplayId = null;
          }
          _screens = screens;
          _loading = false;
          if (screens.isNotEmpty) {
            final selected = _findScreenByIndex(_screenIndex) ??
                screens.firstWhere((x) => x.isPrimary,
                    orElse: () => screens.first);
            _screenDisplayId =
                (_screenIndex == null) ? null : selected.displayId;
            _screenWidth = selected.width.toDouble();
            _screenHeight = selected.height.toDouble();
            if (_regionRight <= _regionLeft || _regionBottom <= _regionTop) {
              _regionLeft = 0.0;
              _regionTop = 0.0;
              _regionRight = 1.0;
              _regionBottom = 1.0;
            }
          }
        });
      }
      _wasRecording = s.isRecording;
      if (s.isRecording) {
        _startPolling();
      } else {
        _stopPolling();
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

  //
  Future<void> _captureScreen() async {
    if (_capturing) return;
    setState(() => _capturing = true);

    try {
      // macOSscreencapture
      final tempDir = Directory.systemTemp;
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final path = '${tempDir.path}/screenshot_$timestamp.png';

      //
      final result = await Process.run('screencapture',
          ['-x', '-t', 'png', '-R', '0,0,$_screenWidth,$_screenHeight', path]);

      if (result.exitCode == 0 || File(path).existsSync()) {
        //
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
          //
          _showRegionSelector();
        }
      } else {
        //
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

  //
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
    final appState = context.read<AppState>();
    final duration = appState.recordingDurationSec;
    final interval = appState.recordingIntervalSec;
    // "Screen" button should always start screen recording from dropdown selection.
    String? mode = 'fullscreen';
    List<double>? region;
    int? screenIndex;
    int? screenDisplayId;

    if (_screenIndex != null) {
      mode = 'fullscreen-single';
      screenIndex = _screenIndex;
      screenDisplayId = _screenDisplayId;
    }

    try {
      final requestedAudioSource = appState.recordingAudioSource;
      if (requestedAudioSource != 'none') {
        final diagnosis = await appState.recordingApi
            .diagnoseAudio(source: requestedAudioSource);

        var useSystem = appState.recordSystemAudio;
        var useMic = appState.recordMicrophoneAudio;
        final notes = <String>[];

        if (useMic && !diagnosis.microphoneAvailable) {
          useMic = false;
          notes.add('Microphone not ready. Microphone recording is disabled.');
        }

        if (useSystem && !diagnosis.systemDeviceAvailable) {
          useSystem = false;
          notes.add(
              'System audio not ready. System audio recording is disabled.');
        }

        final resolvedAudioSource = _resolveAudioSource(useSystem, useMic);
        if (resolvedAudioSource == 'none' &&
            requestedAudioSource != 'none' &&
            notes.isEmpty) {
          notes.add(
              'No available audio input. Recording will continue without audio.');
        }

        if (notes.isNotEmpty && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(notes.join('\n'))),
          );
        }
      }
      if (_mode == 'fullscreen') {
        await FloatingBallService.show();
        await FloatingBallService.prepareScreenRecording(
          screenIndex: _screenIndex,
          screenDisplayId: _screenDisplayId,
        );
      }
      await appState.startRecording(
        duration: duration,
        interval: interval,
        mode: mode,
        region: region,
        screenIndex: screenIndex,
        screenDisplayId: screenDisplayId,
      );
      final notice = appState.consumePendingRecordingNotice();
      if (notice != null && notice.isNotEmpty && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(notice)),
        );
      }
      _wasRecording = true;
      _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to start recording: $e')),
        );
      }
    }
  }

  String _resolveAudioSource(bool useSystem, bool useMic) {
    if (useSystem && useMic) return 'mixed';
    if (useSystem) return 'system_audio';
    if (useMic) return 'microphone';
    return 'none';
  }

  Future<void> _selectRegionWithFloatingBall() async {
    try {
      await FloatingBallService.show();
      await FloatingBallService.prepareRegionSelection(
          screenIndex: _screenIndex, screenDisplayId: _screenDisplayId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Main window minimized. Select region on screen, then start from floating ball.',
          ),
          duration: Duration(seconds: 3),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to select region: $e')),
      );
    }
  }

  Future<void> _selectWindowWithFloatingBall() async {
    try {
      await FloatingBallService.show();
      await FloatingBallService.prepareWindowSelection(
          screenIndex: _screenIndex, screenDisplayId: _screenDisplayId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Main window minimized. Click a window, then confirm recording.',
          ),
          duration: Duration(seconds: 3),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to select window: $e')),
      );
    }
  }

  Future<void> _stop() async {
    try {
      await context.read<AppState>().stopRecording();
      _stopPolling();
      if (mounted) {
        setState(() {
          _mode = 'fullscreen';
          _screenIndex = null;
          _screenDisplayId = null;
        });
      }
      _wasRecording = false;
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
    final isRecording = _status?.isRecording ?? false;
    return [
      Row(
        children: [
          Expanded(
            child: DropdownButtonFormField<int>(
              value: _screenIndex ?? -1,
              decoration: const InputDecoration(
                labelText: 'Full Screen',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
              items: [
                const DropdownMenuItem<int>(
                  value: -1,
                  child: Text('All Screens'),
                ),
                ..._screens.map((e) => DropdownMenuItem<int>(
                      value: e.index,
                      child: Text(
                          '${e.name} (${e.width}x${e.height})${e.isPrimary ? " [Primary]" : ""}'),
                    )),
              ],
              onChanged: isRecording
                  ? null
                  : (v) {
                      _onFullscreenSelected(v);
                    },
            ),
          ),
          const SizedBox(width: 10),
          FilledButton.tonal(
            onPressed: isRecording ? null : _start,
            child: const Text('Screen'),
          ),
        ],
      ),
      const SizedBox(height: 10),
      Row(
        children: [
          Expanded(
            child: FilledButton.tonal(
              onPressed: isRecording ? null : () => _onModeChanged('region'),
              child: const Text('Region'),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: FilledButton.tonal(
              onPressed: isRecording ? null : () => _onModeChanged('window'),
              child: const Text('Window'),
            ),
          ),
        ],
      ),
      const SizedBox(height: 10),
    ];
  }

  Future<void> _onModeChanged(String nextMode) async {
    final isRecording = _status?.isRecording ?? false;
    if (isRecording) return;

    // Allow repeated taps on Region/Window to re-open selector after cancel.
    if (nextMode == 'region') {
      setState(() => _mode = nextMode);
      await _selectRegionWithFloatingBall();
      return;
    }
    if (nextMode == 'window') {
      setState(() => _mode = nextMode);
      await _selectWindowWithFloatingBall();
      return;
    }

    if (_mode == nextMode) return;
    setState(() => _mode = nextMode);

    if (nextMode == 'region') {
      await _selectRegionWithFloatingBall();
    } else if (nextMode == 'window') {
      await _selectWindowWithFloatingBall();
    }
  }

  Future<void> _onFullscreenSelected(int? value) async {
    if (value == null) return;
    final screenIndex = value < 0 ? null : value;
    setState(() {
      _mode = 'fullscreen';
      _screenIndex = screenIndex;
      final selected = _findScreenByIndex(screenIndex);
      if (selected != null) {
        _screenDisplayId = selected.displayId;
        _screenWidth = selected.width.toDouble();
        _screenHeight = selected.height.toDouble();
      } else if (_screens.isNotEmpty) {
        final primary = _screens.firstWhere(
          (x) => x.isPrimary,
          orElse: () => _screens.first,
        );
        _screenDisplayId = (screenIndex == null) ? null : primary.displayId;
        _screenWidth = primary.width.toDouble();
        _screenHeight = primary.height.toDouble();
      } else {
        _screenDisplayId = null;
      }
    });
  }

  RecordingScreenInfo? _findScreenByIndex(int? index) {
    if (index == null) return null;
    for (final s in _screens) {
      if (s.index == index) return s;
    }
    return null;
  }

  List<Widget> _buildActionBar() {
    final isRecording = _status?.isRecording ?? false;
    if (_mode == 'fullscreen') {
      if (!isRecording) return const [];
      return [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            FilledButton.icon(
              onPressed: _stop,
              icon: const Icon(Icons.stop),
              label: const Text('Stop'),
              style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error,
              ),
            ),
          ],
        ),
      ];
    }
    if (_mode == 'region') {
      if (!isRecording) return const [];
      return [
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          FilledButton.icon(
            onPressed: _stop,
            icon: const Icon(Icons.stop),
            label: const Text('Stop'),
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
          ),
        ]),
      ];
    }
    if (_mode == 'window') {
      if (!isRecording) return const [];
      return [
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          FilledButton.icon(
            onPressed: _stop,
            icon: const Icon(Icons.stop),
            label: const Text('Stop'),
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
          ),
        ]),
      ];
    }
    if (!isRecording) return const [];
    return [
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          FilledButton.icon(
            onPressed: _stop,
            icon: const Icon(Icons.stop),
            label: const Text('Stop'),
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
          ),
        ],
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _status == null) {
      return Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Record'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ..._buildModeSelection(),
                ..._buildActionBar(),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

//
class _RegionSelectorDialog extends StatefulWidget {
  final ui.Image screenshotImage;
  final double screenWidth;
  final double screenHeight;
  final double initialLeft;
  final double initialTop;
  final double initialRight;
  final double initialBottom;
  final Function(double left, double top, double right, double bottom)
      onRegionSelected;

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

  //
  bool _isDragging = false;
  bool _isDraggingLeft = false;
  bool _isDraggingTop = false;
  bool _isDraggingRight = false;
  bool _isDraggingBottom = false;
  bool _isMovingRegion = false;

  //
  double _dragStartX = 0;
  double _dragStartY = 0;
  double _dragStartLeft = 0;
  double _dragStartTop = 0;
  double _dragStartRight = 0;
  double _dragStartBottom = 0;

  //
  double get _displayWidth => 800;
  double get _displayHeight =>
      _displayWidth * (widget.screenHeight / widget.screenWidth);

  //
  double get _scale => _displayWidth / widget.screenWidth;

  @override
  void initState() {
    super.initState();
    _left = widget.initialLeft;
    _top = widget.initialTop;
    _right = widget.initialRight;
    _bottom = widget.initialBottom;
  }

  //
  void _handleDragStart(DragStartDetails details) {
    final localPosition = details.localPosition;
    final dx = localPosition.dx;
    final dy = localPosition.dy;

    final leftPx = _left * _displayWidth;
    final topPx = _top * _displayHeight;
    final rightPx = _right * _displayWidth;
    final bottomPx = _bottom * _displayHeight;

    //
    const handleSize = 20.0;
    _isDraggingLeft = (dx - leftPx).abs() < handleSize;
    _isDraggingTop = (dy - topPx).abs() < handleSize;
    _isDraggingRight = (dx - rightPx).abs() < handleSize;
    _isDraggingBottom = (dy - bottomPx).abs() < handleSize;

    //
    if (!_isDraggingLeft &&
        !_isDraggingTop &&
        !_isDraggingRight &&
        !_isDraggingBottom) {
      if (dx > leftPx && dx < rightPx && dy > topPx && dy < bottomPx) {
        _isMovingRegion = true;
      }
    }

    if (_isDraggingLeft ||
        _isDraggingTop ||
        _isDraggingRight ||
        _isDraggingBottom ||
        _isMovingRegion) {
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

  //
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

  //
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
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: Colors.grey.shade600),
              ),
              const SizedBox(height: 16),
              //
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
                    child:
                        SizedBox(width: _displayWidth, height: _displayHeight),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              //
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
                        Text('Region Size:',
                            style: TextStyle(fontWeight: FontWeight.bold)),
                        Text(
                          '${((widthPx / _scale).round()).toString()} × ${((heightPx / _scale).round()).toString()}',
                          style: TextStyle(
                              fontFamily: 'monospace',
                              color: Colors.blue.shade700),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        Text('Position:',
                            style: TextStyle(fontWeight: FontWeight.bold)),
                        Text(
                          '(${(_left * 100).toStringAsFixed(1)}%, ${(_top * 100).toStringAsFixed(1)}%)',
                          style: TextStyle(
                              fontFamily: 'monospace',
                              color: Colors.blue.shade700),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              //
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
                    onPressed: () =>
                        widget.onRegionSelected(_left, _top, _right, _bottom),
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

//
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
    //
    final srcRect =
        Rect.fromLTWH(0, 0, image.width.toDouble(), image.height.toDouble());
    final dstRect = Rect.fromLTWH(0, 0, displayWidth, displayHeight);
    canvas.drawImageRect(image, srcRect, dstRect, Paint());

    //
    final leftPx = left * displayWidth;
    final topPx = top * displayHeight;
    final rightPx = right * displayWidth;
    final bottomPx = bottom * displayHeight;

    //
    final maskPaint = Paint()..color = Colors.black.withOpacity(0.5);

    //
    canvas.drawRect(Rect.fromLTWH(0, 0, displayWidth, topPx), maskPaint);
    //
    canvas.drawRect(
        Rect.fromLTWH(0, bottomPx, displayWidth, displayHeight - bottomPx),
        maskPaint);
    //
    canvas.drawRect(
        Rect.fromLTWH(0, topPx, leftPx, bottomPx - topPx), maskPaint);
    //
    canvas.drawRect(
        Rect.fromLTWH(rightPx, topPx, displayWidth - rightPx, bottomPx - topPx),
        maskPaint);

    //
    final borderPaint = Paint()
      ..color = Colors.red
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    canvas.drawRect(
        Rect.fromLTWH(leftPx, topPx, rightPx - leftPx, bottomPx - topPx),
        borderPaint);

    //
    final handlePaint = Paint()..color = Colors.red;
    const handleSize = 8.0;

    //
    canvas.drawRect(
        Rect.fromLTWH(leftPx - handleSize / 2, topPx - handleSize / 2,
            handleSize, handleSize),
        handlePaint);
    //
    canvas.drawRect(
        Rect.fromLTWH(rightPx - handleSize / 2, topPx - handleSize / 2,
            handleSize, handleSize),
        handlePaint);
    //
    canvas.drawRect(
        Rect.fromLTWH(leftPx - handleSize / 2, bottomPx - handleSize / 2,
            handleSize, handleSize),
        handlePaint);
    //
    canvas.drawRect(
        Rect.fromLTWH(rightPx - handleSize / 2, bottomPx - handleSize / 2,
            handleSize, handleSize),
        handlePaint);
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
