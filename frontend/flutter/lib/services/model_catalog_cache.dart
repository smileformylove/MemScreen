import '../api/model_api.dart';
import 'model_catalog_groups.dart' as model_groups;

class ModelCatalogCache {
  ModelCatalogCache({required Duration ttl}) : _ttl = ttl;

  final Duration _ttl;
  LocalModelCatalog? _catalog;
  DateTime? _cachedAt;

  LocalModelCatalog? get snapshot => _catalog;

  void invalidate() {
    _catalog = null;
    _cachedAt = null;
  }

  LocalModelCatalog? readFresh(DateTime now) {
    if (_catalog == null || _cachedAt == null) {
      return null;
    }
    if (now.difference(_cachedAt!) > _ttl) {
      return null;
    }
    return _catalog;
  }

  void store(LocalModelCatalog catalog, {DateTime? at}) {
    _catalog = catalog;
    _cachedAt = at ?? DateTime.now();
  }

  void markCurrentChatModel(String modelName, {DateTime? at}) {
    final catalog = _catalog;
    if (catalog == null) {
      return;
    }
    final effectiveModel = modelName.trim();
    if (effectiveModel.isEmpty) {
      return;
    }
    _catalog = model_groups.markCurrentChatModel(catalog, effectiveModel);
    _cachedAt = at ?? DateTime.now();
  }

  void markDownloadedModel(String modelName, {DateTime? at}) {
    final catalog = _catalog;
    if (catalog == null) {
      return;
    }
    final effectiveModel = modelName.trim();
    if (effectiveModel.isEmpty) {
      return;
    }
    _catalog = model_groups.markDownloadedModel(catalog, effectiveModel);
    _cachedAt = at ?? DateTime.now();
  }
}
