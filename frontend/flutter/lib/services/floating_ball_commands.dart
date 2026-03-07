class FloatingBallStartRecordingRequest {
  const FloatingBallStartRecordingRequest({
    required this.mode,
    required this.region,
    required this.screenIndex,
    required this.screenDisplayId,
    required this.windowTitle,
  });

  final String mode;
  final List<double>? region;
  final int? screenIndex;
  final int? screenDisplayId;
  final String? windowTitle;

  factory FloatingBallStartRecordingRequest.fromArguments(dynamic arguments) {
    final args = arguments is Map ? arguments : const {};
    final rawMode = args['mode'];
    var mode = rawMode is String && rawMode.isNotEmpty ? rawMode : 'fullscreen';
    if (mode == 'window') {
      mode = 'region';
    }

    List<double>? region;
    final rawRegion = args['region'];
    if (rawRegion is List) {
      region = rawRegion.map((value) => (value as num).toDouble()).toList();
      if (region.length != 4) {
        region = null;
      }
    }

    int? screenIndex;
    final rawScreenIndex = args['screenIndex'] ?? args['screen_index'];
    if (rawScreenIndex is int) {
      screenIndex = rawScreenIndex;
    } else if (rawScreenIndex is num) {
      screenIndex = rawScreenIndex.toInt();
    }

    int? screenDisplayId;
    final rawScreenDisplayId =
        args['screenDisplayId'] ?? args['screen_display_id'];
    if (rawScreenDisplayId is int) {
      screenDisplayId = rawScreenDisplayId;
    } else if (rawScreenDisplayId is num) {
      screenDisplayId = rawScreenDisplayId.toInt();
    }

    final rawWindowTitle = args['windowTitle'] ?? args['window_title'];
    final windowTitle = rawWindowTitle is String && rawWindowTitle.isNotEmpty
        ? rawWindowTitle
        : null;

    if (mode == 'region' && (region == null || region.length != 4)) {
      mode = (screenIndex != null || screenDisplayId != null)
          ? 'fullscreen-single'
          : 'fullscreen';
      region = null;
    }

    return FloatingBallStartRecordingRequest(
      mode: mode,
      region: region,
      screenIndex: screenIndex,
      screenDisplayId: screenDisplayId,
      windowTitle: windowTitle,
    );
  }
}
