import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/process_api.dart';
import '../app_state.dart';

/// type (keypress/click/info)texttime API_HTTP.md / CORE_API 
class SessionEvent {
  SessionEvent({this.type = 'info', this.text = '', this.time = ''});
  String type;
  String text;
  String time;

  Map<String, dynamic> toJson() => {'type': type, 'text': text, 'time': time};
}

class ProcessScreen extends StatefulWidget {
  const ProcessScreen({super.key});

  @override
  State<ProcessScreen> createState() => _ProcessScreenState();
}

class _ProcessScreenState extends State<ProcessScreen> {
  List<ProcessSession> _sessions = [];
  TrackingStatus? _trackingStatus;
  bool _loading = true;
  Timer? _trackingPollTimer;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _trackingPollTimer?.cancel();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final api = context.read<AppState>().processApi;
      final list = await api.getSessions();
      final status = await api.getTrackingStatus();
      if (mounted) {
        setState(() {
          _sessions = list;
          _trackingStatus = status;
          _loading = false;
        });
        if (status.isTracking) _startTrackingPoll();
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _startTrackingPoll() {
    _trackingPollTimer?.cancel();
    _trackingPollTimer = Timer.periodic(const Duration(seconds: 2), (_) async {
      try {
        final status = await context.read<AppState>().processApi.getTrackingStatus();
        if (mounted) setState(() => _trackingStatus = status);
        if (!status.isTracking) _trackingPollTimer?.cancel();
      } catch (_) {}
    });
  }

  Future<void> _startTracking() async {
    try {
      await context.read<AppState>().processApi.startTracking();
      if (mounted) {
        setState(() => _trackingStatus = TrackingStatus(isTracking: true, eventCount: 0));
        _startTrackingPoll();
      }
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Started tracking keyboard/mouse')));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to start tracking: $e')));
    }
  }

  Future<void> _stopTracking() async {
    try {
      await context.read<AppState>().processApi.stopTracking();
      _trackingPollTimer?.cancel();

      // Auto-save session when stopping tracking
      try {
        final result = await context.read<AppState>().processApi.saveSessionFromTracking();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Stopped tracking. Saved ${result.eventsSaved} events (${result.startTime} — ${result.endTime})')),
          );
        }
        // Reload sessions to show the newly saved one
        _load();
      } catch (saveError) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Stopped tracking but failed to save: $saveError')),
          );
        }
      }

      if (mounted) {
        setState(() => _trackingStatus = TrackingStatus(isTracking: false, eventCount: _trackingStatus?.eventCount ?? 0));
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to stop tracking: $e')));
    }
  }

  Future<void> _saveFromTracking() async {
    try {
      final result = await context.read<AppState>().processApi.saveSessionFromTracking();
      _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Saved ${result.eventsSaved} events (${result.startTime} — ${result.endTime})')),
        );
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to save: $e')));
    }
  }

  Future<void> _deleteSession(int id) async {
    try {
      await context.read<AppState>().processApi.deleteSession(id.toString());
      _load();
    } catch (_) {}
  }

  Future<void> _deleteAll() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Clear All Sessions'),
        content: const Text('Are you sure you want to delete all process analysis sessions?'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.of(ctx).pop(true), child: const Text('Confirm')),
        ],
      ),
    );
    if (ok == true) {
      try {
        await context.read<AppState>().processApi.deleteAllSessions();
        _load();
      } catch (_) {}
    }
  }

  void _openSaveSession() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => _SaveSessionSheet(
        onSaved: () {
          Navigator.of(ctx).pop();
          _load();
        },
        onCancel: () => Navigator.of(ctx).pop(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Process Analysis'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_circle_outline),
            tooltip: 'Save session',
            onPressed: _openSaveSession,
          ),
          if (_sessions.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep),
              onPressed: _deleteAll,
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // / Kivy 
                  Card(
                    margin: const EdgeInsets.only(bottom: 16),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(_trackingStatus?.isTracking == true ? Icons.touch_app : Icons.keyboard),
                              const SizedBox(width: 8),
                              Text(
                                'Keyboard/Mouse Tracking',
                                style: Theme.of(context).textTheme.titleMedium,
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _trackingStatus?.isTracking == true
                                ? 'Tracking · ${_trackingStatus!.eventCount} events (local backend)'
                                : 'Track keyboard and mouse events on the backend machine and save as process sessions. Requires accessibility permissions.',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              if (_trackingStatus?.isTracking != true)
                                FilledButton.icon(
                                  onPressed: _startTracking,
                                  icon: const Icon(Icons.play_arrow),
                                  label: const Text('Start Tracking'),
                                )
                              else
                                FilledButton.icon(
                                  onPressed: _stopTracking,
                                  icon: const Icon(Icons.stop),
                                  label: const Text('Stop & Save'),
                                  style: FilledButton.styleFrom(backgroundColor: Colors.orange),
                                ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (_sessions.isEmpty)
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Text('No sessions yet. Add sessions by "Start Tracking" or "Save Session".'),
                      ),
                    )
                  else
                    ...List.generate(_sessions.length, (i) {
                      final s = _sessions[i];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          title: Text('${s.startTime} — ${s.endTime}'),
                          subtitle: Text('Events: ${s.eventCount}  Keystrokes: ${s.keystrokes}  Clicks: ${s.clicks}'),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(
                                icon: const Icon(Icons.analytics),
                                onPressed: () => _openAnalysis(context, s.id),
                              ),
                              IconButton(
                                icon: const Icon(Icons.delete_outline),
                                onPressed: () => _deleteSession(s.id),
                              ),
                            ],
                          ),
                          onTap: () => _openAnalysis(context, s.id),
                        ),
                      );
                    }),
                ],
              ),
            ),
    );
  }

  Future<void> _openAnalysis(BuildContext context, int sessionId) async {
    final api = context.read<AppState>().processApi;
    try {
      final analysis = await api.getSessionAnalysis(sessionId.toString());
      if (!context.mounted) return;
      if (analysis == null) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to load analysis')));
        }
        return;
      }
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (ctx) => ProcessAnalysisScreen(sessionId: sessionId, analysis: analysis),
        ),
      );
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to load analysis: $e')));
      }
    }
  }
}

