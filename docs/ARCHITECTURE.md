# Architecture

## Runtime layers

- Frontend: Flutter desktop app (`frontend/flutter`)
- Backend: FastAPI service (`memscreen/api`)
- Core orchestration: presenters (`memscreen/presenters`)
- Recording/audio services: `memscreen/audio`, `memscreen/services`
- Storage: local filesystem + SQLite under `~/.memscreen`

## Data paths

- videos: `~/.memscreen/videos/`
- databases: `~/.memscreen/db/`
- logs: `~/.memscreen/logs/`

## Launch paths

- all-in-one local launch: `./scripts/launch.sh`
- backend only: `./scripts/launch.sh --mode api`
- docker backend stack: `./scripts/docker-launch.sh`

## Packaging strategy

- one macOS installer package for end users
- backend bootstrap embedded in app bundle (background init)
- lite runtime dependencies auto-installed to `~/.memscreen/runtime/.venv`
- models downloaded on demand (optional)

See `docs/RELEASE_PACKAGING.md`.
