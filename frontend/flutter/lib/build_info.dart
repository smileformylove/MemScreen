import 'dart:io';

class BuildInfo {
  static const String commit = String.fromEnvironment(
    'MEMSCREEN_BUILD_COMMIT',
    defaultValue: 'dev',
  );

  static const String builtAtUtc = String.fromEnvironment(
    'MEMSCREEN_BUILD_TIME',
    defaultValue: 'unknown',
  );

  static const String buildChannel = String.fromEnvironment(
    'MEMSCREEN_BUILD_CHANNEL',
    defaultValue: 'local',
  );

  static String? detectAppBundlePath() {
    try {
      var dir = File(Platform.resolvedExecutable).parent;
      while (dir.path != dir.parent.path) {
        if (dir.path.toLowerCase().endsWith('.app')) {
          return dir.path;
        }
        dir = dir.parent;
      }
    } catch (_) {}
    return null;
  }
}
