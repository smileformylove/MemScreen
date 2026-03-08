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

class SettingsModelSection {
  const SettingsModelSection({
    required this.catalog,
    required this.groups,
    this.recommendedEntry,
  });

  final LocalModelCatalog catalog;
  final List<GroupedCatalogModels> groups;
  final LocalModelEntry? recommendedEntry;
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
    case 'balanced':
      return 500;
    case 'fast':
      return 450;
    case 'ultra_light':
      return 400;
    case 'advanced':
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
      case 'balanced':
        return 500 + size;
      case 'fast':
        return 450 + size;
      case 'ultra_light':
        return 420 + size;
      case 'advanced':
        return 360 + size;
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

bool modelNameMatchesEntry(LocalModelEntry entry, String modelName) {
  final normalized = modelName.trim();
  return entry.name == normalized || entry.installedName == normalized;
}

String? computeRecommendedChatModel(LocalModelCatalog catalog) {
  final available = catalog.availableChatModels.toSet();
  if (available.isEmpty) {
    return catalog.currentChatModel;
  }

  LocalModelEntry? bestEntry;
  var bestScore = -1;
  for (final entry in catalog.models) {
    final entryNames = <String>{
      entry.name,
      if ((entry.installedName ?? '').isNotEmpty) entry.installedName!
    };
    final selectable =
        entry.chatSelectable || entryNames.any(available.contains);
    if (!selectable || !entry.supportsChat) {
      continue;
    }
    final preferredName = (entry.installedName ?? '').isNotEmpty &&
            available.contains(entry.installedName)
        ? entry.installedName!
        : entry.name;
    final score = chatModelPreferenceScore(preferredName, details: entry);
    if (score > bestScore) {
      bestScore = score;
      bestEntry = entry;
    }
  }

  if (bestEntry == null) {
    return catalog.currentChatModel;
  }
  final installedName = bestEntry.installedName;
  if ((installedName ?? '').isNotEmpty && available.contains(installedName)) {
    return installedName;
  }
  return bestEntry.name;
}

LocalModelCatalog markCurrentChatModel(
  LocalModelCatalog catalog,
  String modelName,
) {
  final effectiveModel = modelName.trim();
  final recommended = computeRecommendedChatModel(catalog);
  final updatedModels = catalog.models.map((entry) {
    final isRecommended =
        recommended != null && modelNameMatchesEntry(entry, recommended);
    return entry.copyWith(recommendedChatDefault: isRecommended);
  }).toList();
  return catalog.copyWith(
    currentChatModel: effectiveModel,
    recommendedChatModel: recommended,
    models: updatedModels,
  );
}

LocalModelCatalog markDownloadedModel(
  LocalModelCatalog catalog,
  String modelName,
) {
  final effectiveModel = modelName.trim();
  final updatedModels = catalog.models.map((entry) {
    if (modelNameMatchesEntry(entry, effectiveModel)) {
      return entry.copyWith(
        installed: true,
        installedName: effectiveModel,
        chatSelectable: entry.supportsChat ? true : entry.chatSelectable,
      );
    }
    return entry;
  }).toList();

  final updatedAvailable = List<String>.from(catalog.availableChatModels);
  final matched = updatedModels
      .where((entry) => modelNameMatchesEntry(entry, effectiveModel));
  if (matched.any((entry) => entry.supportsChat) &&
      !updatedAvailable.contains(effectiveModel)) {
    updatedAvailable.add(effectiveModel);
  }

  final interim = catalog.copyWith(
    availableChatModels: updatedAvailable,
    models: updatedModels,
  );
  final recommended = computeRecommendedChatModel(interim);
  final finalModels = interim.models.map((entry) {
    final isRecommended =
        recommended != null && modelNameMatchesEntry(entry, recommended);
    return entry.copyWith(recommendedChatDefault: isRecommended);
  }).toList();

  return interim.copyWith(
    recommendedChatModel: recommended,
    models: finalModels,
  );
}

class ChatModelSelection {
  const ChatModelSelection({
    this.availableModels = const <String>[],
    this.detailsByModel = const <String, LocalModelEntry>{},
    this.currentModel,
    this.recommendedModel,
  });

  final List<String> availableModels;
  final Map<String, LocalModelEntry> detailsByModel;
  final String? currentModel;
  final String? recommendedModel;
}

Map<String, LocalModelEntry> buildChatModelDetailsMap(
  LocalModelCatalog catalog,
  List<String> availableModels,
) {
  final details = <String, LocalModelEntry>{};
  for (final entry in catalog.models) {
    if (availableModels.contains(entry.name)) {
      details[entry.name] = entry;
    }
    if ((entry.installedName ?? '').isNotEmpty &&
        availableModels.contains(entry.installedName)) {
      details[entry.installedName!] = entry;
    }
  }
  return details;
}

ChatModelSelection buildChatModelSelection(
  LocalModelCatalog catalog, {
  List<String>? availableModels,
  String? currentModel,
}) {
  final resolvedAvailable = availableModels ?? catalog.availableChatModels;
  return ChatModelSelection(
    availableModels: resolvedAvailable,
    detailsByModel: buildChatModelDetailsMap(catalog, resolvedAvailable),
    currentModel: currentModel ?? catalog.currentChatModel,
    recommendedModel: catalog.recommendedChatModel,
  );
}

SettingsModelSection buildSettingsModelSection(LocalModelCatalog catalog) {
  final recommended = (catalog.recommendedChatModel ?? '').trim();
  LocalModelEntry? recommendedEntry;
  if (recommended.isNotEmpty) {
    for (final entry in catalog.models) {
      if (modelNameMatchesEntry(entry, recommended)) {
        recommendedEntry = entry;
        break;
      }
    }
  }
  return SettingsModelSection(
    catalog: catalog,
    groups: buildCatalogModelGroups(catalog.models),
    recommendedEntry: recommendedEntry,
  );
}
