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
  String? _currentModel;

  @override
  void initState() {
    super.initState();
    _loadHistory();
    _loadModel();
  }

  @override
  void dispose() {
    _streamSub?.cancel();
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    final api = context.read<AppState>().chatApi;
    try {
      final list = await api.getHistory();
      if (mounted) setState(() => _history = list);
    } catch (_) {}
  }

  Future<void> _loadModel() async {
    final api = context.read<AppState>().chatApi;
    try {
      final m = await api.getCurrentModel();
      if (mounted) setState(() => _currentModel = m);
    } catch (_) {}
  }

  Future<void> _send(bool stream) async {
    final text = _inputController.text.trim();
    if (text.isEmpty || _loading) return;
    _inputController.clear();
    setState(() {
      _history = [..._history, ChatHistoryMessage(role: 'user', content: text)];
      _currentReply = '';
      _loading = true;
    });
    _scrollToBottom();

    final api = context.read<AppState>().chatApi;
    try {
      if (stream) {
        _streamSub = api.sendStream(text).listen((event) {
          if (!mounted) return;
          setState(() {
            switch (event) {
              case ChatStreamChunk(:final text):
                _currentReply += text;
                break;
              case ChatStreamError(:final msg):
                _currentReply = '错误: $msg';
                _loading = false;
                break;
              case ChatStreamDone(:final full):
                _currentReply = full;
                _history = [..._history, ChatHistoryMessage(role: 'assistant', content: full)];
                _currentReply = '';
                _loading = false;
                break;
              default:
                break;
            }
          });
          _scrollToBottom();
        });
      } else {
        final reply = await api.send(text);
        if (!mounted) return;
        setState(() {
          if (reply.error != null) {
            _history = [..._history, ChatHistoryMessage(role: 'assistant', content: '错误: ${reply.error}')];
          } else if (reply.reply != null) {
            _history = [..._history, ChatHistoryMessage(role: 'assistant', content: reply.reply!)];
          }
          _loading = false;
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _history = [..._history, ChatHistoryMessage(role: 'assistant', content: '请求失败: $e')];
          _loading = false;
        });
      }
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
    final theme = Theme.of(context);
    return Column(
      children: [
        AppBar(
          title: const Text('对话'),
          actions: [
            if (_currentModel != null) Padding(
              padding: const EdgeInsets.only(right: 8),
              child: Center(child: Text(_currentModel!, style: theme.textTheme.bodySmall)),
            ),
            IconButton(
              icon: const Icon(Icons.settings),
              onPressed: () => _showModelPicker(context),
            ),
          ],
        ),
        Expanded(
          child: ListView.builder(
            controller: _scrollController,
            padding: const EdgeInsets.all(16),
            itemCount: _history.length + (_currentReply.isNotEmpty ? 1 : 0) + (_loading && _currentReply.isEmpty ? 1 : 0),
            itemBuilder: (context, i) {
              if (i < _history.length) {
                final msg = _history[i];
                return _Bubble(role: msg.role, content: msg.content);
              }
              if (_currentReply.isNotEmpty) {
                return _Bubble(role: 'assistant', content: _currentReply);
              }
              return const Padding(
                padding: EdgeInsets.all(8),
                child: Row(children: [SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2))]),
              );
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
                  decoration: const InputDecoration(hintText: '输入消息...', border: OutlineInputBorder()),
                  maxLines: 2,
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

  Future<void> _showModelPicker(BuildContext context) async {
    final api = context.read<AppState>().chatApi;
    List<String> models = [];
    try {
      models = await api.getModels();
    } catch (_) {}
    if (!context.mounted) return;
    final chosen = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('选择模型'),
        content: SizedBox(
          width: 280,
          child: ListView.builder(
            shrinkWrap: true,
            itemCount: models.length,
            itemBuilder: (_, i) {
              final m = models[i];
              return ListTile(
                title: Text(m),
                selected: m == _currentModel,
                onTap: () => Navigator.of(ctx).pop(m),
              );
            },
          ),
        ),
      ),
    );
    if (chosen != null) {
      try {
        await api.setModel(chosen);
        setState(() => _currentModel = chosen);
      } catch (_) {}
    }
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
        constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.8),
        decoration: BoxDecoration(
          color: isUser ? theme.colorScheme.primaryContainer : theme.colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(content, style: theme.textTheme.bodyLarge),
      ),
    );
  }
}
