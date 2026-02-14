import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:provider/provider.dart';

import '../api/config_api.dart';
import '../app_state.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          const SizedBox(height: 8),
          ListTile(
            leading: const Icon(Icons.link),
            title: const Text('API URL'),
            subtitle: Text(context.watch<AppState>().config.baseUrl),
            onTap: () {
              // URL modification via ConnectionGate when backend unreachable
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                    content: Text(
                        'Use "Config API" when backend is unreachable to modify')),
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
            title: const Text('About'),
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

class AboutScreen extends StatefulWidget {
  const AboutScreen({super.key});

  @override
  State<AboutScreen> createState() => _AboutScreenState();
}

class _AboutScreenState extends State<AboutScreen> {
  late final Future<PackageInfo> _packageInfoFuture;

  @override
  void initState() {
    super.initState();
    _packageInfoFuture = PackageInfo.fromPlatform();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('About')),
      body: FutureBuilder<PackageInfo>(
        future: _packageInfoFuture,
        builder: (context, snapshot) {
          final version = snapshot.hasData ? snapshot.data!.version : 'Loading...';
          return Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('MemScreen Flutter',
                    style:
                        TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text('版本: $version'),
                const SizedBox(height: 16),
                const Text(
                  'Optional Flutter frontend for MemScreen, coexisting with the default Kivy UI. '
                  'Start MemScreen API first (conda activate MemScreen, then python -m memscreen.api), '
                  'then run this app.',
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