/// type  + text/time 
class _EventRow extends StatefulWidget {
  const _EventRow({super.key, required this.event, required this.onRemove});

  final SessionEvent event;
  final VoidCallback onRemove;

  @override
  State<_EventRow> createState() => _EventRowState();
}

class _EventRowState extends State<_EventRow> {
  late final TextEditingController _textController;
  late final TextEditingController _timeController;

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController(text: widget.event.text);
    _timeController = TextEditingController(text: widget.event.time);
  }

  @override
  void dispose() {
    _textController.dispose();
    _timeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final e = widget.event;
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Row(
          children: [
            SizedBox(
              width: 100,
              child: DropdownButtonFormField<String>(
                value: e.type,
                decoration: const InputDecoration(isDense: true),
                items: const [
                  DropdownMenuItem(value: 'info', child: Text('info')),
                  DropdownMenuItem(value: 'keypress', child: Text('keypress')),
                  DropdownMenuItem(value: 'click', child: Text('click')),
                ],
                onChanged: (v) {
                  if (v != null) e.type = v;
                },
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                decoration: const InputDecoration(hintText: 'text', isDense: true),
                controller: _textController,
                onChanged: (v) => e.text = v,
              ),
            ),
            const SizedBox(width: 8),
            SizedBox(
              width: 90,
              child: TextField(
                decoration: const InputDecoration(hintText: 'time', isDense: true),
                controller: _timeController,
                onChanged: (v) => e.time = v,
              ),
            ),
            IconButton(
              icon: const Icon(Icons.remove_circle_outline),
              onPressed: widget.onRemove,
            ),
          ],
        ),
      ),
    );
  }
}

///  start_timeend_timeevents POST /process/sessions
class _SaveSessionSheet extends StatefulWidget {
  const _SaveSessionSheet({required this.onSaved, required this.onCancel});

  final VoidCallback onSaved;
  final VoidCallback onCancel;

  @override
  State<_SaveSessionSheet> createState() => _SaveSessionSheetState();
}

