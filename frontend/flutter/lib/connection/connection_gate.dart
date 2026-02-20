import 'package:flutter/material.dart';

import 'connection_state.dart';

/// Shown when backend is unreachable: message, retry, optional URL config.
class ConnectionGate extends StatelessWidget {
  const ConnectionGate({
    super.key,
    required this.connectionState,
    required this.onRetry,
    this.onConfigureUrl,
  });

  final ApiConnectionState connectionState;
  final VoidCallback onRetry;
  final void Function(String baseUrl)? onConfigureUrl;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.cloud_off,
              size: 64,
              color: theme.colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              'Unable to connect to MemScreen backend',
              style: theme.textTheme.titleLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              connectionState.message ?? 'Please make sure the API service is running (conda activate MemScreen, then python -m memscreen.api).',
              style: theme.textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            if (connectionState.config != null) ...[
              const SizedBox(height: 8),
              Text(
                'API: ${connectionState.config!.baseUrl}',
                style: theme.textTheme.bodySmall,
              ),
            ],
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
            if (onConfigureUrl != null) ...[
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => _showUrlDialog(context),
                child: const Text('Configure API URL'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showUrlDialog(BuildContext context) {
    final controller = TextEditingController(
      text: connectionState.config?.baseUrl ?? 'http://127.0.0.1:8765',
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
                onConfigureUrl?.call(url);
              }
            },
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }
}
