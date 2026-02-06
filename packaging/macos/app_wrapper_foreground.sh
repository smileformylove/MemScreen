#!/bin/bash
# MemScreen launcher wrapper
# This script ensures the app activates properly on macOS

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Launch the actual executable
# Do NOT use exec - we need to stay alive to activate the window
"$SCRIPT_DIR/MemScreen.bin" &
APP_PID=$!

# Wait for the app to fully initialize
# macOS needs time for the window to be created and registered
sleep 2

# Force activate using multiple methods
# Method 1: Direct app name activation
osascript -e 'tell application "MemScreen" to activate' 2>/dev/null || true

# Method 2: Bundle ID activation
osascript -e 'tell application id "com.smileformylove.MemScreen" to activate' 2>/dev/null || true

# Method 3: System Events force to front
osascript -e 'tell application "System Events" to set frontmost of every process whose bundle identifier is "com.smileformylove.MemScreen" to true' 2>/dev/null || true

# Additional activation attempts with delays
sleep 1
osascript -e 'tell application "MemScreen" to activate' 2>/dev/null || true

sleep 1
osascript -e 'tell application "MemScreen" to activate' 2>/dev/null || true

# Wait for the app to finish
wait $APP_PID
