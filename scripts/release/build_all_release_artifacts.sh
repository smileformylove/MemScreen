#!/usr/bin/env bash
# Build release artifact (single-package macOS installer):
# - Flutter app + embedded backend bootstrap (no models bundled)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "[release] building single-package macOS installer"
  "$SCRIPT_DIR/build_frontend_macos.sh"
else
  echo "[release] skipped: single-package installer requires macOS host"
fi

echo "[release] done"
