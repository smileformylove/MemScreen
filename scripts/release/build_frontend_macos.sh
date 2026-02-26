#!/usr/bin/env bash
# Build single-package macOS installer (.dmg).
# Package includes Flutter app + embedded backend bootstrap (no models bundled).
#
# Optional signing/notarization env:
#   CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
#   ENABLE_NOTARIZATION=1
#   APPLE_ID="you@example.com"
#   APPLE_APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
#   APPLE_TEAM_ID="TEAMID"
#   CODESIGN_ENTITLEMENTS="/path/to/entitlements.plist"  # optional

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend/flutter"
DIST_ROOT="$PROJECT_ROOT/dist/release/frontend/macos"
STAGE_DIR="$DIST_ROOT/stage"
NOTARY_TMP_ZIP="$DIST_ROOT/.notary_tmp.zip"
LITE_RUNTIME_REQUIREMENTS="$PROJECT_ROOT/setup/runtime/requirements.lite.txt"

find_flutter() {
  if [[ -n "${FLUTTER_BIN:-}" && -x "${FLUTTER_BIN}" ]]; then
    echo "${FLUTTER_BIN}"
    return
  fi
  if [[ -n "${FLUTTER_ROOT:-}" && -x "${FLUTTER_ROOT}/bin/flutter" ]]; then
    echo "${FLUTTER_ROOT}/bin/flutter"
    return
  fi
  if command -v flutter >/dev/null 2>&1; then
    command -v flutter
    return
  fi
  for p in "$HOME/development/flutter/bin/flutter" "$HOME/Documents/project_code/flutter/bin/flutter"; do
    if [[ -x "$p" ]]; then
      echo "$p"
      return
    fi
  done
  echo ""
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[frontend-package] This script must run on macOS."
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "[frontend-package] Flutter frontend directory not found: $FRONTEND_DIR"
  exit 1
fi

notarytool_args() {
  if [[ -n "${NOTARYTOOL_KEYCHAIN_PROFILE:-}" ]]; then
    echo "--keychain-profile" "${NOTARYTOOL_KEYCHAIN_PROFILE}"
    return
  fi

  if [[ -z "${APPLE_ID:-}" || -z "${APPLE_APP_SPECIFIC_PASSWORD:-}" || -z "${APPLE_TEAM_ID:-}" ]]; then
    echo "[frontend-package] notarization requires one of:"
    echo "  1) NOTARYTOOL_KEYCHAIN_PROFILE"
    echo "  2) APPLE_ID + APPLE_APP_SPECIFIC_PASSWORD + APPLE_TEAM_ID"
    exit 1
  fi

  echo "--apple-id" "${APPLE_ID}" "--password" "${APPLE_APP_SPECIFIC_PASSWORD}" "--team-id" "${APPLE_TEAM_ID}"
}

codesign_app_if_needed() {
  if [[ -z "${CODESIGN_IDENTITY:-}" ]]; then
    echo "[frontend-package] codesign skipped (CODESIGN_IDENTITY is empty)"
    return
  fi

  echo "[frontend-package] codesigning app with identity: ${CODESIGN_IDENTITY}"
  local sign_args=(
    --force
    --deep
    --options runtime
    --timestamp
    --sign "${CODESIGN_IDENTITY}"
  )
  if [[ -n "${CODESIGN_ENTITLEMENTS:-}" ]]; then
    sign_args+=(--entitlements "${CODESIGN_ENTITLEMENTS}")
  fi

  codesign "${sign_args[@]}" "$APP_STAGE_PATH"
  codesign --verify --deep --strict --verbose=2 "$APP_STAGE_PATH"
  echo "[frontend-package] codesign verify passed"
}

notarize_if_needed() {
  if [[ "${ENABLE_NOTARIZATION:-0}" != "1" ]]; then
    echo "[frontend-package] notarization skipped (ENABLE_NOTARIZATION != 1)"
    return
  fi
  if [[ -z "${CODESIGN_IDENTITY:-}" ]]; then
    echo "[frontend-package] notarization requested but CODESIGN_IDENTITY is empty"
    exit 1
  fi
  if ! command -v xcrun >/dev/null 2>&1; then
    echo "[frontend-package] xcrun not found; notarization unavailable"
    exit 1
  fi

  read -r -a NOTARY_ARGS <<< "$(notarytool_args)"

  rm -f "$NOTARY_TMP_ZIP"
  ditto -c -k --sequesterRsrc --keepParent "$APP_STAGE_PATH" "$NOTARY_TMP_ZIP"

  echo "[frontend-package] notarizing app zip"
  xcrun notarytool submit "$NOTARY_TMP_ZIP" "${NOTARY_ARGS[@]}" --wait
  xcrun stapler staple "$APP_STAGE_PATH"
  xcrun stapler validate "$APP_STAGE_PATH"
  rm -f "$NOTARY_TMP_ZIP"

  echo "[frontend-package] notarizing dmg"
  xcrun notarytool submit "$DMG_OUT" "${NOTARY_ARGS[@]}" --wait
  xcrun stapler staple "$DMG_OUT"
  xcrun stapler validate "$DMG_OUT"
}

FLUTTER_CMD="$(find_flutter)"
if [[ -z "$FLUTTER_CMD" ]]; then
  echo "[frontend-package] flutter is not installed or not discoverable."
  exit 1
fi

if [[ ! -f "$LITE_RUNTIME_REQUIREMENTS" ]]; then
  echo "[frontend-package] lite runtime requirements not found: $LITE_RUNTIME_REQUIREMENTS"
  exit 1
fi

VERSION="$(awk -F'"' '/^__version__ = /{print $2}' "$PROJECT_ROOT/memscreen/version.py")"
if [[ -z "$VERSION" ]]; then
  echo "[frontend-package] Failed to parse version from memscreen/version.py"
  exit 1
fi

APP_SRC="$FRONTEND_DIR/build/macos/Build/Products/Release/memscreen_flutter.app"
APP_NAME="MemScreen.app"
APP_STAGE_PATH="$STAGE_DIR/$APP_NAME"
APP_MACOS_DIR="$APP_STAGE_PATH/Contents/MacOS"
APP_RESOURCES_DIR="$APP_STAGE_PATH/Contents/Resources"
BACKEND_DIR="$APP_RESOURCES_DIR/backend"

DMG_OUT="$DIST_ROOT/MemScreen-v${VERSION}-macos.dmg"

prepare_embedded_backend() {
  echo "[frontend-package] preparing embedded backend bootstrap"
  mkdir -p "$BACKEND_DIR/src"

  cp "$PROJECT_ROOT/setup/start_api_only.py" "$BACKEND_DIR/"
  cp "$PROJECT_ROOT/scripts/release/download_models.sh" "$BACKEND_DIR/"
  cp "$LITE_RUNTIME_REQUIREMENTS" "$BACKEND_DIR/requirements.lite.txt"
  rm -rf "$BACKEND_DIR/src/memscreen"
  cp -R "$PROJECT_ROOT/memscreen" "$BACKEND_DIR/src/"

  cat > "$BACKEND_DIR/bootstrap_backend.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

APP_BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${HOME}/.memscreen/runtime"
VENV_DIR="${RUNTIME_DIR}/.venv"
STAMP_FILE="${RUNTIME_DIR}/.backend_installed"
LOCK_DIR="${RUNTIME_DIR}/.bootstrap_lock"
LOG_DIR="${HOME}/.memscreen/logs"
API_LOG="${LOG_DIR}/api_from_app.log"
BOOTSTRAP_LOG="${LOG_DIR}/backend_bootstrap.log"
API_HEALTH_URL="${MEMSCREEN_API_URL:-http://127.0.0.1:8765/health}"
REQ_FILE="${APP_BACKEND_DIR}/requirements.lite.txt"
SOURCE_MARKER="${APP_BACKEND_DIR}/src/memscreen/version.py"
SOURCE_SHA_FILE="${RUNTIME_DIR}/.backend_source_sha"

mkdir -p "$RUNTIME_DIR" "$LOG_DIR"
touch "$BOOTSTRAP_LOG"
exec >>"$BOOTSTRAP_LOG" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] [backend-bootstrap] begin"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [backend-bootstrap] another bootstrap is running"
  exit 0
fi
trap 'rmdir "$LOCK_DIR" >/dev/null 2>&1 || true' EXIT

if ! command -v python3 >/dev/null 2>&1; then
  echo "[backend-bootstrap] python3 not found"
  exit 1
fi

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  echo "[backend-bootstrap] creating runtime venv"
  python3 -m venv "$VENV_DIR"
fi

if [[ ! -f "$SOURCE_MARKER" ]]; then
  echo "[backend-bootstrap] embedded source not found: $SOURCE_MARKER"
  exit 1
fi

CURRENT_SOURCE_SHA="$(
  python3 - "$APP_BACKEND_DIR/src/memscreen" <<'PY'
import hashlib
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
h = hashlib.sha256()
if root.exists():
    for path in sorted(root.rglob("*.py")):
        rel = str(path.relative_to(root)).encode("utf-8", "ignore")
        h.update(rel)
        h.update(b"\0")
        try:
            h.update(path.read_bytes())
        except Exception:
            continue
        h.update(b"\0")
print(h.hexdigest())
PY
)"
PREV_SOURCE_SHA=""
if [[ -f "$SOURCE_SHA_FILE" ]]; then
  PREV_SOURCE_SHA="$(cat "$SOURCE_SHA_FILE" | tr -d '[:space:]')"
