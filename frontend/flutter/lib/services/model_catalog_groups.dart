import '../api/model_api.dart';

class GroupedChatModels {
  const GroupedChatModels(this.label, this.models);

  final String label;
  final List<String> models;
}

class GroupedCatalogModels {
  const GroupedCatalogModels(this.label, this.entries);

  final String label;
  final List<LocalModelEntry> entries;
}

String recommendedUseLabel(LocalModelEntry entry) {
  switch (entry.recommendedUse) {
    case 'ultra_light':
      return 'Ultra-light';
    case 'fast':
      return 'Fast';
    case 'balanced':
      return 'Balanced';
    case 'advanced':
      return 'Advanced';
    case 'vision_fallback':
      return 'Vision';
    case 'embedding':
      return 'Embedding';
    default:
      return 'General';
  }
}

LocalModelEntry? resolveModelDetails(
  String modelName,
  Map<String, LocalModelEntry> byModelName,
) {
  return byModelName[modelName];
}

bool isVisionCapableModel(String modelName, {LocalModelEntry? details}) {
  if (details != null) {
    return details.supportsVision;
  }
  final normalized = modelName.toLowerCase();
  return normalized.startsWith('qwen3.5') ||
      normalized.contains('vl') ||
      normalized.contains('vision');
}

bool isFastModel(String modelName, {LocalModelEntry? details}) {
  if (details != null) {
    return details.recommendedUse == 'ultra_light' ||
        details.recommendedUse == 'fast';
  }
  final normalized = modelName.toLowerCase();
  final match =
      RegExp(r'(\d+(?:\.\d+)?)b', caseSensitive: false).firstMatch(normalized);
  final size = double.tryParse(match?.group(1) ?? '') ?? 0.0;
  return normalized.contains('0.8b') ||
      normalized.contains('1.7b') ||
      normalized.contains(':2b') ||
      (size > 0 && size <= 2.1);
}

int modelPriorityScore(LocalModelEntry entry) {
  switch (entry.recommendedUse) {
    case 'advanced':
      return 500;
    case 'balanced':
      return 450;
    case 'fast':
      return 400;
    case 'ultra_light':
      return 350;
    case 'vision_fallback':
      return 300;
    case 'general':
      return 200;
    case 'embedding':
      return 100;
    default:
      return 0;
  }
}

int chatModelPreferenceScore(String modelName, {LocalModelEntry? details}) {
  final normalized = modelName.toLowerCase();
  final match =
      RegExp(r'(\d+(?:\.\d+)?)b', caseSensitive: false).firstMatch(normalized);
  final size = ((double.tryParse(match?.group(1) ?? '') ?? 0.0) * 10).round();
  if (details != null) {
    switch (details.recommendedUse) {
      case 'advanced':
        return 500 + size;
      case 'balanced':
        return 450 + size;
      case 'fast':
        return 420 + size;
      case 'ultra_light':
        return 390 + size;
      case 'vision_fallback':
        return 320 + size;
      default:
        break;
    }
  }
  if (normalized.startsWith('qwen3.5:9b')) return 500 + size;
  if (normalized.startsWith('qwen3.5:4b')) return 450 + size;
  if (normalized.startsWith('qwen3.5:2b')) return 420 + size;
  if (normalized.startsWith('qwen3.5:0.8b')) return 390 + size;
  if (normalized.startsWith('qwen3-vl')) return 320 + size;
  if (normalized.startsWith('qwen3:')) return 280 + size;
  if (normalized.startsWith('qwen2.5vl')) return 240 + size;
  return size;
}

List<LocalModelEntry> sortCatalogEntries(List<LocalModelEntry> entries) {
  final out = List<LocalModelEntry>.from(entries);
  out.sort((a, b) {
    final priority = modelPriorityScore(b) - modelPriorityScore(a);
    if (priority != 0) {
      return priority;
    }
    final aSize = double.tryParse((a.sizeLabel ?? '').replaceAll('b', '')) ?? 0;
    final bSize = double.tryParse((b.sizeLabel ?? '').replaceAll('b', '')) ?? 0;
    final sizeCompare = bSize.compareTo(aSize);
    if (sizeCompare != 0) {
      return sizeCompare;
    }
    return a.name.compareTo(b.name);
  });
  return out;
}

