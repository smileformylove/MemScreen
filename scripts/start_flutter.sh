#!/usr/bin/env bash
# MemScreen Flutter runner (runtime only)
# - Starts API backend if needed
# - Builds and runs Flutter macOS app
# Environment/bootstrap concerns are handled by scripts/launch.sh

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
PROJECT_NAME="MemScreen Flutter"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GRAY='\033[0;37m'
NC='\033[0m'

API_HOST="${MEMSCREEN_API_HOST:-127.0.0.1}"
API_PORT="${MEMSCREEN_API_PORT:-8765}"
API_URL="http://${API_HOST}:${API_PORT}"
APP_BUILD_DIR="$PROJECT_ROOT/frontend/flutter/build/macos/Build/Products/Release"
APP_BUNDLE_PRIMARY="$APP_BUILD_DIR/MemScreen.app"
APP_BUNDLE_LEGACY="$APP_BUILD_DIR/memscreen_flutter.app"

USER_PYTHON=""
USER_FLUTTER=""
SKIP_PUB_GET="0"
DETACH="0"
SKIP_BUILD="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      USER_PYTHON="${2:-}"
      shift 2
      ;;
    --flutter)
      USER_FLUTTER="${2:-}"
      shift 2
      ;;
    --skip-pub-get)
      SKIP_PUB_GET="1"
      shift
      ;;
    --skip-build)
      SKIP_BUILD="1"
      shift
      ;;
    --detach)
      DETACH="1"
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Usage: $0 [--python /path/to/python] [--flutter /path/to/flutter] [--skip-pub-get] [--skip-build] [--detach]"
      exit 1
      ;;
  esac
done

print_banner() {
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}  ${PROJECT_NAME}${NC}"
  echo -e "${BLUE}  AI-Powered Visual Memory System${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
}

