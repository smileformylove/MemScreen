import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'app_state.dart';
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
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().checkConnection();
    });
  }

  @override
  Widget build(BuildContext context) {
    return const HomeScaffold();
  }
}
