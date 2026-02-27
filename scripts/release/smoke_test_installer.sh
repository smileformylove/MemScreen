#!/usr/bin/env bash
# Smoke test for the packaged macOS installer.
# Goal: verify "no models" runtime can boot backend and expose recording endpoints.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DMG_INPUT="${1:-$PROJECT_ROOT/dist/release/frontend/macos/MemScreen-v*-macos.dmg}"
API_PORT="${MEMSCREEN_API_PORT:-8876}"
API_BASE_URL="${MEMSCREEN_API_BASE_URL:-http://127.0.0.1:${API_PORT}}"
API_HEALTH_URL="${API_BASE_URL}/health"

resolve_dmg() {
  local input="$1"
  if [[ -f "$input" ]]; then
    echo "$input"
    return
  fi
  local matches=()
  # shellcheck disable=SC2206
  matches=($input)
  if [[ "${#matches[@]}" -eq 0 ]]; then
    return 1
  fi
  printf '%s\n' "${matches[@]}" | head -n1
}

DMG_PATH="$(resolve_dmg "$DMG_INPUT" || true)"
if [[ -z "$DMG_PATH" || ! -f "$DMG_PATH" ]]; then
  echo "[smoke] dmg not found: $DMG_INPUT"
  exit 1
fi

TMP_ROOT="$(mktemp -d /tmp/memscreen-release-smoke.XXXXXX)"
TEST_HOME="$TMP_ROOT/home"
APPS_DIR="$TMP_ROOT/Applications"
APP_COPY="$APPS_DIR/MemScreen.app"
ATTACH_LOG="$TMP_ROOT/hdiutil_attach.log"
MOUNT_POINT=""

dump_logs() {
  local log_dir="$TEST_HOME/.memscreen/logs"
  echo "[smoke] --- backend_bootstrap.log ---"
  if [[ -f "$log_dir/backend_bootstrap.log" ]]; then
    tail -n 200 "$log_dir/backend_bootstrap.log"
  else
    echo "(missing)"
  fi
  echo "[smoke] --- api_from_app.log ---"
  if [[ -f "$log_dir/api_from_app.log" ]]; then
    tail -n 200 "$log_dir/api_from_app.log"
  else
    echo "(missing)"
  fi
  echo "[smoke] --- app_wrapper.log ---"
  if [[ -f "$log_dir/app_wrapper.log" ]]; then
    tail -n 120 "$log_dir/app_wrapper.log"
  else
    echo "(missing)"
  fi
}

cleanup() {
  if [[ -d "$APP_COPY" ]]; then
    pkill -f "$APP_COPY/Contents/Resources/backend/start_api_only.py" >/dev/null 2>&1 || true
  fi
  if [[ -n "$MOUNT_POINT" ]]; then
    hdiutil detach "$MOUNT_POINT" -force >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

echo "[smoke] attaching dmg: $DMG_PATH"
hdiutil attach "$DMG_PATH" -nobrowse -readonly >"$ATTACH_LOG"
MOUNT_POINT="$(sed -nE 's#.*(/Volumes/.*)$#\1#p' "$ATTACH_LOG" | tail -n1)"
if [[ -z "$MOUNT_POINT" || ! -d "$MOUNT_POINT" ]]; then
  echo "[smoke] failed to resolve mounted volume"
  cat "$ATTACH_LOG"
  exit 1
fi

if [[ ! -d "$MOUNT_POINT/MemScreen.app" ]]; then
  echo "[smoke] MemScreen.app not found in dmg volume: $MOUNT_POINT"
  exit 1
fi

mkdir -p "$APPS_DIR" "$TEST_HOME"
cp -R "$MOUNT_POINT/MemScreen.app" "$APP_COPY"

BACKEND_BOOTSTRAP="$APP_COPY/Contents/Resources/backend/bootstrap_backend.sh"
if [[ ! -x "$BACKEND_BOOTSTRAP" ]]; then
  echo "[smoke] missing backend bootstrap script: $BACKEND_BOOTSTRAP"
  exit 1
fi

echo "[smoke] starting embedded backend bootstrap on isolated port: $API_PORT"
HOME="$TEST_HOME" \
  MEMSCREEN_API_PORT="$API_PORT" \
  MEMSCREEN_API_URL="$API_HEALTH_URL" \
  "$BACKEND_BOOTSTRAP"

echo "[smoke] waiting for health endpoint: $API_HEALTH_URL"
HEALTH_JSON="$TMP_ROOT/health.json"
for _ in {1..90}; do
  if curl -fsS "$API_HEALTH_URL" >"$HEALTH_JSON"; then
    break
  fi
  sleep 1
done

if [[ ! -s "$HEALTH_JSON" ]]; then
  echo "[smoke] backend health check timed out"
  dump_logs
  exit 1
fi

python3 - "$HEALTH_JSON" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text())
status = str(payload.get("status", "")).strip().lower()
if status != "ok":
    raise SystemExit(f"[smoke] health.status is not ok: {payload}")
print(f"[smoke] health ok: {payload}")
PY

RUNTIME_PY="$TEST_HOME/.memscreen/runtime/.venv/bin/python"
if [[ -x "$RUNTIME_PY" ]]; then
  "$RUNTIME_PY" - <<'PY'
import importlib.util
import os

for mod in ("httpx", "imageio_ffmpeg", "pyaudio"):
    if importlib.util.find_spec(mod) is None:
        raise SystemExit(f"[smoke] missing runtime module: {mod}")

