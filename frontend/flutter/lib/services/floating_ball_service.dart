import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Service for controlling the native macOS floating ball
class FloatingBallService {
  static const _channel = MethodChannel('com.memscreen/floating_ball');

  /// Show the floating ball
  static Future<void> show() async {
    try {
      await _channel.invokeMethod('showFloatingBall');
    } catch (e) {
      debugPrint('[FloatingBall] Error showing: $e');
    }
  }

  /// Hide the floating ball
  static Future<void> hide() async {
    try {
      await _channel.invokeMethod('hideFloatingBall');
    } catch (e) {
      debugPrint('[FloatingBall] Error hiding: $e');
    }
  }

  /// Set recording state
  static Future<void> setRecordingState(bool isRecording) async {
    try {
      await _channel.invokeMethod('setRecordingState', {
        'isRecording': isRecording,
      });
    } catch (e) {
      debugPrint('[FloatingBall] Error setting recording state: $e');
    }
  }

  /// Set paused state
  static Future<void> setPausedState(bool isPaused) async {
    try {
      await _channel.invokeMethod('setPausedState', {
        'isPaused': isPaused,
      });
    } catch (e) {
      debugPrint('[FloatingBall] Error setting paused state: $e');
    }
  }

  /// Quit the application
  static Future<void> quitApp() async {
    try {
      await _channel.invokeMethod('quitApp');
    } catch (e) {
      debugPrint('[FloatingBall] Error quitting: $e');
    }
  }

  /// Minimize main window and enter native region-selection flow (macOS).
  /// screenIndex: null means follow current/default screen.
  static Future<void> prepareRegionSelection({int? screenIndex}) async {
    try {
      final args = <String, dynamic>{};
      if (screenIndex != null) {
        args['screenIndex'] = screenIndex;
      }
      await _channel.invokeMethod('prepareRegionSelection', args);
    } catch (e) {
      debugPrint('[FloatingBall] Error preparing region selection: $e');
    }
  }
}
