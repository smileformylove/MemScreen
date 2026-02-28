import 'dart:async';

import 'api_client.dart';

class ChatApi {
  ChatApi(this.client);
  final ApiClient client;

  /// POST /chat — non-streaming.
  Future<ChatReply> send(String message, {String? threadId}) async {
    final body = <String, dynamic>{'message': message};
    if (threadId != null && threadId.isNotEmpty) {
      body['thread_id'] = threadId;
    }
    final m = await client.post('/chat', body: body);
    return ChatReply(
      reply: m['reply'] as String?,
      error: m['error'] as String?,
    );
  }

  /// POST /chat/stream — SSE stream of chunks.
  Stream<ChatStreamEvent> sendStream(String message,
      {String? threadId}) async* {
    final body = <String, dynamic>{'message': message};
    if (threadId != null && threadId.isNotEmpty) {
      body['thread_id'] = threadId;
    }
    await for (final event in client.postStream('/chat/stream', body: body)) {
      if (event.containsKey('chunk')) {
        yield ChatStreamChunk(event['chunk'] as String? ?? '');
      } else if (event.containsKey('error')) {
        yield ChatStreamError(event['error'] as String? ?? '');
      } else if (event['done'] == true) {
        yield ChatStreamDone(event['full'] as String? ?? '');
      }
    }
  }

  Future<List<String>> getModels() async {
    final m = await client.get('/chat/models');
    final list = m['models'];
    if (list is List) {
      return list.map((e) => e.toString()).toList();
    }
    return [];
  }

  Future<String?> getCurrentModel() async {
    final m = await client.get('/chat/model');
    return m['model'] as String?;
  }

  Future<void> setModel(String model) async {
    await client.put('/chat/model', body: {'model': model});
  }

  Future<List<ChatHistoryMessage>> getHistory({String? threadId}) async {
    final path = (threadId != null && threadId.isNotEmpty)
        ? '/chat/history?thread_id=${Uri.encodeQueryComponent(threadId)}'
        : '/chat/history';
    final m = await client.get(path);
    final list = m['messages'];
    if (list is! List) return [];
    return list.map((e) {
      final map = e as Map<String, dynamic>;
      return ChatHistoryMessage(
        role: map['role'] as String? ?? 'user',
        content: map['content'] as String? ?? '',
        timestamp: map['timestamp'] as String? ?? '',
      );
    }).toList();
  }

  Future<ChatThreadState> getThreads() async {
    final m = await client.get('/chat/threads');
    final list = m['threads'];
    final threads = <ChatThreadSummary>[];
    if (list is List) {
      for (final item in list) {
        if (item is! Map<String, dynamic>) continue;
        threads.add(
          ChatThreadSummary(
            id: item['id'] as String? ?? '',
            title: item['title'] as String? ?? 'New Chat',
            preview: item['preview'] as String? ?? '',
            createdAt: item['created_at'] as String? ?? '',
            updatedAt: item['updated_at'] as String? ?? '',
            messageCount: (item['message_count'] as num?)?.toInt() ?? 0,
            isActive: item['is_active'] as bool? ?? false,
          ),
        );
      }
    }
    return ChatThreadState(
      activeThreadId: m['active_thread_id'] as String? ?? '',
      threads: threads,
    );
  }

  Future<ChatThreadSummary> createThread({String title = ''}) async {
    final m = await client.post('/chat/threads', body: {'title': title});
    final item = (m['thread'] as Map<String, dynamic>?) ?? <String, dynamic>{};
    return ChatThreadSummary(
      id: item['id'] as String? ?? '',
      title: item['title'] as String? ?? 'New Chat',
      preview: item['preview'] as String? ?? '',
      createdAt: item['created_at'] as String? ?? '',
      updatedAt: item['updated_at'] as String? ?? '',
      messageCount: (item['message_count'] as num?)?.toInt() ?? 0,
      isActive: true,
    );
  }

  Future<void> setActiveThread(String threadId) async {
    await client.put('/chat/threads/active', body: {'thread_id': threadId});
  }
}

class ChatReply {
  ChatReply({this.reply, this.error});
  final String? reply;
  final String? error;
}

sealed class ChatStreamEvent {}

class ChatStreamChunk extends ChatStreamEvent {
  ChatStreamChunk(this.text);
  final String text;
}

class ChatStreamError extends ChatStreamEvent {
  ChatStreamError(this.msg);
  final String msg;
}

class ChatStreamDone extends ChatStreamEvent {
  ChatStreamDone(this.full);
  final String full;
}

class ChatHistoryMessage {
  ChatHistoryMessage({
    required this.role,
    required this.content,
    this.timestamp = '',
  });
  final String role;
  final String content;
  final String timestamp;
}

class ChatThreadState {
  ChatThreadState({
    required this.activeThreadId,
    required this.threads,
  });

  final String activeThreadId;
  final List<ChatThreadSummary> threads;
}

class ChatThreadSummary {
  ChatThreadSummary({
    required this.id,
    required this.title,
    required this.preview,
    required this.createdAt,
    required this.updatedAt,
    required this.messageCount,
    required this.isActive,
  });

  final String id;
  final String title;
  final String preview;
  final String createdAt;
  final String updatedAt;
  final int messageCount;
  final bool isActive;
}
