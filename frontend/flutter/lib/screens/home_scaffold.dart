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
  State<HomeScaffold> createState() => _HomeScaffoldState();
}

class _HomeScaffoldState extends State<HomeScaffold> {
  int _index = 0;

  static const _tabs = [
    (icon: Icons.chat, label: '对话'),
    (icon: Icons.account_tree, label: '流程'),
    (icon: Icons.fiber_manual_record, label: '录制'),
    (icon: Icons.video_library, label: '视频'),
    (icon: Icons.settings, label: '设置'),
  ];

  @override
  Widget build(BuildContext context) {
    final connectionState = context.watch<AppState>().connectionState;
    final showBanner = connectionState.status != ConnectionStatus.connected;

    return Scaffold(
      body: Column(
        children: [
          if (showBanner) _ConnectionBanner(state: connectionState),
          Expanded(
            child: IndexedStack(
              index: _index,
              children: const [
                ChatScreen(),
                ProcessScreen(),
                RecordingScreen(),
                VideoScreen(),
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
            .map((t) => NavigationDestination(icon: Icon(t.icon), label: t.label))
            .toList(),
      ),
    );
  }
}

/// 顶部连接状态条：未连接时显示，提供重试与配置 API 入口
class _ConnectionBanner extends StatelessWidget {
  const _ConnectionBanner({required this.state});

  final ApiConnectionState state;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final appState = context.read<AppState>();
    final isConnecting = state.status == ConnectionStatus.connecting;

    return Material(
      color: state.status == ConnectionStatus.error
          ? theme.colorScheme.errorContainer
          : theme.colorScheme.surfaceContainerHighest,
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
                  Icons.cloud_off,
                  size: 20,
                  color: theme.colorScheme.error,
                ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  isConnecting
                      ? '正在连接后端…'
                      : (state.message ?? '后端未连接'),
                  style: theme.textTheme.bodySmall,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (!isConnecting) ...[
                TextButton(
                  onPressed: () => appState.checkConnection(),
                  child: const Text('重试'),
                ),
                TextButton(
                  onPressed: () => _showConfigDialog(context, appState),
                  child: const Text('配置 API'),
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
        title: const Text('API 地址'),
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
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () {
              final url = controller.text.trim();
              if (url.isNotEmpty) {
                Navigator.of(ctx).pop();
                appState.reconnectWithBaseUrl(url);
              }
            },
            child: const Text('确定'),
          ),
        ],
      ),
    );
  }
}