List<GroupedCatalogModels> buildCatalogModelGroups(
    List<LocalModelEntry> entries) {
  final sorted = sortCatalogEntries(entries);
  final recommended = <LocalModelEntry>[];
  final fast = <LocalModelEntry>[];
  final vision = <LocalModelEntry>[];
  final other = <LocalModelEntry>[];

  for (final entry in sorted) {
    if (entry.recommendedChatDefault ||
        entry.recommendedUse == 'balanced' ||
        entry.recommendedUse == 'advanced') {
      recommended.add(entry);
    } else if (entry.recommendedUse == 'fast' ||
        entry.recommendedUse == 'ultra_light') {
      fast.add(entry);
    } else if (entry.supportsVision) {
      vision.add(entry);
    } else {
      other.add(entry);
    }
  }

  if (recommended.isEmpty && sorted.isNotEmpty) {
    recommended.add(sorted.first);
    fast.remove(sorted.first);
    vision.remove(sorted.first);
    other.remove(sorted.first);
  }

  final groups = <GroupedCatalogModels>[];
  if (recommended.isNotEmpty) {
    groups.add(GroupedCatalogModels('Recommended', recommended));
  }
  if (fast.isNotEmpty) {
    groups.add(GroupedCatalogModels('Fast / Light', fast));
  }
  if (vision.isNotEmpty) {
    groups.add(GroupedCatalogModels('Vision / Multimodal', vision));
  }
  if (other.isNotEmpty) {
    groups.add(GroupedCatalogModels('Other', other));
  }
  return groups;
}

List<GroupedChatModels> buildChatModelGroups(
  List<String> modelNames,
  Map<String, LocalModelEntry> detailsByModel,
) {
  final sorted = List<String>.from(modelNames)
    ..sort((a, b) {
      final scoreDiff = chatModelPreferenceScore(
            b,
            details: resolveModelDetails(b, detailsByModel),
          ) -
          chatModelPreferenceScore(
            a,
            details: resolveModelDetails(a, detailsByModel),
          );
      if (scoreDiff != 0) {
        return scoreDiff;
      }
      return a.compareTo(b);
    });

  final recommended = <String>[];
  final fast = <String>[];
  final vision = <String>[];
  final others = <String>[];

  for (final model in sorted) {
    final details = resolveModelDetails(model, detailsByModel);
    final recommendedUse = details?.recommendedUse ?? 'general';
    if (details?.recommendedChatDefault == true ||
        recommendedUse == 'balanced' ||
        recommendedUse == 'advanced') {
      recommended.add(model);
    } else if (isFastModel(model, details: details)) {
      fast.add(model);
    } else if (isVisionCapableModel(model, details: details)) {
      vision.add(model);
    } else {
      others.add(model);
    }
  }

  if (recommended.isEmpty && sorted.isNotEmpty) {
    recommended.add(sorted.first);
    fast.remove(sorted.first);
    vision.remove(sorted.first);
    others.remove(sorted.first);
  }

  final groups = <GroupedChatModels>[];
  if (recommended.isNotEmpty) {
    groups.add(GroupedChatModels('Recommended', recommended));
  }
  if (fast.isNotEmpty) {
    groups.add(GroupedChatModels('Fast / Light', fast));
  }
  if (vision.isNotEmpty) {
    groups.add(GroupedChatModels('Vision / Multimodal', vision));
  }
  if (others.isNotEmpty) {
    groups.add(GroupedChatModels('Other', others));
  }
  return groups;
}

String describeChatModel(String modelName, {LocalModelEntry? details}) {
  if (details != null) {
    final tags = <String>[
      if ((details.sizeLabel ?? '').isNotEmpty) details.sizeLabel!,
      if (details.supportsVision) 'Vision',
      if (details.recommendedChatDefault) 'Recommended',
      details.recommendedUse.replaceAll('_', ' '),
    ];
    return tags.join(' · ');
  }
  return isVisionCapableModel(modelName)
      ? 'Supports multimodal prompts'
      : (isFastModel(modelName)
          ? 'Lower latency option'
          : 'General chat model');
}
