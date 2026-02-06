#!/bin/bash
# MemScreen launcher wrapper
# This script ensures the app activates properly on macOS

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Launch activation in background after a delay
(sleep 3 && osascript -e 'tell application "MemScreen" to activate' 2>/dev/null) &
(sleep 4 && osascript -e 'tell application "MemScreen" to activate' 2>/dev/null) &

# Launch and replace the current process with the app
# This is important for macOS to recognize the app as foreground
exec "$SCRIPT_DIR/MemScreen.bin"
