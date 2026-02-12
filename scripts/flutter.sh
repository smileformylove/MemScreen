#!/bin/bash
# MemScreen Flutter - Quick Start Script
# Starts API backend + Flutter frontend (NO Kivy UI)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

PYTHON_CMD="python3"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  MemScreen Flutter${NC}"
echo -e "${BLUE}  AI-Powered Visual Memory System${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Start API only (no Kivy UI)
cd "$PROJECT_ROOT" && PYTHONPATH="$PROJECT_ROOT/memscreen" $PYTHON_CMD setup/start_api_only.py &
sleep 3 && echo "   ${GREEN}✓${NC} API Backend started"

# Wait for API and start Flutter
sleep 3
cd "$PROJECT_ROOT/frontend/flutter" && /Users/jixiangluo/development/flutter/bin/flutter run -d macos

echo ""
echo -e "${GREEN}Flutter app should now be running with floating ball only!${NC}"
echo -e "${BLUE}API:${NC} http://127.0.0.1:8765"
echo -e "${BLUE}Logs:${NC} ~/.memscreen/logs"
