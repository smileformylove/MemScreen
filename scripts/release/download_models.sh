#!/usr/bin/env bash
# Download Ollama models on demand for MemScreen.
# Usage:
#   ./download_models.sh minimal
#   ./download_models.sh recommended
#   ./download_models.sh full
#   ./download_models.sh custom qwen2.5vl:3b mxbai-embed-large:latest

set -euo pipefail

PRESET="${1:-recommended}"
shift || true

if ! command -v ollama >/dev/null 2>&1; then
  echo "[model-download] ollama is not installed."
  echo "Install: https://ollama.com/download"
  exit 1
fi

ensure_ollama_running() {
  if curl -sSf "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
    return
  fi

  echo "[model-download] starting ollama serve in background..."
  nohup ollama serve >/tmp/memscreen_ollama.log 2>&1 &

  for _ in {1..20}; do
    if curl -sSf "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
      return
    fi
    sleep 1
  done

  echo "[model-download] ollama server is not reachable at 127.0.0.1:11434"
  exit 1
}

MODELS=()
case "$PRESET" in
  minimal)
    MODELS=(
      "qwen3:1.7b"
      "mxbai-embed-large:latest"
    )
    ;;
  recommended)
    MODELS=(
      "qwen3:1.7b"
      "qwen2.5vl:3b"
      "mxbai-embed-large:latest"
    )
    ;;
  full)
    MODELS=(
      "qwen3:1.7b"
      "qwen2.5vl:3b"
      "qwen2.5vl:7b"
      "mxbai-embed-large:latest"
      "nomic-embed-text:latest"
    )
    ;;
  custom)
    if [[ $# -eq 0 ]]; then
      echo "[model-download] custom mode requires model names."
      echo "example: ./download_models.sh custom qwen2.5vl:3b mxbai-embed-large:latest"
      exit 1
    fi
    MODELS=("$@")
    ;;
  *)
    echo "[model-download] unsupported preset: $PRESET"
    echo "supported: minimal | recommended | full | custom"
    exit 1
    ;;
esac

ensure_ollama_running

echo "[model-download] preset: $PRESET"
for model in "${MODELS[@]}"; do
  echo "[model-download] pulling $model"
  ollama pull "$model"
done

echo "[model-download] completed."
