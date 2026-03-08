import 'package:flutter/services.dart';

class NativePermissionService {
  static const _channel = MethodChannel('com.memscreen/native_permissions');

  Future<Map<String, dynamic>> getStatus({bool prompt = false}) async {
    final raw = await _channel.invokeMethod<dynamic>('nativePermissionStatus', {
      'prompt': prompt,
    });
    return raw is Map<String, dynamic>
        ? raw
        : Map<String, dynamic>.from(raw as Map);
  }

  Future<bool> openSettings(String area) async {
    final raw =
        await _channel.invokeMethod<dynamic>('openNativePermissionSettings', {
      'area': area,
    });
    final map = raw is Map<String, dynamic>
        ? raw
        : Map<String, dynamic>.from(raw as Map);
    return map['ok'] == true;
  }
}
