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

- frontend installer packaged separately
- backend runtime packaged separately (no bundled models)
- models downloaded on demand

See `docs/RELEASE_PACKAGING.md`.