import imageio_ffmpeg  # noqa

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
if not ffmpeg_exe or not os.path.exists(ffmpeg_exe):
    raise SystemExit(f"[smoke] imageio-ffmpeg executable is unavailable: {ffmpeg_exe}")
print(f"[smoke] runtime deps ok, bundled ffmpeg={ffmpeg_exe}")
PY
fi

SCREENS_JSON="$TMP_ROOT/screens.json"
SCREENS_CODE="$(curl -sS -o "$SCREENS_JSON" -w '%{http_code}' "$API_BASE_URL/recording/screens" || true)"
if [[ "$SCREENS_CODE" != "200" ]]; then
  echo "[smoke] /recording/screens returned HTTP $SCREENS_CODE"
  cat "$SCREENS_JSON" || true
  dump_logs
  exit 1
fi

python3 - "$SCREENS_JSON" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text())
screens = payload.get("screens")
if not isinstance(screens, list):
    raise SystemExit(f"[smoke] invalid screens payload: {payload}")
if screens:
    first = screens[0]
    if "display_id" not in first:
        raise SystemExit(f"[smoke] screens payload missing display_id: {first}")
print(f"[smoke] recording endpoint ok, screens_count={len(screens)}")
PY

STATUS_JSON="$TMP_ROOT/recording_status.json"
STATUS_CODE="$(curl -sS -o "$STATUS_JSON" -w '%{http_code}' "$API_BASE_URL/recording/status" || true)"
if [[ "$STATUS_CODE" != "200" ]]; then
  echo "[smoke] /recording/status returned HTTP $STATUS_CODE"
  cat "$STATUS_JSON" || true
  dump_logs
  exit 1
fi

CHAT_MODELS_JSON="$TMP_ROOT/chat_models.json"
CHAT_MODELS_CODE="$(curl -sS -o "$CHAT_MODELS_JSON" -w '%{http_code}' "$API_BASE_URL/chat/models" || true)"
if [[ "$CHAT_MODELS_CODE" != "200" ]]; then
  echo "[smoke] /chat/models returned HTTP $CHAT_MODELS_CODE"
  cat "$CHAT_MODELS_JSON" || true
  dump_logs
  exit 1
fi
echo "[smoke] chat models endpoint ok"

MODELS_JSON="$TMP_ROOT/models_catalog.json"
MODELS_CODE="$(curl -sS -o "$MODELS_JSON" -w '%{http_code}' "$API_BASE_URL/models/catalog" || true)"
if [[ "$MODELS_CODE" != "200" ]]; then
  echo "[smoke] /models/catalog returned HTTP $MODELS_CODE"
  cat "$MODELS_JSON" || true
  dump_logs
  exit 1
fi
echo "[smoke] models catalog endpoint ok"

TRACK_STATUS_JSON="$TMP_ROOT/tracking_status.json"
TRACK_STATUS_CODE="$(curl -sS -o "$TRACK_STATUS_JSON" -w '%{http_code}' "$API_BASE_URL/process/tracking/status" || true)"
if [[ "$TRACK_STATUS_CODE" != "200" ]]; then
  echo "[smoke] /process/tracking/status returned HTTP $TRACK_STATUS_CODE"
  cat "$TRACK_STATUS_JSON" || true
  dump_logs
  exit 1
fi

MARK_JSON="$TMP_ROOT/tracking_mark_start.json"
MARK_CODE="$(curl -sS -o "$MARK_JSON" -w '%{http_code}' -X POST "$API_BASE_URL/process/tracking/mark-start" || true)"
if [[ "$MARK_CODE" != "200" && "$MARK_CODE" != "400" ]]; then
  echo "[smoke] /process/tracking/mark-start unexpected HTTP $MARK_CODE"
  cat "$MARK_JSON" || true
  dump_logs
  exit 1
fi
echo "[smoke] tracking mark-start check status=$MARK_CODE"

LEGACY_BODY="$TMP_ROOT/legacy_window_start.json"
python3 - "$SCREENS_JSON" "$LEGACY_BODY" <<'PY'
import json
import pathlib
import sys

screens = json.loads(pathlib.Path(sys.argv[1]).read_text()).get("screens", [])
target = screens[1] if len(screens) > 1 else (screens[0] if screens else {})
payload = {
    "duration": 2,
    "interval": 1.0,
    "mode": "window",
    "region": [100, 100, 400, 300],
    "audio_source": "none",
    "window_title": "Window: SmokeTest",
}
if isinstance(target, dict):
    if target.get("index") is not None:
        payload["screen_index"] = target["index"]
    if target.get("display_id") is not None:
        payload["screen_display_id"] = target["display_id"]
pathlib.Path(sys.argv[2]).write_text(json.dumps(payload))
PY

LEGACY_RESP="$TMP_ROOT/legacy_window_resp.json"
LEGACY_CODE="$(curl -sS -o "$LEGACY_RESP" -w '%{http_code}' \
  -X POST "$API_BASE_URL/recording/start" \
  -H 'Content-Type: application/json' \
  --data-binary "@$LEGACY_BODY" || true)"
if [[ "$LEGACY_CODE" == "400" ]] && rg -n "Invalid recording mode: window" "$LEGACY_RESP" >/dev/null 2>&1; then
  echo "[smoke] legacy window-mode compatibility failed: $(cat "$LEGACY_RESP")"
  dump_logs
  exit 1
fi
if [[ "$LEGACY_CODE" == "200" ]]; then
  curl -fsS -X POST "$API_BASE_URL/recording/stop" >/dev/null || true
fi
echo "[smoke] legacy window-mode check status=$LEGACY_CODE"

echo "[smoke] installer smoke test passed"
