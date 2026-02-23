# MemScreen Docker

This directory contains the Docker deployment assets for MemScreen.

## One-Command Start (Recommended)

From project root:

```bash
./scripts/docker-launch.sh
```

Optional: also pull default Ollama models right away:

```bash
./scripts/docker-launch.sh --pull-models
```

## What starts

- `memscreen-api` (FastAPI backend) on `http://127.0.0.1:8765`
- `ollama` on `http://127.0.0.1:11434`

## Data persistence

Docker volumes are used for persistence:
- `memscreen_data` -> MemScreen runtime data (`~/.memscreen` in container)
- `ollama_data` -> Ollama model cache

## Useful commands

```bash
# View service status
docker compose -f setup/docker/docker-compose.yml ps

# View logs
docker compose -f setup/docker/docker-compose.yml logs -f

# Stop stack
docker compose -f setup/docker/docker-compose.yml down
```
