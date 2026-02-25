#!/usr/bin/env bash
# MemScreen one-command launcher
# Handles environment bootstrap + runtime startup.

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GRAY='\033[0;37m'
NC='\033[0m'

MODE="auto"            # auto | flutter | api
BOOTSTRAP="1"          # 1 | 0
SKIP_PUB_GET="0"       # forwarded to start_flutter.sh

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-auto}"
      shift 2
      ;;
    --no-bootstrap)
      BOOTSTRAP="0"
      shift
      ;;
    --skip-pub-get)
      SKIP_PUB_GET="1"
      shift
      ;;
    -h|--help)
      cat <<USAGE
Usage: ./scripts/launch.sh [options]

Options:
  --mode <auto|flutter|api>  Launch mode (default: auto)
  --no-bootstrap             Skip venv/dependency bootstrap
  --skip-pub-get             Skip 'flutter pub get' before launch
  -h, --help                 Show this help
USAGE
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ "$MODE" != "auto" && "$MODE" != "flutter" && "$MODE" != "api" ]]; then
  echo "Invalid --mode: $MODE (must be auto|flutter|api)"
  exit 1
fi

print_step() {
  echo -e "${GREEN}✓${NC} $1"
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

print_error() {
  echo -e "${RED}✗${NC} $1"
  shift || true
  if [[ $# -gt 0 ]]; then
    echo -e "  ${GRAY}→ $*${NC}"
  fi
}

find_system_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi
  echo ""
}

find_flutter() {
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

ensure_venv_and_deps() {
  local system_python venv_dir venv_python marker
  system_python="$(find_system_python)"
  if [[ -z "$system_python" ]]; then
    print_error "Python not found" "Install Python 3.8+ first"
    exit 1
  fi

  if [[ -d "$PROJECT_ROOT/.venv" ]]; then
    venv_dir="$PROJECT_ROOT/.venv"
  elif [[ -d "$PROJECT_ROOT/venv" ]]; then
    venv_dir="$PROJECT_ROOT/venv"
  else
    venv_dir="$PROJECT_ROOT/.venv"
    print_info "Creating virtual environment" "$venv_dir"
    "$system_python" -m venv "$venv_dir"
  fi

  venv_python="$venv_dir/bin/python"
  if [[ ! -x "$venv_python" ]]; then
    print_error "Virtual environment is broken" "$venv_python not found"
    exit 1
  fi

  marker="$venv_dir/.memscreen_bootstrap.stamp"
  local need_install="0"
  if [[ ! -f "$marker" ]]; then
    need_install="1"
  elif [[ "$PROJECT_ROOT/pyproject.toml" -nt "$marker" ]]; then
    need_install="1"
  fi

  if [[ "$need_install" == "1" ]]; then
    print_info "Installing Python dependencies" "pip install -e ."
    "$venv_python" -m pip install -U pip setuptools wheel >/dev/null
    "$venv_python" -m pip install -e . >/dev/null
    date +"%Y-%m-%d %H:%M:%S" > "$marker"
    print_step "Python dependencies are ready"
  else
    print_step "Python dependencies already up to date"
  fi

  echo "$venv_python"
}

cd "$PROJECT_ROOT"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  MemScreen One-Command Launch${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

VENV_PYTHON=""
if [[ "$BOOTSTRAP" == "1" ]]; then
  # ensure_venv_and_deps emits progress logs; keep only the final path line.
  VENV_PYTHON="$(ensure_venv_and_deps | tail -n 1)"
else
  if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
  elif [[ -x "$PROJECT_ROOT/venv/bin/python" ]]; then
    VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
  else
    VENV_PYTHON="$(find_system_python)"
  fi
fi

if [[ -z "$VENV_PYTHON" ]]; then
  print_error "No usable Python found"
  exit 1
fi

FLUTTER_BIN="$(find_flutter)"
if [[ "$MODE" == "api" ]]; then
  print_step "Starting API only" "python setup/start_api_only.py"
  exec "$VENV_PYTHON" setup/start_api_only.py
fi

if [[ "$MODE" == "flutter" && -z "$FLUTTER_BIN" ]]; then
  print_error "Flutter mode requested but Flutter is not installed"
  print_info "Install Flutter first, or run API mode" "./scripts/launch.sh --mode api"
  exit 1
fi

if [[ "$MODE" == "auto" && -z "$FLUTTER_BIN" ]]; then
  print_info "Flutter not found" "Falling back to API-only mode"
  exec "$VENV_PYTHON" setup/start_api_only.py
fi

print_step "Starting Flutter mode" "with managed API backend"

ARGS=("--python" "$VENV_PYTHON")
if [[ -n "$FLUTTER_BIN" ]]; then
  ARGS+=("--flutter" "$FLUTTER_BIN")
fi
if [[ "$SKIP_PUB_GET" == "1" ]]; then
  ARGS+=("--skip-pub-get")
fi

exec "$SCRIPT_DIR/start_flutter.sh" "${ARGS[@]}"
