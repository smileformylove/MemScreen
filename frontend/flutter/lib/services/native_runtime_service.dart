import 'package:flutter/services.dart';

class NativeRuntimeService {
  static const _channel = MethodChannel('com.memscreen/native_runtime');

  Future<bool> ensureBackendBootstrap() async {
    final raw = await _channel.invokeMethod<dynamic>('ensureBackendBootstrap');
    final map =
        raw is Map ? Map<String, dynamic>.from(raw) : const <String, dynamic>{};
    return map['ok'] == true;
  }
}
