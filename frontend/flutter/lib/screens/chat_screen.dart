import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
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
  List<ChatThreadSummary> _threads = [];
  String _currentReply = '';
  String _activeThreadId = '';
  bool _loading = false;
  StreamSubscription? _streamSub;
  Timer? _thinkingTimer;
  int _thinkingStep = 0;
  String? _selectedContext;
  final List<String> _thinkingLabels = const [
    'Searching recent memories...',
    'Compiling timeline evidence...',
    'Generating suggestions...',
  ];

  @override
  void initState() {
    super.initState();
    _loadThreads();
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

  String get _activeThreadTitle {
    for (final thread in _threads) {
      if (thread.id == _activeThreadId) {
        return thread.title;
      }
    }
    return 'New Chat';
  }

  String _formatThreadStamp(String raw) {
    final text = raw.replaceFirst('T', ' ');
    if (text.length >= 16) return text.substring(0, 16);
    return text;
  }

  Future<void> _loadThreads({bool refreshHistory = true}) async {
    final api = context.read<AppState>().chatApi;
    try {
      final state = await api.getThreads();
      if (!mounted) return;
      setState(() {
        _threads = state.threads;
        if (state.activeThreadId.isNotEmpty) {
          _activeThreadId = state.activeThreadId;
        } else if (_threads.isNotEmpty) {
          _activeThreadId = _threads.first.id;
        }
      });
      if (refreshHistory) {
        await _loadHistory(threadId: _activeThreadId);
      }
    } catch (_) {
      if (refreshHistory) {
        await _loadHistory(threadId: _activeThreadId);
      }
    }
  }

  Future<void> _loadHistory({String? threadId}) async {
    final api = context.read<AppState>().chatApi;
    try {
      final list = await api.getHistory(threadId: threadId);
      if (mounted) {
        setState(() => _history = list);
      }
    } catch (_) {}
  }

  Future<void> _createThread() async {
    if (_loading) return;
    final api = context.read<AppState>().chatApi;
    try {
      final thread = await api.createThread();
      if (!mounted) return;
      setState(() {
        _activeThreadId = thread.id;
        _history = [];
        _currentReply = '';
      });
      await _loadThreads(refreshHistory: true);
      _scrollToBottom();
    } catch (_) {}
  }

  Future<void> _switchThread(String threadId) async {
    if (_loading || threadId.isEmpty || threadId == _activeThreadId) return;
    final api = context.read<AppState>().chatApi;
    try {
      await api.setActiveThread(threadId);
      if (!mounted) return;
      setState(() {
        _activeThreadId = threadId;
        _currentReply = '';
      });
      await _loadThreads(refreshHistory: true);
      _scrollToBottom();
    } catch (_) {}
  }

  Future<void> _openThreadSheet() async {
    final selected = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) {
        final theme = Theme.of(sheetContext);
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      'Chat Threads',
                      style: theme.textTheme.titleMedium,
                    ),
                    const Spacer(),
                    TextButton.icon(
                      onPressed: () => Navigator.pop(sheetContext, '__new__'),
                      icon: const Icon(Icons.add_comment_outlined),
                      label: const Text('New'),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                SizedBox(
                  height: MediaQuery.of(sheetContext).size.height * 0.52,
                  child: ListView.separated(
                    shrinkWrap: true,
                    itemCount: _threads.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final thread = _threads[index];
                      final isActive = thread.id == _activeThreadId;
                      return Material(
                        color: isActive
                            ? theme.colorScheme.primaryContainer
                            : theme.colorScheme.surfaceContainerLow,
                        borderRadius: BorderRadius.circular(14),
                        child: InkWell(
                          borderRadius: BorderRadius.circular(14),
                          onTap: () => Navigator.pop(sheetContext, thread.id),
                          child: Padding(
                            padding: const EdgeInsets.all(12),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        thread.title,
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: theme.textTheme.titleSmall
                                            ?.copyWith(
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Text(
                                      _formatThreadStamp(thread.updatedAt),
                                      style:
                                          theme.textTheme.labelSmall?.copyWith(
                                        color:
                                            theme.colorScheme.onSurfaceVariant,
                                      ),
                                    ),
                                  ],
                                ),
                                if (thread.preview.isNotEmpty) ...[
                                  const SizedBox(height: 6),
                                  Text(
                                    thread.preview,
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style: theme.textTheme.bodySmall?.copyWith(
                                      color: theme.colorScheme.onSurfaceVariant,
                                      height: 1.35,
                                    ),
                                  ),
                                ],
                                const SizedBox(height: 6),
                                Text(
                                  '${thread.messageCount} messages',
                                  style: theme.textTheme.labelSmall?.copyWith(
                                    color: theme.colorScheme.onSurfaceVariant,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
    if (!mounted || selected == null) return;
    if (selected == '__new__') {
      await _createThread();
      return;
    }
    await _switchThread(selected);
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
        _streamSub = api
            .sendStream(messageToSend, threadId: _activeThreadId)
            .listen((event) {
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
                unawaited(_loadThreads(refreshHistory: false));
                break;
            }
          });
          _scrollToBottom();
        });
      } else {
        final reply = await api.send(messageToSend, threadId: _activeThreadId);
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
        unawaited(_loadThreads(refreshHistory: false));
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
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Chat'),
              Text(
                _activeThreadTitle,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
              ),
            ],
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.add_comment_outlined),
              tooltip: 'New Thread',
              onPressed: _loading ? null : _createThread,
            ),
            IconButton(
              icon: const Icon(Icons.history),
              tooltip: 'Threads',
              onPressed: _loading ? null : _openThreadSheet,
            ),
            // Context selector
            if (_selectedContext == null)
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
                  return _Bubble(
                    role: 'assistant',
                    content: _currentReply,
                    isStreaming: true,
                  );
                }
                return _ThinkingRow(label: _thinkingLabels[_thinkingStep]);
              }
              return _ThinkingRow(label: _thinkingLabels[_thinkingStep]);
            },
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
  const _Bubble({
    required this.role,
    required this.content,
    this.isStreaming = false,
  });

  final String role;
  final String content;
  final bool isStreaming;

  static String _normalizeAssistantMarkdown(String input) {
    final normalized = input.replaceAll('\r\n', '\n').replaceAll('\r', '\n');
    final lines = normalized.split('\n');
    final cleaned = <String>[];

    for (final raw in lines) {
      final trimmedRight = raw.replaceFirst(RegExp(r'\s+$'), '');
      final trimmedLeft = trimmedRight.trimLeft();
      final shouldLeftTrim = trimmedLeft.startsWith('#') ||
          trimmedLeft.startsWith('- ') ||
          trimmedLeft.startsWith('* ') ||
          trimmedLeft.startsWith('|') ||
          RegExp(r'^\d+\.\s').hasMatch(trimmedLeft);
      cleaned.add(shouldLeftTrim ? trimmedLeft : trimmedRight);
    }

    return cleaned.join('\n').replaceAll(RegExp(r'\n{3,}'), '\n\n').trim();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUser = role == 'user';
    final bubbleColor = isUser
        ? theme.colorScheme.primaryContainer
        : theme.colorScheme.surfaceContainerHighest;
    final labelColor = isUser
        ? theme.colorScheme.onPrimaryContainer.withValues(alpha: 0.72)
        : theme.colorScheme.onSurfaceVariant;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        constraints:
            BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.84),
        decoration: BoxDecoration(
          color: bubbleColor,
          borderRadius: BorderRadius.circular(16),
          border: isUser
              ? null
              : Border.all(
                  color:
                      theme.colorScheme.outlineVariant.withValues(alpha: 0.45),
                ),
        ),
        child: Column(
          crossAxisAlignment:
              isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            Text(
              isUser ? 'You' : 'MemScreen',
              style: theme.textTheme.labelSmall?.copyWith(
                fontWeight: FontWeight.w600,
                color: labelColor,
                letterSpacing: 0.2,
              ),
            ),
            const SizedBox(height: 8),
            if (isUser || isStreaming)
              SelectableText(content, style: theme.textTheme.bodyLarge)
            else
              MarkdownBody(
                data: _normalizeAssistantMarkdown(content),
                selectable: true,
                softLineBreak: true,
                shrinkWrap: true,
                styleSheet: MarkdownStyleSheet.fromTheme(theme).copyWith(
                  p: theme.textTheme.bodyLarge?.copyWith(height: 1.55),
                  h1: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                    height: 1.25,
                  ),
                  h2: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                    height: 1.3,
                  ),
                  h3: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    height: 1.35,
                  ),
                  strong: theme.textTheme.bodyLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                    height: 1.55,
                  ),
                  blockquote: theme.textTheme.bodyMedium?.copyWith(
                    height: 1.55,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                  code: theme.textTheme.bodyMedium?.copyWith(
                    fontFamily: 'Menlo',
                    height: 1.45,
                    color: theme.colorScheme.onSurface,
                  ),
                  listBullet: theme.textTheme.bodyLarge?.copyWith(height: 1.5),
                  tableHead: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                    height: 1.4,
                  ),
                  tableBody: theme.textTheme.bodyMedium?.copyWith(height: 1.45),
                  tableBorder: TableBorder.all(
                    color:
                        theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
                    width: 0.8,
                  ),
                  tableCellsPadding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 6,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
