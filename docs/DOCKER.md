# Docker

MemScreen provides a Docker stack for backend runtime + Ollama.

## Start

```bash
./scripts/docker-launch.sh
```

Optional model pre-pull:

```bash
./scripts/docker-launch.sh --pull-models
```

## Services

- API: `http://127.0.0.1:8765`
- Ollama: `http://127.0.0.1:11434`

Compose file:
- `setup/docker/docker-compose.yml`

## Common commands

```bash
docker compose -f setup/docker/docker-compose.yml ps
docker compose -f setup/docker/docker-compose.yml logs -f
docker compose -f setup/docker/docker-compose.yml down
```

## Persistence

- `memscreen_data` volume for `~/.memscreen`
- `ollama_data` volume for model cache
