import 'dart:async';

import 'package:flutter/foundation.dart';

import '../api/recording_api.dart';
import 'recording_tracking_coordinator.dart';

class RecordingLifecycleState {
  bool expectedActive = false;
  bool syncingUnexpectedStop = false;
  Timer? watchdogTimer;
}

class RecordingLifecycleCoordinator {
  RecordingLifecycleCoordinator({
    required RecordingApi recordingApi,
    required RecordingTrackingCoordinator trackingCoordinator,
    required bool Function() autoTrackInputWithRecording,
    required bool Function() recordSystemAudio,
    required bool Function() recordMicrophoneAudio,
    required String Function() recordingAudioSource,
    required String Function() recordingVideoFormat,
    required String Function() recordingAudioFormat,
    required bool Function() recordingAudioDenoise,
    required void Function(bool isRecording) updateFloatingBallState,
    required void Function() requestRecordingStatusRefresh,
    required void Function() requestVideoRefresh,
  }) : _recordingApi = recordingApi,
       _trackingCoordinator = trackingCoordinator,
       _autoTrackInputWithRecording = autoTrackInputWithRecording,
       _recordSystemAudio = recordSystemAudio,
       _recordMicrophoneAudio = recordMicrophoneAudio,
       _recordingAudioSource = recordingAudioSource,
       _recordingVideoFormat = recordingVideoFormat,
       _recordingAudioFormat = recordingAudioFormat,
       _recordingAudioDenoise = recordingAudioDenoise,
       _updateFloatingBallState = updateFloatingBallState,
       _requestRecordingStatusRefresh = requestRecordingStatusRefresh,
       _requestVideoRefresh = requestVideoRefresh;

  final RecordingApi _recordingApi;
  final RecordingTrackingCoordinator _trackingCoordinator;
  final bool Function() _autoTrackInputWithRecording;
  final bool Function() _recordSystemAudio;
  final bool Function() _recordMicrophoneAudio;
  final String Function() _recordingAudioSource;
  final String Function() _recordingVideoFormat;
  final String Function() _recordingAudioFormat;
  final bool Function() _recordingAudioDenoise;
  final void Function(bool isRecording) _updateFloatingBallState;
  final void Function() _requestRecordingStatusRefresh;
  final void Function() _requestVideoRefresh;

  Future<void> start({
    required RecordingLifecycleState lifecycleState,
    required RecordingTrackingState trackingState,
    required int duration,
    required double interval,
    String? mode,
    List<double>? region,
    int? screenIndex,
    int? screenDisplayId,
    String? windowTitle,
  }) async {
    await _trackingCoordinator.maybeStartForRecording(
      autoTrackInputWithRecording: _autoTrackInputWithRecording(),
      state: trackingState,
    );
    try {
      final effectiveAudioSource = await _resolveRecordingAudioSourceForStart();
      await _recordingApi.start(
        duration: duration,
        interval: interval,
        mode: mode,
        region: region,
        screenIndex: screenIndex,
        screenDisplayId: screenDisplayId,
        windowTitle: windowTitle,
        audioSource: effectiveAudioSource,
        videoFormat: _recordingVideoFormat(),
        audioFormat: _recordingAudioFormat(),
        audioDenoise: _recordingAudioDenoise(),
      );
      await Future.delayed(const Duration(milliseconds: 500));
      final status = await _recordingApi.getStatus();
      if (!status.isRecording) {
        await _trackingCoordinator.rollbackFailedStart(state: trackingState);
        _updateFloatingBallState(false);
        _requestRecordingStatusRefresh();
        throw Exception(
          'Recording did not start. Please reselect target and retry.',
        );
      }
      if (_autoTrackInputWithRecording() && !trackingState.boundToRecording) {
        await _trackingCoordinator.maybeStartForRecording(
          autoTrackInputWithRecording: _autoTrackInputWithRecording(),
          state: trackingState,
        );
      }
      lifecycleState.expectedActive = true;
      _startWatchdog(
        lifecycleState: lifecycleState,
        trackingState: trackingState,
      );
      _updateFloatingBallState(true);
      _requestRecordingStatusRefresh();
    } catch (_) {
      await _trackingCoordinator.rollbackFailedStart(state: trackingState);
      lifecycleState.expectedActive = false;
      lifecycleState.watchdogTimer?.cancel();
      rethrow;
    }
  }

