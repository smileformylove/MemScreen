#!/usr/bin/env bash
# One-command Docker launcher for MemScreen (API + Ollama)

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
COMPOSE_FILE="$PROJECT_ROOT/setup/docker/docker-compose.yml"

PULL_MODELS="0"
DETACH="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pull-models)
      PULL_MODELS="1"
      shift
      ;;
    --no-detach)
      DETACH="0"
      shift
      ;;
    -h|--help)
      cat <<USAGE
Usage: ./scripts/docker-launch.sh [options]

Options:
  --pull-models   Pull default Ollama models after startup
  --no-detach     Run docker compose in foreground
  -h, --help      Show help
USAGE
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

compose_cmd() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "docker compose"
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
    return
  fi
  echo ""
}

COMPOSE="$(compose_cmd)"
if [[ -z "$COMPOSE" ]]; then
  echo "Docker Compose is not installed."
  echo "Install Docker Desktop (macOS/Windows) or docker + compose plugin (Linux)."
  exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Compose file not found: $COMPOSE_FILE"
  exit 1
fi

echo "Starting MemScreen stack with: $COMPOSE"
if [[ "$DETACH" == "1" ]]; then
  $COMPOSE -f "$COMPOSE_FILE" up -d --build
else
  $COMPOSE -f "$COMPOSE_FILE" up --build
fi

echo ""
echo "MemScreen Docker stack is up."
echo "API:    http://127.0.0.1:8765"
echo "Ollama: http://127.0.0.1:11434"
echo ""
echo "Health checks:"
echo "  curl http://127.0.0.1:8765/health"
echo "  curl http://127.0.0.1:11434/api/tags"

if [[ "$PULL_MODELS" == "1" ]]; then
  echo ""
  echo "Pulling default Ollama models (this may take a while)..."
  $COMPOSE -f "$COMPOSE_FILE" exec -T ollama ollama pull qwen2.5vl:3b || true
  $COMPOSE -f "$COMPOSE_FILE" exec -T ollama ollama pull mxbai-embed-large || true
  echo "Model pull step completed."
fi