print_step() {
  echo -e "${GREEN}✓${NC} $1"
  shift
  echo -e "  ${GRAY}→ $*${NC}"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
  shift || true
  if [[ $# -gt 0 ]]; then
    echo -e "  ${GRAY}→ $*${NC}"
  fi
}

print_info() {
  echo -e "${BLUE}ℹ${NC} $1"
  shift || true
  if [[ $# -gt 0 ]]; then
    echo -e "  ${GRAY}→ $*${NC}"
  fi
}

find_flutter() {
  if [[ -n "$USER_FLUTTER" && -x "$USER_FLUTTER" ]]; then
    echo "$USER_FLUTTER"
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

choose_python() {
  if [[ -n "$USER_PYTHON" && -x "$USER_PYTHON" ]]; then
    echo "$USER_PYTHON"
    return
  fi
  if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    echo "$PROJECT_ROOT/.venv/bin/python"
    return
  fi
  if [[ -x "$PROJECT_ROOT/venv/bin/python" ]]; then
    echo "$PROJECT_ROOT/venv/bin/python"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  echo ""
}

API_STARTED_BY_SCRIPT=0
API_PID=""
APP_PID=""

cleanup() {
  echo ""
  echo -e "${YELLOW}🛑 Cleaning up...${NC}"
  if [[ "$API_STARTED_BY_SCRIPT" == "1" && -n "$API_PID" ]]; then
    kill "$API_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "$APP_PID" ]]; then
    kill "$APP_PID" >/dev/null 2>&1 || true
  fi
  echo -e "${GREEN}✓ Cleanup complete${NC}"
}

trap cleanup EXIT INT TERM

print_banner

PYTHON_CMD="$(choose_python)"
if [[ -z "$PYTHON_CMD" ]]; then
  print_error "Python 3 not found" "Install Python 3.8+ first"
  exit 1
fi

FLUTTER_BIN="$(find_flutter)"
if [[ -z "$FLUTTER_BIN" ]]; then
  print_error "Flutter not found" "Install Flutter or set FLUTTER_ROOT"
  exit 1
fi

echo -e "${GRAY}Python:${NC}   $($PYTHON_CMD --version 2>&1 | head -1)"
echo -e "${GRAY}Flutter:${NC}  $FLUTTER_BIN"
echo -e "${GRAY}API:${NC}      $API_URL"

APP_BUNDLE=""
APP_BIN=""
APP_BUNDLE_HINT="$APP_BUNDLE_PRIMARY"

resolve_app_artifacts() {
  local candidate_bundle
  local candidate_exec
  local candidate_bin

  for candidate_bundle in "$APP_BUNDLE_PRIMARY" "$APP_BUNDLE_LEGACY"; do
    if [[ ! -d "$candidate_bundle" ]]; then
      continue
    fi
    candidate_exec="$(basename "$candidate_bundle" .app)"
    candidate_bin="$candidate_bundle/Contents/MacOS/$candidate_exec"
    if [[ -x "$candidate_bin" ]]; then
      APP_BUNDLE="$candidate_bundle"
      APP_BIN="$candidate_bin"
      APP_BUNDLE_HINT="$candidate_bundle"
      return 0
    fi
  done

  APP_BUNDLE="$APP_BUNDLE_PRIMARY"
  APP_BIN="$APP_BUNDLE/Contents/MacOS/MemScreen"
  APP_BUNDLE_HINT="$APP_BUNDLE_PRIMARY"
  return 1
}

if [[ "$SKIP_BUILD" == "1" ]]; then
  resolve_app_artifacts >/dev/null 2>&1 || true
fi

action_stop_stale() {
  local app_pids
  app_pids="$(
    {
      pgrep -f 'MemScreen.app/Contents/MacOS/MemScreen' || true
      pgrep -f 'memscreen_flutter.app/Contents/MacOS/memscreen_flutter' || true
    } | sort -u
  )"
  if [[ -n "$app_pids" ]]; then
    print_info "Stopping existing MemScreen app instances" "$app_pids"
    kill $app_pids >/dev/null 2>&1 || true
    sleep 1
  fi

  local stale_run_pids
  stale_run_pids="$(pgrep -f 'flutter_tools.snapshot run -d macos' || true)"
  if [[ -n "$stale_run_pids" ]]; then
    print_info "Stopping stale Flutter runner processes" "$stale_run_pids"
    kill $stale_run_pids >/dev/null 2>&1 || true
    sleep 1
  fi

}

print_step "1/3" "Preparing runtime"
action_stop_stale

print_step "2/3" "Starting API backend"
cd "$PROJECT_ROOT"
if curl -s "$API_URL/health" >/dev/null 2>&1; then
  print_info "API already running" "Reusing $API_URL"
else
  # Ensure local checkout source is importable even when package is not installed.
  if [[ "$DETACH" == "1" ]]; then
    mkdir -p "$HOME/.memscreen/logs"
    nohup env PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}" \
      MEMSCREEN_APP_BUNDLE_HINT="$APP_BUNDLE_HINT" \
      "$PYTHON_CMD" setup/start_api_only.py >> "$HOME/.memscreen/logs/api_detach.log" 2>&1 &
    API_STARTED_BY_SCRIPT=0
  else
    PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}" MEMSCREEN_APP_BUNDLE_HINT="$APP_BUNDLE_HINT" "$PYTHON_CMD" setup/start_api_only.py &
    API_STARTED_BY_SCRIPT=1
  fi
  API_PID=$!
  print_info "API PID" "$API_PID"

  max_retries=20
  retries=0
  until curl -s "$API_URL/health" >/dev/null 2>&1; do
    retries=$((retries + 1))
    if [[ $retries -ge $max_retries ]]; then
      print_error "API failed to start" "Checked $API_URL/health for ${max_retries}s"
      exit 1
    fi
    sleep 1
  done
fi

print_step "3/3" "Launching Flutter app"
if [[ "$SKIP_PUB_GET" != "1" ]]; then
  print_info "Installing Flutter dependencies" "flutter pub get"
  (cd "$PROJECT_ROOT/frontend/flutter" && "$FLUTTER_BIN" pub get >/dev/null)
fi

if [[ "$SKIP_BUILD" == "1" ]]; then
  if resolve_app_artifacts; then
    print_info "Reusing existing Flutter build" "$APP_BUNDLE"
  else
    print_info "skip-build requested but app not found" "Running flutter build once"
    (cd "$PROJECT_ROOT/frontend/flutter" && "$FLUTTER_BIN" build macos --release >/dev/null)
  fi
else
  print_info "Building Flutter macOS app" "flutter build macos --release"
  (cd "$PROJECT_ROOT/frontend/flutter" && "$FLUTTER_BIN" build macos --release >/dev/null)
fi

resolve_app_artifacts >/dev/null 2>&1 || true

if [[ ! -x "$APP_BIN" || ! -d "$APP_BUNDLE" ]]; then
  print_error "Built app not found or not executable" "$APP_BIN"
  exit 1
fi

if [[ "$DETACH" == "1" ]]; then
  mkdir -p "$HOME/.memscreen/logs"
  # Use LaunchServices in detach mode so app lifecycle is independent
  # from this shell session.
  nohup open "$APP_BUNDLE" >> "$HOME/.memscreen/logs/flutter_detach.log" 2>&1 &
else
  "$APP_BIN" &
fi
APP_PID=$!

print_info "App PID" "$APP_PID"
echo -e "${GRAY}Logs:${NC}     ~/.memscreen/logs/"

if [[ "$DETACH" == "1" ]]; then
  print_info "Detach mode enabled" "Launcher will exit and keep API/app running"
  API_STARTED_BY_SCRIPT=0
  API_PID=""
  APP_PID=""
  trap - EXIT INT TERM
  exit 0
fi

echo -e "${BLUE}Press Ctrl+C in this terminal to stop${NC}"

while kill -0 "$APP_PID" >/dev/null 2>&1; do
  sleep 1
done

echo ""
echo -e "${YELLOW}🛑 App exited${NC}"
if [[ "$API_STARTED_BY_SCRIPT" == "1" && -n "$API_PID" ]]; then
  kill "$API_PID" >/dev/null 2>&1 || true
fi
