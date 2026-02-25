#!/usr/bin/env bash
# Build all release artifacts:
# 1) frontend installer (macOS only)
# 2) backend runtime bundle (no models)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[release] building backend runtime package"
"$SCRIPT_DIR/build_backend_runtime.sh"

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "[release] building frontend macOS package"
  "$SCRIPT_DIR/build_frontend_macos.sh"
else
  echo "[release] skipping frontend macOS package (requires macOS host)"
fi

echo "[release] done"