  Future<void> stop({
    required RecordingLifecycleState lifecycleState,
    required RecordingTrackingState trackingState,
  }) async {
    await _recordingApi.stop();
    lifecycleState.expectedActive = false;
    lifecycleState.watchdogTimer?.cancel();
    _updateFloatingBallState(false);
    _requestRecordingStatusRefresh();
    _requestVideoRefresh();
    _schedulePostStopRefreshes();
    await _trackingCoordinator.maybeStopAfterRecording(state: trackingState);
  }

  Future<void> syncFromBackend({
    required bool isRecording,
    required RecordingLifecycleState lifecycleState,
    required RecordingTrackingState trackingState,
  }) async {
    if (isRecording) {
      lifecycleState.expectedActive = true;
      _startWatchdog(
        lifecycleState: lifecycleState,
        trackingState: trackingState,
      );
      return;
    }
    if (!lifecycleState.expectedActive) return;
    lifecycleState.expectedActive = false;
    lifecycleState.watchdogTimer?.cancel();
    _updateFloatingBallState(false);
    _requestRecordingStatusRefresh();
    if (lifecycleState.syncingUnexpectedStop) return;
    lifecycleState.syncingUnexpectedStop = true;
    try {
      await _trackingCoordinator.maybeStopAfterRecording(state: trackingState);
      _requestVideoRefresh();
    } catch (e) {
      debugPrint(
        '[RecordingLifecycleCoordinator] Failed to handle unexpected recording stop: $e',
      );
    } finally {
      lifecycleState.syncingUnexpectedStop = false;
    }
  }

  void dispose(RecordingLifecycleState lifecycleState) {
    lifecycleState.watchdogTimer?.cancel();
  }

  Future<String> _resolveRecordingAudioSourceForStart() async {
    final requested = _recordingAudioSource();
    if (requested == 'none') return requested;
    try {
      final diagnosis = await _recordingApi.diagnoseAudio(source: requested);
      var useSystem = _recordSystemAudio();
      var useMic = _recordMicrophoneAudio();

      if (useSystem && !diagnosis.systemDeviceAvailable) {
        useSystem = false;
      }
      if (useMic && !diagnosis.microphoneAvailable) {
        useMic = false;
      }

      final resolved = _composeAudioSource(useSystem, useMic);
      if (resolved != requested) {
        debugPrint(
          '[RecordingLifecycleCoordinator] Audio source fallback: '
          'requested=$requested, resolved=$resolved',
        );
      }
      return resolved;
    } catch (e) {
      debugPrint(
        '[RecordingLifecycleCoordinator] Audio diagnosis failed, '
        'using requested source=$requested: $e',
      );
      return requested;
    }
  }

  String _composeAudioSource(bool useSystem, bool useMic) {
    if (useSystem && useMic) return 'mixed';
    if (useSystem) return 'system_audio';
    if (useMic) return 'microphone';
    return 'none';
  }

  void _startWatchdog({
    required RecordingLifecycleState lifecycleState,
    required RecordingTrackingState trackingState,
  }) {
    lifecycleState.watchdogTimer?.cancel();
    lifecycleState.watchdogTimer = Timer.periodic(const Duration(seconds: 2), (
      _,
    ) async {
      if (!lifecycleState.expectedActive) return;
      try {
        final status = await _recordingApi.getStatus();
        if (!status.isRecording) {
          await syncFromBackend(
            isRecording: false,
            lifecycleState: lifecycleState,
            trackingState: trackingState,
          );
          return;
        }
        if (_autoTrackInputWithRecording() && !trackingState.boundToRecording) {
          await _trackingCoordinator.maybeStartForRecording(
            autoTrackInputWithRecording: _autoTrackInputWithRecording(),
            state: trackingState,
          );
        }
      } catch (e) {
        debugPrint(
          '[RecordingLifecycleCoordinator] Recording watchdog poll failed: $e',
        );
      }
    });
  }

  void _schedulePostStopRefreshes() {
    for (var sec = 1; sec <= 12; sec++) {
      Future.delayed(Duration(seconds: sec), () {
        _requestRecordingStatusRefresh();
        _requestVideoRefresh();
      });
    }
  }
}
