import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

/// Thrown when the API returns 4xx/5xx or network error.
class ApiException implements Exception {
  ApiException(this.message, {this.statusCode, this.body});
  final String message;
  final int? statusCode;
  final String? body;

  @override
  String toString() =>
      'ApiException: $message${statusCode != null ? ' (HTTP $statusCode)' : ''}';
}

/// Generic API client: HTTP, error handling, optional SSE.
class ApiClient {
  ApiClient({ApiConfig? config})
      : config = config ?? ApiConfig.fromEnvironment();

  final ApiConfig config;

  String _url(String path) => config.url(path);

  /// GET with JSON response. Throws [ApiException] on error.
  Future<Map<String, dynamic>> get(String path) async {
    try {
      final uri = Uri.parse(_url(path));
      final response = await http.get(uri).timeout(
            const Duration(seconds: 30),
            onTimeout: () => throw ApiException('Request timeout'),
          );
      return _handleResponse(response);
    } on SocketException {
      throw ApiException(_backendUnavailableMessage());
    } on http.ClientException {
      throw ApiException(_backendUnavailableMessage());
    }
  }

  /// POST with JSON body and optional JSON response.
  Future<Map<String, dynamic>> post(
    String path, {
    Map<String, dynamic>? body,
    Duration timeout = const Duration(seconds: 60),
  }) async {
    try {
      final uri = Uri.parse(_url(path));
      final response = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(timeout, onTimeout: () => throw ApiException('Request timeout'));
      return _handleResponse(response);
    } on SocketException {
      throw ApiException(_backendUnavailableMessage());
    } on http.ClientException {
      throw ApiException(_backendUnavailableMessage());
    }
  }

  /// PUT with JSON body.
  Future<Map<String, dynamic>> put(
    String path, {
    required Map<String, dynamic> body,
  }) async {
    try {
      final uri = Uri.parse(_url(path));
      final response = await http
          .put(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(
            const Duration(seconds: 30),
            onTimeout: () => throw ApiException('Request timeout'),
          );
      return _handleResponse(response);
    } on SocketException {
      throw ApiException(_backendUnavailableMessage());
    } on http.ClientException {
      throw ApiException(_backendUnavailableMessage());
    }
  }

  /// DELETE.
  Future<Map<String, dynamic>> delete(String path) async {
    try {
      final uri = Uri.parse(_url(path));
      final response = await http.delete(uri).timeout(
            const Duration(seconds: 30),
            onTimeout: () => throw ApiException('Request timeout'),
          );
      return _handleResponse(response);
    } on SocketException {
      throw ApiException(_backendUnavailableMessage());
    } on http.ClientException {
      throw ApiException(_backendUnavailableMessage());
    }
  }

  Map<String, dynamic> _handleResponse(http.Response response) {
    final body = response.body;
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (body.isEmpty) return {};
      try {
        return jsonDecode(body) as Map<String, dynamic>;
      } catch (_) {
        return {'raw': body};
      }
    }
    String message = 'HTTP ${response.statusCode}';
    try {
      final m = jsonDecode(body) as Map<String, dynamic>;
      if (m['detail'] != null) message = m['detail'].toString();
    } catch (_) {}
    throw ApiException(message, statusCode: response.statusCode, body: body);
  }

  /// Stream SSE events from POST /chat/stream. Each event is a map (chunk/error/done).
  Stream<Map<String, dynamic>> postStream(
    String path, {
    Map<String, dynamic>? body,
  }) async* {
    final uri = Uri.parse(_url(path));
    final request = http.Request('POST', uri);
    request.headers['Content-Type'] = 'application/json';
    if (body != null) request.body = jsonEncode(body);

    http.StreamedResponse streamed;
    try {
      streamed = await http.Client().send(request);
    } on SocketException {
      throw ApiException(_backendUnavailableMessage());
    } on http.ClientException {
      throw ApiException(_backendUnavailableMessage());
    }
    if (streamed.statusCode != 200) {
      final b = await streamed.stream.bytesToString();
      throw ApiException(
        'HTTP ${streamed.statusCode}',
        statusCode: streamed.statusCode,
        body: b,
      );
    }

    final lines =
        streamed.stream.transform(utf8.decoder).transform(const LineSplitter());

    String? buffer;
    await for (final line in lines) {
      if (line.startsWith('data:')) {
        final data = line.substring(5).trim();
        if (data.isEmpty) continue;
        try {
          final map = jsonDecode(data) as Map<String, dynamic>;
          yield map;
        } catch (_) {}
      }
    }
  }

  String _backendUnavailableMessage() {
    return 'Backend is starting. MemScreen is preparing local runtime, please retry in a few seconds.';
  }
}
