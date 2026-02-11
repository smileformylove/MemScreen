import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api/config_api.dart';
import '../app_state.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('设置')),
      body: ListView(
        children: [
          const SizedBox(height: 8),
          ListTile(
            leading: const Icon(Icons.link),
            title: const Text('API 地址'),
            subtitle: Text(context.watch<AppState>().config.baseUrl),
            onTap: () {
              // URL 修改在连接失败时通过 ConnectionGate 配置
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('请在后端不可达时使用「配置 API 地址」修改')),
              );
            },
          ),
          const Divider(),
          FutureBuilder<ConfigInfo>(
            future: context.read<AppState>().configApi.get(),
            builder: (context, snap) {
              if (!snap.hasData) return const SizedBox.shrink();
              final c = snap.data!;
              return Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.public),
                    title: const Text('Ollama'),
                    subtitle: Text(c.ollamaBaseUrl),
                  ),
                  ListTile(
                    leading: const Icon(Icons.folder),
                    title: const Text('数据库目录'),
                    subtitle: Text(c.dbDir),
                  ),
                  ListTile(
                    leading: const Icon(Icons.video_file),
                    title: const Text('视频目录'),
                    subtitle: Text(c.videosDir),
                  ),
                ],
              );
            },
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('关于'),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (ctx) => const AboutScreen(),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('关于')),
      body: const Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('MemScreen Flutter', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            Text('版本: 0.1.0'),
            SizedBox(height: 16),
            Text(
              'MemScreen 的可选 Flutter 前端，与 Kivy 默认 UI 并存。'
              '需先启动 MemScreen API（conda activate MemScreen 后 python -m memscreen.api），'
              '再运行本应用。',
            ),
          ],
        ),
      ),
    );
  }
}
