#!/bin/bash
### MemScreen Quick Launcher ###
# This is a convenience wrapper for the main launcher in bin/

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
exec "$SCRIPT_DIR/bin/run_ui.sh" "$@"
