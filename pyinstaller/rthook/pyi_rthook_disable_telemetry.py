"""
Runtime hook to disable MemScreen telemetry before import.
"""
import os

# Disable MemScreen telemetry to prevent network hangs during initialization
os.environ['memscreen_TELEMETRY'] = 'False'
