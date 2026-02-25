#!/usr/bin/env bash
# Build frontend-only macOS installer artifacts (.zip + .dmg).
# This package intentionally excludes backend runtime and models.
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

VERSION="$(awk -F'"' '/^__version__ = /{print $2}' "$PROJECT_ROOT/memscreen/version.py")"
if [[ -z "$VERSION" ]]; then
  echo "[frontend-package] Failed to parse version from memscreen/version.py"
  exit 1
fi

APP_SRC="$FRONTEND_DIR/build/macos/Build/Products/Release/memscreen_flutter.app"
APP_NAME="MemScreen.app"
APP_STAGE_PATH="$STAGE_DIR/$APP_NAME"

ZIP_OUT="$DIST_ROOT/MemScreen-frontend-v${VERSION}-macos.zip"
DMG_OUT="$DIST_ROOT/MemScreen-frontend-v${VERSION}-macos.dmg"

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
mkdir -p "$DIST_ROOT"

echo "[frontend-package] flutter pub get"
(cd "$FRONTEND_DIR" && "$FLUTTER_CMD" pub get)

echo "[frontend-package] flutter build macos --release"
(cd "$FRONTEND_DIR" && "$FLUTTER_CMD" build macos --release)

if [[ ! -d "$APP_SRC" ]]; then
  echo "[frontend-package] Built app not found: $APP_SRC"
  exit 1
fi

cp -R "$APP_SRC" "$APP_STAGE_PATH"
codesign_app_if_needed

cat > "$STAGE_DIR/README_FIRST.txt" <<'TXT'
MemScreen Frontend Installer

This package contains only the Flutter desktop app.
To use full local features, point it to a running MemScreen backend API.
Default API URL: http://127.0.0.1:8765

If model features are needed, install models separately:
  scripts/release/download_models.sh
TXT

rm -f "$ZIP_OUT" "$DMG_OUT"

echo "[frontend-package] creating zip: $ZIP_OUT"
ditto -c -k --sequesterRsrc --keepParent "$APP_STAGE_PATH" "$ZIP_OUT"

echo "[frontend-package] creating dmg: $DMG_OUT"
hdiutil create -volname "MemScreen" -srcfolder "$STAGE_DIR" -ov -format UDZO "$DMG_OUT" >/dev/null

notarize_if_needed

echo "[frontend-package] Done"
echo "  zip: $ZIP_OUT"
echo "  dmg: $DMG_OUT"
