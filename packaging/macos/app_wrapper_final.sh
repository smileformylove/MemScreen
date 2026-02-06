#!/bin/bash
# MemScreen launcher wrapper - macOS activation fix

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start activation helper in background (only once)
(
    sleep 3
    for i in {1..5}; do
        osascript -e 'tell application "MemScreen" to activate' 2>/dev/null || true
        sleep 1
    done
) &

# Replace this process with the app (important for macOS)
exec "$SCRIPT_DIR/MemScreen.bin"
