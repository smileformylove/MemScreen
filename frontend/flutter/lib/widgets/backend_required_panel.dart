import 'package:flutter/material.dart';

class BackendRequiredPanel extends StatelessWidget {
  const BackendRequiredPanel({
    super.key,
    required this.title,
    required this.description,
    required this.isStarting,
    required this.onStart,
    this.message,
    this.centered = false,
    this.icon = Icons.smart_toy_outlined,
    this.padding = const EdgeInsets.all(12),
  });

  final String title;
  final String description;
  final bool isStarting;
  final VoidCallback? onStart;
  final String? message;
  final bool centered;
  final IconData icon;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final content = Container(
      padding: padding,
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment:
            centered ? CrossAxisAlignment.center : CrossAxisAlignment.start,
        children: [
          Icon(icon,
              size: centered ? 56 : 24, color: theme.colorScheme.primary),
          SizedBox(height: centered ? 16 : 12),
          Text(
            title,
            textAlign: centered ? TextAlign.center : TextAlign.start,
            style: centered
                ? theme.textTheme.titleLarge
                : theme.textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(
            description,
            textAlign: centered ? TextAlign.center : TextAlign.start,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          if ((message ?? '').isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(
              message!,
              textAlign: centered ? TextAlign.center : TextAlign.start,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.error,
              ),
            ),
          ],
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: isStarting ? null : onStart,
            icon: isStarting
                ? SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: theme.colorScheme.onPrimary,
                    ),
                  )
                : const Icon(Icons.play_arrow),
            label: Text(isStarting ? 'Starting Backend...' : 'Start Backend'),
          ),
        ],
      ),
    );

    if (!centered) {
      return content;
    }
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: content,
      ),
    );
  }
}
