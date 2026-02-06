#!/bin/bash
# Launch MemScreen.app and test recording functionality

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_PATH="$SCRIPT_DIR/../../dist/MemScreen.app"

echo "Launching MemScreen.app..."
echo "Path: $APP_PATH"

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: MemScreen.app not found at $APP_PATH"
    exit 1
fi

# Open the app
open "$APP_PATH"

echo ""
echo "App launched! Please test the recording functionality:"
echo "1. Click on the Recording tab"
echo "2. Check if preview is displayed"
echo "3. Try clicking 'Start Recording'"
echo ""
