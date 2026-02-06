#!/bin/bash
################################################################################
# MemScreen macOS Launch Script
#
# This script launches MemScreen and ensures it activates properly on macOS.
# It works around macOS app activation timing issues by:
# 1. Launching the app in the background
# 2. Waiting for it to fully initialize
# 3. Force-activating it using osascript
################################################################################

set -e

# App path
APP_PATH="$1"

# If no argument provided, try to find the app
if [ -z "$APP_PATH" ]; then
    # Check if app is in /Applications
    if [ -d "/Applications/MemScreen.app" ]; then
        APP_PATH="/Applications/MemScreen.app"
    # Check if app is in dist (development build)
    elif [ -d "dist/MemScreen.app" ]; then
        APP_PATH="dist/MemScreen.app"
    else
        echo "❌ Cannot find MemScreen.app"
        echo "   Please specify path: $0 /path/to/MemScreen.app"
        exit 1
    fi
fi

echo "🚀 Launching MemScreen..."
echo "   Location: $APP_PATH"

# Launch the app in the background
open "$APP_PATH"

# Wait for app to fully initialize (window creation)
echo "⏳ Waiting for app to initialize..."
sleep 2

# Force activate the app using multiple methods
echo "✨ Activating app..."

# Method 1: Direct activation by app name
osascript -e 'tell application "MemScreen" to activate' 2>/dev/null || true

# Method 2: Activation by bundle ID
osascript -e 'tell application id "com.smileformylove.MemScreen" to activate' 2>/dev/null || true

# Method 3: Force to front using System Events
osascript -e 'tell application "System Events" to set frontmost of every process whose bundle identifier is "com.smileformylove.MemScreen" to true' 2>/dev/null || true

# Additional activation attempts with delays
for i in {1..3}; do
    sleep 1
    osascript -e 'tell application "MemScreen" to activate' 2>/dev/null || true
done

echo "✅ MemScreen launched!"
