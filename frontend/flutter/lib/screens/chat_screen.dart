import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/chat_api.dart';
import '../app_state.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  List<ChatHistoryMessage> _history = [];
  String _currentReply = '';
  bool _loading = false;
  StreamSubscription? _streamSub;
  Timer? _thinkingTimer;
  int _thinkingStep = 0;
  String? _selectedContext;
  final List<String> _thinkingLabels = const [
    '正在检索最近记忆...',
    '正在整理时间线证据...',
    '正在生成建议...',
  ];

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  @override
  void dispose() {
    _streamSub?.cancel();
    _stopThinking();
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _startThinking() {
    _thinkingTimer?.cancel();
    _thinkingStep = 0;
    _thinkingTimer = Timer.periodic(const Duration(milliseconds: 1100), (_) {
      if (!mounted || !_loading) return;
      setState(() {
        _thinkingStep = (_thinkingStep + 1) % _thinkingLabels.length;
      });
    });
  }

  void _stopThinking() {
    _thinkingTimer?.cancel();
    _thinkingTimer = null;
  }

  Future<void> _loadHistory() async {
    final api = context.read<AppState>().chatApi;
    try {
      final list = await api.getHistory();
      if (mounted) setState(() => _history = list);
    } catch (_) {}
  }

  Future<void> _send(bool stream) async {
    final text = _inputController.text.trim();
    if (text.isEmpty || _loading) return;
    _inputController.clear();

    // Build message with context
    String messageToSend = text;
    if (_selectedContext != null && _selectedContext != 'no_context') {
      messageToSend = '[Context: $_selectedContext]\n$text';
    }

    setState(() {
      _history = [..._history, ChatHistoryMessage(role: 'user', content: text)];
      _currentReply = '';
      _loading = true;
    });
    _startThinking();
    _scrollToBottom();

    final api = context.read<AppState>().chatApi;
    try {
      await _streamSub?.cancel();
      if (stream) {
        _streamSub = api.sendStream(messageToSend).listen((event) {
          if (!mounted) return;
          setState(() {
            switch (event) {
              case ChatStreamChunk(:final text):
                _currentReply += text;
                break;
              case ChatStreamError(:final msg):
                _currentReply = 'Error: $msg';
                _loading = false;
                _stopThinking();
                break;
              case ChatStreamDone(:final full):
                _currentReply = full;
                _history = [
                  ..._history,
                  ChatHistoryMessage(role: 'assistant', content: full)
                ];
                _currentReply = '';
                _loading = false;
                _stopThinking();
                break;
            }
          });
          _scrollToBottom();
        });
      } else {
        final reply = await api.send(messageToSend);
        if (!mounted) return;
        setState(() {
          if (reply.error != null) {
            _history = [
              ..._history,
              ChatHistoryMessage(
                  role: 'assistant', content: 'Error: ${reply.error}')
            ];
          } else if (reply.reply != null) {
            _history = [
              ..._history,
              ChatHistoryMessage(role: 'assistant', content: reply.reply!)
            ];
          }
          _loading = false;
        });
        _stopThinking();
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _history = [
            ..._history,
            ChatHistoryMessage(role: 'assistant', content: 'Request failed: $e')
          ];
          _loading = false;
        });
      }
      _stopThinking();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        AppBar(
          title: const Text('Chat'),
          actions: [
            // Context selector
            if (_selectedContext != null)
              PopupMenuButton<String>(
                tooltip: 'Context',
                icon: const Icon(Icons.link),
                onSelected: (context) =>
                    setState(() => _selectedContext = context),
                itemBuilder: (context) => [
                  const PopupMenuItem(
                    value: 'no_context',
                    child: Text('No Context'),
                  ),
                  const PopupMenuDivider(),
                  const PopupMenuItem(
                    value: 'video_context',
                    enabled: false, // TODO: Fetch from video list
                    child: Text('From Video'),
                  ),
                  const PopupMenuItem(
                    value: 'session_context',
                    enabled: false, // TODO: Fetch from process sessions
                    child: Text('From Session'),
                  ),
                ],
              )
            else
              IconButton(
                icon: const Icon(Icons.close),
                tooltip: 'Clear context',
                onPressed: () => setState(() => _selectedContext = null),
              ),
          ],
        ),
        Expanded(
          child: SelectionArea(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _history.length +
                  (_currentReply.isNotEmpty ? 1 : 0) +
                  (_loading ? 1 : 0),
              itemBuilder: (context, i) {
                if (i < _history.length) {
                  final msg = _history[i];
                  return _Bubble(role: msg.role, content: msg.content);
                }
                if (_currentReply.isNotEmpty) {
                  if (i == _history.length) {
                    return _Bubble(role: 'assistant', content: _currentReply);
                  }
                  return _ThinkingRow(label: _thinkingLabels[_thinkingStep]);
                }
                return _ThinkingRow(label: _thinkingLabels[_thinkingStep]);
              },
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(8),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _inputController,
                  decoration: InputDecoration(
                    hintText: _selectedContext != null
                        ? 'Enter message with context...'
                        : 'Enter a message...',
                    border: const OutlineInputBorder(),
                  ),
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _send(true),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                onPressed: _loading ? null : () => _send(true),
                icon: const Icon(Icons.send),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ThinkingRow extends StatelessWidget {
  const _ThinkingRow({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 10, left: 4),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          const SizedBox(width: 10),
          Text(
            label,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.role, required this.content});

  final String role;
  final String content;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUser = role == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        constraints:
            BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.8),
        decoration: BoxDecoration(
          color: isUser
              ? theme.colorScheme.primaryContainer
              : theme.colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16),
        ),
        child: SelectableText(content, style: theme.textTheme.bodyLarge),
      ),
    );
  }
}