class _SaveSessionSheetState extends State<_SaveSessionSheet> {
  late final TextEditingController _startController;
  late final TextEditingController _endController;
  final List<SessionEvent> _events = [];

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    final start = now.subtract(const Duration(hours: 1));
    _startController = TextEditingController(text: _formatTime(start));
    _endController = TextEditingController(text: _formatTime(now));
  }

  @override
  void dispose() {
    _startController.dispose();
    _endController.dispose();
    super.dispose();
  }

  static String _formatTime(DateTime t) {
    return '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}:${t.second.toString().padLeft(2, '0')}';
  }

  void _addEvent() {
    setState(() {
      _events.add(SessionEvent(
        type: 'info',
        text: '',
        time: _formatTime(DateTime.now()),
      ));
    });
  }

  void _removeEvent(int i) {
    setState(() => _events.removeAt(i));
  }

  Future<void> _submit(BuildContext context) async {
    final startTime = _startController.text.trim();
    final endTime = _endController.text.trim();
    if (startTime.isEmpty || endTime.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please fill in start and end time')));
      return;
    }
    final api = context.read<AppState>().processApi;
    final eventsJson = _events.map((e) => e.toJson()).toList();
    try {
      await api.saveSession(
        events: eventsJson,
        startTime: startTime,
        endTime: endTime,
      );
      if (!context.mounted) return;
      widget.onSaved();
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Session saved')));
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to save: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.6,
      minChildSize: 0.3,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollController) {
        return Padding(
          padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(height: 8),
              Text('Save Session', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 16),
              Flexible(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            decoration: const InputDecoration(labelText: 'Start Time', hintText: 'HH:MM:SS'),
                            controller: _startController,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: TextField(
                            decoration: const InputDecoration(labelText: 'End Time', hintText: 'HH:MM:SS'),
                            controller: _endController,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Text('Events (type / text / time)', style: Theme.of(context).textTheme.bodySmall),
                        const Spacer(),
                        TextButton.icon(
                          onPressed: _addEvent,
                          icon: const Icon(Icons.add),
                          label: const Text('Add Event'),
                        ),
                      ],
                    ),
                    ...List.generate(_events.length, (i) {
                      final e = _events[i];
                      return _EventRow(
                        key: ValueKey(i),
                        event: e,
                        onRemove: () => _removeEvent(i),
                      );
                    }),
                    const SizedBox(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton(onPressed: widget.onCancel, child: const Text('Cancel')),
                        const SizedBox(width: 8),
                        FilledButton(
                          onPressed: () => _submit(context),
                          child: const Text('Save'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class ProcessAnalysisScreen extends StatelessWidget {
  const ProcessAnalysisScreen({super.key, required this.sessionId, required this.analysis});

  final int sessionId;
  final ProcessAnalysis analysis;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Session $sessionId Analysis')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.analytics, size: 20, color: Colors.blue),
                        const SizedBox(width: 8),
                        Text('Statistics', style: Theme.of(context).textTheme.titleMedium),
                      ],
                    ),
                    const SizedBox(height: 12),
                    _StatRow(
                      icon: Icons.event,
                      label: 'Total Events',
                      value: analysis.eventCount.toString(),
                    ),
                    const SizedBox(height: 8),
                    _StatRow(
                      icon: Icons.keyboard,
                      label: 'Keystrokes',
                      value: analysis.keystrokes.toString(),
                    ),
                    const SizedBox(height: 8),
                    _StatRow(
                      icon: Icons.touch_app,
                      label: 'Mouse Clicks',
                      value: analysis.clicks.toString(),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        const Icon(Icons.schedule, size: 18, color: Colors.grey),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            '${analysis.startTime} — ${analysis.endTime}',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // 
            if (analysis.categories.isNotEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.category, size: 20, color: Colors.green),
                          const SizedBox(width: 8),
                          Text('Categories', style: Theme.of(context).textTheme.titleMedium),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: analysis.categories.entries.map((e) => Chip(
                          label: Text('${e.key}: ${e.value}'),
                          backgroundColor: Colors.green.shade50,
                          labelStyle: TextStyle(color: Colors.green.shade900),
                        )).toList(),
                      ),
                    ],
                  ),
                ),
              ),
            if (analysis.categories.isNotEmpty && analysis.patterns.isNotEmpty)
              const SizedBox(height: 16),

            // 
            if (analysis.patterns.isNotEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.auto_awesome, size: 20, color: Colors.purple),
                          const SizedBox(width: 8),
                          Text('Patterns', style: Theme.of(context).textTheme.titleMedium),
                        ],
                      ),
                      const SizedBox(height: 12),
                      ...analysis.patterns.entries.map((e) => Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  width: 8,
                                  height: 8,
                                  margin: const EdgeInsets.only(top: 6),
                                  decoration: BoxDecoration(
                                    color: Colors.purple,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    '${e.key}: ${e.value}',
                                    style: Theme.of(context).textTheme.bodyMedium,
                                  ),
                                ),
                              ],
                            ),
                          )),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _StatRow extends StatelessWidget {
  const _StatRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 18, color: Colors.grey.shade700),
        const SizedBox(width: 12),
        Text(
          label,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Colors.grey.shade700,
          ),
        ),
        const Spacer(),
        Text(
          value,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: Theme.of(context).colorScheme.primary,
          ),
        ),
      ],
    );
  }
}
