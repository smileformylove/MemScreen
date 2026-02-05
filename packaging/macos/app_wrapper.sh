#!/bin/bash
# MemScreen launcher wrapper
# Launches the bundled app and ensures it activates as foreground application

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Launch the actual executable in the background
"$SCRIPT_DIR/MemScreen.bin" &

# Get the PID of the background process
APP_PID=$!

# Wait a moment for the app to start
sleep 2

# Activate the app using AppleScript
osascript -e "tell application \"MemScreen\" to activate" 2>/dev/null || true

# Wait for the background process
wait $APP_PID