fi
SOURCE_CHANGED=0
if [[ -n "$CURRENT_SOURCE_SHA" && "$CURRENT_SOURCE_SHA" != "$PREV_SOURCE_SHA" ]]; then
  SOURCE_CHANGED=1
fi
if [[ "$SOURCE_CHANGED" == "1" ]]; then
  echo "[backend-bootstrap] embedded backend source changed; restarting API process"
  pkill -f "start_api_only.py" >/dev/null 2>&1 || true
fi

if curl -fsS "$API_HEALTH_URL" >/dev/null 2>&1 && [[ "$SOURCE_CHANGED" != "1" ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [backend-bootstrap] api already healthy (source unchanged)"
  exit 0
fi

if [[ ! -f "$STAMP_FILE" || "$REQ_FILE" -nt "$STAMP_FILE" || "$SOURCE_MARKER" -nt "$STAMP_FILE" ]]; then
  echo "[backend-bootstrap] installing lite runtime dependencies"
  "${VENV_DIR}/bin/python" -m pip install -r "$REQ_FILE"
  date +"%Y-%m-%d %H:%M:%S" > "$STAMP_FILE"
  echo "[backend-bootstrap] install complete"
fi

# Best-effort audio runtime support for packaged app.
# Keep startup resilient: audio extras failing should not block recording/video usage.
if ! "${VENV_DIR}/bin/python" -c "import pyaudio" >/dev/null 2>&1; then
  echo "[backend-bootstrap] installing optional audio dependency: pyaudio"
  if ! "${VENV_DIR}/bin/python" -m pip install pyaudio; then
    echo "[backend-bootstrap] warning: optional pyaudio install failed; audio capture may be unavailable"
  fi
fi

if [[ -n "$CURRENT_SOURCE_SHA" ]]; then
  echo "$CURRENT_SOURCE_SHA" > "$SOURCE_SHA_FILE"
fi

if curl -fsS "$API_HEALTH_URL" >/dev/null 2>&1; then
  echo "[backend-bootstrap] api became healthy during setup"
  exit 0
fi

if pgrep -f "${APP_BACKEND_DIR}/start_api_only.py" >/dev/null 2>&1; then
  echo "[backend-bootstrap] api process already running"
  exit 0
fi

echo "[backend-bootstrap] launching API"
nohup env MEMSCREEN_BACKEND_SRC="${APP_BACKEND_DIR}/src" \
  PYTHONPATH="${APP_BACKEND_DIR}/src${PYTHONPATH:+:$PYTHONPATH}" \
  "${VENV_DIR}/bin/python" "${APP_BACKEND_DIR}/start_api_only.py" >>"$API_LOG" 2>&1 &
echo "[backend-bootstrap] done"
SH
  chmod +x "$BACKEND_DIR/bootstrap_backend.sh"
  chmod +x "$BACKEND_DIR/download_models.sh"
}

install_startup_wrapper() {
  echo "[frontend-package] installing app startup wrapper"
  local real_bin="$APP_MACOS_DIR/memscreen_flutter_real"
  local wrapper_bin="$APP_MACOS_DIR/memscreen_flutter"

  if [[ ! -x "$wrapper_bin" ]]; then
    echo "[frontend-package] flutter app executable missing: $wrapper_bin"
    exit 1
  fi

  mv "$wrapper_bin" "$real_bin"
  cat > "$wrapper_bin" <<'SH'
#!/usr/bin/env bash
set -euo pipefail

APP_BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_BOOTSTRAP="${APP_BIN_DIR}/../Resources/backend/bootstrap_backend.sh"
HEALTH_URL="${MEMSCREEN_API_URL:-http://127.0.0.1:8765/health}"
LOG_DIR="${HOME}/.memscreen/logs"
WRAPPER_LOG="${LOG_DIR}/app_wrapper.log"

if [[ -x "$BACKEND_BOOTSTRAP" ]]; then
  mkdir -p "$LOG_DIR"
  touch "$WRAPPER_LOG"
  nohup "$BACKEND_BOOTSTRAP" >>"$WRAPPER_LOG" 2>&1 &
  for _ in {1..5}; do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

exec "${APP_BIN_DIR}/memscreen_flutter_real" "$@"
SH
  chmod +x "$wrapper_bin"
}

mkdir -p "$DIST_ROOT"
rm -rf "$STAGE_DIR"
rm -f "$DIST_ROOT"/MemScreen-v*-macos.dmg
rm -f "$DIST_ROOT"/MemScreen-frontend-v*-macos.dmg
rm -f "$DIST_ROOT"/MemScreen-frontend-v*-macos.zip
mkdir -p "$STAGE_DIR"

echo "[frontend-package] flutter pub get"
(cd "$FRONTEND_DIR" && "$FLUTTER_CMD" pub get)

echo "[frontend-package] flutter build macos --release"
(cd "$FRONTEND_DIR" && "$FLUTTER_CMD" build macos --release)

if [[ ! -d "$APP_SRC" ]]; then
  echo "[frontend-package] Built app not found: $APP_SRC"
  exit 1
fi

cp -R "$APP_SRC" "$APP_STAGE_PATH"
prepare_embedded_backend
install_startup_wrapper
codesign_app_if_needed

cat > "$STAGE_DIR/README_FIRST.txt" <<'TXT'
MemScreen Installer (No Models Bundled)

This package includes:
- Flutter desktop app
- Embedded backend bootstrap (auto-start in background on launch)
- No bundled model files

At first launch, runtime dependencies are installed automatically into:
  ~/.memscreen/runtime/.venv
This can take a little longer once.

Troubleshooting logs:
  ~/.memscreen/logs/backend_bootstrap.log
  ~/.memscreen/logs/api_from_app.log
  ~/.memscreen/logs/app_wrapper.log

Model capability is optional. To install models:
  open Terminal and run:
  ~/.memscreen/runtime/.venv/bin/python -m pip install ollama
  then use the bundled script in app resources:
  MemScreen.app/Contents/Resources/backend/download_models.sh
TXT

echo "[frontend-package] creating dmg: $DMG_OUT"
hdiutil create -volname "MemScreen" -srcfolder "$STAGE_DIR" -ov -format UDZO "$DMG_OUT" >/dev/null

notarize_if_needed

echo "[frontend-package] Done"
echo "  dmg: $DMG_OUT"
