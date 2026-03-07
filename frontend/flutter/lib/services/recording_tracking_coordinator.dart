import 'dart:async';

import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../api/process_api.dart';

class RecordingTrackingState {
  bool startedByRecording = false;
  bool boundToRecording = false;
  String? pendingRecordingNotice;
}

class RecordingTrackingCoordinator {
  RecordingTrackingCoordinator({
    required ProcessApi processApi,
    required void Function() requestRecordingStatusRefresh,
    required void Function() requestVideoRefresh,
    required void Function(bool isTracking) updateFloatingBallTracking,
  }) : _processApi = processApi,
       _requestRecordingStatusRefresh = requestRecordingStatusRefresh,
       _requestVideoRefresh = requestVideoRefresh,
       _updateFloatingBallTracking = updateFloatingBallTracking;

  final ProcessApi _processApi;
  final void Function() _requestRecordingStatusRefresh;
  final void Function() _requestVideoRefresh;
  final void Function(bool isTracking) _updateFloatingBallTracking;

  Future<void> maybeStartForRecording({
    required bool autoTrackInputWithRecording,
    required RecordingTrackingState state,
  }) async {
    state.startedByRecording = false;
    state.boundToRecording = false;
    if (!autoTrackInputWithRecording) return;
    try {
      final status = await _processApi.getTrackingStatus();
      if (status.isTracking) {
        await _processApi.markTrackingStart();
        state.boundToRecording = true;
        _updateFloatingBallTracking(true);
        _requestRecordingStatusRefresh();
        return;
      }

      await _processApi.startTracking();
      state.startedByRecording = true;
      state.boundToRecording = true;
      _updateFloatingBallTracking(true);
      _requestRecordingStatusRefresh();
    } catch (e) {
      var reason =
          'Key-Mouse tracking did not start. Video recording continues.';
      if (e is ApiException) {
        final details = e.message.trim();
        if (details.isNotEmpty) {
          reason = 'Key-Mouse tracking disabled for this recording: $details';
        }
      }
      state.pendingRecordingNotice = reason;
      debugPrint(
        '[RecordingTrackingCoordinator] Failed to auto-start input tracking: $e',
      );
    }
  }

  Future<void> maybeStopAfterRecording({
    required RecordingTrackingState state,
  }) async {
    if (!state.boundToRecording) return;
    try {
      if (state.startedByRecording) {
        await _processApi.stopTracking();
        _updateFloatingBallTracking(false);
        _requestRecordingStatusRefresh();
      }
      await _saveTrackingSessionForRecording();
    } catch (e) {
      debugPrint(
        '[RecordingTrackingCoordinator] Failed to auto-stop input tracking: $e',
      );
    } finally {
      state.startedByRecording = false;
      state.boundToRecording = false;
    }
  }

  Future<void> rollbackFailedStart({
    required RecordingTrackingState state,
  }) async {
    if (!state.boundToRecording) return;
    try {
      if (state.startedByRecording) {
        await _processApi.stopTracking();
        _updateFloatingBallTracking(false);
        _requestRecordingStatusRefresh();
      }
    } catch (e) {
      debugPrint(
        '[RecordingTrackingCoordinator] Failed to rollback input tracking after start failure: $e',
      );
    } finally {
      state.startedByRecording = false;
      state.boundToRecording = false;
    }
  }

  Future<void> toggleTrackingFromFloatingBall({
    required RecordingTrackingState state,
  }) async {
    final status = await _processApi.getTrackingStatus();
    if (status.isTracking) {
      await _processApi.stopTracking();
      state.startedByRecording = false;
      _updateFloatingBallTracking(false);
      _requestVideoRefresh();
      _requestRecordingStatusRefresh();
      Future.delayed(const Duration(milliseconds: 400), () async {
        try {
          final result = await _processApi.saveSessionFromTracking();
          if (result.eventsSaved > 0) {
            _requestVideoRefresh();
          }
        } catch (e) {
          debugPrint(
            '[RecordingTrackingCoordinator] Error saving tracking session: $e',
          );
        }
      });
      return;
    }

    await _processApi.startTracking();
    state.startedByRecording = false;
    _updateFloatingBallTracking(true);
    _requestRecordingStatusRefresh();
  }

  Future<void> _saveTrackingSessionForRecording() async {
    await Future.delayed(const Duration(milliseconds: 400));
    for (var attempt = 0; attempt < 3; attempt++) {
      try {
        final result = await _processApi.saveSessionFromTracking();
        if (result.eventsSaved > 0) {
          _requestVideoRefresh();
        }
        return;
      } catch (e) {
        final msg = e.toString().toLowerCase();
        final noEvents =
            msg.contains('no events') ||
            msg.contains('no meaningful events') ||
            msg.contains('not enough events');
        if (noEvents) {
          if (attempt == 2) {
            return;
          }
        } else if (attempt == 2) {
          debugPrint(
            '[RecordingTrackingCoordinator] Error auto-saving tracking session: $e',
          );
          return;
        }
        await Future.delayed(Duration(milliseconds: 250 * (attempt + 1)));
      }
    }
  }
}
