import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:video_player/video_player.dart';

import '../api/video_api.dart';
import '../app_state.dart';

class VideoScreen extends StatefulWidget {
  const VideoScreen({super.key});

  @override
  State<VideoScreen> createState() => _VideoScreenState();
}

class _VideoScreenState extends State<VideoScreen> {
  List<VideoItem> _videos = [];
  bool _loading = true;
  late AppState _appState;
  int _lastVideoRefreshVersion = 0;
  Timer? _autoRefreshTimer;
  final ScrollController _timelineScrollController = ScrollController();
  String? _latestTimelineVideoFilename;
  bool _timelineStickToLatest = true;
  bool _loadInFlight = false;
  VideoPlayerController? _controller;
  VideoItem? _currentVideo;

  String _positionLabel = '0:00';
  double _sliderValue = 0.0;
  int _lastPositionSecond = -1;
  final Set<String> _reanalyzingFiles = <String>{};
  String _organizeMode = 'all'; // all | app | day | tag
  final Set<String> _selectedTags = <String>{};
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _appState = context.read<AppState>();
    _lastVideoRefreshVersion = _appState.videoRefreshVersion;
    _appState.addListener(_onAppStateChange);
    _timelineScrollController.addListener(_onTimelineScroll);
    _load(showLoading: true, autoScrollIfNew: true);
    _startAutoRefresh();
  }

  @override
  void dispose() {
    _appState.removeListener(_onAppStateChange);
    _autoRefreshTimer?.cancel();
    _timelineScrollController.removeListener(_onTimelineScroll);
    _timelineScrollController.dispose();
    _searchController.dispose();
    _controller?.dispose();
    super.dispose();
  }

  void _startAutoRefresh() {
    _autoRefreshTimer?.cancel();
    _autoRefreshTimer = Timer.periodic(const Duration(seconds: 4), (_) {
      if (!mounted || _loading) return;
      _load(showLoading: false, autoScrollIfNew: true);
    });
  }

  void _onAppStateChange() {
    if (!mounted) return;

    if (_appState.videoRefreshVersion != _lastVideoRefreshVersion) {
      _lastVideoRefreshVersion = _appState.videoRefreshVersion;
      _load(showLoading: false, autoScrollIfNew: true);
      return;
    }

    if (_appState.desiredTabIndex == 1) {
      _load(showLoading: false, autoScrollIfNew: false);
    }
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final minutes = twoDigits(duration.inMinutes.remainder(60));
    final seconds = twoDigits(duration.inSeconds.remainder(60));
    return '$minutes:$seconds';
  }

  void _updatePosition() {
    if (_controller != null && _controller!.value.isInitialized) {
      final position = _controller!.value.position;
      final duration = _controller!.value.duration;
      final nextLabel = _formatDuration(position);
      final nextSecond = position.inSeconds;
      final nextSlider = duration.inMilliseconds > 0
          ? position.inMilliseconds / duration.inMilliseconds
          : 0.0;
      final sliderChanged = (_sliderValue - nextSlider).abs() >= 0.01;
      final labelChanged = _positionLabel != nextLabel;
      final secondChanged = _lastPositionSecond != nextSecond;
      if (!mounted) return;
      if (labelChanged || (secondChanged && sliderChanged)) {
        setState(() {
          _positionLabel = nextLabel;
          _sliderValue = nextSlider;
          _lastPositionSecond = nextSecond;
        });
      }
    }
  }

  void _onTimelineScroll() {
    if (!_timelineScrollController.hasClients) return;
    _timelineStickToLatest = _timelineIsNearEnd();
  }

  bool _timelineIsNearEnd() {
    if (!_timelineScrollController.hasClients) return true;
    final position = _timelineScrollController.position;
    return (position.maxScrollExtent - position.pixels) <= 28.0;
  }

  bool _isSameVideoList(List<VideoItem> a, List<VideoItem> b) {
    if (identical(a, b)) return true;
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      final av = a[i];
      final bv = b[i];
      if (av.filename != bv.filename ||
          av.timestamp != bv.timestamp ||
          av.fileSize != bv.fileSize ||
          av.duration != bv.duration ||
          av.recordingMode != bv.recordingMode ||
          av.windowTitle != bv.windowTitle ||
          av.contentSummary != bv.contentSummary ||
          (av.analysisStatus ?? '') != (bv.analysisStatus ?? '') ||
          av.tags.join('|') != bv.tags.join('|') ||
          av.contentTags.join('|') != bv.contentTags.join('|') ||
          av.contentKeywords.join('|') != bv.contentKeywords.join('|')) {
        return false;
      }
    }
    return true;
  }

  Future<void> _load({
    bool showLoading = false,
    bool autoScrollIfNew = true,
  }) async {
    if (_loadInFlight) return;
    _loadInFlight = true;
    if (showLoading && mounted) {
      setState(() => _loading = true);
    }

    final wasNearEnd = _timelineIsNearEnd();
    final previousLatest = _latestTimelineVideoFilename;

    try {
      final list = await context.read<AppState>().videoApi.getList();
      final timelineSorted = _sortedByTimestampAscending(list);
      final latestFilename =
          timelineSorted.isNotEmpty ? timelineSorted.last.filename : null;
      if (mounted) {
        final listChanged = !_isSameVideoList(_videos, list);
        final latestChanged = previousLatest != latestFilename;
        if (listChanged ||
            latestChanged ||
            _loading ||
            _latestTimelineVideoFilename == null) {
          setState(() {
            _videos = list;
            _latestTimelineVideoFilename = latestFilename;
            _loading = false;
          });
        } else if (_loading) {
          setState(() => _loading = false);
        }

        final shouldScroll = autoScrollIfNew &&
            latestFilename != null &&
            (previousLatest == null ||
                (latestChanged && (wasNearEnd || _timelineStickToLatest)));
        if (shouldScroll) {
          _scrollTimelineToLatest();
        }
      }
    } catch (_) {
      if (mounted) {
        setState(() => _loading = false);
      }
    } finally {
      _loadInFlight = false;
    }
  }

  List<VideoItem> _sortedByTimestampAscending(List<VideoItem> videos) {
    final out = List<VideoItem>.from(videos);
    out.sort((a, b) {
      final ad = _parseTimestamp(a.timestamp);
      final bd = _parseTimestamp(b.timestamp);
      if (ad == null && bd == null) return a.timestamp.compareTo(b.timestamp);
      if (ad == null) return -1;
      if (bd == null) return 1;
      return ad.compareTo(bd);
    });
    return out;
  }

  void _scrollTimelineToLatest() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || !_timelineScrollController.hasClients) return;
      _timelineScrollController.jumpTo(
        _timelineScrollController.position.maxScrollExtent,
      );
    });
  }

  List<String> get _availableTags {
    final freq = <String, int>{};
    for (final v in _videos) {
      for (final tag in _prioritizedTags(v.tags)) {
        freq[tag] = (freq[tag] ?? 0) + 1;
      }
    }
    final keys = freq.keys.toList()
      ..sort((a, b) {
        final diff = (freq[b] ?? 0).compareTo(freq[a] ?? 0);
        if (diff != 0) return diff;
        return a.compareTo(b);
      });
    return keys;
  }

  List<VideoItem> get _visibleVideos {
    final filteredByTag = _videos.where((v) {
      final tags = v.tags.toSet();
      return _selectedTags.every(tags.contains);
    }).toList();

    final q = _normalizeSearchText(_searchQuery);
    if (q.isEmpty) return filteredByTag;

    final tokens = _extractSearchTokens(q);
    final phrases = _extractSearchPhrases(q, tokens);
    final tagHints = _inferSearchTagHints(q);

    final scored = <MapEntry<VideoItem, int>>[];
    for (final video in filteredByTag) {
      final score = _semanticSearchScore(
        video,
        q: q,
        tokens: tokens,
        phrases: phrases,
        tagHints: tagHints,
      );
      if (score > 0) {
        scored.add(MapEntry(video, score));
      }
    }

    scored.sort((a, b) {
      final scoreDiff = b.value.compareTo(a.value);
      if (scoreDiff != 0) return scoreDiff;
      final ad = _parseTimestamp(a.key.timestamp);
      final bd = _parseTimestamp(b.key.timestamp);
      if (ad == null && bd == null) {
        return b.key.timestamp.compareTo(a.key.timestamp);
      }
      if (ad == null) return 1;
      if (bd == null) return -1;
      return bd.compareTo(ad);
    });
    return scored.map((e) => e.key).toList();
  }

  String _normalizeSearchText(String text) {
    return text.trim().toLowerCase().replaceAll(RegExp(r'\s+'), ' ');
  }

  List<String> _extractSearchTokens(String query) {
    final tokenRegex =
        RegExp(r'[A-Za-z][A-Za-z0-9_./:+-]{1,}|[\u4e00-\u9fff]{2,}');
    const stopwords = {
      'what',
      'when',
      'where',
      'which',
      'who',
      'how',
      'the',
      'this',
      'that',
      'with',
      'from',
      'for',
      'video',
      'videos',
      'recording',
      'recordings',
      'screen',
      'content',
      'show',
      'shown',
      'find',
      'search',
      'and',
      'or',
      'to',
      'of',
      'in',
      'on',
      '我',
      '之前',
      '这个',
      '那个',
      '内容',
      '录屏',
      '视频',
      '检索',
      '查找',
      '搜索',
    };

    final out = <String>[];
    final seen = <String>{};
    for (final m in tokenRegex.allMatches(query)) {
      final token = m.group(0)?.trim().toLowerCase() ?? '';
      if (token.isEmpty || stopwords.contains(token) || token.length < 2) {
        continue;
      }
      if (RegExp(r'^[0-9._-]+$').hasMatch(token)) {
        continue;
      }
      if (seen.add(token)) {
        out.add(token);
      }
    }
    return out.take(14).toList();
  }

  List<String> _extractSearchPhrases(String query, List<String> tokens) {
    final out = <String>[];
    final seen = <String>{};
    final quoteRegex = RegExp('["\\\']([^"\\\']{2,})["\\\']');
    for (final m in quoteRegex.allMatches(query)) {
      final phrase = _normalizeSearchText(m.group(1) ?? '');
      if (phrase.isNotEmpty && seen.add(phrase)) {
        out.add(phrase);
      }
    }
    for (var i = 0; i < tokens.length - 1; i++) {
      final phrase = '${tokens[i]} ${tokens[i + 1]}';
      if (phrase.length >= 5 && seen.add(phrase)) {
        out.add(phrase);
      }
    }
    return out.take(10).toList();
  }

  List<String> _inferSearchTagHints(String query) {
    final rules = <String, List<String>>{
      'topic:coding': [
        'code',
        'coding',
        'vscode',
        'xcode',
        'python',
        'terminal',
        'git',
        'repo',
        '开发',
        '代码',
        '调试',
      ],
      'topic:research': [
        'paper',
        'arxiv',
        'research',
        'literature',
        '论文',
        '研究'
      ],
      'topic:document': [
        'doc',
        'document',
        'pdf',
        'notion',
        'notes',
        '文档',
        '笔记'
      ],
      'topic:browser': [
        'browser',
        'chrome',
        'safari',
        'firefox',
        'web',
        '浏览器',
        '网页'
      ],
      'topic:meeting': ['meeting', 'zoom', 'teams', '会议'],
      'topic:chat': ['chat', 'message', 'slack', 'discord', '消息', '沟通'],
      'topic:design': ['figma', 'design', 'ui', '设计'],
      'purpose:debugging': [
        'error',
        'exception',
        'traceback',
        'failed',
        'bug',
        '错误',
        '报错'
      ],
      'intent:searching': ['search', 'find', 'lookup', 'query', '查找', '搜索'],
      'intent:reading': ['read', 'reading', 'paper', 'pdf', '阅读', '查看'],
      'task:todo': ['todo', 'task', 'plan', '待办', '计划'],
      'app:vscode': ['vscode', 'visual studio code'],
      'app:terminal': ['terminal', 'iterm', 'bash', 'zsh', 'shell'],
      'app:chrome': ['chrome'],
      'app:safari': ['safari'],
      'app:notion': ['notion'],
    };

    final hints = <String>[];
    for (final entry in rules.entries) {
      if (entry.value.any((k) => query.contains(k))) {
        hints.add(entry.key);
      }
    }
    return hints;
  }

  int _semanticSearchScore(
    VideoItem video, {
    required String q,
    required List<String> tokens,
    required List<String> phrases,
    required List<String> tagHints,
  }) {
    final summary = (video.contentSummary ?? '').toLowerCase();
    final window = (video.windowTitle ?? '').toLowerCase();
    final app = _extractAppName(video).toLowerCase();
    final filename = video.filename.toLowerCase();
    final basename = video.filename.split('/').last.toLowerCase();
    final mode = video.recordingMode.toLowerCase();
    final tags = <String>[
      ...video.tags.map((e) => e.toLowerCase()),
      ...video.contentTags.map((e) => e.toLowerCase()),
    ];
    final tagBlob = tags.join(' | ');
    final keywords = video.contentKeywords.map((e) => e.toLowerCase()).toList();
    final keywordBlob = keywords.join(' | ');
    final fullText = [
      summary,
      window,
      app,
      basename,
      filename,
      mode,
      tagBlob,
      keywordBlob,
    ].join(' | ');

    var score = 0;
    if (fullText.contains(q)) score += 30;

    for (final phrase in phrases) {
      if (phrase.isEmpty) continue;
      if (keywordBlob.contains(phrase)) score += 24;
      if (summary.contains(phrase)) score += 22;
      if (window.contains(phrase) || app.contains(phrase)) score += 18;
      if (tagBlob.contains(phrase)) score += 16;
      if (basename.contains(phrase)) score += 12;
    }

    for (final token in tokens) {
      if (token.isEmpty) continue;
      if (keywords.contains(token)) {
        score += 16;
      } else if (keywordBlob.contains(token)) {
        score += 11;
      }
      if (summary.contains(token)) score += 10;
      if (window.contains(token) || app.contains(token)) score += 9;
      if (tagBlob.contains(token)) score += 8;
      if (basename.contains(token) || filename.contains(token)) score += 7;
      if (mode.contains(token)) score += 4;
    }

    for (final hint in tagHints) {
      if (tags.any((t) => t.startsWith(hint))) {
        score += 14;
      }
    }

    final status = (video.analysisStatus ?? '').toLowerCase();
    if (score > 0 && status == 'ready') {
      score += 2;
    }

    return score;
  }

  void _toggleTag(String tag) {
    setState(() {
      if (_selectedTags.contains(tag)) {
        _selectedTags.remove(tag);
      } else {
        _selectedTags.add(tag);
      }
    });
  }

  void _clearFilters() {
    if (_selectedTags.isEmpty) return;
    setState(() => _selectedTags.clear());
  }

  Future<void> _playVideo(VideoItem v) async {
    _controller?.dispose();

    var path = v.filename.startsWith('/')
        ? v.filename
        : '/Users/jixiangluo/.memscreen/videos/${v.filename}';
    try {
      path = await context.read<AppState>().videoApi.resolvePlayablePath(path);
    } catch (_) {
      // Fallback to original source file when playable-path resolution fails.
    }
    final file = File(path);

    if (!await file.exists()) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Video file not found')),
        );
      }
      return;
    }

    try {
      final controller = VideoPlayerController.file(file);
      _controller = controller;
      setState(() {
        _currentVideo = v;
        _sliderValue = 0.0;
        _positionLabel = '0:00';
      });

      await controller.initialize();
      controller.addListener(_updatePosition);

      await controller.play();
      if (mounted) {
        setState(() {});
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to play video: $e')),
        );
        setState(() => _currentVideo = null);
      }
    }
  }

  Future<void> _reanalyzeVideo(VideoItem v) async {
    if (_reanalyzingFiles.contains(v.filename)) return;
    setState(() => _reanalyzingFiles.add(v.filename));
    try {
      final result =
          await context.read<AppState>().videoApi.reanalyze(v.filename);
      if (!mounted) return;
      final tags = (result['content_tags'] is List)
          ? (result['content_tags'] as List).whereType<String>().join(', ')
          : '';
      final keywords = (result['content_keywords'] is List)
          ? (result['content_keywords'] as List)
              .whereType<String>()
              .take(8)
              .join(', ')
          : '';
      var tip = 'Reanalysis complete';
      if (tags.isNotEmpty) {
        tip = 'Tags: $tags';
      }
      if (keywords.isNotEmpty) {
        tip = tags.isNotEmpty
            ? '$tip | Keywords: $keywords'
            : 'Keywords: $keywords';
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(tip),
          duration: const Duration(seconds: 3),
        ),
      );
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Reanalysis failed: $e'),
          backgroundColor: Colors.red.shade700,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _reanalyzingFiles.remove(v.filename));
      }
    }
  }

  void _closeVideo() {
    _controller?.pause();
    _controller?.removeListener(_updatePosition);
    _controller?.dispose();
    _controller = null;
    setState(() => _currentVideo = null);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Videos'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _load(showLoading: false, autoScrollIfNew: false),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                _buildTimeline(),
                _buildOrganizationBar(),
                _buildSearchBar(),
                _buildTagFilterBar(),
                Expanded(
                  child: _currentVideo != null
                      ? _buildVideoPlayer()
                      : _buildOrganizedVideoList(),
                ),
              ],
            ),
    );
  }

  Widget _buildOrganizationBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 6),
      child: Row(
        children: [
          Expanded(
            child: SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'all', label: Text('All')),
                ButtonSegment(value: 'app', label: Text('By App')),
                ButtonSegment(value: 'day', label: Text('By Day')),
                ButtonSegment(value: 'tag', label: Text('By Tag')),
              ],
              selected: {_organizeMode},
              onSelectionChanged: (s) {
                if (s.isEmpty) return;
                setState(() => _organizeMode = s.first);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTagFilterBar() {
    final tags = _availableTags;
    if (tags.isEmpty) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 2, 12, 6),
      alignment: Alignment.centerLeft,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            ...tags.map((tag) {
              final selected = _selectedTags.contains(tag);
              return Padding(
                padding: const EdgeInsets.only(right: 6),
                child: FilterChip(
                  selected: selected,
                  label: Text(_formatTag(tag)),
                  onSelected: (_) => _toggleTag(tag),
                ),
              );
            }),
            const SizedBox(width: 4),
            IconButton(
              onPressed: _selectedTags.isEmpty ? null : _clearFilters,
              icon: const Icon(Icons.filter_alt_off_outlined, size: 18),
              tooltip: 'Clear filters',
            ),
            IconButton(
              onPressed: () =>
                  _load(showLoading: false, autoScrollIfNew: false),
              icon: const Icon(Icons.refresh, size: 18),
              tooltip: 'Refresh',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 0, 12, 6),
      child: TextField(
        controller: _searchController,
        onChanged: (value) => setState(() => _searchQuery = value),
        decoration: InputDecoration(
          isDense: true,
          hintText: 'Search by meaning: content, app, intent, keywords',
          prefixIcon: const Icon(Icons.search, size: 18),
          suffixIcon: _searchQuery.isEmpty
              ? null
              : IconButton(
                  icon: const Icon(Icons.close, size: 16),
                  onPressed: () {
                    _searchController.clear();
                    setState(() => _searchQuery = '');
                  },
                ),
        ),
      ),
    );
  }

  //
  Widget _buildTimeline() {
    final theme = Theme.of(context);
    final videos = _sortedByTimestampAscending(_videos);

    if (videos.isEmpty) {
      return Container(
        height: 50,
        decoration: BoxDecoration(
          color: theme.colorScheme.surfaceContainerHighest,
          border: Border(
            bottom: BorderSide(color: theme.dividerColor, width: 1),
          ),
        ),
        child: Center(
          child: Text(
            'No recordings yet',
            style: TextStyle(
              color: theme.colorScheme.onSurfaceVariant,
              fontSize: 12,
            ),
          ),
        ),
      );
    }

    final children = <Widget>[];
    String? previousTimestamp;
    for (final video in videos) {
      final marker = _timelineMarkerLabel(previousTimestamp, video.timestamp);
      if (marker != null) {
        children.add(_buildTimelineMarker(marker));
      }
      final isPlaying = _currentVideo?.filename == video.filename;
      children.add(_buildVideoTimelineNode(video, isPlaying));
      previousTimestamp = video.timestamp;
    }

    return Container(
      height: 34,
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        border: Border(
          bottom: BorderSide(color: theme.dividerColor, width: 1),
        ),
      ),
      child: ListView(
        key: const PageStorageKey<String>('videos.timeline'),
        controller: _timelineScrollController,
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
        children: children,
      ),
    );
  }

  Widget _buildTimelineMarker(String label) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(left: 8, right: 6),
      child: Row(
        children: [
          Container(
            width: 1,
            height: 20,
            color: theme.colorScheme.outlineVariant,
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 9,
              color: theme.colorScheme.onSurfaceVariant,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(width: 2),
        ],
      ),
    );
  }

  //  -
  Widget _buildVideoTimelineNode(VideoItem video, bool isPlaying) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6),
      child: Tooltip(
        message: _timelineTooltipText(video),
        waitDuration: const Duration(milliseconds: 250),
        child: GestureDetector(
          onTap: () => _playVideo(video),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              //
              Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: isPlaying
                      ? LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            theme.colorScheme.primary,
                            theme.colorScheme.primary.withOpacity(0.7),
                          ],
                        )
                      : null,
                  color:
                      isPlaying ? null : theme.colorScheme.surfaceContainerLow,
                  border: Border.all(
                    color: isPlaying
                        ? theme.colorScheme.primary
                        : theme.dividerColor,
                    width: isPlaying ? 2 : 1,
                  ),
                  boxShadow: isPlaying
                      ? [
                          BoxShadow(
                            color: theme.colorScheme.primary.withOpacity(0.4),
                            blurRadius: 8,
                            spreadRadius: 1,
                          ),
                        ]
                      : null,
                ),
                child: Icon(
                  isPlaying ? Icons.play_arrow : Icons.circle,
                  color: isPlaying
                      ? theme.colorScheme.onPrimary
                      : theme.colorScheme.onSurfaceVariant,
                  size: 12,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                _timelineTime(video.timestamp),
                style: TextStyle(
                  fontSize: 8,
                  color: isPlaying
                      ? theme.colorScheme.primary
                      : theme.colorScheme.onSurfaceVariant,
                  fontWeight: isPlaying ? FontWeight.w600 : FontWeight.normal,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _timelineTime(String ts) {
    if (ts.isEmpty) return '--:--';
    if (ts.length >= 16) return ts.substring(11, 16);
    if (ts.length >= 8) return ts.substring(ts.length - 8, ts.length - 3);
    return ts;
  }

  String? _timelineMarkerLabel(String? previousTs, String currentTs) {
    if (currentTs.isEmpty) return null;
    if (previousTs == null || previousTs.isEmpty) {
      return _formatTimelineHour(currentTs, includeDay: true);
    }
    final current = _parseTimestamp(currentTs);
    final previous = _parseTimestamp(previousTs);
    if (current == null || previous == null) {
      return null;
    }
    final dayChanged = current.year != previous.year ||
        current.month != previous.month ||
        current.day != previous.day;
    final hourChanged = current.hour != previous.hour;
    if (dayChanged) {
      return _formatTimelineHour(currentTs, includeDay: true);
    }
    if (hourChanged) {
      return _formatTimelineHour(currentTs, includeDay: false);
    }
    return null;
  }

  DateTime? _parseTimestamp(String ts) {
    if (ts.isEmpty) return null;
    return DateTime.tryParse(ts.replaceFirst(' ', 'T'));
  }

  String _formatTimelineHour(String ts, {required bool includeDay}) {
    final dt = _parseTimestamp(ts);
    if (dt == null) return _timelineTime(ts);
    final hh = dt.hour.toString().padLeft(2, '0');
    if (!includeDay) {
      return '$hh:00';
    }
    final mm = dt.month.toString().padLeft(2, '0');
    final dd = dt.day.toString().padLeft(2, '0');
    return '$mm-$dd $hh:00';
  }

  String _timelineTooltipText(VideoItem video) {
    final tags = _prioritizedTags(video.tags).map(_formatTag).toList();
    final preview = tags.take(4).toList();
    final tagText = preview.isEmpty ? '-' : preview.join(', ');
    final statusLabel = _analysisStatusLabel(video);
    return [
      'Time: ${video.timestamp}',
      'Duration: ${video.duration.toStringAsFixed(1)}s',
      'App: ${_extractAppName(video)}',
      if (statusLabel != null) 'Status: $statusLabel',
      'Tags: $tagText',
    ].join('\n');
  }

  Widget _buildOrganizedVideoList() {
    switch (_organizeMode) {
      case 'app':
        return _buildByAppList();
      case 'day':
        return _buildByDayList();
      case 'tag':
        return _buildByTagList();
      default:
        return _buildVideoList();
    }
  }

  // All
  Widget _buildVideoList() {
    final videos = _visibleVideos;
    if (videos.isEmpty) {
      final theme = Theme.of(context);
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.video_library,
                size: 64, color: theme.colorScheme.onSurfaceVariant),
            const SizedBox(height: 16),
            Text(
              'No videos',
              style: TextStyle(
                  color: theme.colorScheme.onSurfaceVariant, fontSize: 16),
            ),
          ],
        ),
      );
    }

    return ListView.separated(
      key: const PageStorageKey<String>('videos.all.list'),
      padding: const EdgeInsets.all(16),
      itemCount: videos.length,
      separatorBuilder: (context, index) => const SizedBox(height: 1),
      itemBuilder: (context, index) {
        final v = videos[index];
        return _buildVideoListTile(v);
      },
    );
  }

  Widget _buildByAppList() {
    final grouped = <String, List<VideoItem>>{};
    for (final v in _visibleVideos) {
      final app = _extractAppName(v);
      grouped.putIfAbsent(app, () => []).add(v);
    }
    final keys = grouped.keys.toList()
      ..sort((a, b) {
        final diff = grouped[b]!.length.compareTo(grouped[a]!.length);
        if (diff != 0) return diff;
        return a.compareTo(b);
      });

    return _buildSectionedList(
      sectionKeys: keys,
      sectionVideos: grouped,
      sectionTitleBuilder: (k, list) => '$k · ${list.length} videos',
    );
  }

  Widget _buildByDayList() {
    final grouped = <String, List<VideoItem>>{};
    for (final v in _visibleVideos) {
      final day = _extractDay(v.timestamp);
      grouped.putIfAbsent(day, () => []).add(v);
    }
    final keys = grouped.keys.toList()..sort((a, b) => b.compareTo(a));

    return _buildSectionedList(
      sectionKeys: keys,
      sectionVideos: grouped,
      sectionTitleBuilder: (k, list) {
        final totalSeconds = list.fold<num>(0, (acc, x) => acc + x.duration);
        return '$k · ${list.length} videos · ${totalSeconds.toStringAsFixed(0)}s';
      },
    );
  }

  Widget _buildByTagList() {
    final grouped = <String, List<VideoItem>>{};
    for (final v in _visibleVideos) {
      final tags = _prioritizedTags(v.tags);
      for (final tag in tags) {
        grouped.putIfAbsent(tag, () => []).add(v);
      }
    }
    final keys = grouped.keys.toList()
      ..sort((a, b) {
        final diff = grouped[b]!.length.compareTo(grouped[a]!.length);
        if (diff != 0) return diff;
        return a.compareTo(b);
      });
    return _buildSectionedList(
      sectionKeys: keys,
      sectionVideos: grouped,
      sectionTitleBuilder: (k, list) =>
          '${_formatTag(k)} · ${list.length} videos',
    );
  }

  Widget _buildSectionedList({
    required List<String> sectionKeys,
    required Map<String, List<VideoItem>> sectionVideos,
    required String Function(String key, List<VideoItem> items)
        sectionTitleBuilder,
  }) {
    if (_visibleVideos.isEmpty) {
      return _buildVideoList();
    }
    final theme = Theme.of(context);
    return ListView.builder(
      key: PageStorageKey<String>('videos.sectioned.$_organizeMode'),
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 20),
      itemCount: sectionKeys.length,
      itemBuilder: (context, sectionIndex) {
        final key = sectionKeys[sectionIndex];
        final items = sectionVideos[key] ?? const <VideoItem>[];
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerLowest,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: theme.dividerColor),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerHigh,
                  borderRadius: const BorderRadius.vertical(
                    top: Radius.circular(10),
                  ),
                ),
                child: Text(
                  sectionTitleBuilder(key, items),
                  style: TextStyle(
                    color: theme.colorScheme.onSurface,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              ...items.asMap().entries.map((entry) {
                final i = entry.key;
                final v = entry.value;
                return Column(
                  children: [
                    _buildVideoListTile(v),
                    if (i != items.length - 1)
                      Divider(height: 1, color: theme.dividerColor),
                  ],
                );
              }),
            ],
          ),
        );
      },
    );
  }

  Widget _buildVideoListTile(VideoItem v) {
    final theme = Theme.of(context);
    final isPlaying = _currentVideo?.filename == v.filename;
    final isReanalyzing = _reanalyzingFiles.contains(v.filename);
    final statusLabel = _analysisStatusLabel(v);
    return Container(
      decoration: BoxDecoration(
        color: isPlaying
            ? theme.colorScheme.primaryContainer.withOpacity(0.3)
            : Colors.transparent,
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: isPlaying
                ? theme.colorScheme.primaryContainer
                : theme.colorScheme.surfaceContainerLow,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: isPlaying ? theme.colorScheme.primary : theme.dividerColor,
              width: 1,
            ),
          ),
          child: Icon(
            Icons.movie,
            color: isPlaying
                ? theme.colorScheme.primary
                : theme.colorScheme.onSurfaceVariant,
            size: 24,
          ),
        ),
        title: Text(
          v.filename.split('/').last,
          style: TextStyle(
            color: isPlaying
                ? theme.colorScheme.primary
                : theme.colorScheme.onSurface,
            fontWeight: isPlaying ? FontWeight.bold : FontWeight.normal,
            fontSize: 14,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Wrap(
          spacing: 10,
          runSpacing: 6,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            _metaText(v.timestamp),
            _metaText('${v.duration}s'),
            _metaChip(_extractAppName(v)),
            if (statusLabel != null) _metaChip(statusLabel),
            ..._prioritizedTags(v.tags)
                .take(2)
                .map((x) => _metaChip(_formatTag(x))),
          ],
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: isReanalyzing
                  ? SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: theme.colorScheme.primary,
                      ),
                    )
                  : Icon(Icons.auto_fix_high, color: theme.colorScheme.primary),
              onPressed: isReanalyzing ? null : () => _reanalyzeVideo(v),
              tooltip:
                  isReanalyzing ? 'Reanalyzing...' : 'Reanalyze content tags',
            ),
            IconButton(
              icon: Icon(
                isPlaying ? Icons.pause : Icons.play_arrow,
                color: isPlaying
                    ? theme.colorScheme.primary
                    : theme.colorScheme.onSurfaceVariant,
              ),
              onPressed: () => _playVideo(v),
              tooltip: 'Play',
            ),
            IconButton(
              icon: Icon(Icons.delete_outline, color: theme.colorScheme.error),
              onPressed: () => _deleteVideo(v),
              tooltip: 'Delete',
            ),
          ],
        ),
        onTap: () => _playVideo(v),
      ),
    );
  }

  Widget _metaText(String text) {
    final theme = Theme.of(context);
    return Text(
      text,
      style: TextStyle(color: theme.colorScheme.onSurfaceVariant, fontSize: 12),
    );
  }

  Widget _metaChip(String text) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        text,
        style:
            TextStyle(color: theme.colorScheme.onSurfaceVariant, fontSize: 11),
      ),
    );
  }

  String _extractDay(String ts) {
    if (ts.length >= 10) return ts.substring(0, 10);
    return ts;
  }

  String _extractAppName(VideoItem v) {
    if (v.appName != null && v.appName!.trim().isNotEmpty) {
      return v.appName!.trim();
    }
    final title = (v.windowTitle ?? '').trim();
    if (title.isNotEmpty) {
      if (title.startsWith('Window: ')) {
        final body = title.substring('Window: '.length);
        final idx = body.indexOf(' · ');
        if (idx > 0) return body.substring(0, idx).trim();
        return body;
      }
      final idx = title.indexOf(' · ');
      if (idx > 0) return title.substring(0, idx).trim();
      return title;
    }
    if (v.recordingMode == 'fullscreen-single') return 'Single Screen';
    if (v.recordingMode == 'region') return 'Region Capture';
    return 'All Screens';
  }

  String? _analysisStatusLabel(VideoItem v) {
    final status = (v.analysisStatus ?? '').trim().toLowerCase();
    if (status == 'model_unavailable') return 'No Model';
    if (status == 'pending') return 'Analyzing';
    return null;
  }

  List<String> _topTags(List<String> tags) {
    if (tags.isEmpty) return const [];
    const allowedPrefixes = [
      'topic:',
      'purpose:',
      'intent:',
      'task:',
      'action:',
      'entity:',
      'keyword:',
      'ui:',
      'error:',
      'app:',
      'mode:',
      'audio:'
    ];
    final picked = <String>[];
    for (final tag in tags) {
      if (allowedPrefixes.any((p) => tag.startsWith(p))) {
        picked.add(tag);
      }
    }
    return picked.isEmpty ? tags : picked;
  }

  List<String> _prioritizedTags(List<String> tags) {
    if (tags.isEmpty) return const [];
    final topics = <String>[];
    final purposes = <String>[];
    final intents = <String>[];
    final tasks = <String>[];
    final actions = <String>[];
    final entities = <String>[];
    final keywords = <String>[];
    final uiTags = <String>[];
    final appTags = <String>[];
    final errorTags = <String>[];
    final others = <String>[];
    for (final t in _topTags(tags)) {
      if (t.startsWith('topic:')) {
        topics.add(t);
      } else if (t.startsWith('purpose:')) {
        purposes.add(t);
      } else if (t.startsWith('intent:')) {
        intents.add(t);
      } else if (t.startsWith('task:')) {
        tasks.add(t);
      } else if (t.startsWith('action:')) {
        actions.add(t);
      } else if (t.startsWith('entity:')) {
        entities.add(t);
      } else if (t.startsWith('keyword:')) {
        keywords.add(t);
      } else if (t.startsWith('ui:')) {
        uiTags.add(t);
      } else if (t.startsWith('app:')) {
        appTags.add(t);
      } else if (t.startsWith('error:')) {
        errorTags.add(t);
      } else {
        others.add(t);
      }
    }
    return [
      ...topics,
      ...purposes,
      ...intents,
      ...tasks,
      ...actions,
      ...entities,
      ...keywords,
      ...uiTags,
      ...appTags,
      ...errorTags,
      ...others,
    ];
  }

  String _formatTag(String tag) {
    if (tag.startsWith('topic:')) {
      return 'Topic: ${tag.substring(6)}';
    }
    if (tag.startsWith('purpose:')) {
      return 'Purpose: ${tag.substring(8)}';
    }
    if (tag.startsWith('time:')) {
      return 'Time: ${tag.substring(5)}';
    }
    if (tag.startsWith('length:')) {
      return 'Length: ${tag.substring(7)}';
    }
    if (tag.startsWith('weekday:')) {
      return 'Weekday: ${tag.substring(8)}';
    }
    if (tag.startsWith('audio:')) {
      return 'Audio: ${tag.substring(6)}';
    }
    if (tag.startsWith('entity:')) {
      return 'Entity: ${tag.substring(7)}';
    }
    if (tag.startsWith('intent:')) {
      return 'Intent: ${tag.substring(7)}';
    }
    if (tag.startsWith('ui:')) {
      return 'UI: ${tag.substring(3)}';
    }
    if (tag.startsWith('error:')) {
      return 'Error: ${tag.substring(6)}';
    }
    if (tag.startsWith('action:')) {
      return 'Action: ${tag.substring(7)}';
    }
    if (tag.startsWith('task:')) {
      return 'Task: ${tag.substring(5)}';
    }
    if (tag.startsWith('keyword:')) {
      return 'Keyword: ${tag.substring(8)}';
    }
    if (tag.startsWith('mode:')) {
      return 'Mode: ${tag.substring(5)}';
    }
    if (tag.startsWith('app:')) {
      return 'App: ${tag.substring(4)}';
    }
    return tag;
  }

  //
  Future<void> _deleteVideo(VideoItem video) async {
    final theme = Theme.of(context);

    //
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: theme.colorScheme.surfaceContainerHigh,
        title: Text('Delete Video',
            style: TextStyle(color: theme.colorScheme.onSurface)),
        content: Text(
          'Delete this video?\n${video.filename.split('/').last}',
          style: TextStyle(color: theme.colorScheme.onSurfaceVariant),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel',
                style: TextStyle(color: theme.colorScheme.onSurfaceVariant)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('Delete',
                style: TextStyle(color: theme.colorScheme.error)),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      try {
        //
        final path = video.filename.startsWith('/')
            ? video.filename
            : '/Users/jixiangluo/.memscreen/videos/${video.filename}';
        final file = File(path);
        if (await file.exists()) {
          await file.delete();
        }

        //
        if (_currentVideo?.filename == video.filename) {
          _closeVideo();
        }

        //
        await _load();

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Video deleted'),
              duration: Duration(seconds: 2),
            ),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Delete failed: $e'),
              backgroundColor: Colors.red.shade700,
            ),
          );
        }
      }
    }
  }

  //
  Widget _buildVideoPlayer() {
    final theme = Theme.of(context);

    if (_controller == null || !_controller!.value.isInitialized) {
      return Container(
        color: theme.colorScheme.surface,
        child: const Center(child: CircularProgressIndicator()),
      );
    }

    return Stack(
      alignment: Alignment.center,
      children: [
        //
        Center(
          child: AspectRatio(
            aspectRatio: _controller!.value.aspectRatio,
            child: VideoPlayer(_controller!),
          ),
        ),

        //
        Positioned(
          bottom: 0,
          left: 0,
          right: 0,
          child: Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.transparent,
                  theme.colorScheme.surfaceContainerLow.withOpacity(0.8),
                  theme.colorScheme.surfaceContainerLow.withOpacity(0.95),
                ],
              ),
            ),
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                //
                Row(
                  children: [
                    Text(
                      _positionLabel,
                      style: TextStyle(
                          color: theme.colorScheme.onSurface,
                          fontSize: 13,
                          fontFamily: 'monospace'),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Slider(
                        value: _sliderValue,
                        min: 0.0,
                        max: 1.0,
                        activeColor: theme.colorScheme.primary,
                        inactiveColor:
                            theme.colorScheme.onSurface.withOpacity(0.2),
                        onChanged: (value) {
                          if (_controller != null &&
                              _controller!.value.isInitialized) {
                            final position = Duration(
                              milliseconds: (value *
                                      _controller!
                                          .value.duration.inMilliseconds)
                                  .toInt(),
                            );
                            _controller!.seekTo(position);
                          }
                        },
                      ),
                    ),
                    Text(
                      _formatDuration(_controller!.value.duration),
                      style: TextStyle(
                          color: theme.colorScheme.onSurfaceVariant,
                          fontSize: 13,
                          fontFamily: 'monospace'),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                //
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    IconButton(
                      icon: Icon(
                        _controller!.value.isPlaying
                            ? Icons.pause
                            : Icons.play_arrow,
                        color: theme.colorScheme.onSurface,
                      ),
                      onPressed: () {
                        setState(() {});
                        if (_controller!.value.isPlaying) {
                          _controller!.pause();
                        } else {
                          _controller!.play();
                        }
                      },
                    ),
                    const SizedBox(width: 32),
                    IconButton(
                      icon: Icon(Icons.close,
                          color: theme.colorScheme.onSurfaceVariant),
                      onPressed: _closeVideo,
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                //
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.movie,
                          size: 16, color: theme.colorScheme.primary),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _currentVideo?.filename.split('/').last ?? '',
                          style: TextStyle(
                              color: theme.colorScheme.onSurfaceVariant,
                              fontSize: 11),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
