#!/bin/bash
# MemScreen launcher wrapper
# Launches the bundled app and activates it as foreground application

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Launch the actual executable
# Use exec to replace this shell process with the Python app
exec "$SCRIPT_DIR/MemScreen.bin"
