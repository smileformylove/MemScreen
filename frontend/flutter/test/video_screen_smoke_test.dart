import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:memscreen_flutter/api/video_api.dart';
import 'package:memscreen_flutter/app_state.dart';
import 'package:memscreen_flutter/connection/connection_state.dart';
import 'package:memscreen_flutter/screens/video_screen.dart';

class FakeVideoAppState extends AppState {
  FakeVideoAppState() : super();

  @override
  bool get isBackendConnected => false;

  @override
  int get currentTabIndex => 1;

  @override
  ApiConnectionState get connectionState => ApiConnectionState(
        status: ConnectionStatus.error,
        message: 'Backend not connected',
      );

  @override
  Future<List<VideoItem>> loadVideosForUi() async {
    return [
      VideoItem(
        filename: '/Users/test/.memscreen/videos/demo.mov',
        timestamp: '2026-03-09 12:00:00',
        frameCount: 10,
        fps: 5,
        duration: 2,
        fileSize: 2048,
        recordingMode: 'fullscreen',
        appName: 'MemScreen',
        tags: const ['topic:demo'],
        contentSummary: 'Local cached demo recording',
      ),
    ];
  }
}

void main() {
  testWidgets('Video screen surfaces local fallback mode', (tester) async {
    tester.view.physicalSize = const Size(1600, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    final appState = FakeVideoAppState();
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: const MaterialApp(home: VideoScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Local library mode'), findsOneWidget);
    expect(
      find.textContaining('reanalysis needs the backend'),
      findsOneWidget,
    );
    expect(find.byTooltip('Reanalysis needs backend'), findsOneWidget);
  });
}
