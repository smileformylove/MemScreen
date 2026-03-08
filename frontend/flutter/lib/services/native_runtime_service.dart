import 'package:flutter/services.dart';

class NativeRuntimeBootstrapResult {
  const NativeRuntimeBootstrapResult({
    required this.ok,
    required this.status,
    this.message,
  });

  final bool ok;
  final String status;
  final String? message;

  bool get shouldWaitForBackend => ok;

  factory NativeRuntimeBootstrapResult.fromDynamic(dynamic raw) {
    final map = raw is Map
        ? Map<String, dynamic>.from(raw)
        : const <String, dynamic>{};
    return NativeRuntimeBootstrapResult(
      ok: map['ok'] == true,
      status: map['status'] as String? ?? 'unknown',
      message: map['message'] as String?,
    );
  }
}

class NativeRuntimeService {
  static const _channel = MethodChannel('com.memscreen/native_runtime');

  Future<NativeRuntimeBootstrapResult> ensureBackendBootstrap() async {
    final raw = await _channel.invokeMethod<dynamic>('ensureBackendBootstrap');
    return NativeRuntimeBootstrapResult.fromDynamic(raw);
  }
}
