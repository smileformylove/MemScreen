<div align="center">

<img src="assets/logo.png" alt="MemScreen Logo" width="260"/>

# MemScreen

### A practical macOS screen recorder and recording album manager

**100% Local • 100% Private • AI-Powered Visual Memory System**

[![Product Hunt](https://img.shields.io/badge/Product%20Hunt-Featured-orange?style=for-the-badge&logo=producthunt&logoColor=white)](https://www.producthunt.com/products/memscreen)
[![ShipIt](https://img.shields.io/badge/ShipIt-Published-purple?style=for-the-badge)](https://www.shipit.buzz/products/memscreen)
[![NXGenTools](https://img.shields.io/badge/NXGenTools-Published-blue?style=for-the-badge)](https://www.nxgntools.com/tools/memscreen)
[![Version](https://img.shields.io/badge/version-v0.6.3-brightgreen?style=for-the-badge&labelColor=333)](https://github.com/smileformylove/MemScreen)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)
[![100% Local](https://img.shields.io/badge/Data-100%25%20Local-success?style=for-the-badge&labelColor=06D6A0)](https://github.com/smileformylove/MemScreen)
[![No Cloud](https://img.shields.io/badge/Privacy-No%20Cloud-blue?style=for-the-badge&labelColor=457B9D)](https://github.com/smileformylove/MemScreen)
[![GitHub stars](https://img.shields.io/github/stars/smileformylove/MemScreen?style=for-the-badge&logo=github&labelColor=333)](https://github.com/smileformylove/MemScreen/stargazers)

[⚡ Quick Start](#-quick-start) • [✨ Features](#-features) • [📖 Docs](#-documentation) • [🧱 Architecture](#-architecture-at-a-glance)

</div>

---

## What MemScreen Is

MemScreen is a **screen recording app for macOS** with a built-in **recording album**.

It helps you:

- Record your screen quickly (full screen, specific display, region, or window)
- Keep recordings organized and searchable in one place
- Review timeline and metadata without leaving the app
- Optionally use local AI features to tag and retrieve content

The core product value is still recorder + album first, AI second.

---

## Why This Project

Most recorders stop at “save an mp4 file”.
MemScreen continues into:

- Continuous personal recording workflow
- Better recall through gallery organization
- Local-first indexing and retrieval

If you want a macOS recorder that also acts like a manageable personal archive, this project is designed for that.

---

## Product Advantages

- Recorder + Album in one product, not just an exported mp4 file
- Full workflows for `Screen`, `Region`, and `Window` recording on macOS
- Local timeline organization by app/day/tag for fast review
- Optional local AI understanding for content tagging and retrieval
- 100% local data path with no required cloud upload

---

## MemScreen vs Similar Products

| Product | Capture Focus | Recorder + Album | Local-First Privacy | AI Tag/Retrieval | Primary Positioning |
| --- | --- | --- | --- | --- | --- |
| **MemScreen** | Screen/Region/Window recording | **Yes (built-in)** | **Yes (100% local by default)** | **Yes (optional local AI)** | Recording + personal video memory |
| Rewind | Continuous personal capture | Partial | Strong local-first (mode-dependent) | Yes | Personal memory and recall assistant |
| Recall | Saved content summarization (web/media/docs) | No | Mixed (app + cloud surfaces) | Yes | Knowledge capture and summarization |
| OBS Studio | Live capture and streaming | Partial | Partial | No | Live streaming and advanced capture |
| Loom | Cloud collaboration recording | Partial | No (cloud-centric) | Partial | Team sharing and async communication |
| CleanShot X | Quick screenshot/screencast utility | Partial | Partial | No | Screenshots and quick captures |
| Screen Studio | Polished recording export | Partial | Partial | No | Demo/tutorial video production |

> Note: Feature sets of third-party products may evolve over time.

---

## Features

### 1) Recording (macOS-first)

- Full screen recording
  - All screens
  - Single selected screen
- Region recording
- Window recording
- Floating ball workflow on macOS for quick control

### 2) Audio

- Two independent toggles in Settings:
  - `System audio`
  - `Microphone`
- Both enabled by default
- Runtime mapping:
  - system+mic -> `mixed`
  - system only -> `system_audio`
  - mic only -> `microphone`
  - both off -> `none`
- macOS system-audio capture path includes loopback routing + restore logic

### 3) Video Album

- Timeline-based browsing
- By-app / by-day / by-tag organization
- Tooltip metadata on timeline nodes
- Built-in playback and reanalysis

### 4) Input Tracking

- Keyboard/Mouse tracking (optional)
- Can be auto-coupled to recording sessions

### 5) Local AI (optional layer)

- Local model-backed tagging and retrieval
- Chat interface to query recording memory
- Works without cloud APIs (when local model runtime is available)
- If no model runtime is configured, recording and album features still work normally

---

## macOS Notes

MemScreen is currently best on macOS because the product integrates:

- Native floating ball window flow
- macOS screen capture permissions
- macOS audio routing behavior

If you use it on macOS, ensure permissions are granted:

- Screen Recording
- Accessibility (for key-mouse tracking)
- Microphone (if mic capture enabled)

---

## Quick Start

### Recommended (one command)

```bash
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen
python3 -m venv venv
source venv/bin/activate
pip install -e .
./scripts/launch.sh
```

This script:

- Bootstraps Python dependencies
- Starts API backend
- Builds and starts Flutter macOS app

### Optional modes

```bash
# API only
./scripts/launch.sh --mode api

# Flutter mode
./scripts/launch.sh --mode flutter
```

### Docker (backend stack / isolated runtime)

```bash
./scripts/docker-launch.sh
```

See `setup/docker/README.md` for details.

---

## Typical Workflow

1. Start MemScreen
2. Choose recording mode (`Screen`, `Region`, or `Window`)
3. Record with audio toggles configured in Settings
4. Stop recording
5. Review immediately in Videos timeline/album
6. Reanalyze or chat-search if needed

---

## Data Storage

All local user data stays under `~/.memscreen/`:

- `~/.memscreen/videos/` - recording files
- `~/.memscreen/db/` - metadata databases
- `~/.memscreen/logs/` - runtime logs

No cloud upload is required by default.

---

## Architecture At A Glance

- **Frontend:** Flutter (primary UI)
- **Backend/API:** FastAPI
- **Core logic:** Presenter-oriented Python modules (`memscreen/presenters`)
- **Recording:** screen capture + local encoding + local metadata persistence
- **Audio:** system/mic capture with mixed mode and macOS output routing support
- **Storage:** SQLite + local file system

Key folders:

- `frontend/flutter/` - Flutter desktop app
- `memscreen/api/` - HTTP API endpoints
- `memscreen/presenters/` - recording/video/chat/process orchestration
- `memscreen/audio/` - audio capture/routing logic
- `scripts/` - launch and runtime scripts

---

## Documentation

- Installation: `docs/INSTALLATION.md`
- Recording guide: `docs/RECORDING_GUIDE.md`
- Audio guide: `docs/AUDIO_RECORDING.md`
- Floating ball: `docs/FLOATING_BALL.md`
- Architecture: `docs/ARCHITECTURE.md`
- Flutter guide: `docs/FLUTTER.md`
- Testing guide: `docs/TESTING_GUIDE.md`

---

## Roadmap (Short)

- Better global hotkeys
- Stronger video organization and retrieval
- More robust packaging/distribution flow
- Multi-device workflow exploration

---

## GitHub Growth

[![Star History Chart](https://api.star-history.com/svg?repos=smileformylove/MemScreen&type=Date)](https://www.star-history.com/#smileformylove/MemScreen&Date)

---

## Contributing

- Report issues: [GitHub Issues](https://github.com/smileformylove/MemScreen/issues)
- Feature discussion: [GitHub Discussions](https://github.com/smileformylove/MemScreen/discussions)
- PRs welcome

---

## License

MIT License. See `LICENSE`.
