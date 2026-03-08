import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../connection/connection_state.dart';
import '../app_state.dart';
import 'chat_screen.dart';
import 'process_screen.dart';
import 'recording_screen.dart';
import 'settings_screen.dart';
import 'video_screen.dart';

class HomeScaffold extends StatefulWidget {
  const HomeScaffold({super.key});

  @override
  State<HomeScaffold> createState() => HomeScaffoldState();
}

/// Public state class for external access
class HomeScaffoldState extends State<HomeScaffold> {
  int _index = 3;

  @override
  void initState() {
    super.initState();
    // Listen for tab changes from AppState (triggered by floating ball)
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final appState = context.read<AppState>();
      appState.addListener(_onAppStateChange);
    });
  }

  @override
  void dispose() {
    context.read<AppState>().removeListener(_onAppStateChange);
    super.dispose();
  }

  void _onAppStateChange() {
    final appState = context.read<AppState>();
    if (appState.desiredTabIndex != null) {
      setState(() {
        _index = appState.desiredTabIndex!;
      });
      // Clear the desired tab after consuming it
      appState.clearDesiredTab();
    }
  }

  bool _hasPermissionIssues(Map<String, dynamic>? status) {
    if (status == null) return false;

    bool denied(String key) {
      final section = status[key];
      return section is Map<String, dynamic> && section['granted'] != true;
    }

    return denied('screen_recording') ||
        denied('accessibility') ||
        denied('input_monitoring');
  }

  static const _tabs = [
    (icon: Icons.fiber_manual_record, label: 'Record'),
    (icon: Icons.video_library, label: 'Videos'),
    (icon: Icons.account_tree, label: 'Process'),
    (icon: Icons.chat, label: 'Chat'),
    (icon: Icons.settings, label: 'Settings'),
  ];

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final connectionState = appState.connectionState;
    final permissionStatus = appState.permissionStatus;
    final showBanner = connectionState.status != ConnectionStatus.connected;

    return Scaffold(
      body: Column(
        children: [
          if (showBanner)
            _ConnectionBanner(
              state: connectionState,
              localFirstAvailable: appState.supportsLocalFirstCoreFeatures,
            ),
          if (_hasPermissionIssues(permissionStatus))
            _PermissionBanner(status: permissionStatus!),
          Expanded(
            child: IndexedStack(
              index: _index,
              children: const [
                RecordingScreen(),
                VideoScreen(),
                ProcessScreen(),
                ChatScreen(),
                SettingsScreen(),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: _tabs
            .map((t) =>
                NavigationDestination(icon: Icon(t.icon), label: t.label))
            .toList(),
      ),
    );
  }
}

///  API
class _ConnectionBanner extends StatelessWidget {
  const _ConnectionBanner(
      {required this.state, required this.localFirstAvailable});

  final ApiConnectionState state;
  final bool localFirstAvailable;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final appState = context.read<AppState>();
    final isConnecting = state.status == ConnectionStatus.connecting;

    final useSoftWarning =
        localFirstAvailable && state.status == ConnectionStatus.error;

    return Material(
      color: useSoftWarning
          ? theme.colorScheme.secondaryContainer
          : (state.status == ConnectionStatus.error
              ? theme.colorScheme.errorContainer
              : theme.colorScheme.surfaceContainerHighest),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            children: [
              if (isConnecting)
                SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: theme.colorScheme.primary,
                  ),
                )
              else
                Icon(
                  useSoftWarning ? Icons.sync_problem : Icons.cloud_off,
                  size: 20,
                  color: useSoftWarning
                      ? theme.colorScheme.onSecondaryContainer
                      : theme.colorScheme.error,
                ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  isConnecting
                      ? 'Connecting to backend...'
                      : (useSoftWarning
                          ? 'Backend features are unavailable. Recording, Videos, and Process still work locally.'
                          : (state.message ?? 'Backend not connected')),
                  style: theme.textTheme.bodySmall,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (!isConnecting) ...[
                TextButton(
                  onPressed: () => appState.checkConnection(),
                  child: const Text('Retry'),
                ),
                TextButton(
                  onPressed: () => _showConfigDialog(context, appState),
                  child: const Text('Config API'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  void _showConfigDialog(BuildContext context, AppState appState) {
    final controller = TextEditingController(
      text: state.config?.baseUrl ?? 'http://127.0.0.1:8765',
    );
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('API URL'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'http://127.0.0.1:8765',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              final url = controller.text.trim();
              if (url.isNotEmpty) {
                Navigator.of(ctx).pop();
                appState.reconnectWithBaseUrl(url);
              }
            },
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }
}

class _PermissionBanner extends StatelessWidget {
  const _PermissionBanner({required this.status});

  final Map<String, dynamic> status;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final appState = context.read<AppState>();

    String line(String key, String label) {
      final section = status[key];
      final granted =
          section is Map<String, dynamic> && section['granted'] == true;
      return granted ? '✓ $label' : '✗ $label';
    }

    return Material(
      color: theme.colorScheme.tertiaryContainer,
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.privacy_tip,
                  color: theme.colorScheme.onTertiaryContainer),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Permissions needed: ${line('screen_recording', 'Screen Recording')} · '
                  '${line('accessibility', 'Accessibility')} · '
                  '${line('input_monitoring', 'Input Monitoring')}',
                  style: theme.textTheme.bodySmall,
                ),
              ),
              TextButton(
                onPressed: () =>
                    appState.refreshPermissionStatus(promptSystem: true),
                child: const Text('Check'),
              ),
              TextButton(
                onPressed: () {
                  appState.setDesiredTabIndex(4);
                },
                child: const Text('Settings'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
