import 'dart:async';

import 'api_client.dart';

class ChatApi {
  ChatApi(this.client);
  final ApiClient client;

  /// POST /chat — non-streaming.
  Future<ChatReply> send(String message) async {
    final m = await client.post('/chat', body: {'message': message});
    return ChatReply(
      reply: m['reply'] as String?,
      error: m['error'] as String?,
    );
  }

  /// POST /chat/stream — SSE stream of chunks.
  Stream<ChatStreamEvent> sendStream(String message) async* {
    await for (final event in client.postStream('/chat/stream', body: {'message': message})) {
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

  Future<List<ChatHistoryMessage>> getHistory() async {
    final m = await client.get('/chat/history');
    final list = m['messages'];
    if (list is! List) return [];
    return list.map((e) {
      final map = e as Map<String, dynamic>;
      return ChatHistoryMessage(
        role: map['role'] as String? ?? 'user',
        content: map['content'] as String? ?? '',
      );
    }).toList();
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
  ChatHistoryMessage({required this.role, required this.content});
  final String role;
  final String content;
}
