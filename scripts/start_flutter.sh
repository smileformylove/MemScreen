#!/bin/bash
# MemScreen Flutter - Unified Startup Script
# Automatically starts API backend, then launches Flutter frontend
# Use: ./start_flutter.sh or just `flutter` (if you create alias)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
PROJECT_NAME="MemScreen Flutter"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Helper functions
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
    echo -e "  ${GRAY}→ $2${NC}"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    echo -e "  ${GRAY}→ $2${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
    echo -e "  ${GRAY}→ $2${NC}"
}

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Cleaning up...${NC}"
    if [ "$API_STARTED_BY_SCRIPT" = "1" ] && [ -n "${API_PID:-}" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    if [ -n "${APP_PID:-}" ]; then
        kill $APP_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Signal handlers
trap cleanup EXIT INT TERM

print_banner

API_STARTED_BY_SCRIPT=0

# Check dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Get paths
PYTHON_CMD="python3"
API_PYTHON_CMD="python3"
VENV_DIR=""
if [ -f "venv/bin/activate" ]; then
    VENV_DIR="venv"
    VENV_BIN="venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    VENV_DIR=".venv"
    VENV_BIN=".venv/bin/activate"
fi

# Don't check for conda - just use system python if no venv
if [ -n "$VENV_DIR" ]; then
    source $VENV_BIN
    print_info "Virtual environment: $VENV_DIR"
fi

# Prefer a non-framework Python for API process on macOS.
# Homebrew framework Python appears as Python.app and can add an extra Dock icon.
if [ -x "$HOME/Documents/software/miniconda3/bin/python3" ]; then
    API_PYTHON_CMD="$HOME/Documents/software/miniconda3/bin/python3"
fi

# Find Flutter
FLUTTER_BIN=""
if [ -n "$FLUTTER_ROOT" ]; then
    FLUTTER_BIN="$FLUTTER_ROOT/bin/flutter"
elif [ -f "$HOME/development/flutter/bin/flutter" ]; then
    FLUTTER_BIN="$HOME/development/flutter/bin/flutter"
elif [ -f "$HOME/Documents/project_code/flutter/bin/flutter" ]; then
    FLUTTER_BIN="$HOME/Documents/project_code/flutter/bin/flutter"
else
    FLUTTER_BIN="$(which flutter 2>/dev/null)"
fi

if [ ! -f "$FLUTTER_BIN" ]; then
    print_error "Flutter not found at: $FLUTTER_BIN"
    print_info "Set FLUTTER_ROOT or add Flutter to PATH"
    exit 1
fi

# Show system info
echo -e "${GRAY}Python:${NC}   $(python3 --version 2>&1 | head -1)"
echo -e "${GRAY}Flutter:${NC}  $FLUTTER_BIN"
echo -e "${GRAY}VEnv:${NC}     $VENV_DIR (${VENV_BIN:-system})"
echo -e "${GRAY}API Py:${NC}   $API_PYTHON_CMD"

# Step 1: Start API Backend
print_step "1/3" "Starting API Backend"
cd "$PROJECT_ROOT"

# Activate virtual environment
if [ -n "$VENV_DIR" ]; then
    source $VENV_BIN
    print_info "Virtual environment: $VENV_DIR"
fi

# Avoid duplicate Flutter instances (main reason for multiple Dock icons)
EXISTING_APP_PIDS="$(pgrep -f 'memscreen_flutter.app/Contents/MacOS/memscreen_flutter' || true)"
if [ -n "$EXISTING_APP_PIDS" ]; then
    print_info "Stopping existing MemScreen app instances" "$EXISTING_APP_PIDS"
    kill $EXISTING_APP_PIDS 2>/dev/null || true
    sleep 1
fi

# Clean up stale flutter tooling runners left by previous `flutter run` sessions.
STALE_FLUTTER_RUN_PIDS="$(pgrep -f 'flutter_tools.snapshot run -d macos --release' || true)"
if [ -n "$STALE_FLUTTER_RUN_PIDS" ]; then
    print_info "Stopping stale Flutter runner processes" "$STALE_FLUTTER_RUN_PIDS"
    kill $STALE_FLUTTER_RUN_PIDS 2>/dev/null || true
    sleep 1
fi

# Avoid Kivy/floating-ball interference from legacy process instances.
KIVY_PIDS="$(pgrep -f 'memscreen/ui/kivy_app.py|memscreen-ui|setup/start.py' || true)"
if [ -n "$KIVY_PIDS" ]; then
    print_info "Stopping possible Kivy/legacy UI processes" "$KIVY_PIDS"
    kill $KIVY_PIDS 2>/dev/null || true
    sleep 1
fi

# Clean stale trigger files used by Kivy floating-ball IPC.
MEMSCREEN_HOME="$HOME/.memscreen"
for trigger_file in switch_screen.txt region_trigger.txt recording_trigger.txt; do
    if [ -f "$MEMSCREEN_HOME/$trigger_file" ]; then
        rm -f "$MEMSCREEN_HOME/$trigger_file" 2>/dev/null || true
    fi
done

# Start API backend in background (NO Kivy UI) only when not already running
if curl -s http://127.0.0.1:8765/health > /dev/null 2>&1; then
    print_info "API already running" "Reusing http://127.0.0.1:8765"
else
    API_PYTHONPATH="$PROJECT_ROOT/memscreen"
    if [ -n "$VENV_DIR" ]; then
        for site_pkg in "$PROJECT_ROOT/$VENV_DIR"/lib/python*/site-packages; do
            if [ -d "$site_pkg" ]; then
                API_PYTHONPATH="$API_PYTHONPATH:$site_pkg"
                break
            fi
        done
    fi

    PYTHONPATH="$API_PYTHONPATH" "$API_PYTHON_CMD" setup/start_api_only.py &
    API_PID=$!
    API_STARTED_BY_SCRIPT=1
    print_info "API PID: $API_PID"

    # Wait for API to start
    echo -e "   ${GRAY}Waiting for API to be ready...${NC}"
    sleep 3
fi

# Check API health
MAX_RETRIES=5
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://127.0.0.1:8765/health > /dev/null 2>&1; then
        print_step "2/3" "API is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    print_error "API failed to start after $MAX_RETRIES attempts"
    cleanup
    exit 1
fi

echo ""
print_step "2/3" "API Backend running at ${GREEN}http://127.0.0.1:8765${NC}"

# Step 2: Build and start Flutter Frontend
print_step "3/3" "Starting Flutter Frontend"
sleep 3  # Wait for API to be fully ready

# Install dependencies
print_info "Installing Flutter dependencies..."
(cd frontend/flutter && $FLUTTER_BIN pub get > /dev/null 2>&1)
echo ""

print_info "Building Flutter macOS app"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Build and run app binary directly.
# This avoids leftover flutter tooling processes that can keep API alive after app quit.
cd frontend/flutter
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export PATH="/Users/jixiangluo/.gem/ruby/3.4.0/bin:$PATH"
$FLUTTER_BIN build macos --release > /dev/null

APP_BIN="$PROJECT_ROOT/frontend/flutter/build/macos/Build/Products/Release/memscreen_flutter.app/Contents/MacOS/memscreen_flutter"
if [ ! -x "$APP_BIN" ]; then
    print_error "Built app not found or not executable" "$APP_BIN"
    exit 1
fi

"$APP_BIN" &
APP_PID=$!
cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}Flutter app started!${NC}"
print_info "App PID: $APP_PID"

