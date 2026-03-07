# Architecture

## Product priority

MemScreen is organized around a clear product order:

1. recorder
2. video album / retrieval
3. optional local AI understanding

That priority matters when making architectural changes: recording and album flows should remain usable even when model runtime is unavailable.

## Runtime layers

- Frontend: Flutter desktop app in `frontend/flutter`
- Backend: FastAPI service in `memscreen/api`
- Orchestration layer: presenter-style Python modules in `memscreen/presenters`
- Domain/services: audio, model capability, session analysis, region config in `memscreen/audio` and `memscreen/services`
- Memory / AI layer: `memscreen/memory`, `memscreen/llm`, `memscreen/embeddings`, `memscreen/vector_store`
- Storage: local filesystem plus SQLite under `~/.memscreen`

## Main code map

- `frontend/flutter/lib/main.dart`: Flutter application entrypoint
- `frontend/flutter/lib/app_state.dart`: shared app state, connection state, recording defaults, floating-ball bridge
- `frontend/flutter/lib/screens/`: primary desktop screens (`Record`, `Videos`, `Process`, `Chat`, `Settings`)
- `frontend/flutter/lib/api/`: typed HTTP clients used by Flutter
- `memscreen/api/__main__.py`: API startup entrypoint
- `memscreen/api/app.py`: FastAPI routes for chat, models, process tracking, recording, videos, config, health
- `memscreen/api/deps.py`: lazy dependency creation and singleton wiring for presenters and memory
- `memscreen/presenters/`: core business orchestration for chat, recording, video, process mining
- `memscreen/audio/audio_recorder.py`: platform-heavy audio capture and routing logic
- `memscreen/memory/memory.py`: memory kernel, vector search integration, dynamic memory, telemetry hooks
- `memscreen/storage/sqlite.py`: reusable SQLite manager used by memory history
- `scripts/launch.sh`: local bootstrap and runtime launcher

## Request flow

```text
Flutter screen
  -> frontend API client
  -> FastAPI route
  -> deps.py lazy singleton
  -> presenter
  -> service / memory / SQLite / files
  -> JSON response
  -> AppState / screen refresh
```

## Data paths

- videos: `~/.memscreen/videos/`
- databases: `~/.memscreen/db/`
- logs: `~/.memscreen/logs/`
- Flutter user settings: `~/.memscreen/flutter_settings.json`

## Launch paths

- all-in-one local launch: `./scripts/launch.sh`
- backend only: `./scripts/launch.sh --mode api`
- Flutter with managed backend: `./scripts/launch.sh --mode flutter`
- docker backend stack: `./scripts/docker-launch.sh`

## Current structural hotspots

- `memscreen/api/app.py` contains many unrelated route groups in one file
- `frontend/flutter/lib/app_state.dart` combines connection, settings, recording orchestration, tracking binding, and platform channel logic
- `memscreen/presenters/chat_presenter.py` is a large multi-responsibility module
- `memscreen/presenters/recording_presenter.py` and `memscreen/audio/audio_recorder.py` mix orchestration, persistence, and platform concerns
- SQLite access is partly centralized but still duplicated across presenters and services

## Optimization guidance

- Keep recording and album paths lightweight and resilient
- Move toward router/service/repository boundaries on the backend
- Split frontend state by domain rather than growing one global notifier
- Treat model-backed features as optional dependencies, not startup blockers

For a phased execution plan, see `docs/OPTIMIZATION_ROADMAP.md`.
