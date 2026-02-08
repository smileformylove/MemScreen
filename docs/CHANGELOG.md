# Changelog

All notable changes to MemScreen will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-02-07

### Added
- **Floating Ball First Mode** (macOS) - Application starts with floating ball only, main window minimized
- **Branded Floating Ball** - Displays logo with circular masking instead of solid color
- **User Guide** - Comprehensive `docs/USER_GUIDE.md` with usage instructions
- **Improved README** - Added floating ball mode instructions and tips

### Changed
- Floating ball control is now the primary interface on macOS
- Right-click menu provides access to all features
- Left-click toggles main window visibility
- Drag to reposition anywhere on screen

### Fixed
- Duplicate floating ball creation when starting recording
- Floating ball state management across recording start/stop
- Window restoration when using floating ball to start recording

### Removed
- 15+ test and debug files (test_*.py, debug_*.py, etc.)
- Unused implementation files (floating_ball_app.py, native_region_selector.py, unified_ui.py)
- Debug documentation (DEBUGGING_GUIDE.md, DIAGNOSIS.md, etc.)
- Deprecated script commands from pyproject.toml

### Updated
- Version bumped to 0.6.0
- All version strings updated across codebase
- README.md reorganized with clearer feature descriptions
- Project structure cleaned and organized

## [0.5.0] - 2026-02-04

### Added
- **Intelligent Agent** - Auto-classification and smart routing (3-5x faster, 70% fewer tokens)
- **Dynamic Memory System** - 15 categories, 7 query intents, smart search
- **Custom Region Recording** - Visual crosshair guides, re-selectable regions
- **Native Floating Ball** (macOS) - Real floating window with cross-space visibility
- Centralized documentation in `docs/` directory

### Changed
- Improved memory organization with category-based storage
- Enhanced recording workflow with region selector
- Better screen switching mechanism

## [0.4.0] - 2026-01-XX

### Added
- **Local AI Agent** - Task planning & skill execution
- **Enhanced AI Chat** - Humanized, warm responses
- **Zero Cloud** - No API keys, no data transmission

## Older Versions

For versions prior to 0.4.0, please check the git history.

---

## Version Numbering

- **Major** (X.0.0) - Breaking changes, major features
- **Minor** (0.X.0) - New features, enhancements
- **Patch** (0.0.X) - Bug fixes, minor improvements