echo ""
echo -e "${BLUE}💬 Press Ctrl+C in this terminal to stop${NC}"

echo ""
echo -e "${GRAY}API: http://127.0.0.1:8765${NC}"
echo -e "${GRAY}Logs: ~/.memscreen/logs/${NC}"

echo ""
echo -e "${BLUE}💡 Tip: Create an alias for easier startup:${NC}"
echo -e "${GRAY}  echo 'alias flutter=\"$(dirname \"$0\")/start_flutter.sh\"' >> ~/.bashrc  # or ~/.zshrc"

echo ""

# Keep both processes running and monitor app exit
# When app exits, also shut down API
while kill -0 $APP_PID 2>/dev/null; do
    sleep 1
done

echo ""
echo -e "${YELLOW}🛑 App exited, shutting down API...${NC}"

# Kill API process when Flutter exits
if [ "$API_STARTED_BY_SCRIPT" = "1" ] && [ -n "${API_PID:-}" ]; then
    kill $API_PID 2>/dev/null || true
fi

# Wait for API to fully shutdown
if [ "$API_STARTED_BY_SCRIPT" = "1" ] && [ -n "${API_PID:-}" ]; then
    wait $API_PID 2>/dev/null || true
fi

echo -e "${GREEN}✓ All processes stopped${NC}"
