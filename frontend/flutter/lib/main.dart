import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'app_state.dart';
import 'connection/connection_state.dart';
import 'screens/home_scaffold.dart';

void main() {
  runApp(const MemScreenApp());
}

class MemScreenApp extends StatelessWidget {
  const MemScreenApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppState(),
      child: MaterialApp(
        title: 'MemScreen',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
          useMaterial3: true,
        ),
        home: const _HomeWrapper(),
      ),
    );
  }
}

/// Starts on main screen; triggers connection check in background.
class _HomeWrapper extends StatefulWidget {
  const _HomeWrapper();

  @override
  State<_HomeWrapper> createState() => _HomeWrapperState();
}

class _HomeWrapperState extends State<_HomeWrapper> {
  Timer? _connectionRetryTimer;
  Timer? _initialConnectionTimer;
  int _connectionRetryCount = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final appState = context.read<AppState>();
      appState.refreshPermissionStatus();
      _initialConnectionTimer = Timer(const Duration(seconds: 5), () {
        if (!mounted) return;
        appState.checkConnection();
        _startConnectionRetryLoop();
      });
    });
  }

  void _startConnectionRetryLoop() {
    _connectionRetryTimer?.cancel();
    _connectionRetryTimer = Timer.periodic(const Duration(seconds: 3), (_) {
      if (!mounted) return;
      final appState = context.read<AppState>();
      if (appState.connectionState.status == ConnectionStatus.connected) {
        _connectionRetryTimer?.cancel();
        return;
      }
      if (_connectionRetryCount >= 40) {
        _connectionRetryTimer?.cancel();
        return;
      }
      _connectionRetryCount += 1;
      appState.checkConnection();
    });
  }

  @override
  void dispose() {
    _initialConnectionTimer?.cancel();
    _connectionRetryTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return const HomeScaffold();
  }
}
